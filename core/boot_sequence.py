import time
import socket
import numpy as np
from PIL import Image, ImageDraw, ImageFont

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("1.1.1.1", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()

def run_boot_sequence(driver, width=64, height=32):
    print("[INFO] Starting Boot & Hardware Test Sequence...")

    # 1. Primary Colors & White Test Flash (0.4s each)
    test_colors = [
        ("RED", (255, 0, 0)),
        ("GREEN", (0, 255, 0)),
        ("BLUE", (0, 0, 255)),
        ("WHITE", (255, 255, 255))
    ]

    for name, col in test_colors:
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        frame[:] = col
        driver.display_frame(frame)
        time.sleep(0.4)

    # 2. Test Pattern / Splash Screen with IP Address
    ip = get_local_ip()
    splash = Image.new("RGB", (width, height), (5, 5, 20))
    draw = ImageDraw.Draw(splash)
    
    # Outer Border
    draw.rectangle((0, 0, width - 1, height - 1), outline=(0, 200, 255))
    
    # Text header
    font = ImageFont.load_default()
    draw.text((14, 3), "ONLINE", fill=(255, 230, 0), font=font)
    
    # Display IP Address
    # In 64x32, 15 chars like 192.168.178.104 fits nicely
    draw.text((2, 17), ip, fill=(0, 255, 200), font=font)
    
    splash_arr = np.array(splash)
    driver.display_frame(splash_arr)
    time.sleep(2.5)

    # 3. Smooth Fade Out to Black
    for alpha in np.linspace(1.0, 0.0, 15):
        fade_frame = (splash_arr * alpha).astype(np.uint8)
        driver.display_frame(fade_frame)
        time.sleep(0.02)

    print("[INFO] Boot sequence finished. Transitioning to visuals...")
