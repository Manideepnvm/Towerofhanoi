# Screen settings
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60

# Tower settings
TOWER_WIDTH = 15 # Thicker for solid look
TOWER_HEIGHT = 300
TOWER_Y = 250
TOWER_BASE_WIDTH = 140
TOWER_BASE_HEIGHT = 15

# Disk settings
DISK_HEIGHT = 40 # Thicker disks
BASE_DISK_WIDTH = 220
DISK_ROUNDING = 8 # Less rounded, more machined

# Theme: Crystal & Metal (Professional, High Contrast)
COLOR_BG_DARK = (245, 247, 250)     # Off-white / Metallic Mist
COLOR_BG_LIGHT = (255, 255, 255)    # Pure White
COLOR_GRID = (200, 210, 220, 100)   # Subtle Steel Grid

# Metal Colors (Gradients are procedural, these are base tones)
# We will define base tones for specific metal types
DISK_COLORS = [
    (220, 20, 60),   # Ruby Red
    (46, 139, 87),   # Emerald Green
    (65, 105, 225),  # Sapphire Blue
    (153, 50, 204),  # Amethyst Purple
    (255, 215, 0),   # Gold
    (0, 206, 209)    # Turquoise
]

# UI Colors (Crystal Clear)
COLOR_WHITE = (10, 10, 20)           # Actually Dark Blue-Black for Text (High Contrast)
COLOR_TEXT_GLOW = (255, 255, 255)    # No glow, but maybe highlight
COLOR_TEXT_DIM = (80, 90, 100)       # Dark Gray
COLOR_OVERLAY = (255, 255, 255, 150) # Frosted Glass

# Tower Colors
COLOR_TOWER_GLOW = (200, 200, 200) # Shiny highlight
COLOR_TOWER_CORE = (100, 100, 100) # Dark Steel rod
COLOR_BASE_GLOW = (160, 160, 160)  # Polished Base

# Hand tracking
PINCH_THRESHOLD = 50
ACTION_COOLDOWN = 0.3
ACTION_MESSAGE_DURATION = 2.0

# Pinch Indicator
PINCH_COLOR_IDLE = (100, 100, 100, 100)
PINCH_COLOR_ACTIVE = (0, 120, 255, 200) # Professional Blue
PINCH_COLOR_ERROR = (200, 50, 50, 200)

# Particle Settings (Subtle glints)
PARTICLE_COUNT = 10
PARTICLE_LIFETIME = 0.5
