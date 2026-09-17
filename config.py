"""
Hardware and Visuals Configuration for 64x32 Waveshare HUB75-D LED Matrix
"""

class MatrixConfig:
    # Panel dimensions
    ROWS = 32
    COLS = 64
    CHAIN_LENGTH = 1
    PARALLEL = 1
    
    # Wiring & Bonnet settings
    HARDWARE_MAPPING = "adafruit-hat"
    
    # Waveshare P5 panel driver chip
    PANEL_TYPE = "FM6126A"
    
    # GPIO Slowdown:
    # 1 gives maximum refresh rate on Pi 3
    GPIO_SLOWDOWN = 1
    
    # Brightness (0 to 100%)
    DEFAULT_BRIGHTNESS = 65
    
    # High-Refresh Anti-Flicker Tuning:
    # 8 PWM bits = full 24-bit TrueColor (16.7M colors) while achieving ~250-280Hz refresh rate!
    PWM_BITS = 8
    PWM_DITHER_BITS = 1
    PWM_LSB_NANOSECONDS = 130
    
    # Scan rate / Multiplexing
    MULTIPLEXING = 0
    ROW_ADDRESS_TYPE = 0
    
    # Performance
    FPS_LIMIT = 50
    SHOW_REFRESH_RATE = False
