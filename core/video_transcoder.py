import os
import json
import time
import re
import subprocess
import shutil
import numpy as np

MEDIA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "media", "videos"))
ACTIVE_FILE = os.path.join(MEDIA_DIR, "active.json")
SETTINGS_FILE = os.path.join(MEDIA_DIR, "settings.json")
YT_DLP_PATH = "/home/mini/.local/bin/yt-dlp"

def sanitize_id(title):
    cleaned = re.sub(r'[^a-zA-Z0-9_-]', '_', title).strip('_')
    return cleaned[:40] if cleaned else "video"

class VideoManager:
    def __init__(self, media_dir=MEDIA_DIR):
        self.media_dir = media_dir
        os.makedirs(self.media_dir, exist_ok=True)
        self.settings_file = os.path.join(self.media_dir, "settings.json")
        self.active_file = os.path.join(self.media_dir, "active.json")
        self._ensure_settings()

    def _ensure_settings(self):
        if not os.path.exists(self.settings_file):
            active_id = None
            if os.path.exists(self.active_file):
                try:
                    with open(self.active_file, "r") as f:
                        active_id = json.load(f).get("active_id")
                except Exception:
                    pass
            if not active_id:
                videos = self.list_videos()
                if videos:
                    active_id = videos[0]["id"]

            default_settings = {
                "active_id": active_id,
                "playback_mode": "playlist",
                "crossfade_sec": 1.8
            }
            try:
                with open(self.settings_file, "w") as f:
                    json.dump(default_settings, f, indent=2)
            except Exception:
                pass

    def get_settings(self):
        self._ensure_settings()
        try:
            with open(self.settings_file, "r") as f:
                data = json.load(f)
                return {
                    "active_id": data.get("active_id"),
                    "playback_mode": data.get("playback_mode", "playlist"),
                    "crossfade_sec": float(data.get("crossfade_sec", 1.8))
                }
        except Exception:
            return {
                "active_id": None,
                "playback_mode": "playlist",
                "crossfade_sec": 1.8
            }

    def update_settings(self, active_id=None, playback_mode=None, crossfade_sec=None):
        settings = self.get_settings()
        if active_id is not None:
            settings["active_id"] = active_id
        if playback_mode is not None:
            if playback_mode in ("playlist", "loop"):
                settings["playback_mode"] = playback_mode
        if crossfade_sec is not None:
            try:
                settings["crossfade_sec"] = max(0.5, min(5.0, float(crossfade_sec)))
            except (ValueError, TypeError):
                pass

        try:
            with open(self.settings_file, "w") as f:
                json.dump(settings, f, indent=2)
            # Maintain active.json for backwards compatibility
            if settings.get("active_id"):
                with open(self.active_file, "w") as f:
                    json.dump({"active_id": settings["active_id"]}, f, indent=2)
        except Exception as e:
            print(f"[WARN] Failed to write settings: {e}")
        return settings

    def get_active_id(self):
        settings = self.get_settings()
        active_id = settings.get("active_id")
        if active_id:
            npy_path = os.path.join(self.media_dir, f"{active_id}.npy")
            if os.path.exists(npy_path):
                return active_id
        videos = self.list_videos()
        if videos:
            first_id = videos[0]["id"]
            self.set_active_id(first_id)
            return first_id
        return None

    def set_active_id(self, video_id):
        self.update_settings(active_id=video_id)

    def get_next_playlist_id(self, current_id):
        videos = self.list_videos()
        if not videos:
            return None
        ids = [v["id"] for v in videos]
        if current_id in ids:
            curr_idx = ids.index(current_id)
            next_idx = (curr_idx + 1) % len(ids)
            return ids[next_idx]
        return ids[0]

    def list_videos(self):
        videos = []
        active_id = self.get_settings().get("active_id")

        if not os.path.exists(self.media_dir):
            return videos

        for fname in os.listdir(self.media_dir):
            if fname.endswith(".json") and fname not in ("active.json", "settings.json"):
                json_path = os.path.join(self.media_dir, fname)
                try:
                    with open(json_path, "r") as f:
                        meta = json.load(f)
                        vid_id = meta.get("id")
                        npy_path = os.path.join(self.media_dir, f"{vid_id}.npy")
                        if os.path.exists(npy_path):
                            meta["is_active"] = (vid_id == active_id)
                            meta["file_size_mb"] = round(os.path.getsize(npy_path) / (1024 * 1024), 2)
                            videos.append(meta)
                except Exception as e:
                    print(f"[WARN] Error reading metadata {fname}: {e}")

        videos.sort(key=lambda x: x.get("created_at", ""), reverse=False)
        return videos

    def delete_video(self, video_id):
        for ext in [".npy", ".json", ".mp4", ".webm", ".mkv", ".gif"]:
            path = os.path.join(self.media_dir, f"{video_id}{ext}")
            if os.path.exists(path):
                try:
                    os.remove(path)
                except Exception as e:
                    print(f"[WARN] Failed to remove {path}: {e}")

        settings = self.get_settings()
        if settings.get("active_id") == video_id:
            remaining = self.list_videos()
            if remaining:
                self.set_active_id(remaining[0]["id"])
            else:
                self.update_settings(active_id=None)
                if os.path.exists(self.active_file):
                    try:
                        os.remove(self.active_file)
                    except Exception:
                        pass
        return True

    def transcode_file(self, input_file, video_id=None, title=None, aspect_mode="fill", target_fps=25, width=64, height=32):
        if not video_id:
            base = os.path.splitext(os.path.basename(input_file))[0]
            video_id = f"{sanitize_id(base)}_{int(time.time())}"

        if not title:
            title = os.path.splitext(os.path.basename(input_file))[0].replace("_", " ").title()

        if aspect_mode == "fill":
            vf = f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height},format=rgb24"
        else:
            vf = f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black,format=rgb24"

        raw_path = f"/tmp/{video_id}_temp.raw"
        npy_path = os.path.join(self.media_dir, f"{video_id}.npy")
        json_path = os.path.join(self.media_dir, f"{video_id}.json")

        cmd = [
            "ffmpeg", "-y", "-i", input_file,
            "-vf", vf,
            "-r", str(target_fps),
            "-f", "rawvideo",
            "-pix_fmt", "rgb24",
            raw_path
        ]

        print(f"[INFO] Transcoding {input_file} -> {npy_path} (mode={aspect_mode}, fps={target_fps})...")
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            if os.path.exists(raw_path):
                os.remove(raw_path)
            raise RuntimeError(f"FFmpeg error: {res.stderr[-300:]}")

        if not os.path.exists(raw_path) or os.path.getsize(raw_path) == 0:
            if os.path.exists(raw_path):
                os.remove(raw_path)
            raise RuntimeError("FFmpeg produced empty output")

        file_size = os.path.getsize(raw_path)
        frame_size = width * height * 3
        num_frames = file_size // frame_size

        if num_frames == 0:
            os.remove(raw_path)
            raise RuntimeError("Video has 0 frames")

        raw_arr = np.memmap(raw_path, dtype=np.uint8, mode="r", shape=(num_frames, height, width, 3))
        np.save(npy_path, raw_arr)
        del raw_arr
        os.remove(raw_path)

        duration = round(num_frames / target_fps, 2)
        meta = {
            "id": video_id,
            "title": title,
            "fps": target_fps,
            "frames": num_frames,
            "duration": duration,
            "aspect_mode": aspect_mode,
            "filename": f"{video_id}.npy",
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        with open(json_path, "w") as f:
            json.dump(meta, f, indent=2)

        self.set_active_id(video_id)
        print(f"[INFO] Video '{title}' transcoded successfully: {num_frames} frames ({duration}s).")
        return meta

    def download_and_transcode_url(self, url, aspect_mode="fill", target_fps=25):
        vid_id = f"vid_{int(time.time())}"
        temp_download = os.path.join(self.media_dir, f"{vid_id}_source")

        title = "Internet Video"
        downloaded_file = None

        if os.path.exists(YT_DLP_PATH):
            cmd = [
                YT_DLP_PATH,
                "-f", "bestvideo[height<=720]/bestvideo/best",
                "-o", f"{temp_download}.%(ext)s",
                "--print", "after_move:filepath",
                "--print", "title",
                url
            ]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if res.returncode == 0:
                lines = [line.strip() for line in res.stdout.strip().split("\n") if line.strip()]
                if len(lines) >= 2:
                    downloaded_file = lines[0]
                    title = lines[1]
                elif len(lines) == 1:
                    downloaded_file = lines[0]

        if not downloaded_file or not os.path.exists(downloaded_file):
            ext = ".mp4"
            if ".webm" in url:
                ext = ".webm"
            elif ".gif" in url:
                ext = ".gif"
            downloaded_file = f"{temp_download}{ext}"
            cmd = ["curl", "-L", "-s", "-o", downloaded_file, url]
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if res.returncode != 0 or not os.path.exists(downloaded_file) or os.path.getsize(downloaded_file) < 1000:
                if os.path.exists(downloaded_file):
                    os.remove(downloaded_file)
                raise RuntimeError("Failed to download video from URL")

        meta = self.transcode_file(
            downloaded_file,
            video_id=vid_id,
            title=title,
            aspect_mode=aspect_mode,
            target_fps=target_fps
        )

        if os.path.exists(downloaded_file):
            try:
                os.remove(downloaded_file)
            except Exception:
                pass

        return meta
