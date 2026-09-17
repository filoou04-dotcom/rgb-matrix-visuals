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
    # 2 provides cleaner signal transitions on Pi 3 and eliminates ghosting/vertical lines
    GPIO_SLOWDOWN = 2
    
    # Brightness (0 to 100%)
    DEFAULT_BRIGHTNESS = 60
    
    # Anti-flicker & Timing optimization:
    # 10 PWM bits delivers significantly higher refresh rates (>250Hz)
    PWM_BITS = 10
    # 200ns ensures clean OE and latch timings on FM6126A
    PWM_LSB_NANOSECONDS = 200
    PWM_DITHER_BITS = 0
    
    # Scan rate / Multiplexing
    MULTIPLEXING = 0
    ROW_ADDRESS_TYPE = 0
    
    # Performance
    FPS_LIMIT = 50
    SHOW_REFRESH_RATE = False
