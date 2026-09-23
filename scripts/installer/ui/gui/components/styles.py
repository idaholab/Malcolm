#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Styles for Malcolm GUI Installer
===============================

Constants defining the visual styling for the Malcolm GUI installer.
This module should contain only styling constants - no functionality.
"""

# Font configurations
FONT_FAMILY = "Helvetica"

# Font sizes
FONT_SIZE_TITLE = 20
FONT_SIZE_SECTION = 14
FONT_SIZE_NORMAL = 12

# Padding and spacing
PADDING_LARGE = 20
PADDING_MEDIUM = 10
PADDING_SMALL = 5

# Standard paddings for different elements
TITLE_PADDING = (PADDING_LARGE, PADDING_MEDIUM)  # (20, 10)
DESCRIPTION_PADDING = (0, PADDING_LARGE)  # (0, 20)
SECTION_PADDING = (PADDING_LARGE, PADDING_SMALL)  # (20, 5)
SECTION_DESC_PADDING = (0, PADDING_MEDIUM)  # (0, 10)
FRAME_PADDING = (PADDING_LARGE, PADDING_MEDIUM)  # (20, 10)
ELEMENT_PADDING = (PADDING_MEDIUM, PADDING_MEDIUM)  # (10, 10)

# Text wrapping
DEFAULT_WRAPLENGTH = 400

# Colors
COLOR_SUCCESS = "#2fa572"  # Green for success messages
COLOR_ERROR = "#e74c3c"  # Red for error messages
ERROR_TEXT_COLOR = ("red", "#ff6b6b")
COLOR_TRANSPARENT = "transparent"

# General text colors
TEXT_COLOR_NORMAL = ("gray10", "gray90")
TEXT_COLOR_MUTED = ("gray50", "gray70")
TEXT_COLOR_DISABLED = ("gray50", "gray70")

# Container styling
CONTAINER_COLORS_BY_DEPTH = {
    0: {"bg": ("gray96", "gray14"), "border": ("gray85", "gray28")},
    1: {"bg": ("gray94", "gray18"), "border": ("gray82", "gray30")},
    2: {"bg": ("gray92", "gray20"), "border": ("gray78", "gray32")},
    3: {"bg": ("gray90", "gray22"), "border": ("gray75", "gray35")},
}

PANEL_COLORS = {
    "flat": {
        "enabled": {"bg": ("gray94", "gray18"), "border": ("gray82", "gray28")},
        "disabled": {"bg": ("gray90", "gray21"), "border": ("gray78", "gray38")},
    },
    "nested": {
        "enabled": {"bg": ("gray92", "gray17"), "border": ("gray80", "gray30")},
        "disabled": {"bg": ("gray88", "gray22"), "border": ("gray75", "gray40")},
    },
}

PANEL_DISABLED_COLORS = {
    "flat": {"bg": ("gray75", "gray30"), "border": ("gray65", "gray45")},
    "nested": {"bg": ("gray70", "gray35"), "border": ("gray60", "gray50")},
}

SECTION_COLORS = {
    "even": {"bg": ("gray96", "gray14"), "border": ("gray85", "gray28")},
    "odd": {"bg": ("gray94", "gray16"), "border": ("gray83", "gray30")},
}

TAB_BG_FALLBACK = ("gray95", "gray12")

CONTAINER_CORNER_RADIUS = 8
PANEL_CORNER_RADIUS = 6
TOGGLE_CORNER_RADIUS = 4
TOOLTIP_CORNER_RADIUS = 4
DIALOG_CORNER_RADIUS = 10

PANEL_BORDER_WIDTH = 1
ERROR_BORDER_WIDTH = 2
DEFAULT_BORDER_WIDTH = 1
DIALOG_BORDER_WIDTH = 2

ERROR_BORDER_COLOR = "red"
DEFAULT_BORDER_COLOR = ("gray60", "gray40")
DIALOG_BORDER_COLOR = ("gray70", "gray30")

TOGGLE_HOVER_COLOR = ("gray85", "gray30")
TOGGLE_TEXT_COLOR = ("gray40", "gray70")
TOOLTIP_BG_COLOR = ("gray95", "gray20")
LOCK_ICON_COLOR = ("gray50", "gray60")
INFO_PANEL_BG = ("gray90", "gray20")

# Font styles - tuples of (size, weight)
FONT_TITLE = (FONT_SIZE_TITLE, "bold")
FONT_SECTION = (FONT_SIZE_SECTION, "bold")
FONT_NORMAL = (FONT_SIZE_NORMAL, "normal")
FONT_BOLD = (FONT_SIZE_NORMAL, "bold")

# Hierarchical indentation for nested UI elements
INDENT_BASE = 0  # Base indentation for top-level elements
INDENT_LEVEL_1 = 50  # First level of indentation
INDENT_LEVEL_2 = 100  # Second level of indentation
INDENT_LEVEL_3 = 150  # Third level of indentation

# Padding for hierarchical UI elements (left, right)
PADDING_HIERARCHY_BASE = (PADDING_MEDIUM, 0)  # Base padding for top-level elements
PADDING_HIERARCHY_LEVEL_1 = (PADDING_LARGE, 0)  # First level padding
PADDING_HIERARCHY_LEVEL_2 = (PADDING_LARGE * 2, 0)  # Second level padding
PADDING_HIERARCHY_LEVEL_3 = (PADDING_LARGE * 3, 0)  # Third level padding
