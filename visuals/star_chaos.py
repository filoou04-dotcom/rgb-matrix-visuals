import math
import random
import numpy as np
from .base import VisualEffect

class StarChaos(VisualEffect):
    """
    Programm 7: Strahlend weisse Stern-Grafik im Zentrum, umgeben von einem
    chaotischen, sanft pulsierenden und schwebenden Pixel-Muster aus ueberwiegend
    weissen sowie bunt leuchtenden roten, blauen und gruenen Einzelpixeln
    auf tiefschwarzem Hintergrund.
    """

    def __init__(self, width=64, height=32, palette_manager=None, name="StarChaos"):
        super().__init__(width, height, palette_manager, name=name)

        self.cx = 31.5
        self.cy = 15.5

        y_coords, x_coords = np.mgrid[0:height, 0:width].astype(np.float32)
        self.dx = x_coords - self.cx
        self.dy = y_coords - self.cy
        self.r = np.sqrt(self.dx**2 + self.dy**2)

        # Core star shapes
        self.diamond = np.maximum(0.0, 1.0 - (np.abs(self.dx) / 3.2 + np.abs(self.dy) / 3.2))
        self.core = np.exp(-self.r**2 / 4.0)

        # Surrounding chaotic pixel cloud
        # Proportions: ~74% radiant white, 9% red, 9% blue, 8% green
        self.num_particles = 160
        self.p_base_x = np.zeros(self.num_particles, dtype=np.float32)
        self.p_base_y = np.zeros(self.num_particles, dtype=np.float32)
        self.p_color = np.zeros((self.num_particles, 3), dtype=np.float32)

        self.p_speed_twinkle = np.zeros(self.num_particles, dtype=np.float32)
        self.p_phase_twinkle = np.zeros(self.num_particles, dtype=np.float32)
        self.p_drift_speed_x = np.zeros(self.num_particles, dtype=np.float32)
        self.p_drift_speed_y = np.zeros(self.num_particles, dtype=np.float32)
        self.p_drift_phase_x = np.zeros(self.num_particles, dtype=np.float32)
        self.p_drift_phase_y = np.zeros(self.num_particles, dtype=np.float32)
        self.p_drift_amp_x = np.zeros(self.num_particles, dtype=np.float32)
        self.p_drift_amp_y = np.zeros(self.num_particles, dtype=np.float32)

        random.seed(1337)
        for i in range(self.num_particles):
            # Scatter chaotically, keeping outside immediate central star diamond
            while True:
                bx = random.uniform(1.0, width - 2.0)
                by = random.uniform(1.0, height - 2.0)
                if (bx - self.cx)**2 + (by - self.cy)**2 > 5.5**2:
                    break
            self.p_base_x[i] = bx
            self.p_base_y[i] = by

            # Color selection: deutlich mehr weiss
            rand_col = random.random()
            if rand_col < 0.74:
                # Strahlend weiss
                self.p_color[i] = [255.0, 255.0, 255.0]
            elif rand_col < 0.83:
                # Bunt leuchtend Rot
                self.p_color[i] = [255.0, 30.0, 30.0]
            elif rand_col < 0.92:
                # Bunt leuchtend Blau
                self.p_color[i] = [45.0, 120.0, 255.0]
            else:
                # Bunt leuchtend Gruen
                self.p_color[i] = [35.0, 255.0, 55.0]

            # Individual twinkle dynamics
            self.p_speed_twinkle[i] = random.uniform(1.6, 4.8)
            self.p_phase_twinkle[i] = random.uniform(0.0, 2.0 * math.pi)

            # Individual subtle drift trajectory
            self.p_drift_speed_x[i] = random.uniform(0.4, 1.1)
            self.p_drift_speed_y[i] = random.uniform(0.4, 1.1)
            self.p_drift_phase_x[i] = random.uniform(0.0, 2.0 * math.pi)
            self.p_drift_phase_y[i] = random.uniform(0.0, 2.0 * math.pi)
            self.p_drift_amp_x[i] = random.uniform(0.8, 1.6)
            self.p_drift_amp_y[i] = random.uniform(0.6, 1.3)

    def update(self, dt):
        super().update(dt)

    def render(self) -> np.ndarray:
        buf = np.zeros((self.height, self.width, 3), dtype=np.float32)

        # 1. Central Radiant White Star Graphic
        # Subtle harmonic breathing & micro-rotation
        rot_angle = 0.08 * math.sin(self.time * 1.2)
        cos_a = math.cos(rot_angle)
        sin_a = math.sin(rot_angle)
        dx_rot = self.dx * cos_a - self.dy * sin_a
        dy_rot = self.dx * sin_a + self.dy * cos_a

        # Vertical and horizontal cardinal star flares
        ray_v = np.exp(-np.abs(dx_rot)**1.5 / 0.8) * np.exp(-np.abs(dy_rot) / 8.5)
        ray_h = np.exp(-np.abs(dy_rot)**1.5 / 0.8) * np.exp(-np.abs(dx_rot) / 12.0)

        # Diagonal celestial star rays
        d1 = np.abs(dx_rot + dy_rot) * 0.7071
        d2 = np.abs(dx_rot - dy_rot) * 0.7071
        ray_d = (
            np.exp(-d1**1.5 / 0.7) * np.exp(-d2 / 5.5) +
            np.exp(-d2**1.5 / 0.7) * np.exp(-d1 / 5.5)
        ) * 0.75

        # Organic flare breathing
        pulse_core = 0.90 + 0.10 * math.sin(self.time * 2.2)
        pulse_rays = 0.85 + 0.15 * math.cos(self.time * 1.7)
        pulse_diag = 0.80 + 0.20 * math.sin(self.time * 3.1)

        star_intensity = (
            self.core * 1.15 * pulse_core +
            self.diamond * 1.05 * pulse_core +
            (ray_v + ray_h) * 0.95 * pulse_rays +
            ray_d * 0.85 * pulse_diag
        )
        star_intensity = np.clip(star_intensity, 0.0, 1.0)
        buf += star_intensity[:, :, None] * np.array([255.0, 255.0, 255.0], dtype=np.float32)

        # 2. Chaotic Pixel Field (Leicht bewegend)
        # Smooth Lissajous drift
        drift_x = self.p_base_x + self.p_drift_amp_x * np.sin(
            self.time * self.p_drift_speed_x + self.p_drift_phase_x
        )
        drift_y = self.p_base_y + self.p_drift_amp_y * np.cos(
            self.time * self.p_drift_speed_y + self.p_drift_phase_y
        )

        # Smooth organic twinkling
        twinkle = 0.35 + 0.65 * np.sin(self.time * self.p_speed_twinkle + self.p_phase_twinkle)
        twinkle = np.clip(twinkle, 0.0, 1.0) ** 1.8

        ix = np.clip(np.round(drift_x).astype(int), 0, self.width - 1)
        iy = np.clip(np.round(drift_y).astype(int), 0, self.height - 1)

        for i in range(self.num_particles):
            b_val = twinkle[i]
            if b_val > 0.04:
                col = self.p_color[i] * b_val
                # Maximum blend on deep black background
                buf[iy[i], ix[i]] = np.maximum(buf[iy[i], ix[i]], col)

        return np.clip(buf, 0, 255).astype(np.uint8)
