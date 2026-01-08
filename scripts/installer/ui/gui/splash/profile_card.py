#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2025 Battelle Energy Alliance, LLC.  All rights reserved.

"""Clickable profile selection card widget."""

from typing import Callable, Optional, Tuple
from PIL import Image
import customtkinter

from scripts.installer.ui.gui.splash.image_animator import ImageAnimator
from scripts.installer.ui.gui.splash import SPLASH_IMAGE_SIZE


class ProfileCard(customtkinter.CTkFrame):
    """
    Interactive card displaying a profile logo with click handling.

    Supports hover effects and animation state updates (opacity, scale, position).
    Uses ImageAnimator for PIL-based opacity simulation.
    """

    def __init__(
        self,
        parent,
        profile_name: str,
        image: Image.Image,
        display_size: Tuple[int, int] = SPLASH_IMAGE_SIZE,
        preserve_aspect: bool = True,
        on_click: Optional[Callable[[str], None]] = None,
        label_text: Optional[str] = None,
        initial_opacity: float = 1.0,
    ):
        """
        Initialize profile card.

        Args:
            parent: Parent widget
            profile_name: Profile identifier (e.g., "malcolm", "hedgehog")
            image: PIL Image for the profile logo
            display_size: (width, height) for image display
            preserve_aspect: Whether to preserve original aspect ratio
            on_click: Callback when card is clicked
            label_text: Optional text label below image
            initial_opacity: Starting opacity (0.0 to 1.0), use 0.0 to start invisible
        """
        super().__init__(parent, fg_color="transparent", bg_color="transparent", corner_radius=0)

        self._profile_name = profile_name
        self._on_click = on_click
        self._display_size = display_size
        self._hover_enabled = True
        self._click_enabled = True

        # Create image animator for opacity/scale effects
        self._animator = ImageAnimator(image, display_size, preserve_aspect=preserve_aspect)

        # Current animation state
        self._current_opacity = initial_opacity
        self._current_scale = 1.0

        # Build UI with initial opacity
        self._build_ui(label_text, initial_opacity)

        # Bind events
        self._bind_events()

    def _build_ui(self, label_text: Optional[str], initial_opacity: float = 1.0) -> None:
        """Build the card UI with image and optional label."""
        # Create initial image at specified opacity
        # Preserve transparency when fully opaque
        ctk_image = self._animator.create_ctk_image(
            opacity=initial_opacity, preserve_transparency=(initial_opacity >= 1.0)
        )

        self._image_label = customtkinter.CTkLabel(
            self,
            image=ctk_image,
            text="",
            cursor="hand2",
        )
        self._image_label.pack(padx=10, pady=10)

        # Optional text label below image
        if label_text:
            self._text_label = customtkinter.CTkLabel(
                self,
                text=label_text,
                font=("Helvetica", 14, "bold"),
            )
            self._text_label.pack(pady=(0, 10))
        else:
            self._text_label = None

    def _bind_events(self) -> None:
        """Bind mouse events for click and hover."""
        # Bind to both frame and image label
        for widget in [self, self._image_label]:
            widget.bind("<Button-1>", self._handle_click)
            widget.bind("<Enter>", self._on_enter)
            widget.bind("<Leave>", self._on_leave)

        if self._text_label:
            self._text_label.bind("<Button-1>", self._handle_click)
            self._text_label.bind("<Enter>", self._on_enter)
            self._text_label.bind("<Leave>", self._on_leave)

    def _handle_click(self, event) -> None:
        """Handle click event."""
        if self._click_enabled and self._on_click:
            self._on_click(self._profile_name)

    def _on_enter(self, event) -> None:
        """Handle mouse enter for hover effect."""
        if not self._hover_enabled:
            return

        # Subtle scale-up effect on hover
        self._image_label.configure(cursor="hand2")

    def _on_leave(self, event) -> None:
        """Handle mouse leave for hover effect."""
        if not self._hover_enabled:
            return

        # Reset cursor
        self._image_label.configure(cursor="hand2")

    def set_opacity(self, opacity: float) -> None:
        """
        Update card opacity by regenerating image.

        Args:
            opacity: Opacity level (0.0 to 1.0)
        """
        self._current_opacity = opacity

        try:
            if not self.winfo_exists():
                return
        except Exception:
            return

        # Generate new frame with updated opacity
        # Preserve transparency when fully opaque
        ctk_image = self._animator.create_ctk_image(
            opacity=opacity, scale=self._current_scale, preserve_transparency=(opacity >= 1.0)
        )

        self._image_label.configure(image=ctk_image)

    def set_scale(self, scale: float) -> None:
        """
        Update card scale by regenerating image.

        Args:
            scale: Scale factor (1.0 = original size)
        """
        self._current_scale = scale

        try:
            if not self.winfo_exists():
                return
        except Exception:
            return

        # Generate new frame with updated scale
        # Preserve transparency when fully opaque
        ctk_image = self._animator.create_ctk_image(
            opacity=self._current_opacity, scale=scale, preserve_transparency=(self._current_opacity >= 1.0)
        )

        self._image_label.configure(image=ctk_image)

    def set_opacity_and_scale(self, opacity: float, scale: float) -> None:
        """
        Update both opacity and scale in a single operation.

        More efficient than calling set_opacity and set_scale separately.

        Args:
            opacity: Opacity level (0.0 to 1.0)
            scale: Scale factor (1.0 = original size)
        """
        self._current_opacity = opacity
        self._current_scale = scale

        try:
            if not self.winfo_exists():
                return
        except Exception:
            return

        # Preserve transparency when fully opaque
        ctk_image = self._animator.create_ctk_image(
            opacity=opacity, scale=scale, preserve_transparency=(opacity >= 1.0)
        )
        self._image_label.configure(image=ctk_image)

    def enable_hover(self, enabled: bool = True) -> None:
        """Enable or disable hover effects."""
        self._hover_enabled = enabled
        if not enabled:
            # Remove any current highlight
            self.configure(fg_color="transparent")

    def enable_click(self, enabled: bool = True) -> None:
        """Enable or disable click handling."""
        self._click_enabled = enabled
        # Update cursor
        cursor = "hand2" if enabled else ""
        self._image_label.configure(cursor=cursor)

    def get_profile_name(self) -> str:
        """Get the profile name for this card."""
        return self._profile_name

    def get_display_size(self) -> Tuple[int, int]:
        """Get the display size of the image."""
        return self._animator.get_display_size()
