import os
import json
import time
import numpy as np
from .base import VisualEffect
from core.video_transcoder import VideoManager

class VideoPlayer(VisualEffect):
    def __init__(self, width=64, height=32, palette_manager=None, name="VideoPlayer"):
        super().__init__(width, height, palette_manager, name=name)
        self.vm = VideoManager()
        self.current_video_id = None
        self.frames = None
        self.total_frames = 0
        self.video_fps = 25.0
        self.frame_pos = 0.0
        self.last_check_time = 0.0
        self._load_active_video()

    def reset(self):
        self._load_active_video(force=True)
        self.frame_pos = 0.0

    def _load_active_video(self, force=False):
        active_id = self.vm.get_active_id()
        if not force and active_id == self.current_video_id and self.frames is not None:
            return

        self.current_video_id = active_id
        if not active_id:
            self.frames = None
            self.total_frames = 0
            return

        npy_path = os.path.join(self.vm.media_dir, f"{active_id}.npy")
        json_path = os.path.join(self.vm.media_dir, f"{active_id}.json")

        if not os.path.exists(npy_path):
            self.frames = None
            self.total_frames = 0
            return

        try:
            self.frames = np.load(npy_path, mmap_mode="r")
            self.total_frames = len(self.frames)
            self.video_fps = 25.0
            if os.path.exists(json_path):
                with open(json_path, "r") as f:
                    meta = json.load(f)
                    self.video_fps = float(meta.get("fps", 25.0))
            self.frame_pos = 0.0
            print(f"[INFO] VideoPlayer loaded '{active_id}': {self.total_frames} frames @ {self.video_fps} FPS")
        except Exception as e:
            print(f"[ERROR] VideoPlayer failed to load '{active_id}': {e}")
            self.frames = None
            self.total_frames = 0

    def update(self, dt):
        super().update(dt)

        # Check periodically if active video changed
        now = time.perf_counter()
        if now - self.last_check_time > 0.5:
            self.last_check_time = now
            self._load_active_video()

        if self.frames is not None and self.total_frames > 0:
            self.frame_pos += dt * self.video_fps
            if self.frame_pos >= self.total_frames:
                self.frame_pos = self.frame_pos % self.total_frames

    def render(self) -> np.ndarray:
        if self.frames is not None and self.total_frames > 0:
            idx = int(self.frame_pos) % self.total_frames
            return np.array(self.frames[idx], dtype=np.uint8)

        # Fallback standby screen if no video loaded
        t = self.time * 2.0
        grid = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        # Pulsing ambient blue-purple pattern
        pulse = 0.5 + 0.5 * np.sin(t)
        grid[:, :, 2] = int(30 * pulse)
        grid[:, :, 0] = int(15 * pulse)
        # Center indicator dot
        cx, cy = self.width // 2, self.height // 2
        grid[cy, cx] = [200, 200, 255]
        grid[cy, cx-1] = [100, 100, 200]
        grid[cy, cx+1] = [100, 100, 200]
        grid[cy-1, cx] = [100, 100, 200]
        grid[cy+1, cx] = [100, 100, 200]
        return grid
