import json
import os
import time
import socket
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

class EngineState:
    def __init__(self):
        self.lock = threading.Lock()
        self.current_effect = "plasma"
        self.mode = "cycle"  # "cycle" or "manual"
        self.target_effect = None
        self.brightness = 65
        self.fps = 50.0
        self.measured_fps = 50.0
        self.active = True
        self.effects = ["plasma", "metaballs", "waves"]
        self.cycle_time = 20.0
        self.start_time = time.time()

    def set_effect(self, effect_name):
        with self.lock:
            if effect_name == "cycle":
                self.mode = "cycle"
            elif effect_name in self.effects:
                self.mode = "manual"
                self.target_effect = effect_name

    def set_brightness(self, val):
        with self.lock:
            self.brightness = max(5, min(100, int(val)))

    def set_active(self, is_active):
        with self.lock:
            self.active = bool(is_active)

    def get_hardware_stats(self):
        temp = 0.0
        try:
            with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                temp = round(int(f.read().strip()) / 1000.0, 1)
        except Exception:
            temp = 0.0

        throttled_hex = "0x0"
        undervoltage_now = False
        undervoltage_past = False
        throttled_now = False
        status_text = "Optimal"
        status_color = "#00e676"

        try:
            import subprocess
            out = subprocess.check_output(["vcgencmd", "get_throttled"], text=True).strip()
            val_str = out.split("=")[-1]
            throttled_hex = val_str
            val = int(val_str, 16)
            
            undervoltage_now = bool(val & 0x1)
            throttled_now = bool(val & 0x4)
            undervoltage_past = bool(val & 0x10000)

            if undervoltage_now:
                status_text = "Warnung: Unterspannung JETZT aktiv (<4.65V)!"
                status_color = "#ff1744"
            elif throttled_now:
                status_text = "Warnung: CPU gedrosselt (Hitze/Strom)!"
                status_color = "#ff9100"
            elif undervoltage_past:
                status_text = "Normalbetrieb (Fruehere Unterspannung registriert)"
                status_color = "#ffd600"
            else:
                status_text = "Systemzustand stabil"
                status_color = "#00e676"
        except Exception:
            pass

        uptime_sec = int(time.time() - self.start_time)
        m, s = divmod(uptime_sec, 60)
        h, m = divmod(m, 60)
        uptime_str = f"{h}h {m}m {s}s" if h else f"{m}m {s}s"

        return {
            "temp": temp,
            "throttled_hex": throttled_hex,
            "undervoltage_now": undervoltage_now,
            "undervoltage_past": undervoltage_past,
            "throttled_now": throttled_now,
            "status_text": status_text,
            "status_color": status_color,
            "uptime": uptime_str
        }

HTML_DASHBOARD = """<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>RGB LED Matrix Controller</title>
    <style>
        :root {
            --bg: #0b0f19;
            --card-bg: #151b2b;
            --card-border: #232d42;
            --accent: #00f0ff;
            --accent-glow: rgba(0, 240, 255, 0.35);
            --text: #f0f6fc;
            --text-muted: #8b9bb4;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; -webkit-tap-highlight-color: transparent; }
        body { background: var(--bg); color: var(--text); padding: 16px; display: flex; justify-content: center; min-height: 100vh; }
        .container { width: 100%; max-width: 520px; display: flex; flex-direction: column; gap: 16px; }
        
        header { display: flex; justify-content: space-between; align-items: center; padding-bottom: 12px; border-bottom: 1px solid var(--card-border); }
        .title-area { display: flex; align-items: center; gap: 8px; }
        .dot { width: 10px; height: 10px; border-radius: 50%; background: #00e676; box-shadow: 0 0 10px #00e676; }
        h1 { font-size: 1.2rem; font-weight: 700; letter-spacing: 0.5px; }
        .badge { background: #1e2638; border: 1px solid var(--card-border); padding: 4px 10px; border-radius: 20px; font-size: 0.75rem; color: var(--accent); font-weight: 600; }

        .card { background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 16px; padding: 18px; box-shadow: 0 4px 20px rgba(0,0,0,0.3); }
        .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
        
        .stat-label { font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; font-weight: 600; margin-bottom: 4px; }
        .stat-value { font-size: 1.5rem; font-weight: 800; color: #fff; }
        .status-pill { display: inline-block; padding: 6px 12px; border-radius: 10px; font-size: 0.8rem; font-weight: 600; margin-top: 6px; width: 100%; text-align: center; }

        .section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; }
        .section-title { font-size: 0.85rem; font-weight: 700; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.8px; }
        
        /* Effect Buttons */
        .btn-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; }
        .effect-btn { background: #1b2234; color: var(--text); border: 1px solid var(--card-border); padding: 14px 10px; border-radius: 12px; font-size: 0.95rem; font-weight: 600; cursor: pointer; transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1); display: flex; align-items: center; justify-content: center; gap: 8px; }
        .effect-btn:active { transform: scale(0.98); }
        .effect-btn.active { background: var(--accent); color: #000; border-color: var(--accent); box-shadow: 0 0 16px var(--accent-glow); font-weight: 700; }

        /* Brightness Slider & Presets */
        .brightness-val { font-size: 1.3rem; font-weight: 800; color: var(--accent); }
        .slider-wrap { margin: 12px 0 16px 0; }
        input[type="range"] { width: 100%; height: 8px; border-radius: 4px; background: #232d42; outline: none; -webkit-appearance: none; accent-color: var(--accent); cursor: pointer; }
        input[type="range"]::-webkit-slider-thumb { -webkit-appearance: none; width: 22px; height: 22px; border-radius: 50%; background: var(--accent); box-shadow: 0 0 12px var(--accent); cursor: pointer; }

        .presets { display: flex; gap: 8px; justify-content: space-between; }
        .preset-btn { flex: 1; background: #1b2234; border: 1px solid var(--card-border); color: var(--text-muted); padding: 8px 4px; border-radius: 8px; font-size: 0.8rem; font-weight: 600; cursor: pointer; transition: 0.2s; }
        .preset-btn:hover { color: #fff; border-color: var(--accent); }

        /* Power Switch */
        .switch-row { display: flex; justify-content: space-between; align-items: center; margin-top: 4px; }
        .power-btn { background: #1b2234; color: #fff; border: 1px solid var(--card-border); padding: 10px 18px; border-radius: 10px; font-weight: 700; font-size: 0.9rem; cursor: pointer; transition: 0.2s; display: flex; align-items: center; gap: 8px; }
        .power-btn.on { background: #1b4b35; border-color: #00e676; color: #00e676; }
        .power-btn.off { background: #4b1b1b; border-color: #ff1744; color: #ff1744; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="title-area">
                <div class="dot" id="live-dot"></div>
                <h1>LED Matrix Control</h1>
            </div>
            <span class="badge">64x32 HUB75-D</span>
        </header>

        <!-- Live Hardware Stats -->
        <div class="card grid-2">
            <div>
                <div class="stat-label">CPU Temperatur</div>
                <div class="stat-value" id="temp-val">-- °C</div>
            </div>
            <div>
                <div class="stat-label">Matrix Refresh</div>
                <div class="stat-value" id="fps-val">-- FPS</div>
            </div>
            <div style="grid-column: span 2;">
                <div class="stat-label">Hardware-Status & Netzteil</div>
                <div id="status-pill" class="status-pill" style="background: #1b2234; color: #8b9bb4;">Verbinde mit Matrix...</div>
            </div>
        </div>

        <!-- Visuals Selection -->
        <div class="card">
            <div class="section-header">
                <span class="section-title">Animation W&auml;hlen</span>
                <span id="current-badge" style="font-size: 0.8rem; color: var(--accent); font-weight: 600;">--</span>
            </div>
            <div class="btn-grid">
                <button class="effect-btn" id="btn-cycle" onclick="setEffect(cycle)">
                    <span>&#128257;</span> Auto-Cycle
                </button>
                <button class="effect-btn" id="btn-plasma" onclick="setEffect(plasma)">
                    <span>&#127754;</span> Fluid Plasma
                </button>
                <button class="effect-btn" id="btn-metaballs" onclick="setEffect(metaballs)">
                    <span>&#129514;</span> Metaballs
                </button>
                <button class="effect-btn" id="btn-waves" onclick="setEffect(waves)">
                    <span>&#127752;</span> Fluid Waves
                </button>
            </div>
        </div>

        <!-- Brightness Slider & Presets -->
        <div class="card">
            <div class="section-header">
                <span class="section-title">LED Helligkeit</span>
                <span class="brightness-val" id="bright-val">65 %</span>
            </div>
            
            <div class="slider-wrap">
                <input type="range" id="bright-slider" min="5" max="100" value="65" 
                       oninput="onSliderDrag(this.value)" 
                       onchange="sendBrightness(this.value)">
            </div>

            <div class="presets">
                <button class="preset-btn" onclick="applyPreset(25)">25 %</button>
                <button class="preset-btn" onclick="applyPreset(50)">50 %</button>
                <button class="preset-btn" onclick="applyPreset(70)">70 %</button>
                <button class="preset-btn" onclick="applyPreset(100)">100 %</button>
            </div>
        </div>

        <!-- Power & Display State -->
        <div class="card">
            <div class="switch-row">
                <div>
                    <div class="stat-label">Display Zustand</div>
                    <div style="font-size: 0.95rem; font-weight: 600;" id="power-desc">Panel aktiv</div>
                </div>
                <button id="power-btn" class="power-btn on" onclick="togglePower()">
                    <span>&#9211;</span> AN
                </button>
            </div>
        </div>
    </div>

    <script>
        let isDragging = false;
        let isActive = true;
        let updateTimer = null;

        async function updateStatus() {
            try {
                const res = await fetch("/api/status");
                if (!res.ok) return;
                const data = await res.json();
                
                document.getElementById("temp-val").innerText = data.temp + " °C";
                document.getElementById("fps-val").innerText = Math.round(data.measured_fps) + " FPS";
                
                const pill = document.getElementById("status-pill");
                pill.innerText = data.status_text;
                pill.style.background = data.status_color + "22";
                pill.style.color = data.status_color;
                pill.style.border = "1px solid " + data.status_color + "66";

                if (!isDragging) {
                    document.getElementById("bright-val").innerText = data.brightness + " %";
                    document.getElementById("bright-slider").value = data.brightness;
                }

                // Badges and buttons
                document.querySelectorAll(".effect-btn").forEach(b => b.classList.remove("active"));
                if (data.mode === "cycle") {
                    document.getElementById("btn-cycle").classList.add("active");
                    document.getElementById("current-badge").innerText = "Zyklus: " + data.effect.toUpperCase();
                } else if (document.getElementById("btn-" + data.effect)) {
                    document.getElementById("btn-" + data.effect).classList.add("active");
                    document.getElementById("current-badge").innerText = data.effect.toUpperCase();
                }

                // Power button
                isActive = data.active;
                const pBtn = document.getElementById("power-btn");
                const pDesc = document.getElementById("power-desc");
                if (data.active) {
                    pBtn.className = "power-btn on";
                    pBtn.innerHTML = "<span>&#9211;</span> AN";
                    pDesc.innerText = "Panel aktiv";
                } else {
                    pBtn.className = "power-btn off";
                    pBtn.innerHTML = "<span>&#9211;</span> AUS";
                    pDesc.innerText = "Panel dunkel (Standby)";
                }
            } catch (e) {
                console.error(e);
            }
        }

        function onSliderDrag(val) {
            isDragging = true;
            document.getElementById("bright-val").innerText = val + " %";
            // Debounced send while dragging
            clearTimeout(updateTimer);
            updateTimer = setTimeout(() => sendBrightness(val), 100);
        }

        async function sendBrightness(val) {
            isDragging = false;
            await fetch("/api/control", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ brightness: parseInt(val) })
            });
        }

        function applyPreset(val) {
            document.getElementById("bright-slider").value = val;
            document.getElementById("bright-val").innerText = val + " %";
            sendBrightness(val);
        }

        async function setEffect(name) {
            await fetch("/api/control", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ effect: name })
            });
            updateStatus();
        }

        async function togglePower() {
            await fetch("/api/control", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ active: !isActive })
            });
            updateStatus();
        }

        setInterval(updateStatus, 1500);
        updateStatus();
    </script>
</body>
</html>
"""

class MatrixRequestHandler(BaseHTTPRequestHandler):
    state: EngineState = None

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_DASHBOARD.encode("utf-8"))
        elif self.path == "/api/status":
            stats = self.state.get_hardware_stats()
            with self.state.lock:
                payload = {
                    "effect": self.state.current_effect,
                    "mode": self.state.mode,
                    "brightness": self.state.brightness,
                    "fps": self.state.fps,
                    "measured_fps": self.state.measured_fps,
                    "active": self.state.active,
                    "effects": self.state.effects,
                    **stats
                }
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(payload).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/api/control":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            try:
                data = json.loads(body.decode("utf-8"))
                if "effect" in data:
                    self.state.set_effect(data["effect"])
                if "brightness" in data:
                    self.state.set_brightness(data["brightness"])
                if "active" in data:
                    self.state.set_active(data["active"])
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b"{\"status\":\"ok\"}")
            except Exception as e:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(str(e).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # Suppress console spam to keep stdout clean

def start_web_server(engine_state, port=80):
    handler = MatrixRequestHandler
    handler.state = engine_state
    
    server = None
    for p in [port, 8080]:
        try:
            server = HTTPServer(("0.0.0.0", p), handler)
            print(f"[INFO] Web Dashboard active at: http://0.0.0.0:{p}")
            break
        except Exception as e:
            if p == port:
                continue
            print(f"[WARN] Could not bind web server to port {p}: {e}")

    if server:
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        return server
    return None
