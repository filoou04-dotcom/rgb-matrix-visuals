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

        # Playback settings
        self.playback_mode = "playlist"  # "playlist" or "loop"
        self.crossfade_sec = 1.8         # 1.5 - 2.0s crossfade duration

        # Next video preloader for playlist crossfade
        self.next_video_id = None
        self.next_frames = None
        self.next_total = 0
        self.next_fps = 25.0

        # Manual transition state (when user switches video via web UI)
        self.manual_transition = None

        self.last_settings_check = 0.0
        self._load_active_video(initial=True)

    def reset(self):
        self.manual_transition = None
        self.next_frames = None
        self.next_video_id = None
        self._load_active_video(force=True)
        self.frame_pos = 0.0

    def _sync_settings(self):
        settings = self.vm.get_settings()
        self.playback_mode = settings.get("playback_mode", "playlist")
        self.crossfade_sec = float(settings.get("crossfade_sec", 1.8))
        target_active_id = settings.get("active_id")

        # Check if user manually requested a different video
        if target_active_id and target_active_id != self.current_video_id and self.manual_transition is None:
            if self.frames is not None and self.total_frames > 0:
                self._start_manual_transition(target_active_id)
            else:
                self._load_active_video(force=True)

    def _load_video_data(self, video_id):
        if not video_id:
            return None, 0, 25.0
        npy_path = os.path.join(self.vm.media_dir, f"{video_id}.npy")
        json_path = os.path.join(self.vm.media_dir, f"{video_id}.json")
        if not os.path.exists(npy_path):
            return None, 0, 25.0

        try:
            frames = np.load(npy_path, mmap_mode="r")
            fps = 25.0
            if os.path.exists(json_path):
                with open(json_path, "r") as f:
                    meta = json.load(f)
                    fps = float(meta.get("fps", 25.0))
            return frames, len(frames), fps
        except Exception as e:
            print(f"[ERROR] Failed to load video {video_id}: {e}")
            return None, 0, 25.0

    def _load_active_video(self, initial=False, force=False):
        settings = self.vm.get_settings()
        self.playback_mode = settings.get("playback_mode", "playlist")
        self.crossfade_sec = float(settings.get("crossfade_sec", 1.8))
        active_id = self.vm.get_active_id()

        if not force and active_id == self.current_video_id and self.frames is not None:
            return

        self.current_video_id = active_id
        self.frames, self.total_frames, self.video_fps = self._load_video_data(active_id)
        self.frame_pos = 0.0
        if self.frames is not None:
            print(f"[INFO] VideoPlayer active: '{active_id}' ({self.total_frames} frames @ {self.video_fps} FPS, mode={self.playback_mode})")

    def _start_manual_transition(self, target_id):
        in_frames, in_total, in_fps = self._load_video_data(target_id)
        if in_frames is None or in_total == 0:
            return

        print(f"[INFO] Starting manual crossfade '{self.current_video_id}' -> '{target_id}' ({self.crossfade_sec}s)...")
        self.manual_transition = {
            "out_frames": self.frames,
            "out_pos": self.frame_pos,
            "out_fps": self.video_fps,
            "out_total": self.total_frames,
            "in_frames": in_frames,
            "in_pos": 0.0,
            "in_fps": in_fps,
            "in_total": in_total,
            "in_id": target_id,
            "duration": max(0.5, self.crossfade_sec),
            "elapsed": 0.0
        }

    def update(self, dt):
        super().update(dt)

        now = time.perf_counter()
        if now - self.last_settings_check > 0.5:
            self.last_settings_check = now
            self._sync_settings()

        # 1. Handling manual crossfade
        if self.manual_transition is not None:
            mt = self.manual_transition
            mt["elapsed"] += dt
            mt["out_pos"] += dt * mt["out_fps"]
            mt["in_pos"] += dt * mt["in_fps"]

            if mt["elapsed"] >= mt["duration"]:
                # Finish manual crossfade
                self.frames = mt["in_frames"]
                self.current_video_id = mt["in_id"]
                self.total_frames = mt["in_total"]
                self.video_fps = mt["in_fps"]
                self.frame_pos = mt["in_pos"]
                self.manual_transition = None
                self.next_frames = None
                self.next_video_id = None
                print(f"[INFO] Manual crossfade complete. Now playing '{self.current_video_id}'.")
            return

        # 2. Normal playback & automated transitions
        if self.frames is None or self.total_frames == 0:
            return

        N = self.total_frames
        xfade_frames = int(self.crossfade_sec * self.video_fps)
        xfade_frames = min(xfade_frames, max(1, N // 3))
        xfade_start = N - xfade_frames

        self.frame_pos += dt * self.video_fps

        # Check preloading for playlist mode
        if self.playback_mode == "playlist":
            if self.frame_pos >= xfade_start:
                if self.next_video_id is None:
                    next_id = self.vm.get_next_playlist_id(self.current_video_id)
                    if next_id and next_id != self.current_video_id:
                        nf, n_tot, n_fps = self._load_video_data(next_id)
                        if nf is not None and n_tot > 0:
                            self.next_video_id = next_id
                            self.next_frames = nf
                            self.next_total = n_tot
                            self.next_fps = n_fps

            # Boundary crossing: Video finished, advance to next
            if self.frame_pos >= N:
                if self.next_frames is not None and self.next_total > 0:
                    offset = (self.frame_pos - xfade_start) * (self.next_fps / self.video_fps)
                    self.frames = self.next_frames
                    self.current_video_id = self.next_video_id
                    self.total_frames = self.next_total
                    self.video_fps = self.next_fps
                    self.frame_pos = offset
                    self.next_frames = None
                    self.next_video_id = None
                    self.vm.set_active_id(self.current_video_id)
                    print(f"[INFO] Playlist transition complete -> '{self.current_video_id}'")
                else:
                    # Single video playlist fallback: seamless loop
                    self.frame_pos = self.frame_pos - xfade_start
        else:
            # Single video loop mode
            if self.frame_pos >= N:
                self.frame_pos = self.frame_pos - xfade_start

    def render(self) -> np.ndarray:
        # 1. Render manual crossfade
        if self.manual_transition is not None:
            mt = self.manual_transition
            prog = min(1.0, max(0.0, mt["elapsed"] / mt["duration"]))
            alpha = 0.5 - 0.5 * np.cos(np.pi * prog)

            idx_out = min(int(mt["out_pos"]) % mt["out_total"], mt["out_total"] - 1)
            idx_in = min(int(mt["in_pos"]) % mt["in_total"], mt["in_total"] - 1)

            frame_out = mt["out_frames"][idx_out]
            frame_in = mt["in_frames"][idx_in]
            return ((1.0 - alpha) * frame_out + alpha * frame_in).astype(np.uint8)

        # 2. Render normal video playback
        if self.frames is not None and self.total_frames > 0:
            N = self.total_frames
            xfade_frames = int(self.crossfade_sec * self.video_fps)
            xfade_frames = min(xfade_frames, max(1, N // 3))
            xfade_start = N - xfade_frames

            # Normal single frame (outside crossfade zone)
            if self.frame_pos < xfade_start:
                idx = int(self.frame_pos) % N
                return np.array(self.frames[idx], dtype=np.uint8)

            # Inside crossfade zone
            prog = min(1.0, max(0.0, (self.frame_pos - xfade_start) / max(1, xfade_frames)))
            alpha = 0.5 - 0.5 * np.cos(np.pi * prog)

            idx_out = min(int(self.frame_pos), N - 1)
            frame_out = self.frames[idx_out]

            if self.playback_mode == "playlist" and self.next_frames is not None:
                # Crossfade to next playlist video
                idx_in = int((self.frame_pos - xfade_start) * (self.next_fps / self.video_fps)) % self.next_total
                frame_in = self.next_frames[idx_in]
            else:
                # Seamless single-video loop crossfade
                idx_in = int(self.frame_pos - xfade_start) % N
                frame_in = self.frames[idx_in]

            return ((1.0 - alpha) * frame_out + alpha * frame_in).astype(np.uint8)

        # Fallback standby screen
        t = self.time * 2.0
        grid = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        pulse = 0.5 + 0.5 * np.sin(t)
        grid[:, :, 2] = int(30 * pulse)
        grid[:, :, 0] = int(15 * pulse)
        cx, cy = self.width // 2, self.height // 2
        grid[cy, cx] = [200, 200, 255]
        grid[cy, cx-1] = [100, 100, 200]
        grid[cy, cx+1] = [100, 100, 200]
        grid[cy-1, cx] = [100, 100, 200]
        grid[cy+1, cx] = [100, 100, 200]
        return grid
