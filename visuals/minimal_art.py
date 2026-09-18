import math
import numpy as np
from .base import VisualEffect

class MinimalArtSuite(VisualEffect):
    """
    Minimalist generative art composition in four distinct movements.
    Focuses on precise geometric linework, kinetic typography/grids, 
    and strictly curated color palettes (warm beiges and deep blue/lila/pink).
    """
    def __init__(self, width=64, height=32, palette_manager=None):
        super().__init__(width, height, palette_manager, name="Minimal")
        
        self.movement_duration = 24.0  # seconds per movement
        self.transition_duration = 1.2 # cross-fade duration
        self.total_movements = 4

        # Curated Palette 1: Warm Beige / Ivory / Sandstone
        self.c_beige_bg = np.array([6, 5, 4], dtype=np.float32)
        self.c_beige_dark = np.array([55, 48, 40], dtype=np.float32)
        self.c_beige_mid = np.array([160, 142, 120], dtype=np.float32)
        self.c_beige_light = np.array([226, 214, 188], dtype=np.float32)
        self.c_beige_ivory = np.array([248, 242, 230], dtype=np.float32)

        # Curated Palette 2: Midnight Blue / Lila / Neon Pink
        self.c_dusk_bg = np.array([3, 5, 18], dtype=np.float32)
        self.c_dusk_navy = np.array([14, 25, 65], dtype=np.float32)
        self.c_dusk_lila = np.array([125, 45, 195], dtype=np.float32)
        self.c_dusk_lilac = np.array([185, 120, 240], dtype=np.float32)
        self.c_dusk_pink = np.array([255, 30, 125], dtype=np.float32)
        self.c_dusk_highlight = np.array([255, 205, 235], dtype=np.float32)

        # Pre-computed coordinate meshes for ultra-fast vectorized rendering
        self.x_idx = np.arange(width, dtype=np.float32)
        self.y_idx = np.arange(height, dtype=np.float32)

    def update(self, dt):
        super().update(dt)

    def _render_movement_1(self, local_t):
        """
        Satz I: Kinetisches Raster (Grid & Scanlines)
        Palette: Warme Beigetöne / Sand / Elfenbein auf samtigem Schwarz.
        Schnelle, rhythmische horizontale und vertikale Achsenschnitte.
        """
        frame = np.full((self.height, self.width, 3), self.c_beige_bg, dtype=np.float32)

        # 1. Background subtle modular grid (8x8 cells)
        grid_x = (self.x % 8 == 0).astype(np.float32)
        grid_y = (self.y % 8 == 0).astype(np.float32)
        bg_grid = np.maximum(grid_x, grid_y) * 0.18
        frame += bg_grid[:, :, None] * self.c_beige_dark

        # 2. Fast rhythmic scanning crosshairs
        # Vertical sweep with dynamic speed curve
        vx = (math.sin(local_t * 1.8) * 0.5 + 0.5) * (self.width - 1)
        dist_x = np.abs(self.x - vx)
        line_v = np.clip(1.0 - dist_x * 0.9, 0.0, 1.0)
        
        # Second counter-moving vertical scan
        vx2 = ((local_t * 22.0) % (self.width + 10)) - 5.0
        dist_x2 = np.abs(self.x - vx2)
        line_v2 = np.clip(1.0 - dist_x2 * 1.2, 0.0, 1.0)

        # Horizontal sweep
        vy = (math.cos(local_t * 1.4) * 0.5 + 0.5) * (self.height - 1)
        dist_y = np.abs(self.y - vy)
        line_h = np.clip(1.0 - dist_y * 0.9, 0.0, 1.0)

        # Step line (quantized jump every 0.6s)
        step_idx = int(local_t * 2.5) % 4
        step_y = 4 + step_idx * 7
        dist_step = np.abs(self.y - step_y)
        line_step = np.clip(1.0 - dist_step * 1.4, 0.0, 1.0) * 0.75

        # Render vertical and horizontal cuts
        frame += line_v[:, :, None] * self.c_beige_light
        frame += (line_v2 * 0.85)[:, :, None] * self.c_beige_mid
        frame += line_h[:, :, None] * self.c_beige_light
        frame += line_step[:, :, None] * self.c_beige_mid

        # 3. Intersecting nodes flash in bright ivory
        intersections = (line_v * line_h + line_v * line_step)
        inter_mask = np.clip(intersections * 2.2, 0.0, 1.0)
        frame += inter_mask[:, :, None] * (self.c_beige_ivory - frame)

        # 4. Kinetic bounding bracket that follows the crosshair
        bx = int(vx)
        by = int(vy)
        bx0 = max(0, bx - 5)
        bx1 = min(self.width, bx + 6)
        by0 = max(0, by - 4)
        by1 = min(self.height, by + 5)
        # Draw frame corners
        frame[by0, bx0:bx1] = self.c_beige_mid
        frame[by1 - 1, bx0:bx1] = self.c_beige_mid
        frame[by0:by1, bx0] = self.c_beige_mid
        frame[by0:by1, bx1 - 1] = self.c_beige_mid

        return np.clip(frame, 0, 255).astype(np.uint8)

    def _render_movement_2(self, local_t):
        """
        Satz II: Diagonale Vektorebenen (Kinetic Planes & Angles)
        Palette: Dunkelblau / Lila / Neon-Pink.
        Scharfe geometrische Schnitte, dynamische Streifen und Kantengleitung.
        """
        frame = np.full((self.height, self.width, 3), self.c_dusk_bg, dtype=np.float32)

        # Diagonal coordinate projection (angle ~ 30 degrees)
        diag_1 = (self.x * 0.866 + self.y * 0.5)
        diag_2 = (self.x * -0.707 + self.y * 0.707)

        # 1. Sliding diagonal ribbon layers (Lila / Navy)
        band_wave = np.sin(diag_1 * 0.28 - local_t * 3.8)
        band_mask = (band_wave > 0.35).astype(np.float32)
        frame += band_mask[:, :, None] * self.c_dusk_navy

        band_wave2 = np.sin(diag_1 * 0.14 + local_t * 2.2)
        band_mask2 = (band_wave2 > 0.5).astype(np.float32)
        frame += band_mask2[:, :, None] * self.c_dusk_lila

        # 2. Razor-sharp Pink Accent Vector lines
        # Vector 1: Fast moving sweep
        pos_p1 = (local_t * 35.0) % 80.0 - 15.0
        dist_p1 = np.abs(diag_1 - pos_p1)
        line_pink1 = np.clip(1.0 - dist_p1 * 1.1, 0.0, 1.0)
        frame += line_pink1[:, :, None] * self.c_dusk_pink

        # Vector 2: Counter-sweeping line in Lilac
        pos_p2 = 60.0 - ((local_t * 28.0) % 85.0)
        dist_p2 = np.abs(diag_2 - pos_p2)
        line_lilac = np.clip(1.0 - dist_p2 * 1.2, 0.0, 1.0)
        frame += line_lilac[:, :, None] * self.c_dusk_lilac

        # 3. Intersection flash in electric highlight
        cross_flash = line_pink1 * line_lilac
        frame += (cross_flash * 2.5)[:, :, None] * self.c_dusk_highlight

        # 4. Horizontal split mask: bottom third reacts to phase
        split_y = int(self.height * 0.68)
        frame[split_y, :] = self.c_dusk_pink * 0.7
        # Invert the bottom block slightly with lila tint
        frame[split_y + 1:, :, 0] = np.clip(frame[split_y + 1:, :, 0] + 15, 0, 255)
        frame[split_y + 1:, :, 2] = np.clip(frame[split_y + 1:, :, 2] + 30, 0, 255)

        return np.clip(frame, 0, 255).astype(np.uint8)

    def _render_movement_3(self, local_t):
        """
        Satz III: Moiré & Phaseninterferenz (Phase Shift Frequency)
        Palette: Helle Beigetöne / Graphit / Schiefer.
        Zwei hochfrequente Linienraster überlagern sich und erzeugen Schwebungen.
        """
        frame = np.full((self.height, self.width, 3), self.c_beige_bg, dtype=np.float32)

        # Frequency Modulation over time
        f1 = 0.65 + 0.15 * math.sin(local_t * 0.9)
        f2 = 0.58 + 0.18 * math.cos(local_t * 1.1)

        # Carrier 1: Vertical raster lines
        raster1 = 0.5 + 0.5 * np.sin(self.x * f1 + local_t * 2.4)
        
        # Carrier 2: Angle-tilted phase wave
        phase_angle = 0.25 * math.sin(local_t * 0.5)
        carrier2_x = self.x + self.y * phase_angle
        raster2 = 0.5 + 0.5 * np.sin(carrier2_x * f2 - local_t * 3.1)

        # Moiré interference product
        moire = raster1 * raster2

        # High-contrast thresholding for graphic print-like clarity
        clean_bars = np.where(moire > 0.42, (moire - 0.42) / 0.58, 0.0)

        # Base graphite layer
        frame += (raster1 * 0.35)[:, :, None] * self.c_beige_dark

        # Moiré bands rendered in warm sandstone and ivory
        frame += (clean_bars * 0.75)[:, :, None] * self.c_beige_mid
        peaks = np.clip((clean_bars - 0.6) * 2.5, 0.0, 1.0)
        frame += peaks[:, :, None] * self.c_beige_ivory

        # Center minimalist framing line
        center_y = self.height // 2
        frame[center_y, :] = self.c_beige_light

        return np.clip(frame, 0, 255).astype(np.uint8)

    def _render_movement_4(self, local_t):
        """
        Satz IV: Impuls & Geometrischer Kollaps (Pulse & Frames)
        Palette: Dunkelblau / Lila / Neon Pink.
        Rechteckige Boxen expandieren rhythmisch von innen nach außen und kollabieren.
        """
        frame = np.full((self.height, self.width, 3), self.c_dusk_bg, dtype=np.float32)

        # Tempo: 120 BPM syncopated pulse (beat every 0.5 seconds)
        beat = (local_t * 2.0) % 1.0
        cycle_idx = int(local_t * 2.0)

        cx, cy = 31.5, 15.5

        # 1. Multiple expanding rectangular concentric frames
        for i in range(4):
            offset = (beat + i * 0.25) % 1.0
            scale = offset * 34.0  # radius expansion
            w_box = scale * 1.9
            h_box = scale

            x0 = int(cx - w_box * 0.5)
            x1 = int(cx + w_box * 0.5)
            y0 = int(cy - h_box * 0.5)
            y1 = int(cy + h_box * 0.5)

            # Intensity fades out as it expands outward
            intensity = math.exp(-offset * 2.8)
            col = self.c_dusk_pink if (i % 2 == 0) else self.c_dusk_lilac

            if 0 <= x0 < self.width and 0 <= x1 < self.width and 0 <= y0 < self.height and 0 <= y1 < self.height:
                frame[y0, max(0, x0):min(self.width, x1)] += col * intensity
                frame[y1, max(0, x0):min(self.width, x1)] += col * intensity
                frame[max(0, y0):min(self.height, y1), x0] += col * intensity
                frame[max(0, y0):min(self.height, y1), x1] += col * intensity

        # 2. Central focal geometry
        core_flash = math.exp(-beat * 6.0)
        frame[14:18, 30:34] = (self.c_dusk_highlight * core_flash) + (self.c_dusk_lila * (1.0 - core_flash))

        # 3. Fast horizontal rhythmic ticks at top and bottom
        tick_phase = int(local_t * 24.0) % self.width
        tick_w = 6
        tx0 = max(0, tick_phase - tick_w)
        tx1 = min(self.width, tick_phase + tick_w)
        frame[0, tx0:tx1] = self.c_dusk_pink
        frame[self.height - 1, tx0:tx1] = self.c_dusk_lilac

        return np.clip(frame, 0, 255).astype(np.uint8)

    def render(self) -> np.ndarray:
        t = self.time
        total_cycle = self.total_movements * self.movement_duration
        current_cycle_t = t % total_cycle

        movement_idx = int(current_cycle_t // self.movement_duration)
        local_t = current_cycle_t % self.movement_duration

        # Render current movement
        render_methods = [
            self._render_movement_1,
            self._render_movement_2,
            self._render_movement_3,
            self._render_movement_4
        ]
        
        current_frame = render_methods[movement_idx](local_t)

        # Check for smooth cross-dissolve to next movement
        time_until_next = self.movement_duration - local_t
        if time_until_next <= self.transition_duration:
            next_idx = (movement_idx + 1) % self.total_movements
            next_frame = render_methods[next_idx](self.transition_duration - time_until_next)
            
            # Linear alpha crossfade
            blend = (self.transition_duration - time_until_next) / self.transition_duration
            mixed = (1.0 - blend) * current_frame.astype(np.float32) + blend * next_frame.astype(np.float32)
            return np.clip(mixed, 0, 255).astype(np.uint8)

        return current_frame
