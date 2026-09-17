import sys
import os
from PIL import Image

try:
    from rgbmatrix import RGBMatrix, RGBMatrixOptions
    HAS_HARDWARE = True
except ImportError:
    HAS_HARDWARE = False

class MatrixDriver:
    def __init__(self, config):
        self.config = config
        self.matrix = None
        self.canvas = None
        self.has_hardware = HAS_HARDWARE
        self._init_matrix()

    def _init_matrix(self):
        if not self.has_hardware:
            print("[INFO] Running in mock/emulated mode (rgbmatrix not installed on this host).")
            return

        # Bind to isolated CPU core 3 for jitter-free real-time rendering
        try:
            os.sched_setaffinity(0, {3})
            print("[INFO] Pinned process to isolated CPU Core 3")
        except Exception as e:
            pass

        options = RGBMatrixOptions()
        options.rows = self.config.ROWS
        options.cols = self.config.COLS
        options.chain_length = self.config.CHAIN_LENGTH
        options.parallel = self.config.PARALLEL
        options.hardware_mapping = self.config.HARDWARE_MAPPING
        options.gpio_slowdown = self.config.GPIO_SLOWDOWN
        options.brightness = self.config.DEFAULT_BRIGHTNESS
        options.pwm_bits = self.config.PWM_BITS
        options.pwm_lsb_nanoseconds = self.config.PWM_LSB_NANOSECONDS
        options.multiplexing = self.config.MULTIPLEXING
        options.row_address_type = self.config.ROW_ADDRESS_TYPE
        options.show_refresh_rate = self.config.SHOW_REFRESH_RATE

        if hasattr(self.config, "PWM_DITHER_BITS"):
            options.pwm_dither_bits = self.config.PWM_DITHER_BITS

        if hasattr(self.config, "PANEL_TYPE") and self.config.PANEL_TYPE:
            options.panel_type = self.config.PANEL_TYPE

        self.matrix = RGBMatrix(options=options)
        self.canvas = self.matrix.CreateFrameCanvas()
        print(f"[INFO] Initialized RGB Matrix: {self.config.COLS}x{self.config.ROWS} (Bonnet: {self.config.HARDWARE_MAPPING}, Panel: {self.config.PANEL_TYPE}, Slowdown: {self.config.GPIO_SLOWDOWN}, PWM Bits: {self.config.PWM_BITS})")

    def display_frame(self, rgb_numpy_array):
        """
        Takes a (H, W, 3) uint8 numpy array, converts to PIL Image, and swaps buffers.
        """
        img = Image.fromarray(rgb_numpy_array, mode="RGB")
        if self.has_hardware and self.canvas is not None:
            self.canvas.SetImage(img)
            self.canvas = self.matrix.SwapOnVSync(self.canvas)
        return img

    def set_brightness(self, brightness):
        if self.has_hardware and self.matrix:
            self.matrix.brightness = max(0, min(100, brightness))

    def clear(self):
        if self.has_hardware and self.matrix:
            self.matrix.Clear()
