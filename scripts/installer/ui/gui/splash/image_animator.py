#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2025 Battelle Energy Alliance, LLC.  All rights reserved.

"""PIL-based image animation utilities for opacity and scale effects."""

from typing import Optional, Tuple
from PIL import Image
import customtkinter

from scripts.installer.ui.gui.splash import (
    BG_COLOR_LIGHT,
    BG_COLOR_DARK,
    SPLASH_IMAGE_SIZE,
)


class ImageAnimator:
    """
    Handles image transformations for animation effects.

    Since customtkinter doesn't support native opacity, this class uses
    PIL to create alpha-blended frames that simulate fade effects by
    blending the image with the background color.

    Images are pre-scaled at initialization to avoid expensive per-frame
    resizing operations.
    """

    def __init__(
        self,
        original_image: Image.Image,
        display_size: Tuple[int, int] = SPLASH_IMAGE_SIZE,
        bg_color_light: Tuple[int, int, int] = BG_COLOR_LIGHT,
        bg_color_dark: Tuple[int, int, int] = BG_COLOR_DARK,
        preserve_aspect: bool = True,
    ):
        """
        Initialize image animator with pre-scaled image.

        Args:
            original_image: The source PIL Image to animate
            display_size: Target size for display (pre-scale to this)
            bg_color_light: Background color for light mode (RGB)
            bg_color_dark: Background color for dark mode (RGB)
        """
        self._bg_color_light = bg_color_light
        self._bg_color_dark = bg_color_dark
        self._display_size = display_size
        self._preserve_aspect = preserve_aspect

        # Pre-scale to display size with high quality
        self._scaled_image = self._prepare_image(original_image, display_size)

        # Keep only latest CTkImage reference to allow GC of previous frames
        self._current_ctk_image: Optional[customtkinter.CTkImage] = None

    def _prepare_image(
        self, image: Image.Image, target_size: Tuple[int, int]
    ) -> Image.Image:
        """
        Prepare image for animation by scaling and ensuring RGBA mode.

        Args:
            image: Source image
            target_size: Target dimensions (width, height)

        Returns:
            Pre-scaled RGBA image
        """
        # Ensure RGBA mode for alpha blending
        if image.mode != "RGBA":
            image = image.convert("RGBA")

        img_width, img_height = image.size
        target_width, target_height = target_size

        if not self._preserve_aspect:
            return image.resize((target_width, target_height), Image.LANCZOS)

        # Scale to fit within target while preserving aspect ratio
        scale = min(target_width / img_width, target_height / img_height)
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)

        # High quality resize
        return image.resize((new_width, new_height), Image.LANCZOS)

    def get_frame(
        self,
        opacity: float,
        scale: float = 1.0,
        preserve_transparency: bool = False,
    ) -> Image.Image:
        """
        Generate an animation frame with specified opacity and scale.

        Args:
            opacity: Opacity level (0.0 = invisible, 1.0 = fully visible)
            scale: Scale factor (1.0 = display size, <1.0 = smaller)
            preserve_transparency: If True and opacity=1.0, keep original alpha channel
                                   instead of blending with background

        Returns:
            PIL Image with alpha-blended opacity effect
        """
        bg_color = self._get_current_bg_color()
        return self._get_frame_for_bg(opacity, scale, bg_color, preserve_transparency)

    def _get_frame_for_bg(
        self,
        opacity: float,
        scale: float,
        bg_color: Tuple[int, int, int],
        preserve_transparency: bool,
    ) -> Image.Image:
        """Generate a frame blended with the provided background color."""
        # Clamp values
        opacity = max(0.0, min(1.0, opacity))
        scale = max(0.1, min(2.0, scale))

        # Start with pre-scaled image
        image = self._scaled_image.copy()

        # Apply additional scaling if needed
        if scale != 1.0:
            new_width = int(image.width * scale)
            new_height = int(image.height * scale)
            image = image.resize((new_width, new_height), Image.LANCZOS)

        # If preserving transparency and fully opaque, return image as-is
        if preserve_transparency and opacity >= 1.0:
            return image

        # Apply opacity by blending with background
        return self._blend_with_background(image, opacity, bg_color)

    def create_ctk_image(
        self,
        opacity: float,
        scale: float = 1.0,
        preserve_transparency: bool = False,
    ) -> customtkinter.CTkImage:
        """
        Create a CTkImage for the current frame.

        Replaces the previous CTkImage reference to allow garbage collection.

        Args:
            opacity: Opacity level (0.0 to 1.0)
            scale: Scale factor
            preserve_transparency: If True and opacity=1.0, keep original alpha channel

        Returns:
            CTkImage suitable for display in labels
        """
        frame_light = self._get_frame_for_bg(
            opacity, scale, self._bg_color_light, preserve_transparency
        )
        frame_dark = self._get_frame_for_bg(
            opacity, scale, self._bg_color_dark, preserve_transparency
        )

        # Create new CTkImage (previous reference will be GC'd)
        self._current_ctk_image = customtkinter.CTkImage(
            light_image=frame_light,
            dark_image=frame_dark,
            size=(frame_light.width, frame_light.height),
        )

        return self._current_ctk_image

    def _blend_with_background(
        self,
        image: Image.Image,
        opacity: float,
        bg_color: Tuple[int, int, int],
    ) -> Image.Image:
        """
        Blend image with solid background color to simulate transparency.

        Args:
            image: RGBA image to blend
            opacity: Opacity level (0.0 to 1.0)
            bg_color: Background color (RGB)

        Returns:
            Blended RGBA image
        """
        # Create solid background
        bg = Image.new("RGBA", image.size, (*bg_color, 255))

        # If fully opaque, just composite normally
        if opacity >= 1.0:
            return Image.alpha_composite(bg, image)

        # If invisible, return just background
        if opacity <= 0.0:
            return bg

        # Modify alpha channel based on opacity
        r, g, b, a = image.split()
        # Scale the alpha channel by opacity factor
        a = a.point(lambda x: int(x * opacity))
        image_with_opacity = Image.merge("RGBA", (r, g, b, a))

        # Composite over background
        return Image.alpha_composite(bg, image_with_opacity)

    def _get_current_bg_color(self) -> Tuple[int, int, int]:
        """Get current background color based on appearance mode."""
        try:
            mode = customtkinter.get_appearance_mode()
            if mode and mode.lower() == "dark":
                return self._bg_color_dark
        except Exception:
            pass
        return self._bg_color_light

    def get_display_size(self) -> Tuple[int, int]:
        """Get the current display size of the pre-scaled image."""
        return (self._scaled_image.width, self._scaled_image.height)
