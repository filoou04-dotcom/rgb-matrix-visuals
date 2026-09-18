import random
import numpy as np
from .base import VisualEffect

# Bitmaps for 10-pixel-tall human silhouette in profile walking right.
# 1 = white pixel, 0 = black/transparent.
# Each frame is 10 rows high, 7 cols wide.

WALK_FRAMES = [
    # Frame 0: Contact (left forward, right back)
    [
        [0, 0, 1, 1, 0, 0, 0],  # head
        [0, 0, 1, 1, 0, 0, 0],  # head
        [0, 1, 1, 1, 0, 0, 0],  # neck / shoulder
        [0, 0, 1, 1, 1, 0, 0],  # chest / torso
        [0, 0, 1, 1, 0, 0, 0],  # torso
        [0, 0, 1, 1, 0, 0, 0],  # waist
        [0, 0, 1, 1, 0, 0, 0],  # pelvis
        [0, 1, 0, 0, 1, 0, 0],  # thighs split
        [1, 0, 0, 0, 0, 1, 0],  # calves split
        [1, 1, 0, 0, 0, 1, 1],  # feet contact
    ],
    # Frame 1: Recoil / Down (knees bent, moving weight forward)
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
    # Frame 2: Passing (leg swinging under body)
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
    # Frame 3: High point / Stride out
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
    # Frame 4: Contact opposite (right forward, left back)
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
    # Frame 5: Recoil opposite
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
    # Frame 6: Passing opposite
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
    # Frame 7: Stride out opposite
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

# Frame: Standing still
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

SPRITES = [np.array(f, dtype=np.uint8) for f in WALK_FRAMES]
SPRITE_STAND = np.array(STAND_FRAME, dtype=np.uint8)

class SilhouetteWalker(VisualEffect):
    """
    Programm 4:
    A pure white silhouette of a person (~10 pixels tall) walking
    across the dark void from left to right, randomly pausing to stand,
    then resuming and repeating smoothly.
    """
    def __init__(self, width=64, height=32, palette_manager=None):
        super().__init__(width, height, palette_manager, name="SilhouetteWalker")
        
        # Position and motion
        self.x_pos = -8.0
        self.y_pos = 20  # Feet will touch row y=29 (leaves 2px margin at bottom)
        self.walk_speed = 10.5  # pixels per second (~6.5s to cross)
        self.step_rate = 8.5    # animation frames per second
        
        # State machine: 'WALKING' or 'PAUSED'
        self.state = 'WALKING'
        self.state_timer = 0.0
        self.walk_frame_time = 0.0
        self.current_frame_idx = 0
        
        # Schedule next pause
        self._schedule_next_pause()

    def _schedule_next_pause(self):
        # Pause after walking between 2.0 and 5.0 seconds
        self.time_until_pause = random.uniform(2.2, 5.2)

    def update(self, dt):
        super().update(dt)
        self.state_timer += dt

        if self.state == 'WALKING':
            # Advance horizontal position
            self.x_pos += self.walk_speed * dt
            
            # Animate walk cycle
            self.walk_frame_time += dt
            self.current_frame_idx = int(self.walk_frame_time * self.step_rate) % len(SPRITES)

            # Check if it should pause (only when on-screen between x=12 and x=50)
            if self.state_timer >= self.time_until_pause and 12.0 < self.x_pos < 50.0:
                self.state = 'PAUSED'
                self.state_timer = 0.0
                self.pause_duration = random.uniform(1.8, 3.8)
            
            # Wrap around when fully walked off right edge
            if self.x_pos > self.width + 4.0:
                self.x_pos = -8.0
                self.state_timer = 0.0
                self._schedule_next_pause()

        elif self.state == 'PAUSED':
            # Remain standing still
            if self.state_timer >= self.pause_duration:
                self.state = 'WALKING'
                self.state_timer = 0.0
                self._schedule_next_pause()

    def render(self) -> np.ndarray:
        # Pure dark background
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)

        # Select sprite: walking frame or standing frame
        sprite = SPRITE_STAND if self.state == 'PAUSED' else SPRITES[self.current_frame_idx]
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
