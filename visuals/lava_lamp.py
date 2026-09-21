import math
import numpy as np
from .base import VisualEffect

class LavaLamp(VisualEffect):
    """
    Programm 8: Virtuelle Lavalampe in Orange- und Cyan-Toenen.
    Beginnt im kalten, starren Zustand und erwaermt sich ueber 10 Sekunden
    (Aufwaelbung, zaehe Wachssaeulen / Stalagmiten, Abschnuerung),
    bevor sie in einen stetigen, beruhigenden Konvektionskreislauf uebergeht.
    """

    def __init__(self, width=64, height=32, palette_manager=None, name="LavaLamp"):
        super().__init__(width, height, palette_manager, name=name)

        self.cx = 31.5
        self.cy = 15.5
        self.sim_time = 0.0

        y_coords, x_coords = np.mgrid[0:height, 0:width].astype(np.float32)
        self.x = x_coords
        self.y = y_coords

        # Taillierte Glasform der Lavalampe
        self.glass_w = 26.0 - 3.0 * np.sin(np.pi * self.y / float(height))
        self.glass_dist = np.abs(self.x - self.cx) - self.glass_w
        self.glass_rim = np.exp(-(self.glass_dist**2) / 1.2)[:, :, None] * np.array([50.0, 190.0, 220.0], dtype=np.float32)
        self.outside_glass = self.glass_dist > 0.5

        # 5 zirkulierende Konvektionstropfen fuer den Dauerbetrieb
        self.blobs = [
            {"ax": 5.0, "wx": 0.35, "fx": 0.0, "v": 0.08, "offset": 0.0, "r": 5.2},
            {"ax": 7.0, "wx": 0.28, "fx": 2.0, "v": 0.07, "offset": 0.35, "r": 4.6},
            {"ax": 4.0, "wx": 0.42, "fx": 4.0, "v": 0.09, "offset": 0.65, "r": 5.5},
            {"ax": 8.0, "wx": 0.30, "fx": 1.2, "v": 0.06, "offset": 0.85, "r": 3.8},
            {"ax": 3.0, "wx": 0.45, "fx": 3.5, "v": 0.10, "offset": 0.20, "r": 4.2},
        ]

    def reset(self):
        """Wird bei Programmwechsel aufgerufen, um die Kaltphase neu zu starten."""
        self.sim_time = 0.0

    def _get_convection_blob_pos(self, b, t):
        bx = self.cx + b["ax"] * math.sin(t * b["wx"] + b["fx"])
        cycle = (t * b["v"] + b["offset"]) % 1.0

        if cycle < 0.45:
            # Aufstieg durch thermischen Auftrieb
            p = cycle / 0.45
            ease = p * p * (3.0 - 2.0 * p)
            by = 26.0 - 21.0 * ease
            stretch_y = 1.25
        elif cycle < 0.55:
            # Abkuehlung und Verweilen an der oberen Glasdecke
            p = (cycle - 0.45) / 0.10
            by = 5.0 + 1.5 * math.sin(p * math.pi)
            stretch_y = 0.95
        elif cycle < 0.90:
            # Abkuehlung und langsames Absinken
            p = (cycle - 0.55) / 0.35
            ease = p * p * (3.0 - 2.0 * p)
            by = 6.0 + 20.0 * ease
            stretch_y = 1.15
        else:
            # Rueckkehr und Wiederaufwaermung im Bodenreservoir
            p = (cycle - 0.90) / 0.10
            by = 26.0 + 1.8 * math.sin(p * math.pi)
            stretch_y = 0.90

        return bx, by, stretch_y

    def update(self, dt):
        super().update(dt)
        self.sim_time += dt

    def render(self) -> np.ndarray:
        t = self.sim_time
        w = min(1.0, max(0.0, t / 10.0))

        field = np.zeros((self.height, self.width), dtype=np.float32)

        # Bodenreservoir
        res_y = 29.0 - 1.5 * w
        field += np.exp(-((self.y - res_y)**2) / (10.0 + 3.0 * w)) * (1.6 + 0.3 * (1.0 - w))

        if t < 2.5:
            # Phase 1: Kaltzustand (starr und unbeweglich)
            field += (3.2**2) / ((self.x - 24.0)**2 + (self.y - 6.0)**2 + 1.5)
        elif t < 5.5:
            # Phase 2: Erweichung & Zaehe Stalagmitensaeulen schieben sich nach oben
            p = (t - 2.5) / 3.0
            ease = p * p * (3.0 - 2.0 * p)
            h1 = 26.0 - 12.0 * ease
            field += 1.8 * np.exp(-((self.x - 27.0)**2) / 12.0) * np.exp(-((self.y - h1)**2) / 20.0) * (self.y >= h1 - 3.0)
            h2 = 27.0 - 8.0 * ease
            field += 1.5 * np.exp(-((self.x - 36.0)**2) / 11.0) * np.exp(-((self.y - h2)**2) / 18.0) * (self.y >= h2 - 3.0)
            field += (3.2**2) / ((self.x - 24.0)**2 + (self.y - (6.0 + 1.0 * ease))**2 + 1.5)
        elif t < 9.0:
            # Phase 3: Schnuerung & Erstes Abloesen von Tropfen
            p = (t - 5.5) / 3.5
            ease = p * p * (3.0 - 2.0 * p)
            b1_y = 14.0 - 8.0 * ease
            field += (4.8**2) / ((self.x - 27.0)**2 + ((self.y - b1_y) * 0.9)**2 + 1.5)
            b2_y = 19.0 - 6.0 * ease
            field += (4.2**2) / ((self.x - 36.0)**2 + ((self.y - b2_y) * 0.9)**2 + 1.5)
            field += (3.0**2) / ((self.x - 24.0 + 3.0 * ease)**2 + (self.y - (7.0 + 4.0 * ease))**2 + 1.5)
        else:
            # Phase 4: Stetiger vollfluessiger Konvektionskreislauf
            conv_t = t - 9.0
            for b in self.blobs:
                bx, by, sy = self._get_convection_blob_pos(b, conv_t)
                r = b["r"]
                d2 = (self.x - bx)**2 + ((self.y - by) / sy)**2
                field += (r**2) / (d2 + 1.5)

        # 1. Flaechenfarben: Kuehles Cyan-Fluid als Hintergrund
        wax_threshold = 1.15
        fluid_rgb = np.zeros((self.height, self.width, 3), dtype=np.float32)
        fluid_rgb[:, :] = [3.0, 26.0, 44.0]  # Deep aquatic teal

        # Heizspule / Bodenbeleuchtung
        heater_intensity = 0.5 + 0.5 * w
        bulb_glow = np.exp(-((self.y - 31.0)**2) / 38.0)[:, :, None] * np.array([0.0, 150.0, 190.0], dtype=np.float32) * heater_intensity
        fluid_rgb += bulb_glow

        # 2. Heisses Lava-Wachs (Doppelter Farbverlauf: Koralle -> Orange -> Gold)
        wax_core = np.clip((field - wax_threshold) / 1.4, 0.0, 1.0)
        col_wax_rim = np.array([215.0, 50.0, 0.0], dtype=np.float32)
        col_wax_mid = np.array([255.0, 95.0, 0.0], dtype=np.float32)
        col_wax_core = np.array([255.0, 195.0, 30.0], dtype=np.float32)

        c1 = col_wax_rim + (col_wax_mid - col_wax_rim) * np.clip(wax_core * 2.0, 0.0, 1.0)[:, :, None]
        c2 = col_wax_mid + (col_wax_core - col_wax_mid) * np.clip(wax_core * 2.0 - 1.0, 0.0, 1.0)[:, :, None]
        wax_col = np.where(wax_core[:, :, None] < 0.5, c1, c2)

        # Subpixel Antialiasing
        edge_alpha = np.clip((field - (wax_threshold - 0.22)) / 0.44, 0.0, 1.0)[:, :, None]
        frame = fluid_rgb * (1.0 - edge_alpha) + wax_col * edge_alpha

        # Glasmaskierung und Reflexionen
        frame[self.outside_glass] = [0.0, 0.0, 0.0]
        frame += self.glass_rim * (0.6 + 0.2 * heater_intensity)

        return np.clip(frame, 0, 255).astype(np.uint8)
