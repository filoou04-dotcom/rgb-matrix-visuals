import numpy as np
from .base import VisualEffect

class LiquidMetaballs(VisualEffect):
    """
    Liquid blobs (metaballs) merging and splitting smoothly.
    Cycles continuously through the full color spectrum.
    """
    def __init__(self, width=64, height=32, palette_manager=None, num_balls=5):
        super().__init__(width, height, palette_manager, name="LiquidMetaballs")
        self.num_balls = num_balls
        self.color_speed = 0.05
        
        # Balls: [x, y, vx, vy, radius] in normalized coordinates [0, 1]
        np.random.seed(42)
        self.pos = np.random.uniform(0.2, 0.8, (num_balls, 2)).astype(np.float32)
        angles = np.random.uniform(0, 2 * np.pi, num_balls)
        speeds = np.random.uniform(0.12, 0.25, num_balls)
        self.vel = np.stack([np.cos(angles) * speeds, np.sin(angles) * speeds], axis=-1).astype(np.float32)
        self.radii = np.random.uniform(0.12, 0.20, num_balls).astype(np.float32)

    def update(self, dt):
        super().update(dt)
        # Update ball positions
        self.pos += self.vel * dt
        
        # Bounce off boundaries
        for i in range(self.num_balls):
            if self.pos[i, 0] <= 0.05 or self.pos[i, 0] >= 0.95:
                self.vel[i, 0] *= -1.0
                self.pos[i, 0] = np.clip(self.pos[i, 0], 0.05, 0.95)
            if self.pos[i, 1] <= 0.05 or self.pos[i, 1] >= 0.95:
                self.vel[i, 1] *= -1.0
                self.pos[i, 1] = np.clip(self.pos[i, 1], 0.05, 0.95)

    def render(self) -> np.ndarray:
        aspect = self.height / self.width
        potential = np.zeros((self.height, self.width), dtype=np.float32)
        
        for i in range(self.num_balls):
            bx, by = self.pos[i, 0], self.pos[i, 1]
            r = self.radii[i]
            dx = self.x_norm - bx
            dy = (self.y_norm - by) * aspect
            dist_sq = dx * dx + dy * dy + 0.0005  # Avoid division by zero
            potential += (r * r) / dist_sq

        # Normalize potential for visual mapping
        field = np.clip(potential * 0.18, 0.0, 1.0)
        
        # Color cycle over time
        hue_offset = (self.time * self.color_speed) % 1.0
        
        # Apply smooth liquid threshold / glow
        rgb = self.palette.sample_rainbow(field, hue_offset=hue_offset)
        
        # Mask out very dark background for distinct liquid drops
        intensity = np.clip(potential * 0.45, 0.0, 1.0)[..., np.newaxis]
        return (rgb * intensity).astype(np.uint8)
