import math
import random
import numpy as np
from .base import VisualEffect

class NeonEye(VisualEffect):
    """
    Realistic animated neon-green eye for 64x32 LED matrix.
    Fills nearly the entire display with anatomically detailed almond eyelids,
    palpebral crease, spherical sclera shading, radiating iris striae,
    breathing pupil (hippus), 3D corneal catchlight glints, natural saccades,
    and spontaneous blinks.
    """

    def __init__(self, width=64, height=32, palette_manager=None, name="NeonEye"):
        super().__init__(width, height, palette_manager, name=name)

        # Anatomical eye center and dimensions (fills nearly entire 64x32 panel)
        self.cx = 31.5
        self.cy = 15.5
        self.wx = 28.5  # Horizontal span: x from ~3.0 to ~60.0
        self.H_top = 12.5  # Vertical top lid span
        self.H_bot = 11.5  # Vertical bottom lid span

        # Normalized horizontal coordinates
        u = (self.x - self.cx) / self.wx
        self.u_valid = np.abs(u) <= 1.0
        self.u_clamped = np.clip(u, -1.0, 1.0)
        self.u2 = np.sqrt(np.maximum(0.0, 1.0 - self.u_clamped**2))

        # Rest contours for upper and lower eyelids (natural human almond curvature)
        self.y_top_rest = self.cy - self.H_top * self.u2 * (1.0 - 0.12 * self.u_clamped)
        self.y_bot_rest = self.cy + self.H_bot * self.u2 * (1.0 + 0.08 * self.u_clamped)

        # Precomputed spherical sclera curvature shading
        d_sphere = np.sqrt(((self.x - self.cx) / 28.5)**2 + ((self.y - self.cy) / 12.0)**2)
        self.sphere_shading = np.clip(1.0 - 0.65 * (d_sphere ** 1.8), 0.15, 1.0)

        # Fine capillary micro-vein texture in sclera
        vein_pattern = np.sin(self.x * 1.25 + np.sin(self.y * 1.4) * 2.2) * np.cos(self.y * 1.7)
        self.vein_mask = (vein_pattern > 0.62) & (np.abs(self.u_clamped) > 0.35)

        # Gaze state machine
        self.current_gaze = np.array([0.0, 0.0], dtype=np.float32)
        self.target_gaze = np.array([0.0, 0.0], dtype=np.float32)
        self.start_gaze = np.array([0.0, 0.0], dtype=np.float32)
        self.saccade_t = 0.0
        self.saccade_dur = 0.15
        self.is_saccading = False
        self.fixation_timer = 2.0

        # Blink state machine
        self.blink_timer = 3.0
        self.is_blinking = False
        self.blink_t = 0.0
        self.blink_close_dur = 0.085
        self.blink_hold_dur = 0.035
        self.blink_open_dur = 0.145
        self.blink_progress = 0.0
        self.queued_double_blink = False

        # Color palette constants (Neon Green aesthetic)
        self.col_sclera = np.array([8.0, 42.0, 16.0], dtype=np.float32)
        self.col_sclera_vein = np.array([16.0, 75.0, 26.0], dtype=np.float32)
        self.col_iris_dark = np.array([4.0, 95.0, 30.0], dtype=np.float32)
        self.col_iris_bright = np.array([30.0, 255.0, 80.0], dtype=np.float32)
        self.col_iris_ruff = np.array([135.0, 255.0, 90.0], dtype=np.float32)
        self.col_rim_top = np.array([0.0, 230.0, 70.0], dtype=np.float32)
        self.col_rim_bot = np.array([25.0, 200.0, 75.0], dtype=np.float32)
        self.col_crease = np.array([0.0, 75.0, 25.0], dtype=np.float32)

    def _pick_next_gaze(self):
        targets = [
            (0.0, 0.0),
            (0.0, 0.0),
            (-7.0, -0.8),
            (-5.5, 1.8),
            (7.0, -0.8),
            (5.5, 1.8),
            (-3.5, -2.2),
            (3.5, -2.2),
            (-2.0, 0.5),
            (2.0, 0.5),
            (0.0, 2.2),
            (random.uniform(-1.5, 1.5), random.uniform(-1.0, 1.0))
        ]
        return np.array(random.choice(targets), dtype=np.float32)

    def update(self, dt):
        super().update(dt)

        # 1. Gaze Saccades & Fixations
        if self.is_saccading:
            self.saccade_t += dt
            t_norm = np.clip(self.saccade_t / self.saccade_dur, 0.0, 1.0)
            # Quintic smoothstep for smooth ballistic movement without jerk
            ease = t_norm * t_norm * t_norm * (t_norm * (t_norm * 6.0 - 15.0) + 10.0)
            self.current_gaze = self.start_gaze + (self.target_gaze - self.start_gaze) * ease

            if self.saccade_t >= self.saccade_dur:
                self.current_gaze = self.target_gaze.copy()
                self.is_saccading = False
                self.fixation_timer = random.uniform(1.4, 3.4)
        else:
            self.fixation_timer -= dt
            if self.fixation_timer <= 0.0:
                self.is_saccading = True
                self.saccade_t = 0.0
                self.saccade_dur = random.uniform(0.12, 0.17)
                self.start_gaze = self.current_gaze.copy()
                self.target_gaze = self._pick_next_gaze()

        # 2. Spontaneous Blinking
        if self.is_blinking:
            self.blink_t += dt
            t_close = self.blink_close_dur
            t_hold = t_close + self.blink_hold_dur
            t_open = t_hold + self.blink_open_dur

            if self.blink_t < t_close:
                # Fast down-sweep
                p = self.blink_t / t_close
                self.blink_progress = p * p  # Accelerate downward
            elif self.blink_t < t_hold:
                # Closed pause
                self.blink_progress = 1.0
            elif self.blink_t < t_open:
                # Smooth reopening
                p = (self.blink_t - t_hold) / self.blink_open_dur
                self.blink_progress = 1.0 - (p * (2.0 - p))
            else:
                self.blink_progress = 0.0
                self.is_blinking = False

                if self.queued_double_blink:
                    self.queued_double_blink = False
                    self.blink_timer = 0.16
                else:
                    self.blink_timer = random.uniform(2.5, 5.0)
                    self.queued_double_blink = (random.random() < 0.22)
        else:
            self.blink_timer -= dt
            if self.blink_timer <= 0.0:
                self.is_blinking = True
                self.blink_t = 0.0
                self.blink_progress = 0.0

    def render(self) -> np.ndarray:
        # Micro-tremor / ocular drift when fixating
        if not self.is_saccading:
            tremor_x = 0.25 * math.sin(self.time * 4.5) + 0.10 * math.sin(self.time * 11.3)
            tremor_y = 0.20 * math.cos(self.time * 3.8) + 0.08 * math.cos(self.time * 9.7)
        else:
            tremor_x = 0.0
            tremor_y = 0.0

        gx = float(self.current_gaze[0] + tremor_x)
        gy = float(self.current_gaze[1] + tremor_y)
        gaze_center_x = self.cx + gx
        gaze_center_y = self.cy + gy

        # Eyelid positioning with blink interpolation
        y_top = self.y_top_rest + self.blink_progress * (self.y_bot_rest - self.y_top_rest + 0.3)
        y_bot = self.y_bot_rest - self.blink_progress * 1.5

        inside_eye = (self.y >= y_top) & (self.y <= y_bot) & self.u_valid

        buf = np.zeros((self.height, self.width, 3), dtype=np.float32)

        # Upper eyelid cast shadow on eyeball surface
        lid_shadow = np.clip((self.y - y_top) / 3.0, 0.35, 1.0)
        shading = self.sphere_shading * lid_shadow

        # 1. Sclera
        sclera_color = self.col_sclera[None, None, :] * shading[:, :, None]
        vein_tint = self.col_sclera_vein[None, None, :] * shading[:, :, None]
        sclera_color[self.vein_mask] = vein_tint[self.vein_mask]
        buf[inside_eye] = sclera_color[inside_eye]

        # 2. Iris
        dx_iris = self.x - gaze_center_x
        dy_iris = self.y - gaze_center_y
        r_iris = np.sqrt(dx_iris**2 + dy_iris**2)
        theta = np.arctan2(dy_iris, dx_iris)

        R_iris = 11.4
        # Pupil breathing (hippus) and saccadic constriction
        hippus = 0.45 * math.sin(self.time * 1.7) + 0.20 * math.cos(self.time * 2.9)
        saccade_constrict = -0.35 if self.is_saccading else 0.0
        R_pupil = 4.3 + hippus + saccade_constrict

        iris_mask = inside_eye & (r_iris <= R_iris)

        # Radiating iris striae and concentric crypt rings
        fiber1 = np.sin(18.0 * theta + np.sin(3.5 * r_iris))
        fiber2 = np.sin(38.0 * theta - 0.3 * np.sin(2.2 * r_iris))
        fiber3 = math.cos(self.time * 0.35) * np.cos(56.0 * theta)
        fiber = 0.5 + 0.26 * fiber1 + 0.14 * fiber2 + 0.10 * fiber3
        fiber = np.clip(fiber, 0.0, 1.0)

        limbal = np.clip((R_iris - r_iris) / 1.6, 0.0, 1.0)
        ruff = np.exp(-((r_iris - (R_pupil + 0.9))**2) / 0.75)

        iris_col = self.col_iris_dark + (self.col_iris_bright - self.col_iris_dark) * fiber[:, :, None]
        iris_col = iris_col * limbal[:, :, None] + self.col_iris_ruff * ruff[:, :, None]
        iris_col = iris_col * lid_shadow[:, :, None]
        buf[iris_mask] = iris_col[iris_mask]

        # 3. Pupil (void black with subpixel anti-aliasing)
        pupil_factor = np.clip((r_iris - (R_pupil - 0.4)) / 0.8, 0.0, 1.0)
        pupil_factor = pupil_factor ** 2
        pupil_mask = inside_eye & (r_iris <= R_pupil + 0.4)
        buf[pupil_mask] = buf[pupil_mask] * pupil_factor[pupil_mask, None]

        # 4. Corneal Specular Catchlight (3D parallax glint)
        clx1 = self.cx + gx * 0.65 - 3.1
        cly1 = self.cy + gy * 0.65 - 2.6
        d_cl1 = np.sqrt((self.x - clx1)**2 + (self.y - cly1)**2 * 1.3)
        spec1_core = np.exp(-(d_cl1**2) / 0.65)[:, :, None] * np.array([245.0, 255.0, 245.0], dtype=np.float32)
        spec1_halo = np.exp(-(d_cl1**2) / 2.4)[:, :, None] * np.array([75.0, 255.0, 130.0], dtype=np.float32)

        clx2 = clx1 + 2.3
        cly2 = cly1 + 1.8
        d_cl2 = np.sqrt((self.x - clx2)**2 + (self.y - cly2)**2)
        spec2_core = np.exp(-(d_cl2**2) / 0.45)[:, :, None] * np.array([215.0, 255.0, 225.0], dtype=np.float32)

        total_spec = spec1_core + spec1_halo + spec2_core
        buf[inside_eye] += total_spec[inside_eye]

        # 5. Eyelid Rims, Wet Waterline and Closed Seam
        rim_scale = 1.0 - 0.25 * np.abs(self.u_clamped)
        dist_top = np.abs(self.y - y_top)
        rim_top = np.exp(-(dist_top**2) / 0.65) * self.u_valid * rim_scale
        dist_bot = np.abs(self.y - y_bot)
        rim_bot = np.exp(-(dist_bot**2) / 0.65) * self.u_valid * rim_scale

        open_factor = 1.0 - 0.5 * self.blink_progress
        buf += rim_top[:, :, None] * (self.col_rim_top * open_factor)
        buf += rim_bot[:, :, None] * (self.col_rim_bot * open_factor)

        # 6. Upper Palpebral Crease (remains at upper arch during blinks)
        if self.blink_progress > 0.05:
            crease_top = np.exp(-((self.y - self.y_top_rest)**2) / 0.75) * self.u_valid * rim_scale
            buf += crease_top[:, :, None] * (self.col_crease * self.blink_progress)

        # 7. Ambient ocular socket glow outside lids
        dist_outer = np.maximum(0.0, np.maximum(y_top - self.y, self.y - y_bot))
        outer_mask = (~inside_eye) & self.u_valid & (dist_outer <= 2.2)
        socket_glow = np.exp(-(dist_outer**2) / 1.4) * rim_scale
        buf[outer_mask] += socket_glow[outer_mask, None] * np.array([0.0, 45.0, 15.0], dtype=np.float32)

        return np.clip(buf, 0, 255).astype(np.uint8)
