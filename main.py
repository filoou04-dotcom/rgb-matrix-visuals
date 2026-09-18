#!/usr/bin/env python3
import sys
import time
import signal
import argparse
from config import MatrixConfig
from core.matrix_driver import MatrixDriver
from core.palette import ColorPaletteManager
from core.boot_sequence import run_boot_sequence
from core.web_server import EngineState, start_web_server
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
    parser.add_argument("--panel-type", type=str, default="FM6126A",
                        help="Panel driver chip type (default: FM6126A)")
    parser.add_argument("--port", type=int, default=80,
                        help="Web dashboard HTTP port (default: 80)")
    parser.add_argument("--startup-test", action="store_true", default=True,
                        help="Run short color & IP diagnostic test on start (default: True)")
    parser.add_argument("--no-startup-test", dest="startup_test", action="store_false",
                        help="Skip startup test sequence")
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

    # Optional Boot & Hardware Diagnostic Sequence
    if args.startup_test:
        run_boot_sequence(driver, MatrixConfig.COLS, MatrixConfig.ROWS)

    # Instantiate visual effects dynamically
    effects_map = {
        name: cls(MatrixConfig.COLS, MatrixConfig.ROWS, palette)
        for name, cls in EFFECTS.items()
    }
    effects_list = list(effects_map.values())
    effects_rev_map = {v: k for k, v in effects_map.items()}
    
    # Initialize Shared Web Engine State
    engine_state = EngineState()
    engine_state.brightness = args.brightness
    engine_state.fps = args.fps
    engine_state.cycle_time = args.cycle_time
    engine_state.mode = "cycle" if args.effect == "cycle" else "manual"
    engine_state.current_effect = "minimal" if args.effect == "cycle" else args.effect
    engine_state.effects = list(effects_map.keys())

    # Launch lightweight Web Dashboard in background thread
    start_web_server(engine_state, port=args.port)

    effect_idx = 0
    if args.effect != "cycle" and args.effect in effects_map:
        effect_idx = list(effects_map.keys()).index(args.effect)

    current_effect = effects_list[effect_idx]
    last_cycle_time = time.perf_counter()
    target_dt = 1.0 / max(1, args.fps)
    last_time = time.perf_counter()
    current_brightness = args.brightness

    # FPS Calculation metrics
    fps_frame_count = 0
    fps_last_calc = time.perf_counter()

    try:
        while running:
            now = time.perf_counter()
            dt = now - last_time
            last_time = now

            # Measure live rendering FPS (averaged over 1.0 second)
            fps_frame_count += 1
            if now - fps_last_calc >= 1.0:
                engine_state.measured_fps = round(fps_frame_count / (now - fps_last_calc), 1)
                fps_frame_count = 0
                fps_last_calc = now

            # Check web UI controls: Brightness
            if engine_state.brightness != current_brightness:
                current_brightness = engine_state.brightness
                driver.set_brightness(current_brightness)

            # Check web UI controls: Power
            if not engine_state.active:
                driver.clear()
                time.sleep(0.1)
                continue

            # Check web UI controls: Manual effect selection
            if engine_state.target_effect:
                target = engine_state.target_effect
                engine_state.target_effect = None
                if target in effects_map:
                    current_effect = effects_map[target]
                    print(f"[INFO] Web Control: switched effect to {current_effect.name}")

            # Auto-cycle mode
            if engine_state.mode == "cycle" and (now - last_cycle_time >= engine_state.cycle_time):
                effect_idx = (effect_idx + 1) % len(effects_list)
                current_effect = effects_list[effect_idx]
                last_cycle_time = now
                print(f"[INFO] Auto-Cycle: switched effect to {current_effect.name}")

            engine_state.current_effect = effects_rev_map.get(current_effect, "minimal")

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
