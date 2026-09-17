import numpy as np

def hsv_to_rgb(h, s, v):
    """
    Vectorized HSV to RGB conversion.
    h: hue in [0, 1) or array
    s: saturation in [0, 1] or array
    v: value in [0, 1] or array
    Returns: uint8 numpy array with shape matching broadcast of (h, s, v) + (3,)
    """
    h6 = (h % 1.0) * 6.0
    i = np.floor(h6).astype(int)
    f = h6 - i
    p = v * (1.0 - s)
    q = v * (1.0 - s * f)
    t = v * (1.0 - s * (1.0 - f))
    
    i_mod = i % 6
    r = np.zeros_like(h, dtype=np.float32)
    g = np.zeros_like(h, dtype=np.float32)
    b = np.zeros_like(h, dtype=np.float32)
    
    mask = (i_mod == 0)
    r[mask], g[mask], b[mask] = v[mask], t[mask], p[mask]
    mask = (i_mod == 1)
    r[mask], g[mask], b[mask] = q[mask], v[mask], p[mask]
    mask = (i_mod == 2)
    r[mask], g[mask], b[mask] = p[mask], v[mask], t[mask]
    mask = (i_mod == 3)
    r[mask], g[mask], b[mask] = p[mask], q[mask], v[mask]
    mask = (i_mod == 4)
    r[mask], g[mask], b[mask] = t[mask], p[mask], v[mask]
    mask = (i_mod == 5)
    r[mask], g[mask], b[mask] = v[mask], p[mask], q[mask]
    
    rgb = np.stack([r, g, b], axis=-1)
    return (np.clip(rgb, 0.0, 1.0) * 255.0).astype(np.uint8)


class ColorPaletteManager:
    """
    Provides dynamic color palettes, full color spectrum cycling,
    and fast precalculated lookup tables.
    """
    def __init__(self, lut_size=1024):
        self.lut_size = lut_size
        self._lut_hues = np.linspace(0.0, 1.0, lut_size, endpoint=False)
        self._lut_ones = np.ones(lut_size, dtype=np.float32)
        # Precomputed full rainbow RGB lookup table (LUT)
        self.rainbow_lut = hsv_to_rgb(self._lut_hues, self._lut_ones, self._lut_ones)
    
    def sample_rainbow(self, t_values, hue_offset=0.0):
        """
        Samples rainbow colors given normalized t values [0, 1] + hue_offset.
        """
        indices = (((t_values + hue_offset) % 1.0) * self.lut_size).astype(int) % self.lut_size
        return self.rainbow_lut[indices]

    @staticmethod
    def cosine_palette(t, a, b, c, d):
        """
        Inigo Quilez procedural cosine palette:
        color = a + b * cos(2 * pi * (c * t + d))
        """
        two_pi = 2.0 * np.pi
        t_arr = np.expand_dims(t, axis=-1) if t.ndim > 0 and (t.shape[-1] != 1) else t
        angles = two_pi * (c * t_arr + d)
        rgb = a + b * np.cos(angles)
        return (np.clip(rgb, 0.0, 1.0) * 255.0).astype(np.uint8)

    @staticmethod
    def get_fire_palette(t):
        a = np.array([0.5, 0.5, 0.5])
        b = np.array([0.5, 0.5, 0.5])
        c = np.array([1.0, 1.0, 1.0])
        d = np.array([0.0, 0.33, 0.67])
        return ColorPaletteManager.cosine_palette(t, a, b, c, d)

    @staticmethod
    def get_electric_blue_palette(t):
        a = np.array([0.5, 0.5, 0.5])
        b = np.array([0.5, 0.5, 0.5])
        c = np.array([2.0, 1.0, 0.0])
        d = np.array([0.5, 0.20, 0.25])
        return ColorPaletteManager.cosine_palette(t, a, b, c, d)
