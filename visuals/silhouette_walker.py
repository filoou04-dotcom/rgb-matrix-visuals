import math
import random
import numpy as np
from .base import VisualEffect

# Walk cycle frames for a 10-pixel-tall human profile (facing right by default)
WALK_FRAMES = [
    # Frame 0: Contact (lead leg forward, rear leg back)
    [
        [0, 0, 1, 1, 0, 0, 0],
        [0, 0, 1, 1, 0, 0, 0],
        [0, 1, 1, 1, 0, 0, 0],
        [0, 0, 1, 1, 1, 0, 0],
        [0, 0, 1, 1, 0, 0, 0],
        [0, 0, 1, 1, 0, 0, 0],
        [0, 0, 1, 1, 0, 0, 0],
        [0, 1, 0, 0, 1, 0, 0],
        [1, 0, 0, 0, 0, 1, 0],
        [1, 1, 0, 0, 0, 1, 1],
    ],
    # Frame 1: Recoil / Down
    [
        [0, 0, 1, 1, 0, 0, 0],
        [0, 0, 1, 1, 0, 0, 0],
        [0, 1, 1, 1, 0, 0, 0],
        [0, 0, 1, 1, 1, 0, 0],
        [0, 0, 1, 1, 0, 0, 0],
        [0, 0, 1, 1, 0, 0, 0],
        [0, 0, 1, 1, 0, 0, 0],
        [0, 0, 1, 1, 0, 0, 0],
        [0, 1, 0, 0, 1, 0, 0],
        [0, 1, 0, 0, 0, 1, 0],
    ],
    # Frame 2: Passing
    [
        [0, 0, 1, 1, 0, 0, 0],
        [0, 0, 1, 1, 0, 0, 0],
        [0, 1, 1, 1, 0, 0, 0],
        [0, 0, 1, 1, 1, 0, 0],
        [0, 0, 1, 1, 0, 0, 0],
        [0, 0, 1, 1, 0, 0, 0],
        [0, 0, 1, 1, 0, 0, 0],
        [0, 0, 1, 1, 0, 0, 0],
        [0, 0, 1, 0, 1, 0, 0],
        [0, 0, 1, 0, 0, 0, 0],
    ],
    # Frame 3: Stride out
    [
        [0, 0, 1, 1, 0, 0, 0],
        [0, 0, 1, 1, 0, 0, 0],
        [0, 1, 1, 1, 0, 0, 0],
        [0, 0, 1, 1, 1, 0, 0],
        [0, 0, 1, 1, 0, 0, 0],
        [0, 0, 1, 1, 0, 0, 0],
        [0, 0, 1, 1, 0, 0, 0],
        [0, 1, 0, 1, 0, 0, 0],
        [0, 1, 0, 0, 1, 0, 0],
        [0, 1, 0, 0, 0, 1, 0],
    ],
    # Frame 4: Opposite contact
    [
        [0, 0, 1, 1, 0, 0, 0],
        [0, 0, 1, 1, 0, 0, 0],
        [0, 1, 1, 1, 0, 0, 0],
        [0, 0, 1, 1, 1, 0, 0],
        [0, 0, 1, 1, 0, 0, 0],
        [0, 0, 1, 1, 0, 0, 0],
        [0, 0, 1, 1, 0, 0, 0],
        [0, 0, 1, 0, 1, 0, 0],
        [0, 1, 0, 0, 0, 1, 0],
        [1, 1, 0, 0, 1, 1, 0],
    ],
    # Frame 5: Opposite recoil
    [
        [0, 0, 1, 1, 0, 0, 0],
        [0, 0, 1, 1, 0, 0, 0],
        [0, 1, 1, 1, 0, 0, 0],
        [0, 0, 1, 1, 1, 0, 0],
        [0, 0, 1, 1, 0, 0, 0],
        [0, 0, 1, 1, 0, 0, 0],
        [0, 0, 1, 1, 0, 0, 0],
        [0, 0, 1, 1, 0, 0, 0],
        [0, 0, 1, 0, 1, 0, 0],
        [0, 0, 1, 0, 0, 1, 0],
    ],
    # Frame 6: Opposite passing
    [
        [0, 0, 1, 1, 0, 0, 0],
        [0, 0, 1, 1, 0, 0, 0],
        [0, 1, 1, 1, 0, 0, 0],
        [0, 0, 1, 1, 1, 0, 0],
        [0, 0, 1, 1, 0, 0, 0],
        [0, 0, 1, 1, 0, 0, 0],
        [0, 0, 1, 1, 0, 0, 0],
        [0, 0, 1, 1, 0, 0, 0],
        [0, 1, 0, 1, 0, 0, 0],
        [0, 0, 0, 1, 0, 0, 0],
    ],
    # Frame 7: Opposite stride
    [
        [0, 0, 1, 1, 0, 0, 0],
        [0, 0, 1, 1, 0, 0, 0],
        [0, 1, 1, 1, 0, 0, 0],
        [0, 0, 1, 1, 1, 0, 0],
        [0, 0, 1, 1, 0, 0, 0],
        [0, 0, 1, 1, 0, 0, 0],
        [0, 0, 1, 1, 0, 0, 0],
        [0, 0, 1, 0, 1, 0, 0],
        [0, 1, 0, 0, 1, 0, 0],
        [0, 1, 0, 0, 0, 1, 0],
    ]
]

STAND_FRAME = [
    [0, 0, 1, 1, 0, 0, 0],
    [0, 0, 1, 1, 0, 0, 0],
    [0, 1, 1, 1, 0, 0, 0],
    [0, 0, 1, 1, 1, 0, 0],
    [0, 0, 1, 1, 0, 0, 0],
    [0, 0, 1, 1, 0, 0, 0],
    [0, 0, 1, 1, 0, 0, 0],
    [0, 0, 1, 1, 0, 0, 0],
    [0, 0, 1, 1, 0, 0, 0],
    [0, 0, 1, 1, 1, 0, 0],
]

# Front-facing standing/turning frame
FRONT_STAND_FRAME = [
    [0, 0, 1, 1, 0, 0, 0],  # head
    [0, 0, 1, 1, 0, 0, 0],  # head
    [0, 1, 1, 1, 1, 0, 0],  # shoulders
    [1, 0, 1, 1, 0, 1, 0],  # arms by side, chest
    [1, 0, 1, 1, 0, 1, 0],  # torso
    [0, 1, 1, 1, 1, 0, 0],  # waist
    [0, 0, 1, 1, 0, 0, 0],  # pelvis
    [0, 1, 0, 0, 1, 0, 0],  # thighs
    [0, 1, 0, 0, 1, 0, 0],  # calves
    [1, 1, 0, 0, 1, 1, 0],  # feet
]

# Horizontally flipped for walking right-to-left
SPRITES_LEFT = [np.fliplr(np.array(f, dtype=np.uint8)) for f in WALK_FRAMES]
SPRITE_STAND_LEFT = np.fliplr(np.array(STAND_FRAME, dtype=np.uint8))
SPRITE_FRONT_STAND = np.array(FRONT_STAND_FRAME, dtype=np.uint8)

class SilhouetteWalker(VisualEffect):
    """
    Programm 4:
    A white silhouette of a person (height ~10px) walking from RIGHT to LEFT.
    Pass 1: Walks completely across from right to left.
    Pass 2: Enters from right, stops slightly off-center, pauses, turns to the
            viewer, then sprints forward in dynamic 3D perspective until the
            entire panel is completely covered in solid white, followed by a cut.
    """
    def __init__(self, width=64, height=32, palette_manager=None):
        super().__init__(width, height, palette_manager, name="SilhouetteWalker")
        
        # Spatial setup
        self.y_pos = 20  # Base row: feet touch y=29
        self.feet_y = 29.0
        self.walk_speed = 11.5   # pixels per second
        self.step_rate = 9.0     # walk cycle frames per second
        
        # State machine
        # 'PASS1_WALK', 'PASS1_PAUSE', 'PASS2_WALK', 'PASS2_STOP', 'RUSH_FORWARD', 'WHITE_OUT', 'BLACK_OUT'
        self.pass_num = 1
        self.state = 'PASS1_WALK'
        self.state_timer = 0.0
        self.walk_frame_time = 0.0
        self.current_frame_idx = 0
        
        # Start at right edge, walking left
        self.x_pos = float(width + 8)
        self.stop_x = 38.0  # Slightly right of center (width=64, center=32)
        self.pause_duration = 2.0
        self.stop_duration = 1.6
        self.rush_duration = 2.8
        self.whiteout_duration = 1.0
        self.blackout_duration = 0.6
        
        # Schedule optional mid-walk pause during pass 1
        self.pass1_pause_x = random.uniform(18.0, 42.0)
        self.pass1_has_paused = False

    def reset_to_pass1(self):
        self.pass_num = 1
        self.state = 'PASS1_WALK'
        self.state_timer = 0.0
        self.x_pos = float(self.width + 8)
        self.pass1_has_paused = False
        self.pass1_pause_x = random.uniform(18.0, 42.0)

    def update(self, dt):
        super().update(dt)
        self.state_timer += dt

        # Pass 1: Walking across from right to left
        if self.state == 'PASS1_WALK':
            self.x_pos -= self.walk_speed * dt
            self.walk_frame_time += dt
            self.current_frame_idx = int(self.walk_frame_time * self.step_rate) % len(SPRITES_LEFT)

            # Optional natural pause during Pass 1
            if not self.pass1_has_paused and self.x_pos <= self.pass1_pause_x:
                self.state = 'PASS1_PAUSE'
                self.state_timer = 0.0
                self.pause_duration = random.uniform(1.5, 2.5)
                self.pass1_has_paused = True

            # Walked off the left edge
            if self.x_pos < -9.0:
                self.pass_num = 2
                self.state = 'PASS2_WALK'
                self.state_timer = 0.0
                self.x_pos = float(self.width + 8)

        elif self.state == 'PASS1_PAUSE':
            if self.state_timer >= self.pause_duration:
                self.state = 'PASS1_WALK'
                self.state_timer = 0.0

        # Pass 2: Walking from right, stopping slightly off-center
        elif self.state == 'PASS2_WALK':
            self.x_pos -= self.walk_speed * dt
            self.walk_frame_time += dt
            self.current_frame_idx = int(self.walk_frame_time * self.step_rate) % len(SPRITES_LEFT)

            if self.x_pos <= self.stop_x:
                self.x_pos = self.stop_x
                self.state = 'PASS2_STOP'
                self.state_timer = 0.0
                self.stop_duration = 1.6  # Moment of hesitation before turning

        # Standing still, then turning to viewer
        elif self.state == 'PASS2_STOP':
            if self.state_timer >= self.stop_duration:
                self.state = 'RUSH_FORWARD'
                self.state_timer = 0.0
                self.rush_duration = 2.8  # Seconds of explosive forward sprint

        # Sprinting towards the viewer (exponential perspective growth)
        elif self.state == 'RUSH_FORWARD':
            if self.state_timer >= self.rush_duration:
                self.state = 'WHITE_OUT'
                self.state_timer = 0.0
                self.whiteout_duration = 1.0  # Hold full white screen

        # Screen entirely covered in white
        elif self.state == 'WHITE_OUT':
            if self.state_timer >= self.whiteout_duration:
                self.state = 'BLACK_OUT'
                self.state_timer = 0.0
                self.blackout_duration = 0.6  # Brief blackout cut

        # Blackout reset back to Pass 1
        elif self.state == 'BLACK_OUT':
            if self.state_timer >= self.blackout_duration:
                self.reset_to_pass1()

    def _render_perspective_runner(self, progress: float) -> np.ndarray:
        """
        Renders the front-facing runner scaling dynamically with perspective expansion.
        progress in [0.0, 1.0] over the rush duration.
        """
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        
        # Non-linear acceleration: apparent size increases quadratically (1/z projection)
        # Scale: 1.0 at start (10px height) -> 7.5 at finish (over 70px tall, completely filling panel)
        scale = 1.0 + (progress ** 2.3) * 6.5
        
        # Center horizontally drifts towards center of screen (from stop_x=38 towards 32)
        cx = self.stop_x + (32.0 - self.stop_x) * min(1.0, progress * 1.3)
        
        # The runner's feet anchor drops downward off-screen as they get closer
        feet_y = self.feet_y + progress * 18.0
        
        # Running cycle parameters (approx 3.5 steps/sec)
        run_freq = 22.0
        phase = progress * run_freq
        
        total_h = 10.0 * scale
        head_r = 1.2 * scale
        
        # Vertical head/body bobbing
        bob = abs(math.sin(phase)) * 0.45 * scale
        head_cy = feet_y - total_h + head_r - bob
        torso_top = head_cy + head_r * 0.8
        torso_bottom = feet_y - 3.2 * scale - bob
        
        # Arm swing
        arm_swing = math.sin(phase) * 1.6 * scale
        
        # Precomputed coordinate mesh
        y_f = self.y
        x_f = self.x
        
        # 1. Head (ellipse)
        head_dist_sq = (x_f - cx)**2 + ((y_f - head_cy) * 1.15)**2
        mask_head = head_dist_sq <= (head_r * 1.15)**2
        
        # 2. Torso & Shoulders (tapered trapezoid)
        shoulder_w = 2.4 * scale
        in_torso_y = (y_f >= torso_top) & (y_f <= torso_bottom)
        y_rel = (y_f - torso_top) / max(0.1, (torso_bottom - torso_top))
        half_w = (shoulder_w * (1.0 - y_rel * 0.28)) * 0.5
        mask_torso = in_torso_y & (np.abs(x_f - cx) <= half_w)
        
        # 3. Pumping Arms
        arm_w = max(1.0, 0.8 * scale)
        left_arm_x = cx - half_w - arm_w * 0.55
        right_arm_x = cx + half_w + arm_w * 0.55
        mask_arm1 = (y_f >= torso_top) & (y_f <= torso_top + 3.4 * scale) & (np.abs(x_f - left_arm_x) <= arm_w * 0.6)
        mask_arm2 = (y_f >= torso_top) & (y_f <= torso_top + 3.4 * scale) & (np.abs(x_f - right_arm_x) <= arm_w * 0.6)
        
        # 4. Striding Legs
        leg_w = max(1.0, 0.75 * scale)
        in_leg_y = (y_f > torso_bottom) & (y_f <= feet_y)
        leg1_x = cx - (0.35 * scale) - (math.sin(phase) * 0.6 * scale)
        leg2_x = cx + (0.35 * scale) + (math.sin(phase) * 0.6 * scale)
        mask_leg1 = in_leg_y & (np.abs(x_f - leg1_x) <= leg_w * 0.6)
        mask_leg2 = in_leg_y & (np.abs(x_f - leg2_x) <= leg_w * 0.6)
        
        body_mask = mask_head | mask_torso | mask_arm1 | mask_arm2 | mask_leg1 | mask_leg2
        
        # 5. Full coverage flood when crashing into camera (scale > 5.0)
        if scale >= 5.0:
            flood_progress = min(1.0, (scale - 5.0) / 2.0)
            flood_r = flood_progress * 55.0
            dist_sq = (x_f - cx)**2 + (y_f - 16.0)**2
            body_mask = body_mask | (dist_sq <= flood_r**2)
            
        frame[body_mask] = [255, 255, 255]
        return frame

    def render(self) -> np.ndarray:
        # State: Solid Whiteout
        if self.state == 'WHITE_OUT':
            return np.full((self.height, self.width, 3), 255, dtype=np.uint8)

        # State: Blackout reset
        if self.state == 'BLACK_OUT':
            return np.zeros((self.height, self.width, 3), dtype=np.uint8)

        # State: Rushing forward at the viewer
        if self.state == 'RUSH_FORWARD':
            progress = min(1.0, self.state_timer / self.rush_duration)
            return self._render_perspective_runner(progress)

        # Profile silhouette rendering (walking or standing)
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        
        if self.state in ('PASS1_WALK', 'PASS2_WALK'):
            sprite = SPRITES_LEFT[self.current_frame_idx]
        elif self.state == 'PASS1_PAUSE':
            sprite = SPRITE_STAND_LEFT
        elif self.state == 'PASS2_STOP':
            # In the second half of the stop duration, turn towards front
            if self.state_timer >= (self.stop_duration * 0.65):
                sprite = SPRITE_FRONT_STAND
            else:
                sprite = SPRITE_STAND_LEFT
        else:
            sprite = SPRITE_STAND_LEFT

        s_h, s_w = sprite.shape
        int_x = int(round(self.x_pos))
        int_y = int(self.y_pos)

        # Blit sprite with boundary clipping
        for r in range(s_h):
            py = int_y + r
            if 0 <= py < self.height:
                for c in range(s_w):
                    px = int_x + c
                    if 0 <= px < self.width and sprite[r, c] == 1:
                        frame[py, px] = [255, 255, 255]

        return frame
