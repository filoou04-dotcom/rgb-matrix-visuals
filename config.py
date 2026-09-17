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
    # 'adafruit-hat' is standard for Adafruit RGB Matrix Bonnet and compatible clones
    HARDWARE_MAPPING = 'adafruit-hat'
    
    # GPIO Slowdown:
    # Pi 3 typically needs 1. Pi 4 needs 4. Pi 0/1/2 needs 0.
    GPIO_SLOWDOWN = 1
    
    # Brightness (0 to 100%)
    DEFAULT_BRIGHTNESS = 70
    
    # Color PWM precision
    PWM_BITS = 11
    PWM_LSB_NANOSECONDS = 130
    
    # Scan rate / Multiplexing
    # HUB75-D 1:16 scan for 32 rows uses standard direct address (0)
    MULTIPLEXING = 0
    ROW_ADDRESS_TYPE = 0
    
    # Performance
    FPS_LIMIT = 50
    SHOW_REFRESH_RATE = False
