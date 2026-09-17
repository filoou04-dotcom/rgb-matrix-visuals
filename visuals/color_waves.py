import numpy as np
from .base import VisualEffect

class FluidWaves(VisualEffect):
    """
    Flowing ribbon waves resembling an Aurora Borealis or liquid silk,
    sweeping all colors across the display.
    """
    def __init__(self, width=64, height=32, palette_manager=None):
        super().__init__(width, height, palette_manager, name="FluidWaves")
        self.color_speed = 0.07

    def update(self, dt):
        super().update(dt)

    def render(self) -> np.ndarray:
        t = self.time
        # Multiple wave oscillations
        wave1 = 0.5 + 0.3 * np.sin(self.x_norm * 3.5 + t * 1.5)
        wave2 = 0.5 + 0.25 * np.sin(self.x_norm * 5.0 - t * 1.1 + 1.0)
        wave3 = 0.5 + 0.2 * np.cos(self.x_norm * 2.0 + t * 0.8)
        
        avg_wave = (wave1 + wave2 + wave3) / 3.0
        
        # Distance from dynamic wave center
        dist = np.abs(self.y_norm - avg_wave)
        glow = np.exp(-dist * 8.0)
        
        # Horizontal flow field
        flow = (self.x_norm + t * 0.2) % 1.0
        
        hue_offset = (t * self.color_speed) % 1.0
        colors = self.palette.sample_rainbow(flow, hue_offset=hue_offset)
        
        # Apply fluid intensity
        intensity = glow[..., np.newaxis]
        return np.clip(colors * intensity, 0, 255).astype(np.uint8)
