#!/usr/bin/env bash
#!/usr/bin/env python3
import sys
import time
import signal
import argparse
from config import MatrixConfig
from core.matrix_driver import MatrixDriver
from core.palette import ColorPaletteManager
from visuals import EFFECTS

running = True

def signal_handler(sig, frame):
    global running
    print("\n[INFO] Stopping matrix display gracefully...")
    running = False

def parse_args():
    parser = argparse.ArgumentParser(description="Fluid Visuals for RGB LED Matrix (Waveshare HUB75-D 64x32)")
    parser.add_argument("--effect", type=str, default="cycle", choices=list(EFFECTS.keys()) + ["cycle"],
                        help="Visual effect to display (default: cycle)")
    parser.add_argument("--cycle-time", type=float, default=20.0,
                        help="Seconds before switching to next effect when in cycle mode (default: 20s)")
    parser.add_argument("--brightness", type=int, default=MatrixConfig.DEFAULT_BRIGHTNESS,
                        help=f"LED Brightness 1-100 (default: {MatrixConfig.DEFAULT_BRIGHTNESS})")
    parser.add_argument("--slowdown", type=int, default=MatrixConfig.GPIO_SLOWDOWN,
                        help=f"GPIO slowdown (default: {MatrixConfig.GPIO_SLOWDOWN})")
    parser.add_argument("--fps", type=int, default=MatrixConfig.FPS_LIMIT,
                        help=f"Target frames per second (default: {MatrixConfig.FPS_LIMIT})")
    parser.add_argument("--mapping", type=str, default=MatrixConfig.HARDWARE_MAPPING,
                        help=f"Hardware mapping (default: {MatrixConfig.HARDWARE_MAPPING})")
    parser.add_argument("--panel-type", type=str, default=getattr(MatrixConfig, "PANEL_TYPE", "FM6126A"),
                        help=f"Panel driver chip type (default: {"FM6126A"})")
    return parser.parse_args()

def main():
    global running
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    args = parse_args()
    
    # Apply CLI overrides to config
    MatrixConfig.DEFAULT_BRIGHTNESS = args.brightness
    MatrixConfig.GPIO_SLOWDOWN = args.slowdown
    MatrixConfig.FPS_LIMIT = args.fps
    MatrixConfig.HARDWARE_MAPPING = args.mapping
    MatrixConfig.PANEL_TYPE = args.panel_type

    print("=" * 60)
    print(f"Starting LED Matrix Visuals ({MatrixConfig.COLS}x{MatrixConfig.ROWS})")
    print(f"Effect: {args.effect} | Brightness: {args.brightness}% | Target FPS: {args.fps}")
    print(f"Mapping: {args.mapping} | Panel Type: {args.panel_type}")
    print("=" * 60)

    # Initialize Hardware and Palette Manager
    driver = MatrixDriver(MatrixConfig)
    palette = ColorPaletteManager()

    # Instantiate visual effects
    effects_list = [
        EFFECTS["plasma"](MatrixConfig.COLS, MatrixConfig.ROWS, palette),
        EFFECTS["metaballs"](MatrixConfig.COLS, MatrixConfig.ROWS, palette),
        EFFECTS["waves"](MatrixConfig.COLS, MatrixConfig.ROWS, palette)
    ]
    
    effect_idx = 0
    if args.effect != "cycle":
        effect_idx = [e.name.lower() for e in effects_list].index(EFFECTS[args.effect](1, 1, palette).name.lower())

    current_effect = effects_list[effect_idx]
    last_cycle_time = time.perf_counter()
    target_dt = 1.0 / max(1, args.fps)
    last_time = time.perf_counter()

    try:
        while running:
            now = time.perf_counter()
            dt = now - last_time
            last_time = now

            # Switch effect if in cycle mode
            if args.effect == "cycle" and (now - last_cycle_time >= args.cycle_time):
                effect_idx = (effect_idx + 1) % len(effects_list)
                current_effect = effects_list[effect_idx]
                last_cycle_time = now
                print(f"[INFO] Switched effect to: {current_effect.name}")

            # Update simulation & render frame
            current_effect.update(dt)
            frame_rgb = current_effect.render()

            # Output to matrix
            driver.display_frame(frame_rgb)

            # Cap frame rate
            render_duration = time.perf_counter() - now
            sleep_time = target_dt - render_duration
            if sleep_time > 0:
                time.sleep(sleep_time)

    finally:
        driver.clear()
        print("[INFO] Display cleared. Goodbye!")

if __name__ == "__main__":
    main()
