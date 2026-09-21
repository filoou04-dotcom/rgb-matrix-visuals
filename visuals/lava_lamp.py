import math
import numpy as np
from .base import VisualEffect

class LavaLamp(VisualEffect):
    """
    Programm 8: Virtuelle Retro-Lavalampe (Hochkant, rahmenlos, fotorealistisch).
    Klassische Mathmos-Aesthetik: gedaempfte Retro-Farbpalette aus Terrakotta/Bernstein
    in tiefem petrol-tuerkisen Fluid mit volumetrischem Sockel-Gegenlicht,
    Subsurface-Scattering-Halo und natuerlicher tropfenfoermiger Hydrodynamik.
    
    Startet mit einer 10-sekundigen Aufwaermsequenz (Kaltzustand -> zystische
    Stalagmiten -> Abschnuerung) und geht danach in einen beruhigenden,
    stetigen Konvektionsfluss ueber.
    """

    def __init__(self, width=64, height=32, palette_manager=None, name="LavaLamp", orientation="cw"):
        super().__init__(width, height, palette_manager, name=name)

        self.orientation = orientation  # "cw" (Standard) oder "ccw"
        self.sim_h = 64
        self.sim_w = 32
        self.cx = 15.5
        self.sim_time = 0.0

        # Koordinatengitter im nativen 32x64 Raum
        y_coords, x_coords = np.mgrid[0:self.sim_h, 0:self.sim_w].astype(np.float32)
        self.x = x_coords
        self.y = y_coords

        # Vorberechneter natuerlicher Helligkeitsverlauf des Fluids (Retro Petrol/Teal)
        self.base_fluid = np.zeros((self.sim_h, self.sim_w, 3), dtype=np.float32)
        for y in range(self.sim_h):
            t_y = y / float(self.sim_h - 1)
            # Von tiefem, rauchigen Mitternachts-Petrol oben zu waermerem Indigoteal unten
            self.base_fluid[y, :] = (1.0 - t_y) * np.array([3.0, 18.0, 26.0], dtype=np.float32) + \
                                    t_y * np.array([8.0, 50.0, 68.0], dtype=np.float32)

        # Volumetrisches Gegenlicht der Gluehlampe im Sockel
        bulb_dist = (self.y - 63.0)**2
        self.bulb_glow = np.exp(-bulb_dist / 220.0)[:, :, None]
        self.bulb_color = np.array([24.0, 85.0, 95.0], dtype=np.float32)

        # Konvektionstropfen mit unterschiedlichen Radien, Zyklen und Geschwindigkeiten
        self.blobs = [
            {"ax": 3.8, "wx": 0.32, "fx": 0.0, "v": 0.075, "offset": 0.0, "r": 5.4},
            {"ax": 4.5, "wx": 0.26, "fx": 2.1, "v": 0.065, "offset": 0.35, "r": 4.8},
            {"ax": 3.2, "wx": 0.40, "fx": 4.2, "v": 0.085, "offset": 0.65, "r": 5.6},
            {"ax": 5.0, "wx": 0.28, "fx": 1.4, "v": 0.055, "offset": 0.85, "r": 4.0},
            {"ax": 2.5, "wx": 0.44, "fx": 3.6, "v": 0.090, "offset": 0.20, "r": 4.4},
        ]

    def reset(self):
        """Startet den Aufwaermzyklus bei manuellem Programmaufruf neu."""
        self.sim_time = 0.0

    def set_orientation(self, orientation: str):
        """Erlaubt Wechsel der 90-Grad-Ausrichtung (cw oder ccw)."""
        if orientation in ("cw", "ccw"):
            self.orientation = orientation

    def _get_convection_blob_pos(self, b, t):
        bx = self.cx + b["ax"] * math.sin(t * b["wx"] + b["fx"])
        cycle = (t * b["v"] + b["offset"]) % 1.0

        if cycle < 0.45:
            # Auftrieb & hydrodynamische Streckung beim Aufsteigen
            p = cycle / 0.45
            ease = p * p * (3.0 - 2.0 * p)
            by = 56.0 - 46.0 * ease
            stretch_y = 1.25
        elif cycle < 0.55:
            # Abkuehlung und Verweilen an der kuehlen Decke (leichte Abflachung)
            p = (cycle - 0.45) / 0.10
            by = 10.0 + 2.5 * math.sin(p * math.pi)
            stretch_y = 0.90
        elif cycle < 0.90:
            # Erhoehte Dichte und gemaechliches Absinken
            p = (cycle - 0.55) / 0.35
            ease = p * p * (3.0 - 2.0 * p)
            by = 10.0 + 46.0 * ease
            stretch_y = 1.15
        else:
            # Wiederverschmelzen mit dem heissen Bodenreservoir
            p = (cycle - 0.90) / 0.10
            by = 56.0 + 2.0 * math.sin(p * math.pi)
            stretch_y = 0.85

        return bx, by, stretch_y

    def update(self, dt):
        super().update(dt)
        self.sim_time += dt

    def render(self) -> np.ndarray:
        t = self.sim_time
        w = min(1.0, max(0.0, t / 10.0))  # 10s Aufwaermfortschritt

        field = np.zeros((self.sim_h, self.sim_w), dtype=np.float32)

        # Heisses Bodenreservoir (dehnt sich mit zunehmender Waerme aus)
        res_y = 60.0 - 2.5 * w
        field += np.exp(-((self.y - res_y)**2) / (20.0 + 6.0 * w)) * (1.7 + 0.3 * (1.0 - w))

        if t < 2.5:
            # Phase 1: Kaltzustand (starr; erkalteter Tropfen haftet oben)
            field += (3.8**2) / ((self.x - 14.0)**2 + (self.y - 11.0)**2 + 1.8)
        elif t < 5.5:
            # Phase 2: Zaehe Stalagmiten schieben sich gemaechlich empor
            p = (t - 2.5) / 3.0
            ease = p * p * (3.0 - 2.0 * p)
            h1 = 56.0 - 26.0 * ease
            field += 1.8 * np.exp(-((self.x - 12.0)**2) / 14.0) * np.exp(-((self.y - h1)**2) / 35.0) * (self.y >= h1 - 4.0)
            h2 = 58.0 - 18.0 * ease
            field += 1.5 * np.exp(-((self.x - 20.0)**2) / 12.0) * np.exp(-((self.y - h2)**2) / 30.0) * (self.y >= h2 - 4.0)
            field += (3.8**2) / ((self.x - 14.0)**2 + (self.y - (11.0 + 2.0 * ease))**2 + 1.8)
        elif t < 8.5:
            # Phase 3: Schnuerung (Rayleigh-Plateau) und erstes Abloesen
            p = (t - 5.5) / 3.0
            ease = p * p * (3.0 - 2.0 * p)
            b1_y = 30.0 - 18.0 * ease
            field += (5.2**2) / ((self.x - 12.0)**2 + ((self.y - b1_y) * 0.85)**2 + 1.8)
            b2_y = 40.0 - 14.0 * ease
            field += (4.6**2) / ((self.x - 20.0)**2 + ((self.y - b2_y) * 0.85)**2 + 1.8)
            field += (3.5**2) / ((self.x - 14.0 + 2.0 * ease)**2 + (self.y - (13.0 + 8.0 * ease))**2 + 1.8)
        else:
            # Phase 4: Vollstaendiger, stetiger Konvektionskreislauf
            conv_t = t - 8.5
            for b in self.blobs:
                bx, by, sy = self._get_convection_blob_pos(b, conv_t)
                r = b["r"]
                d2 = (self.x - bx)**2 + ((self.y - by) / sy)**2
                field += (r**2) / (d2 + 1.8)

        # 1. Fluessigkeit mit thermischer Beleuchtung
        heater_int = 0.45 + 0.55 * w
        fluid_rgb = self.base_fluid + (self.bulb_glow * self.bulb_color * heater_int)

        # 2. Subsurface-Scattering-Halo (weiches Glimmen des heissen Wachses in die Fluessigkeit)
        wax_threshold = 1.12
        halo = np.clip((field - 0.65) / 0.50, 0.0, 1.0)[:, :, None]
        halo_color = np.array([85.0, 36.0, 14.0], dtype=np.float32)
        fluid_rgb = fluid_rgb * (1.0 - 0.40 * halo) + halo_color * (0.40 * halo)

        # 3. Authentisches Retro-Wachs (Terrakotta/Lava-Orange -> Glutrot -> warmer Bernstein-Kern)
        col_wax_rim = np.array([160.0, 38.0, 10.0], dtype=np.float32)
        col_wax_mid = np.array([215.0, 85.0, 12.0], dtype=np.float32)
        col_wax_core = np.array([242.0, 150.0, 28.0], dtype=np.float32)

        wax_core = np.clip((field - wax_threshold) / 1.35, 0.0, 1.0)
        c1 = col_wax_rim + (col_wax_mid - col_wax_rim) * np.clip(wax_core * 2.0, 0.0, 1.0)[:, :, None]
        c2 = col_wax_mid + (col_wax_core - col_wax_mid) * np.clip(wax_core * 2.0 - 1.0, 0.0, 1.0)[:, :, None]
        wax_col = np.where(wax_core[:, :, None] < 0.5, c1, c2)

        # Weiches Subpixel-Anti-Aliasing der Wachskontur
        edge_alpha = np.clip((field - (wax_threshold - 0.20)) / 0.40, 0.0, 1.0)[:, :, None]
        canvas = fluid_rgb * (1.0 - edge_alpha) + wax_col * edge_alpha

        # Drehung fuer Hochkant-Darstellung auf dem 64x32 Hardware-Panel (ohne Rahmen)
        if self.orientation == "ccw":
            out_frame = np.rot90(canvas, 1)
        else:
            out_frame = np.rot90(canvas, -1)

        return np.clip(out_frame, 0, 255).astype(np.uint8)
