#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2025 Battelle Energy Alliance, LLC.  All rights reserved.

"""Animated splash screen module for GUI installer profile selection."""

# Animation timing constants (30fps = 33ms intervals)
FRAME_DELAY_MS = 33  # ~30fps for smoother performance

# Animation durations (in milliseconds)
FADE_IN_DURATION_MS = 1500
FADE_OUT_DURATION_MS = 800
SLIDE_TO_CENTER_DURATION_MS = 800
SLIDE_UP_DURATION_MS = 1000
TABS_FADE_IN_DURATION_MS = 500

# Loading dots animation
LOADING_DOT_INTERVAL_MS = 400

# Image display sizes
MALCOLM_IMAGE_SIZE = (220, 220)   # Display size for Malcolm logo
HEDGEHOG_IMAGE_SIZE = (255, 220)  # Display size for Hedgehog logo (slightly wider)
SPLASH_IMAGE_SIZE = (220, 220)    # Default fallback size
HEADER_IMAGE_SIZE = (60, 60)      # Final header anchor size

# Layout spacing
CARD_SPACING = 200  # Horizontal space between profile cards

# Background colors for alpha blending (RGB tuples)
BG_COLOR_LIGHT = (242, 242, 242)  # Match CTk light theme gray95
BG_COLOR_DARK = (26, 26, 26)      # Match CTk dark theme gray10
