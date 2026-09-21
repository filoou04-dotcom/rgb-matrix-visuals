import os
import io
import time
import math
import json
import logging
import threading
import urllib.request
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
from .base import VisualEffect

logger = logging.getLogger(__name__)

CACHE_DIR = "/home/mini/rgb-matrix-visuals/assets/cam_cache"

# Tiny 5x3 pixel-art font for location tags
FONT_5X3 = {
    "D": [[1, 1, 0], [1, 0, 1], [1, 0, 1], [1, 0, 1], [1, 1, 0]],
    "O": [[1, 1, 1], [1, 0, 1], [1, 0, 1], [1, 0, 1], [1, 1, 1]],
    "M": [[1, 0, 1], [1, 1, 1], [1, 0, 1], [1, 0, 1], [1, 0, 1]],
    "R": [[1, 1, 0], [1, 0, 1], [1, 1, 0], [1, 0, 1], [1, 0, 1]],
    "K": [[1, 0, 1], [1, 1, 0], [1, 0, 0], [1, 1, 0], [1, 0, 1]],
    "H": [[1, 0, 1], [1, 0, 1], [1, 1, 1], [1, 0, 1], [1, 0, 1]],
    "N": [[1, 0, 1], [1, 1, 1], [1, 1, 1], [1, 0, 1], [1, 0, 1]],
}

class LiveCamWorker(threading.Thread):
    """
    Asynchronous background worker fetching live webcam frames from Mainz.
    Runs completely decoupled from the 50 FPS matrix display loop.
    """
    def __init__(self, update_callback):
        super().__init__(daemon=True)
        self.update_callback = update_callback
        self.running = True
        self.last_dom_check = 0.0

    def fetch_image(self, url, timeout=8):
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read()
        return Image.open(io.BytesIO(data)).convert("RGB")

    def get_latest_dom_url(self):
        try:
            now = time.gmtime()
            year = str(now.tm_year)
            month = f"{now.tm_mon:02d}"
            day = f"{now.tm_mday:02d}"
            url = f"https://mainzer-dom-cam.de/resized/{year}/{month}/{day}/images.json"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=6) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            keys = sorted(data.keys())
            if keys:
                return f"https://mainzer-dom-cam.de/resized/{year}/{month}/{day}/{keys[-1]}.jpg"
        except Exception as e:
            logger.debug(f"Dom URL fetch error: {e}")
        return None

    def process_frame(self, img, cam_type):
        W, H = img.size
        crop_h = W // 2

        if cam_type == "dom":
            top = max(0, (H - crop_h) // 2)
            cropped = img.crop((0, top, W, min(H, top + crop_h)))
            sharp = cropped.filter(ImageFilter.UnsharpMask(radius=3, percent=220, threshold=2))
            c_boost, s_boost = 1.40, 1.35
        elif cam_type == "markt":
            top = max(0, int((H - crop_h) * 0.25))
            cropped = img.crop((0, top, W, min(H, top + crop_h)))
            sharp = cropped.filter(ImageFilter.UnsharpMask(radius=3, percent=200, threshold=2))
            c_boost, s_boost = 1.42, 1.35
        else:  # rhein
            top = max(0, int((H - crop_h) * 0.35))
            cropped = img.crop((0, top, W, min(H, top + crop_h)))
            sharp = cropped.filter(ImageFilter.UnsharpMask(radius=3, percent=200, threshold=2))
            c_boost, s_boost = 1.45, 1.40

        scaled = sharp.resize((64, 32), Image.Resampling.LANCZOS)
        enhanced = ImageEnhance.Contrast(scaled).enhance(c_boost)
        enhanced = ImageEnhance.Color(enhanced).enhance(s_boost)
        return np.array(enhanced, dtype=np.uint8)

    def run(self):
        try:
            os.makedirs(CACHE_DIR, exist_ok=True)
        except Exception as e:
            logger.debug(f"Cache dir warning: {e}")
        time.sleep(2.0)

        while self.running:
            # 1. Update Marktplatz (updates every 60s)
            try:
                img_markt = self.fetch_image("https://mzcam.kunden-mediamachine.de/markt/bild.jpg")
                arr_markt = self.process_frame(img_markt, "markt")
                self.update_callback(1, arr_markt, "markt")
            except Exception as e:
                logger.debug(f"Error fetching markt cam: {e}")

            time.sleep(4.0)

            # 2. Update Rheinpanorama (updates every 60s)
            try:
                img_rhein = self.fetch_image("https://mzcam.kunden-mediamachine.de/bastionvonschoenborn/bild.jpg")
                arr_rhein = self.process_frame(img_rhein, "rhein")
                self.update_callback(2, arr_rhein, "rhein")
            except Exception as e:
                logger.debug(f"Error fetching rhein cam: {e}")

            time.sleep(4.0)

            # 3. Update Dom Cam (updates every 10 min, poll every 3 min)
            now = time.time()
            if now - self.last_dom_check > 180.0:
                self.last_dom_check = now
                try:
                    dom_url = self.get_latest_dom_url()
                    if dom_url:
                        img_dom = self.fetch_image(dom_url)
                        arr_dom = self.process_frame(img_dom, "dom")
                        self.update_callback(0, arr_dom, "dom")
                except Exception as e:
                    logger.debug(f"Error fetching dom cam: {e}")

            time.sleep(25.0)


class MainzLiveCam(VisualEffect):
    """
    Live Public Webcams from Mainz (Programm 6).
    Cycles through 3 iconic locations with 64x32 smart crop:
    0: DOM - Mainzer Dom St. Martin (Erbacher Hof)
    1: MRK - Mainzer Marktplatz & Domportal
    2: RHN - Rheinpanorama & Theodor-Heuss-Bruecke
    Features active difference motion capture (highlighting moving cars/people),
    atmospheric water shimmer on the Rhine, and smooth crossfades.
    """

    def __init__(self, width=64, height=32, palette_manager=None, name="MainzLiveCam"):
        super().__init__(width, height, palette_manager, name=name)

        self.cam_names = ["DOM", "MRK", "RHN"]
        self.lock = threading.Lock()

        self.slot_dwell = 24.0
        self.slot_trans = 2.0
        self.slot_total = self.slot_dwell + self.slot_trans
        self.cam_timer = 0.0

        self.motion_maps = [np.zeros((32, 64), dtype=np.float32) for _ in range(3)]
        self.frames = [np.zeros((32, 64, 3), dtype=np.uint8) for _ in range(3)]
        self._load_cache()

        self.worker = LiveCamWorker(self._on_frame_update)
        self.worker.start()

    def _load_cache(self):
        cache_files = ["dom.npy", "markt.npy", "rhein.npy"]
        for idx, filename in enumerate(cache_files):
            filepath = os.path.join(CACHE_DIR, filename)
            if os.path.exists(filepath):
                try:
                    arr = np.load(filepath)
                    if arr.shape == (32, 64, 3):
                        self.frames[idx] = arr
                except Exception as e:
                    logger.debug(f"Failed loading cache {filepath}: {e}")

    def _on_frame_update(self, cam_idx, new_frame, cache_name):
        with self.lock:
            old_frame = self.frames[cam_idx]
            if old_frame is not None and old_frame.sum() > 0:
                diff = np.abs(new_frame.astype(np.float32) - old_frame.astype(np.float32)).mean(axis=2)
                motion_detected = diff > 15.0
                if np.any(motion_detected):
                    self.motion_maps[cam_idx][motion_detected] = np.clip(
                        diff[motion_detected] / 35.0, 0.45, 1.0
                    )

            self.frames[cam_idx] = new_frame
            try:
                np.save(os.path.join(CACHE_DIR, f"{cache_name}.npy"), new_frame)
            except Exception:
                pass

    def update(self, dt):
        super().update(dt)
        self.cam_timer += dt
        decay = math.pow(0.985, dt * 50.0)
        with self.lock:
            for m in self.motion_maps:
                m *= decay

    def _draw_badge(self, buf, text, opacity):
        if opacity <= 0.01:
            return
        cur_x = 2
        y0 = 2
        for ch in text:
            if ch in FONT_5X3:
                grid = FONT_5X3[ch]
                for r in range(5):
                    for c in range(3):
                        if grid[r][c]:
                            buf[min(31, y0 + r + 1), min(63, cur_x + c + 1)] = [0, 0, 0]
                            col = int(255 * opacity)
                            buf[y0 + r, cur_x + c] = [col, col, col]
                cur_x += 4

    def render(self) -> np.ndarray:
        total_cycle = self.slot_total * 3
        cycle_time = self.cam_timer % total_cycle
        cur_idx = int(cycle_time // self.slot_total)
        t_local = cycle_time % self.slot_total

        with self.lock:
            frame_curr = self.frames[cur_idx].astype(np.float32)
            motion_curr = self.motion_maps[cur_idx].copy()

            if t_local >= self.slot_dwell:
                next_idx = (cur_idx + 1) % 3
                frame_next = self.frames[next_idx].astype(np.float32)
                alpha = 0.5 - 0.5 * math.cos(math.pi * (t_local - self.slot_dwell) / self.slot_trans)
                blended = (1.0 - alpha) * frame_curr + alpha * frame_next
            else:
                blended = frame_curr.copy()

        pulse = 0.7 + 0.3 * math.sin(self.time * 6.0)
        glow_intensity = motion_curr * pulse
        glow_mask = glow_intensity > 0.08
        if np.any(glow_mask):
            glow_val = glow_intensity[glow_mask, None]
            col_amber = np.array([255.0, 210.0, 115.0], dtype=np.float32)
            blended[glow_mask] = blended[glow_mask] * (1.0 - glow_val * 0.65) + col_amber * (glow_val * 0.65)

        if cur_idx == 2:
            water_y = np.clip((self.y - 17.0) / 10.0, 0.0, 1.0)
            ripple = (
                0.06 * np.sin(self.x * 0.45 + self.time * 2.5) *
                np.cos(self.y * 0.70 - self.time * 1.8)
            ) * water_y
            blended += blended * ripple[:, :, None]

        buf = np.clip(blended, 0, 255).astype(np.uint8)

        if t_local < 3.5:
            if t_local < 0.3:
                badge_op = t_local / 0.3
            elif t_local < 2.5:
                badge_op = 1.0
            else:
                badge_op = 1.0 - (t_local - 2.5) / 1.0
            self._draw_badge(buf, self.cam_names[cur_idx], badge_op)

        return buf
