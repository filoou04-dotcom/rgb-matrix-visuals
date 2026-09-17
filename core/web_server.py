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
        self.mode = "cycle"
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
        status_text = "Stabil"
        status_level = "ok"

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
                status_text = "Unterspannung aktiv (<4.65V)"
                status_level = "error"
            elif throttled_now:
                status_text = "CPU gedrosselt (Temperatur/Spannung)"
                status_level = "warning"
            elif undervoltage_past:
                status_text = "Unterspannung in Historie registriert"
                status_level = "warning"
            else:
                status_text = "Normalbetrieb"
                status_level = "ok"
        except Exception:
            pass

        uptime_sec = int(time.time() - self.start_time)
        m, s = divmod(uptime_sec, 60)
        h, m = divmod(m, 60)
        uptime_str = f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"

        return {
            "temp": temp,
            "throttled_hex": throttled_hex,
            "undervoltage_now": undervoltage_now,
            "undervoltage_past": undervoltage_past,
            "throttled_now": throttled_now,
            "status_text": status_text,
            "status_level": status_level,
            "uptime": uptime_str
        }

HTML_DASHBOARD = """<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>RGB Matrix Controller</title>
    <style>
        :root {
            --bg: #09090b;
            --surface: #121215;
            --surface-elevated: #18181b;
            --border: #27272a;
            --border-hover: #3f3f46;
            --text-primary: #f4f4f5;
            --text-secondary: #a1a1aa;
            --text-tertiary: #71717a;
            --accent: #ffffff;
            --success: #10b981;
            --warning: #f59e0b;
            --error: #ef4444;
            --font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Inter", sans-serif;
            --font-mono: ui-monospace, "SF Mono", "Roboto Mono", Menlo, Consolas, monospace;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            -webkit-tap-highlight-color: transparent;
        }

        body {
            background-color: var(--bg);
            color: var(--text-primary);
            font-family: var(--font-sans);
            font-size: 13px;
            line-height: 1.5;
            padding: 24px 16px;
            display: flex;
            justify-content: center;
            min-height: 100vh;
            -webkit-font-smoothing: antialiased;
        }

        .container {
            width: 100%;
            max-width: 440px;
            display: flex;
            flex-direction: column;
            gap: 16px;
        }

        /* Header */
        header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-bottom: 12px;
            border-bottom: 1px solid var(--border);
        }

        .header-title {
            font-size: 13px;
            font-weight: 600;
            letter-spacing: 0.04em;
            text-transform: uppercase;
            color: var(--text-primary);
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .header-status-dot {
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background-color: var(--success);
        }

        .header-meta {
            font-family: var(--font-mono);
            font-size: 11px;
            color: var(--text-tertiary);
            letter-spacing: 0.02em;
        }

        /* Card Component */
        .card {
            background-color: var(--surface);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 14px 16px;
        }

        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
        }

        .card-label {
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            color: var(--text-tertiary);
        }

        .card-badge {
            font-family: var(--font-mono);
            font-size: 11px;
            color: var(--text-secondary);
        }

        /* Metrics Grid */
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 12px;
        }

        .metric-block {
            display: flex;
            flex-direction: column;
            gap: 2px;
        }

        .metric-label {
            font-size: 11px;
            color: var(--text-tertiary);
        }

        .metric-value {
            font-family: var(--font-mono);
            font-size: 18px;
            font-weight: 500;
            color: var(--text-primary);
            letter-spacing: -0.02em;
        }

        .metric-value.unit {
            font-size: 12px;
            color: var(--text-secondary);
            font-weight: 400;
            margin-left: 2px;
        }

        .status-row {
            margin-top: 12px;
            padding-top: 10px;
            border-top: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .status-indicator {
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 12px;
            color: var(--text-secondary);
        }

        .status-dot {
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background-color: var(--success);
        }

        .status-dot.ok { background-color: var(--success); }
        .status-dot.warning { background-color: var(--warning); }
        .status-dot.error { background-color: var(--error); }

        /* Segmented Button Group (Effect Selection) */
        .segmented-control {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 4px;
            background-color: var(--surface-elevated);
            padding: 3px;
            border-radius: 6px;
            border: 1px solid var(--border);
        }

        .segment-btn {
            background: transparent;
            border: none;
            color: var(--text-secondary);
            padding: 7px 0;
            font-family: var(--font-sans);
            font-size: 12px;
            font-weight: 500;
            border-radius: 4px;
            cursor: pointer;
            text-align: center;
            transition: all 0.15s ease;
        }

        .segment-btn:hover {
            color: var(--text-primary);
        }

        .segment-btn.active {
            background-color: var(--border);
            color: var(--text-primary);
            font-weight: 600;
        }

        /* Range Slider */
        .slider-container {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .slider-meta {
            display: flex;
            justify-content: space-between;
            align-items: baseline;
        }

        .slider-value-display {
            font-family: var(--font-mono);
            font-size: 15px;
            font-weight: 500;
            color: var(--text-primary);
        }

        input[type="range"] {
            -webkit-appearance: none;
            appearance: none;
            width: 100%;
            height: 4px;
            border-radius: 2px;
            background-color: var(--border);
            outline: none;
            cursor: pointer;
        }

        input[type="range"]::-webkit-slider-thumb {
            -webkit-appearance: none;
            appearance: none;
            width: 14px;
            height: 14px;
            border-radius: 50%;
            background-color: var(--text-primary);
            border: 1px solid var(--border-hover);
            cursor: pointer;
            transition: transform 0.1s ease;
        }

        input[type="range"]::-webkit-slider-thumb:hover {
            transform: scale(1.15);
        }

        /* Preset Buttons */
        .preset-row {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 6px;
        }

        .preset-btn {
            background-color: var(--surface-elevated);
            border: 1px solid var(--border);
            color: var(--text-secondary);
            font-family: var(--font-mono);
            font-size: 11px;
            padding: 6px 0;
            border-radius: 4px;
            cursor: pointer;
            transition: border-color 0.15s ease, color 0.15s ease;
            text-align: center;
        }

        .preset-btn:hover {
            border-color: var(--border-hover);
            color: var(--text-primary);
        }

        /* Output / Power Toggle Row */
        .toggle-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .toggle-text {
            display: flex;
            flex-direction: column;
            gap: 2px;
        }

        .toggle-title {
            font-size: 13px;
            font-weight: 500;
            color: var(--text-primary);
        }

        .toggle-subtitle {
            font-size: 11px;
            color: var(--text-tertiary);
        }

        .btn-toggle {
            background-color: var(--surface-elevated);
            border: 1px solid var(--border);
            color: var(--text-primary);
            font-family: var(--font-sans);
            font-size: 12px;
            font-weight: 500;
            padding: 6px 14px;
            border-radius: 4px;
            cursor: pointer;
            transition: all 0.15s ease;
        }

        .btn-toggle:hover {
            border-color: var(--border-hover);
        }

        .btn-toggle.state-off {
            color: var(--text-tertiary);
            background-color: transparent;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <div class="header-title">
                <span class="header-status-dot" id="header-dot"></span>
                Matrix Controller
            </div>
            <div class="header-meta">64x32 HUB75-D</div>
        </header>

        <!-- System Metrics -->
        <div class="card">
            <div class="card-header">
                <span class="card-label">Telemetrie</span>
                <span class="card-badge" id="uptime-val">00:00</span>
            </div>
            <div class="metrics-grid">
                <div class="metric-block">
                    <span class="metric-label">CPU Temperatur</span>
                    <div>
                        <span class="metric-value" id="temp-val">--</span>
                        <span class="metric-value unit">&deg;C</span>
                    </div>
                </div>
                <div class="metric-block">
                    <span class="metric-label">Bildrate</span>
                    <div>
                        <span class="metric-value" id="fps-val">--</span>
                        <span class="metric-value unit">FPS</span>
                    </div>
                </div>
            </div>
            <div class="status-row">
                <div class="status-indicator">
                    <span class="status-dot" id="status-dot"></span>
                    <span id="status-text">Pr&uuml;fe System...</span>
                </div>
                <div class="card-badge" id="throttle-hex">0x0</div>
            </div>
        </div>

        <!-- Animation Mode Selection -->
        <div class="card">
            <div class="card-header">
                <span class="card-label">Visualisierung</span>
                <span class="card-badge" id="mode-badge">Zyklus</span>
            </div>
            <div class="segmented-control">
                <button class="segment-btn active" id="btn-cycle" onclick="setEffect('cycle')">Auto</button>
                <button class="segment-btn" id="btn-plasma" onclick="setEffect('plasma')">Plasma</button>
                <button class="segment-btn" id="btn-metaballs" onclick="setEffect('metaballs')">Metaballs</button>
                <button class="segment-btn" id="btn-waves" onclick="setEffect('waves')">Waves</button>
            </div>
        </div>

        <!-- Brightness Slider -->
        <div class="card">
            <div class="slider-container">
                <div class="slider-meta">
                    <span class="card-label">Helligkeit</span>
                    <span class="slider-value-display" id="bright-val">65%</span>
                </div>
                <input type="range" id="bright-slider" min="5" max="100" value="65"
                       oninput="onSliderInput(this.value)"
                       onchange="sendBrightness(this.value)">
                <div class="preset-row">
                    <button class="preset-btn" onclick="applyPreset(25)">25%</button>
                    <button class="preset-btn" onclick="applyPreset(50)">50%</button>
                    <button class="preset-btn" onclick="applyPreset(75)">75%</button>
                    <button class="preset-btn" onclick="applyPreset(100)">100%</button>
                </div>
            </div>
        </div>

        <!-- Output / Power State -->
        <div class="card">
            <div class="toggle-row">
                <div class="toggle-text">
                    <span class="toggle-title">Ausgabe</span>
                    <span class="toggle-subtitle" id="power-subtitle">Matrix aktiv</span>
                </div>
                <button class="btn-toggle" id="power-btn" onclick="togglePower()">Aktiv</button>
            </div>
        </div>
    </div>

    <script>
        let isDragging = false;
        let isActive = true;
        let debounceTimer = null;

        async function updateStatus() {
            try {
                const res = await fetch("/api/status");
                if (!res.ok) return;
                const data = await res.json();

                document.getElementById("temp-val").textContent = data.temp;
                document.getElementById("fps-val").textContent = Math.round(data.measured_fps);
                document.getElementById("uptime-val").textContent = data.uptime;
                document.getElementById("throttle-hex").textContent = data.throttled_hex;

                // Status text and indicator
                const statusDot = document.getElementById("status-dot");
                const statusText = document.getElementById("status-text");
                statusText.textContent = data.status_text;
                statusDot.className = "status-dot " + (data.status_level || "ok");

                // Brightness slider update if not dragging
                if (!isDragging) {
                    document.getElementById("bright-val").textContent = data.brightness + "%";
                    document.getElementById("bright-slider").value = data.brightness;
                }

                // Effect selection state
                document.querySelectorAll(".segment-btn").forEach(btn => btn.classList.remove("active"));
                if (data.mode === "cycle") {
                    document.getElementById("btn-cycle").classList.add("active");
                    document.getElementById("mode-badge").textContent = "Auto (" + data.effect + ")";
                } else {
                    const btn = document.getElementById("btn-" + data.effect);
                    if (btn) btn.classList.add("active");
                    document.getElementById("mode-badge").textContent = data.effect;
                }

                // Power state
                isActive = data.active;
                const powerBtn = document.getElementById("power-btn");
                const powerSub = document.getElementById("power-subtitle");
                const headerDot = document.getElementById("header-dot");
                if (data.active) {
                    powerBtn.className = "btn-toggle";
                    powerBtn.textContent = "Aktiv";
                    powerSub.textContent = "Matrix aktiv";
                    headerDot.style.backgroundColor = "var(--success)";
                } else {
                    powerBtn.className = "btn-toggle state-off";
                    powerBtn.textContent = "Standby";
                    powerSub.textContent = "Panel dunkel";
                    headerDot.style.backgroundColor = "var(--text-tertiary)";
                }
            } catch (e) {
                console.error("Telemetry update error:", e);
            }
        }

        function onSliderInput(val) {
            isDragging = true;
            document.getElementById("bright-val").textContent = val + "%";
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => sendBrightness(val), 80);
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
            document.getElementById("bright-val").textContent = val + "%";
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
        if self.path in ("/", "/index.html"):
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
                self.wfile.write(b'{"status":"ok"}')
            except Exception as e:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(str(e).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass

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
