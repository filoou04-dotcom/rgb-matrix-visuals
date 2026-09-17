import numpy as np
from .base import VisualEffect

class FluidPlasma(VisualEffect):
    """
    Fluid wave plasma using sinusoidal interference patterns.
    Smoothly journeys through all colors of the visible spectrum.
    """
    def __init__(self, width=64, height=32, palette_manager=None):
        super().__init__(width, height, palette_manager, name="FluidPlasma")
        self.kx = 6.0
        self.ky = 6.0
        self.color_speed = 0.08  # Cycle through all colors over time

    def update(self, dt):
        super().update(dt)

    def render(self) -> np.ndarray:
        t = self.time
        
        # Wave 1: Horizontal drift
        v1 = np.sin(self.x_norm * self.kx * np.pi + t * 1.3)
        
        # Wave 2: Vertical drift
        v2 = np.sin(self.y_norm * self.ky * np.pi + t * 1.1)
        
        # Wave 3: Diagonal interference
        v3 = np.sin((self.x_norm + self.y_norm) * 5.0 * np.pi + t * 0.9)
        
        # Wave 4: Dynamic moving center ripple
        cx = 0.5 + 0.3 * np.sin(t * 0.5)
        cy = 0.5 + 0.3 * np.cos(t * 0.7)
        dist = np.sqrt((self.x_norm - cx) ** 2 + ((self.y_norm - cy) * (self.height / self.width)) ** 2)
        v4 = np.sin(dist * 12.0 * np.pi - t * 2.0)
        
        # Combined normalized field in [0, 1]
        field = (v1 + v2 + v3 + v4 + 4.0) / 8.0
        
        # Cycle through all colors over time
        hue_offset = (t * self.color_speed) % 1.0
        
        # Sample smooth rainbow palette
        return self.palette.sample_rainbow(field, hue_offset=hue_offset)
