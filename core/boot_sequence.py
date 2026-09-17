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

def make_test_pattern(width=64, height=32):
    """
    Classic broadcast SMPTE-style color bar calibration test pattern.
    """
    img = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(img)

    # 1. 8 Main Color Bars (top 20 rows)
    # White, Yellow, Cyan, Green, Magenta, Red, Blue, Black
    bars = [
        (255, 255, 255),  # White
        (255, 255, 0),    # Yellow
        (0, 255, 255),    # Cyan
        (0, 255, 0),      # Green
        (255, 0, 255),    # Magenta
        (255, 0, 0),      # Red
        (0, 0, 255),      # Blue
        (20, 20, 20)      # Dark / Black
    ]
    bar_w = width // len(bars)
    for i, color in enumerate(bars):
        x0 = i * bar_w
        x1 = (i + 1) * bar_w if i < len(bars) - 1 else width
        draw.rectangle((x0, 0, x1 - 1, 18), fill=color)

    # 2. Grayscale Ramp (rows 19 to 24)
    gray_steps = 8
    gw = width // gray_steps
    for i in range(gray_steps):
        val = int((i / (gray_steps - 1)) * 255)
        x0 = i * gw
        x1 = (i + 1) * gw if i < gray_steps - 1 else width
        draw.rectangle((x0, 19, x1 - 1, 24), fill=(val, val, val))

    # 3. Complementary blocks & alignment (rows 25 to 31)
    comp_colors = [
        (0, 0, 255), (0, 0, 0), (255, 0, 255), (0, 0, 0),
        (0, 255, 255), (0, 0, 0), (255, 255, 255), (100, 100, 100)
    ]
    cw = width // len(comp_colors)
    for i, color in enumerate(comp_colors):
        x0 = i * cw
        x1 = (i + 1) * cw if i < len(comp_colors) - 1 else width
        draw.rectangle((x0, 25, x1 - 1, 31), fill=color)

    return np.array(img, dtype=np.uint8)

def run_boot_sequence(driver, width=64, height=32):
    print("[INFO] Starting Boot Diagnostics (RGBW -> Test Pattern -> Scrolling IP)...")

    # Step 1: Full-screen Flash R -> G -> B -> W (0.35s each)
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
        time.sleep(0.35)

    # Step 2: SMPTE Color Bar Test Pattern (hold for 2.0s)
    pattern = make_test_pattern(width, height)
    driver.display_frame(pattern)
    time.sleep(2.0)

    # Step 3: Smooth Scrolling IP Banner
    ip = get_local_ip()
    msg = f"  ONLINE  •  IP: {ip}  •  ONLINE  "
    font = ImageFont.load_default()
    
    # Calculate text width
    bbox = font.getbbox(msg)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    # Pre-render text onto an off-screen strip
    text_img = Image.new("RGB", (text_w, height), (0, 0, 0))
    text_draw = ImageDraw.Draw(text_img)
    
    # Top status bar: glowing mini line
    # Scrolling text in vibrant cyan/amber
    text_draw.text((0, (height - text_h) // 2), msg, fill=(0, 255, 220), font=font)

    # Scroll smoothly across from right to left
    # Speed: ~50 pixels per second
    fps = 40
    dt = 1.0 / fps
    total_distance = width + text_w
    scroll_speed = 45.0  # pixels per second

    x_pos = float(width)
    while x_pos > -text_w:
        frame = Image.new("RGB", (width, height), (5, 5, 15))
        draw = ImageDraw.Draw(frame)
        
        # Border
        draw.rectangle((0, 0, width - 1, height - 1), outline=(0, 100, 255))
        
        # Paste text slice
        frame.paste(text_img, (int(x_pos), 0))
        
        driver.display_frame(np.array(frame, dtype=np.uint8))
        time.sleep(dt)
        x_pos -= scroll_speed * dt

    # Step 4: Quick fade to black before visuals
    fade = np.zeros((height, width, 3), dtype=np.uint8)
    driver.display_frame(fade)
    time.sleep(0.2)
    print("[INFO] Boot sequence complete. Transitioning to visual engine...")
