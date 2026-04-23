"""Racing-themed color palettes for pyobd."""

# Alien Green Slime Mode
ALIEN_SLIME = {
    'name': 'Alien Green Slime',
    'primary_bg': (10, 20, 10),      # dark green-black
    'secondary_bg': (20, 35, 20),    # slightly lighter
    'primary_text': (0, 255, 0),     # neon green
    'secondary_text': (150, 150, 150),  # gray for labels
    'accent': (0, 255, 0),           # bright green
    'warning': (255, 255, 0),        # acidic yellow
    'danger': (255, 0, 0),           # red
    'border': (0, 200, 0),           # medium green
    'good_value': (0, 255, 0),       # neon green
    'caution_value': (255, 255, 0),  # yellow
    'critical_value': (255, 0, 0),   # red
}

# Tron 3000 Cyberr Mode
TRON_3000 = {
    'name': 'Tron 3000 Cyberr',
    'primary_bg': (5, 10, 25),       # deep dark blue
    'secondary_bg': (15, 25, 50),    # slightly lighter
    'primary_text': (0, 255, 255),   # bright cyan
    'secondary_text': (100, 150, 200),  # light blue-gray
    'accent': (255, 0, 255),         # magenta
    'warning': (0, 204, 255),        # light blue
    'danger': (255, 50, 150),        # hot pink
    'border': (0, 200, 255),         # cyan
    'good_value': (0, 255, 255),     # cyan
    'caution_value': (0, 204, 255),  # light blue
    'critical_value': (255, 50, 150),  # hot pink
}

# Lava Mode (bonus)
LAVA = {
    'name': 'Lava',
    'primary_bg': (20, 10, 5),       # dark red-brown
    'secondary_bg': (40, 20, 10),    # slightly lighter
    'primary_text': (255, 150, 0),   # orange
    'secondary_text': (150, 100, 80),  # brown-gray
    'accent': (255, 100, 0),         # bright orange
    'warning': (255, 200, 0),        # gold
    'danger': (255, 0, 0),           # red
    'border': (255, 100, 0),         # orange
    'good_value': (255, 150, 0),     # orange
    'caution_value': (255, 200, 0),  # gold
    'critical_value': (255, 0, 0),   # red
}

# Ocean Mode (bonus)
OCEAN = {
    'name': 'Ocean',
    'primary_bg': (5, 20, 35),       # dark blue
    'secondary_bg': (15, 40, 60),    # lighter blue
    'primary_text': (0, 200, 255),   # bright cyan
    'secondary_text': (100, 150, 200),  # light blue
    'accent': (0, 255, 200),         # turquoise
    'warning': (255, 200, 0),        # gold
    'danger': (255, 50, 50),         # salmon red
    'border': (0, 200, 255),         # cyan
    'good_value': (0, 255, 200),     # turquoise
    'caution_value': (255, 200, 0),  # gold
    'critical_value': (255, 50, 50),  # salmon
}

# All available themes
THEMES = {
    'alien': ALIEN_SLIME,
    'tron': TRON_3000,
    'lava': LAVA,
    'ocean': OCEAN,
}

DEFAULT_THEME = 'tron'


def get_theme(theme_name):
    """Get theme palette by name."""
    return THEMES.get(theme_name, THEMES[DEFAULT_THEME])


def get_all_themes():
    """Get list of all available themes."""
    return list(THEMES.keys())
