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
    
    # Waveshare P5 panels use the FM6126A shift register driver chip
    PANEL_TYPE = "FM6126A"
    
    # GPIO Slowdown:
    # Pi 3 needs 1
    GPIO_SLOWDOWN = 1
    
    # Brightness (0 to 100%)
    DEFAULT_BRIGHTNESS = 70
    
    # Color PWM precision
    PWM_BITS = 11
    PWM_LSB_NANOSECONDS = 130
    
    # Scan rate / Multiplexing
    MULTIPLEXING = 0
    ROW_ADDRESS_TYPE = 0
    
    # Performance
    FPS_LIMIT = 50
    SHOW_REFRESH_RATE = False
