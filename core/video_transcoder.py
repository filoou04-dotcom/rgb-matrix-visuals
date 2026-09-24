import os
import json
import time
import re
import subprocess
import shutil
import numpy as np

MEDIA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "media", "videos"))
ACTIVE_FILE = os.path.join(MEDIA_DIR, "active.json")
YT_DLP_PATH = "/home/mini/.local/bin/yt-dlp"

def sanitize_id(title):
    cleaned = re.sub(r'[^a-zA-Z0-9_-]', '_', title).strip('_')
    return cleaned[:40] if cleaned else "video"

class VideoManager:
    def __init__(self, media_dir=MEDIA_DIR):
        self.media_dir = media_dir
        os.makedirs(self.media_dir, exist_ok=True)

    def get_active_id(self):
        if os.path.exists(ACTIVE_FILE):
            try:
                with open(ACTIVE_FILE, "r") as f:
                    data = json.load(f)
                    return data.get("active_id")
            except Exception:
                pass
        videos = self.list_videos()
        if videos:
            return videos[0]["id"]
        return None

    def set_active_id(self, video_id):
        with open(ACTIVE_FILE, "w") as f:
            json.dump({"active_id": video_id}, f, indent=2)

    def list_videos(self):
        videos = []
        active_id = None
        if os.path.exists(ACTIVE_FILE):
            try:
                with open(ACTIVE_FILE, "r") as f:
                    active_id = json.load(f).get("active_id")
            except Exception:
                pass

        if not os.path.exists(self.media_dir):
            return videos

        for fname in os.listdir(self.media_dir):
            if fname.endswith(".json") and fname != "active.json":
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

        videos.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return videos

    def delete_video(self, video_id):
        for ext in [".npy", ".json", ".mp4", ".webm", ".mkv", ".gif"]:
            path = os.path.join(self.media_dir, f"{video_id}{ext}")
            if os.path.exists(path):
                try:
                    os.remove(path)
                except Exception as e:
                    print(f"[WARN] Failed to remove {path}: {e}")

        if self.get_active_id() == video_id:
            remaining = self.list_videos()
            if remaining:
                self.set_active_id(remaining[0]["id"])
            else:
                if os.path.exists(ACTIVE_FILE):
                    os.remove(ACTIVE_FILE)
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
