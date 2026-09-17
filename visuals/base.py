from abc import ABC, abstractmethod
import numpy as np

class VisualEffect(ABC):
    """
    Abstract base class for all LED matrix visual effects.
    """
    def __init__(self, width=64, height=32, palette_manager=None, name="BaseVisual"):
        self.width = width
        self.height = height
        self.palette = palette_manager
        self.name = name
        self.time = 0.0
        
        # Precomputed coordinate grids normalized to [0, 1] or aspect-corrected
        y_coords, x_coords = np.mgrid[0:height, 0:width]
        self.x = x_coords.astype(np.float32)
        self.y = y_coords.astype(np.float32)
        self.x_norm = self.x / float(width)
        self.y_norm = self.y / float(height)

    @abstractmethod
    def update(self, dt):
        """Update simulation state with delta time in seconds."""
        self.time += dt

    @abstractmethod
    def render(self) -> np.ndarray:
        """
        Renders the current frame.
        Must return a uint8 numpy array of shape (height, width, 3).
        """
        pass
