import math
import random
import numpy as np
from .base import VisualEffect

THEMES = [
    {
        "name": "retro_pink",
        "core": np.array([255.0, 175.0, 225.0], dtype=np.float32),
        "mid":  np.array([235.0, 35.0, 120.0], dtype=np.float32),
        "rim":  np.array([140.0, 12.0, 65.0], dtype=np.float32),
        "halo": np.array([60.0, 12.0, 38.0], dtype=np.float32),
        "bulb": np.array([32.0, 18.0, 26.0], dtype=np.float32),
    },
    {
        "name": "vintage_amber",
        "core": np.array([245.0, 160.0, 30.0], dtype=np.float32),
        "mid":  np.array([215.0, 85.0, 12.0], dtype=np.float32),
        "rim":  np.array([155.0, 38.0, 10.0], dtype=np.float32),
        "halo": np.array([75.0, 30.0, 12.0], dtype=np.float32),
        "bulb": np.array([32.0, 26.0, 18.0], dtype=np.float32),
    },
    {
        "name": "ruby_wine",
        "core": np.array([255.0, 110.0, 50.0], dtype=np.float32),
        "mid":  np.array([200.0, 22.0, 22.0], dtype=np.float32),
        "rim":  np.array([115.0, 8.0, 18.0], dtype=np.float32),
        "halo": np.array([55.0, 10.0, 14.0], dtype=np.float32),
        "bulb": np.array([30.0, 18.0, 20.0], dtype=np.float32),
    },
    {
        "name": "electric_violet",
        "core": np.array([225.0, 180.0, 255.0], dtype=np.float32),
        "mid":  np.array([155.0, 40.0, 230.0], dtype=np.float32),
        "rim":  np.array([85.0, 15.0, 150.0], dtype=np.float32),
        "halo": np.array([45.0, 10.0, 75.0], dtype=np.float32),
        "bulb": np.array([26.0, 18.0, 34.0], dtype=np.float32),
    },
    {
        "name": "golden_peach",
        "core": np.array([255.0, 205.0, 130.0], dtype=np.float32),
        "mid":  np.array([240.0, 110.0, 55.0], dtype=np.float32),
        "rim":  np.array([170.0, 45.0, 25.0], dtype=np.float32),
        "halo": np.array([70.0, 25.0, 15.0], dtype=np.float32),
        "bulb": np.array([34.0, 26.0, 20.0], dtype=np.float32),
    },
    {
        "name": "ocean_teal",
        "core": np.array([160.0, 245.0, 235.0], dtype=np.float32),
        "mid":  np.array([20.0, 160.0, 150.0], dtype=np.float32),
        "rim":  np.array([10.0, 95.0, 100.0], dtype=np.float32),
        "halo": np.array([10.0, 45.0, 50.0], dtype=np.float32),
        "bulb": np.array([18.0, 28.0, 30.0], dtype=np.float32),
    },
]

DENSITY_MODES = ["sparse", "viscous", "stalactite_heavy", "dense", "balanced"]

class LavaLamp(VisualEffect):
    """
    Programm 8: Generative Retro-Lavalampe (Hochkant, rahmenlos).
    Prozedural generierte Zyklen alle 15 Sekunden:
    - Weiche Farbuebergaenge (Pink, Bernstein, Rubin, Violett, Pfirsich, Teal)
    - Neutraler, dunkler Anthrazit/Obsidian-Hintergrund
    - Dynamische Dichtemutationen (von minimalistisch bis ueberbordend)
    - Stalaktiten und Tropfenbildung von oben (Kuehlungsreservoir)
    - Stroemungsmarmorierung und Hitzekerne im Inneren des Wachses
    """

    def __init__(self, width=64, height=32, palette_manager=None, name="LavaLamp", orientation="cw"):
        super().__init__(width, height, palette_manager, name=name)

        self.orientation = orientation
        self.sim_h = 64
        self.sim_w = 32
        self.cx = 15.5
        self.sim_time = 0.0

        # Koordinaten
        y_coords, x_coords = np.mgrid[0:self.sim_h, 0:self.sim_w].astype(np.float32)
        self.x = x_coords
        self.y = y_coords

        # Neutraler, dunkler Rauchglas-Hintergrund
        self.base_bg = np.zeros((self.sim_h, self.sim_w, 3), dtype=np.float32)
        for y in range(self.sim_h):
            t_y = y / float(self.sim_h - 1)
            self.base_bg[y, :] = (1.0 - t_y) * np.array([6.0, 7.0, 9.0], dtype=np.float32) + \
                                 t_y * np.array([15.0, 17.0, 21.0], dtype=np.float32)

        bulb_dist = (self.y - 63.0)**2
        self.bulb_glow = np.exp(-bulb_dist / 240.0)[:, :, None]

        # 6 Blob-Knoten mit individuellen Parametern
        self.blobs = [
            {"bx0": 13.0, "ax": 3.6, "wx": 0.32, "phase": 0.05, "base_v": 0.070, "dir": 1},
            {"bx0": 18.0, "ax": 4.2, "wx": 0.28, "phase": 0.35, "base_v": 0.062, "dir": 1},
            {"bx0": 14.0, "ax": 3.0, "wx": 0.40, "phase": 0.65, "base_v": 0.080, "dir": 1},
            {"bx0": 19.0, "ax": 4.5, "wx": 0.25, "phase": 0.85, "base_v": 0.055, "dir": 1},
            {"bx0": 12.0, "ax": 2.8, "wx": 0.44, "phase": 0.20, "base_v": 0.065, "dir": -1}, # Stalaktiten-Tropfen
            {"bx0": 17.0, "ax": 3.5, "wx": 0.36, "phase": 0.70, "base_v": 0.075, "dir": -1}, # Stalaktiten-Tropfen
        ]

        # Generative Epoch-Steuerung (15s Zeitfenster)
        self.epoch_duration = 15.0
        self.blend_duration = 3.0
        self.epoch_time = 0.0

        self.theme_idx = 1 # Start mit vintage_amber
        self.curr_epoch = self._generate_epoch_state(self.theme_idx, "balanced")
        self.next_epoch = self._generate_epoch_state((self.theme_idx + 1) % len(THEMES), "viscous")

    def reset(self):
        """Wird bei manuellem Programmwechsel aufgerufen."""
        self.sim_time = 0.0
        self.epoch_time = 0.0
        self.theme_idx = 1
        self.curr_epoch = self._generate_epoch_state(self.theme_idx, "balanced")
        self.next_epoch = self._generate_epoch_state(0, "stalactite_heavy")

    def set_orientation(self, orientation: str):
        if orientation in ("cw", "ccw"):
            self.orientation = orientation

    def _generate_epoch_state(self, theme_idx, force_mode=None):
        theme = THEMES[theme_idx % len(THEMES)]
        mode = force_mode or random.choice(DENSITY_MODES)

        radii = [0.0] * 6
        stretches = [1.2] * 6
        speed_mult = 1.0
        top_amp = 1.3
        bot_amp = 1.6

        if mode == "sparse":
            # Fast keine Lava: 1 bis 2 isolierte Tropfen
            radii[0] = random.uniform(5.5, 6.5)
            radii[1] = random.uniform(4.8, 5.8)
            stretches[0] = 1.1
            stretches[1] = 1.15
            speed_mult = 0.75
            top_amp = 0.4
            bot_amp = 1.1
        elif mode == "dense":
            # Ganz viel Lava: Grosse Saeulen und Tropfen
            radii[0] = random.uniform(5.5, 6.5)
            radii[1] = random.uniform(5.0, 6.0)
            radii[2] = random.uniform(5.8, 6.8)
            radii[3] = random.uniform(4.5, 5.5)
            radii[4] = random.uniform(4.8, 5.8)
            radii[5] = random.uniform(4.2, 5.2)
            for i in range(6):
                stretches[i] = 1.25
            speed_mult = 1.05
            top_amp = 1.7
            bot_amp = 2.0
        elif mode == "viscous":
            # Dickfluessig: Zaeh, langgezogen, langsam
            radii[0] = random.uniform(6.5, 7.6)
            radii[1] = random.uniform(6.0, 7.2)
            radii[2] = random.uniform(5.8, 6.8)
            stretches[0] = 1.60
            stretches[1] = 1.50
            stretches[2] = 1.40
            speed_mult = 0.55
            top_amp = 1.4
            bot_amp = 1.8
        elif mode == "stalactite_heavy":
            # Mehr Lava von oben: Grosses oberes Reservoir und herabstuerzende Tropfen
            radii[0] = random.uniform(5.0, 6.0)
            radii[1] = random.uniform(4.5, 5.5)
            radii[4] = random.uniform(5.6, 6.8) # Abwaertstropfen
            radii[5] = random.uniform(5.0, 6.2) # Abwaertstropfen
            stretches[4] = 1.40
            stretches[5] = 1.35
            speed_mult = 0.90
            top_amp = 1.8
            bot_amp = 1.4
        else: # balanced
            radii[0] = 5.4
            radii[1] = 4.8
            radii[2] = 5.6
            radii[4] = 4.6
            stretches[0] = 1.25
            stretches[1] = 1.20
            stretches[2] = 1.30
            stretches[4] = 1.25
            speed_mult = 1.0
            top_amp = 1.3
            bot_amp = 1.6

        return {
            "theme": theme,
            "mode": mode,
            "radii": radii,
            "stretches": stretches,
            "speed_mult": speed_mult,
            "top_amp": top_amp,
            "bot_amp": bot_amp,
        }

    def _get_blob_coords(self, b, speed_mult, stretch_override):
        bx = b["bx0"] + b["ax"] * math.sin(self.sim_time * b["wx"])
        c = b["phase"] % 1.0

        if b["dir"] == 1:
            # Aufsteigender Konvektionstropfen
            if c < 0.45:
                p = c / 0.45
                ease = p * p * (3.0 - 2.0 * p)
                by = 56.0 - 46.0 * ease
                sy = stretch_override
            elif c < 0.55:
                p = (c - 0.45) / 0.10
                by = 10.0 + 2.5 * math.sin(p * math.pi)
                sy = 0.90
            elif c < 0.90:
                p = (c - 0.55) / 0.35
                ease = p * p * (3.0 - 2.0 * p)
                by = 10.0 + 46.0 * ease
                sy = stretch_override * 0.92
            else:
                p = (c - 0.90) / 0.10
                by = 56.0 + 2.0 * math.sin(p * math.pi)
                sy = 0.85
        else:
            # Stalaktiten-Tropfen: Bildet sich oben und stuerzt abwaerts
            if c < 0.35:
                # Sammeln und Einschnueren an der Decke
                p = c / 0.35
                by = 5.0 + 8.0 * (p * p)
                sy = stretch_override * 1.15
            elif c < 0.65:
                # Schneller Fall nach unten
                p = (c - 0.35) / 0.30
                ease = p * p * (3.0 - 2.0 * p)
                by = 13.0 + 43.0 * ease
                sy = stretch_override
            elif c < 0.85:
                # Verschmelzen im heissen Bodenbad
                p = (c - 0.65) / 0.20
                by = 56.0 + 3.0 * math.sin(p * math.pi)
                sy = 0.85
            else:
                # Traeger Aufstieg zur Decke
                p = (c - 0.85) / 0.15
                ease = p * p * (3.0 - 2.0 * p)
                by = 56.0 - 51.0 * ease
                sy = stretch_override * 0.90

        return bx, by, sy

    def update(self, dt):
        super().update(dt)
        self.sim_time += dt
        self.epoch_time += dt

        # Fortschritt in der 15s-Epoche
        if self.epoch_time >= self.epoch_duration:
            self.epoch_time -= self.epoch_duration
            self.curr_epoch = self.next_epoch
            # Waehle naechstes Thema (garantiert anders als das aktuelle)
            cur_name = self.curr_epoch["theme"]["name"]
            other_indices = [i for i, th in enumerate(THEMES) if th["name"] != cur_name]
            next_idx = random.choice(other_indices)
            self.next_epoch = self._generate_epoch_state(next_idx)

        # Aktuelle dynamische Multiplikatoren fuer Tropfenbewegung
        trans_start = self.epoch_duration - self.blend_duration
        if self.epoch_time > trans_start:
            p = (self.epoch_time - trans_start) / self.blend_duration
            blend = p * p * (3.0 - 2.0 * p)
        else:
            blend = 0.0

        sp_mult = (1.0 - blend) * self.curr_epoch["speed_mult"] + blend * self.next_epoch["speed_mult"]

        for b in self.blobs:
            b["phase"] = (b["phase"] + b["base_v"] * sp_mult * dt) % 1.0

    def render(self) -> np.ndarray:
        t = self.sim_time
        w = min(1.0, max(0.0, t / 10.0))  # Kalt-Aufwaermphase in den ersten 10 Sekunden

        # 1. Weiche Interpolation zwischen aktueller und naechster Epoche
        trans_start = self.epoch_duration - self.blend_duration
        if self.epoch_time > trans_start:
            p = (self.epoch_time - trans_start) / self.blend_duration
            blend = p * p * (3.0 - 2.0 * p)
        else:
            blend = 0.0

        th_curr = self.curr_epoch["theme"]
        th_next = self.next_epoch["theme"]

        col_core = (1.0 - blend) * th_curr["core"] + blend * th_next["core"]
        col_mid  = (1.0 - blend) * th_curr["mid"]  + blend * th_next["mid"]
        col_rim  = (1.0 - blend) * th_curr["rim"]  + blend * th_next["rim"]
        col_halo = (1.0 - blend) * th_curr["halo"] + blend * th_next["halo"]
        col_bulb = (1.0 - blend) * th_curr["bulb"] + blend * th_next["bulb"]

        top_amp = (1.0 - blend) * self.curr_epoch["top_amp"] + blend * self.next_epoch["top_amp"]
        bot_amp = (1.0 - blend) * self.curr_epoch["bot_amp"] + blend * self.next_epoch["bot_amp"]

        field = np.zeros((self.sim_h, self.sim_w), dtype=np.float32)

        # Bodenbad (dehnt sich bei Waerme aus)
        res_y = 60.5 - 2.0 * w
        field += np.exp(-((self.y - res_y)**2) / (20.0 + 4.0 * w)) * (bot_amp * (0.8 + 0.2 * w))

        # Deckenreservoir fuer Erkaltung ("Lava von oben")
        if t >= 6.0:
            top_w = min(1.0, (t - 6.0) / 4.0)
            field += np.exp(-((self.y - 2.5)**2) / 18.0) * (top_amp * top_w)

        # Warmup-Phasen vs. Konvektionsbetrieb
        if t < 2.5:
            # Phase 1: Kaltzustand
            field += (3.8**2) / ((self.x - 14.0)**2 + (self.y - 11.0)**2 + 1.8)
        elif t < 5.5:
            # Phase 2: Zaehe Stalagmiten
            p = (t - 2.5) / 3.0
            ease = p * p * (3.0 - 2.0 * p)
            h1 = 56.0 - 26.0 * ease
            field += 1.8 * np.exp(-((self.x - 12.0)**2) / 14.0) * np.exp(-((self.y - h1)**2) / 35.0) * (self.y >= h1 - 4.0)
            h2 = 58.0 - 18.0 * ease
            field += 1.5 * np.exp(-((self.x - 20.0)**2) / 12.0) * np.exp(-((self.y - h2)**2) / 30.0) * (self.y >= h2 - 4.0)
            field += (3.8**2) / ((self.x - 14.0)**2 + (self.y - (11.0 + 2.0 * ease))**2 + 1.8)
        elif t < 8.5:
            # Phase 3: Einschnuerung
            p = (t - 5.5) / 3.0
            ease = p * p * (3.0 - 2.0 * p)
            b1_y = 30.0 - 18.0 * ease
            field += (5.2**2) / ((self.x - 12.0)**2 + ((self.y - b1_y) * 0.85)**2 + 1.8)
            b2_y = 40.0 - 14.0 * ease
            field += (4.6**2) / ((self.x - 20.0)**2 + ((self.y - b2_y) * 0.85)**2 + 1.8)
            field += (3.5**2) / ((self.x - 14.0 + 2.0 * ease)**2 + (self.y - (13.0 + 8.0 * ease))**2 + 1.8)
        else:
            # Phase 4: Stetiger generativer Konvektionsfluss
            radii_c = self.curr_epoch["radii"]
            radii_n = self.next_epoch["radii"]
            stretch_c = self.curr_epoch["stretches"]
            stretch_n = self.next_epoch["stretches"]
            sp_mult = (1.0 - blend) * self.curr_epoch["speed_mult"] + blend * self.next_epoch["speed_mult"]

            for i, b in enumerate(self.blobs):
                r = (1.0 - blend) * radii_c[i] + blend * radii_n[i]
                if r <= 0.2:
                    continue
                sy_target = (1.0 - blend) * stretch_c[i] + blend * stretch_n[i]
                bx, by, sy = self._get_blob_coords(b, sp_mult, sy_target)
                d2 = (self.x - bx)**2 + ((self.y - by) / sy)**2
                field += (r**2) / (d2 + 1.8)

        # 2. Hintergrund: Neutrales Obsidian/Anthrazit mit dezentem Sockelglimmen
        bulb_intensity = 0.45 + 0.55 * w
        bg = self.base_bg + (self.bulb_glow * col_bulb * bulb_intensity)

        # 3. Subsurface-Scattering (warmes Ausstrahlen des Wachses in die Fluessigkeit)
        wax_threshold = 1.12
        halo = np.clip((field - 0.60) / 0.52, 0.0, 1.0)[:, :, None]
        frame = bg * (1.0 - 0.55 * halo) + col_halo * (0.55 * halo)

        # 4. Wachskoerper (Doppelter Verlauf: Rim -> Mid -> Core)
        wax_core = np.clip((field - wax_threshold) / 1.35, 0.0, 1.0)
        c1 = col_rim + (col_mid - col_rim) * np.clip(wax_core * 2.0, 0.0, 1.0)[:, :, None]
        c2 = col_mid + (col_core - col_mid) * np.clip(wax_core * 2.0 - 1.0, 0.0, 1.0)[:, :, None]
        wax_col = np.where(wax_core[:, :, None] < 0.5, c1, c2)

        # 5. Innere Stroemungsadern & Konvektionsturbulenz (Marmorierungsdetails)
        internal_vein = 0.5 + 0.5 * np.sin(self.y * 0.45 + np.sin(self.x * 0.35 + t * 0.7) * 2.0)
        core_boost = np.clip((field - 2.0) / 1.1, 0.0, 1.0)[:, :, None]
        wax_col += core_boost * (internal_vein[:, :, None] * 30.0)

        # 6. Weiches Antialiasing der Konturkanten
        edge_alpha = np.clip((field - (wax_threshold - 0.20)) / 0.40, 0.0, 1.0)[:, :, None]
        canvas = frame * (1.0 - edge_alpha) + wax_col * edge_alpha

        # 7. Rotation fuer Hochkant-Darstellung ohne Rahmen
        if self.orientation == "ccw":
            out_frame = np.rot90(canvas, 1)
        else:
            out_frame = np.rot90(canvas, -1)

        return np.clip(out_frame, 0, 255).astype(np.uint8)
