# RGB Matrix Visuals (Waveshare HUB75-D 64x32)

Fluid, organic generative visuals running on a Raspberry Pi 3 with Adafruit/Waveshare RGB Matrix Bonnet and a 64x32 HUB75-D LED panel.

## Features
- **Fluid Plasma:** Multi-wave sinusoidal interference continuously flowing through all colors of the visible spectrum.
- **Liquid Metaballs:** Merging and dividing liquid drops with smooth equipotential blending.
- **Fluid Waves:** Aurora / liquid silk ribbons with sweeping color fields.
- **Vectorized NumPy Engine:** Ultra-low CPU usage and high FPS on Raspberry Pi.
- **Modular & Pluggable:** Easily add new visualizers by subclassing `VisualEffect`.

## Usage
```bash
# Run cycle mode (auto-switches effect every 20 seconds)
sudo python3 main.py --effect cycle

# Run specific effect
sudo python3 main.py --effect plasma
sudo python3 main.py --effect metaballs
sudo python3 main.py --effect waves

# Customize brightness and FPS
sudo python3 main.py --brightness 80 --fps 50
```
