import os
import numpy as np
from .base import VisualEffect

class ThermalDither(VisualEffect):
    """
    Programm 5:
    Silkscreen halftone dithered thermographic street scene with
    smooth horizontal camera panning across the crowd and pedestrians.
    """
    def __init__(self, width=64, height=32, palette_manager=None):
        super().__init__(width, height, palette_manager, name="ThermalDither")
        
        # Load precomputed Atkinson dithered pan frames
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        data_path = os.path.join(base_dir, "assets", "thermal_pan_frames.npy")
        if os.path.exists(data_path):
            self.frames = np.load(data_path)
        else:
            self.frames = np.zeros((1, height, width, 3), dtype=np.uint8)

        self.num_frames = len(self.frames)
        self.pan_period = 18.0  # seconds for a full left-right-left pan cycle

    def update(self, dt):
        super().update(dt)

    def render(self) -> np.ndarray:
        if self.num_frames <= 1:
            return self.frames[0]
            
        cycle_t = (self.time % self.pan_period) / self.pan_period
        idx = int(cycle_t * self.num_frames) % self.num_frames
        return self.frames[idx]
