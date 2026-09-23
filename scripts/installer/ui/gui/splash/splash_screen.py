#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2025 Battelle Energy Alliance, LLC.  All rights reserved.

"""Animated splash screen for Malcolm GUI installer profile selection."""

from pathlib import Path
from typing import TYPE_CHECKING, Callable, Optional, Tuple
from PIL import Image
import customtkinter

from scripts.malcolm_utils import get_main_script_dir
from scripts.malcolm_constants import PROFILE_MALCOLM, PROFILE_HEDGEHOG
from scripts.installer.utils.logger_utils import InstallerLogger
from scripts.installer.ui.gui.splash import (
    FADE_IN_DURATION_MS,
    FADE_OUT_DURATION_MS,
    SLIDE_TO_CENTER_DURATION_MS,
    SLIDE_UP_DURATION_MS,
    MALCOLM_IMAGE_SIZE,
    HEDGEHOG_IMAGE_SIZE,
    HEADER_IMAGE_SIZE,
    CARD_SPACING,
)
from scripts.installer.ui.gui.splash.animation_controller import (
    AnimationController,
    AnimationConfig,
    lerp,
    lerp_int,
)
from scripts.installer.ui.gui.splash.profile_card import ProfileCard
from scripts.installer.ui.gui.splash.loading_dots import LoadingDots

if TYPE_CHECKING:
    from scripts.installer.core.malcolm_config import MalcolmConfig


class SplashScreen:
    """
    Full-window animated splash screen for profile selection.

    Displays Malcolm and Hedgehog logos side-by-side with fade-in animation,
    allows user to click to select profile, then animates transition.

    Animation sequence:
    1. Fade-in both profile cards
    2. User clicks to select profile
    3. Unselected fades out, selected slides to center
    4. Loading dots display while MainWindow prepares
    5. Selected image slides up and shrinks
    6. Callback invoked with selected profile and header image
    """

    def __init__(
        self,
        root: customtkinter.CTk,
        malcolm_config: "MalcolmConfig",
        on_complete: Callable[[str, Optional[customtkinter.CTkImage]], None],
        on_loading_start: Optional[Callable[[str], None]] = None,
    ):
        """
        Initialize the splash screen.

        Args:
            root: The root CTk window
            malcolm_config: MalcolmConfig instance for setting profile value
            on_complete: Callback(profile_name, header_image) when animation completes
            on_loading_start: Optional callback(profile_name) when loading phase begins,
                              allowing parent to start building UI in background
        """
        self._root = root
        self._malcolm_config = malcolm_config
        self._on_complete = on_complete
        self._on_loading_start = on_loading_start

        # Animation controller
        self._animation_controller: Optional[AnimationController] = None

        # Profile cards
        self._malcolm_card: Optional[ProfileCard] = None
        self._hedgehog_card: Optional[ProfileCard] = None

        # UI elements
        self._container: Optional[customtkinter.CTkFrame] = None
        self._title_label: Optional[customtkinter.CTkLabel] = None
        self._loading_dots: Optional[LoadingDots] = None

        # State
        self._selected_profile: Optional[str] = None
        self._header_image: Optional[customtkinter.CTkImage] = None

        # Track after IDs for cleanup
        self._after_ids: list[str] = []

        # Card positions (updated on resize)
        self._malcolm_position: Tuple[int, int] = (0, 0)
        self._hedgehog_position: Tuple[int, int] = (0, 0)
        self._center_position: Tuple[int, int] = (0, 0)
        self._header_position: Tuple[int, int] = (0, 0)

    def show(self) -> None:
        """Display the splash screen and start fade-in animation."""
        self._root.title("Profile Selection")
        self._build_ui()

    def _build_ui(self) -> None:
        """Build the splash screen UI."""
        # Main container frame - fills the window
        self._container = customtkinter.CTkFrame(self._root, fg_color="transparent")
        self._container.pack(fill="both", expand=True)

        # Create animation controller
        self._animation_controller = AnimationController(self._container)

        # Load images
        malcolm_image, hedgehog_image = self._load_images()

        # Title label - "SELECT RUN PROFILE"
        self._title_label = customtkinter.CTkLabel(
            self._container,
            text="SELECT RUN PROFILE",
            font=("Helvetica", 20, "bold"),
        )
        # Will be positioned via place() after computing layout

        # Create profile cards (initially invisible via initial_opacity=0.0)
        self._malcolm_card = ProfileCard(
            self._container,
            profile_name=PROFILE_MALCOLM,
            image=malcolm_image,
            display_size=MALCOLM_IMAGE_SIZE,
            preserve_aspect=False,
            on_click=self._on_profile_click,
            label_text="Malcolm",
            initial_opacity=1.0,
        )

        self._hedgehog_card = ProfileCard(
            self._container,
            profile_name=PROFILE_HEDGEHOG,
            image=hedgehog_image,
            display_size=HEDGEHOG_IMAGE_SIZE,
            preserve_aspect=False,
            on_click=self._on_profile_click,
            label_text="Hedgehog",
            initial_opacity=1.0,
        )

        # Loading dots (hidden initially)
        self._loading_dots = LoadingDots(
            self._container,
            base_text="Loading",
            font=("Helvetica", 16),
        )

        # Bind resize event
        self._container.bind("<Configure>", self._on_resize)

        # Initial layout
        self._update_layout()

    def _load_images(self) -> Tuple[Image.Image, Image.Image]:
        """Load Malcolm and Hedgehog logo images."""
        base_dir = get_main_script_dir()
        if base_dir:
            script_dir = Path(base_dir).resolve().parent
        else:
            script_dir = Path(__file__).resolve().parent.parent.parent.parent.parent

        # Malcolm icon
        malcolm_paths = [
            script_dir / "docs/images/icon/icon.png",
            script_dir / "docs/images/icon/icon_dark.png",
        ]
        malcolm_image = self._load_first_available(malcolm_paths)

        # Hedgehog logo
        hedgehog_paths = [
            script_dir / "docs/images/hedgehog/logo/hedgehog-color-large.png",
            script_dir / "docs/images/hedgehog/logo/hedgehog-color.png",
        ]
        hedgehog_image = self._load_first_available(hedgehog_paths)

        return malcolm_image, hedgehog_image

    def _load_first_available(self, paths: list[Path]) -> Image.Image:
        """Load the first available image from a list of paths."""
        for path in paths:
            if path.exists():
                try:
                    return Image.open(path)
                except Exception as e:
                    InstallerLogger.debug(f"Could not load image from {path}: {e}")
                    continue

        # Fallback: create a placeholder image
        InstallerLogger.warning(f"No image found in {paths}, using placeholder")
        placeholder = Image.new("RGBA", (200, 200), (128, 128, 128, 255))
        return placeholder

    def _update_layout(self) -> None:
        """Compute and update card positions based on container size."""
        try:
            self._container.update_idletasks()
            container_width = self._container.winfo_width()
            container_height = self._container.winfo_height()
        except Exception:
            return

        if container_width < 10 or container_height < 10:
            return

        # Card dimensions (different sizes for each)
        malcolm_card_width = MALCOLM_IMAGE_SIZE[0] + 20
        malcolm_card_height = MALCOLM_IMAGE_SIZE[1] + 60
        hedgehog_card_width = HEDGEHOG_IMAGE_SIZE[0] + 20
        hedgehog_card_height = HEDGEHOG_IMAGE_SIZE[1] + 60

        # Use max height for vertical centering
        max_card_height = max(malcolm_card_height, hedgehog_card_height)

        # Horizontal positions with proper spacing
        total_width = malcolm_card_width + CARD_SPACING + hedgehog_card_width
        start_x = (container_width - total_width) // 2

        malcolm_x = start_x
        hedgehog_x = start_x + malcolm_card_width + CARD_SPACING

        # Vertical: center cards vertically, leave room for title above
        title_height = 60  # Space for title
        card_y = (container_height - max_card_height + title_height) // 2

        self._malcolm_position = (malcolm_x, card_y)
        self._hedgehog_position = (hedgehog_x, card_y)

        # Center position (for selected card animation) - use Malcolm size
        center_x = (container_width - malcolm_card_width) // 2
        self._center_position = (center_x, card_y)

        # Header position (top-left to match MainWindow header layout)
        # Accounts for: main_frame padx=10 + header_frame padx=10 + logo_label padx=10
        header_y = 20
        header_x = 30
        self._header_position = (header_x, header_y)

        # Title position (above the cards)
        title_x = container_width // 2
        title_y = card_y - 50

        # Place elements
        if self._malcolm_card:
            self._malcolm_card.place(x=self._malcolm_position[0], y=self._malcolm_position[1])

        if self._hedgehog_card:
            self._hedgehog_card.place(x=self._hedgehog_position[0], y=self._hedgehog_position[1])

        if self._title_label:
            self._title_label.place(x=title_x, y=title_y, anchor="center")

    def _on_resize(self, event) -> None:
        """Handle container resize."""
        self._update_layout()

    def _start_fade_in(self) -> None:
        """Start the fade-in animation for both cards."""
        config = AnimationConfig(duration_ms=FADE_IN_DURATION_MS, easing="ease_out_cubic")

        def on_frame(progress: float) -> None:
            if self._malcolm_card:
                self._malcolm_card.set_opacity(progress)
            if self._hedgehog_card:
                self._hedgehog_card.set_opacity(progress)

        self._animation_controller.animate(config, on_frame)

    def _on_profile_click(self, profile_name: str) -> None:
        """Handle profile card click."""
        if self._selected_profile is not None:
            return  # Already selected

        self._selected_profile = profile_name

        # Disable hover and click on both cards
        if self._malcolm_card:
            self._malcolm_card.enable_hover(False)
            self._malcolm_card.enable_click(False)
        if self._hedgehog_card:
            self._hedgehog_card.enable_hover(False)
            self._hedgehog_card.enable_click(False)

        # Hide title
        if self._title_label:
            self._title_label.place_forget()

        # Start selection animation
        self._animate_selection()

    def _animate_selection(self) -> None:
        """Animate: hide unselected immediately, then slide selected to center."""
        selected_card = (
            self._malcolm_card
            if self._selected_profile == PROFILE_MALCOLM
            else self._hedgehog_card
        )
        unselected_card = (
            self._hedgehog_card
            if self._selected_profile == PROFILE_MALCOLM
            else self._malcolm_card
        )

        start_pos = (
            self._malcolm_position
            if self._selected_profile == PROFILE_MALCOLM
            else self._hedgehog_position
        )
        end_pos = self._center_position

        # Immediately hide the unselected card (no fade animation)
        if unselected_card:
            unselected_card.place_forget()

        # Now slide selected to center
        slide_config = AnimationConfig(
            duration_ms=SLIDE_TO_CENTER_DURATION_MS, easing="ease_out_cubic"
        )

        def slide_frame(progress: float) -> None:
            if selected_card:
                x = lerp_int(start_pos[0], end_pos[0], progress)
                y = lerp_int(start_pos[1], end_pos[1], progress)
                selected_card.place(x=x, y=y)

        def slide_complete() -> None:
            self._show_loading_phase()

        self._animation_controller.animate(slide_config, slide_frame, slide_complete)

    def _show_loading_phase(self) -> None:
        """Show loading dots and prepare MainWindow in background."""
        # Position loading dots below the selected card
        try:
            container_width = self._container.winfo_width()
            loading_y = self._center_position[1] + MALCOLM_IMAGE_SIZE[1] + 80
            self._loading_dots.place(x=container_width // 2, y=loading_y, anchor="center")
            self._loading_dots.start()
        except Exception:
            pass

        # Set the profile value in config (non-blocking)
        from scripts.installer.configs.constants.configuration_item_keys import KEY_CONFIG_ITEM_MALCOLM_PROFILE

        self._malcolm_config.set_value(KEY_CONFIG_ITEM_MALCOLM_PROFILE, self._selected_profile)

        # Notify parent to start building MainWindow in background
        if self._on_loading_start:
            self._on_loading_start(self._selected_profile)

        # Minimum loading time for visual effect, then proceed
        after_id = self._container.after(800, self._on_loading_complete)
        self._after_ids.append(after_id)

    def _on_loading_complete(self) -> None:
        """Called when loading phase completes."""
        # Stop loading dots
        if self._loading_dots:
            self._loading_dots.stop()
            self._loading_dots.place_forget()

        # Start slide-up animation
        self._animate_slide_up()

    def _animate_slide_up(self) -> None:
        """Animate selected card sliding up and shrinking to header position."""
        selected_card = (
            self._malcolm_card
            if self._selected_profile == PROFILE_MALCOLM
            else self._hedgehog_card
        )

        start_pos = self._center_position
        end_pos = self._header_position
        start_scale = 1.0
        end_scale = HEADER_IMAGE_SIZE[0] / MALCOLM_IMAGE_SIZE[0]  # ~0.3

        config = AnimationConfig(duration_ms=SLIDE_UP_DURATION_MS, easing="ease_out_cubic")

        def on_frame(progress: float) -> None:
            if selected_card:
                x = lerp_int(start_pos[0], end_pos[0], progress)
                y = lerp_int(start_pos[1], end_pos[1], progress)
                scale = lerp(start_scale, end_scale, progress)
                selected_card.set_opacity_and_scale(1.0, scale)
                selected_card.place(x=x, y=y)

        def on_complete() -> None:
            self._finalize()

        self._animation_controller.animate(config, on_frame, on_complete)

    def _finalize(self) -> None:
        """Finalize splash screen and invoke callback."""
        # Create header image for MainWindow
        selected_card = (
            self._malcolm_card
            if self._selected_profile == PROFILE_MALCOLM
            else self._hedgehog_card
        )

        if selected_card:
            # Create a small CTkImage for the header
            from scripts.installer.ui.gui.splash.image_animator import ImageAnimator

            # Load original image again for header
            malcolm_image, hedgehog_image = self._load_images()
            header_source = (
                malcolm_image
                if self._selected_profile == PROFILE_MALCOLM
                else hedgehog_image
            )

            animator = ImageAnimator(header_source, display_size=HEADER_IMAGE_SIZE)
            self._header_image = animator.create_ctk_image(opacity=1.0, preserve_transparency=True)

        # Invoke callback
        if self._on_complete:
            self._on_complete(self._selected_profile, self._header_image)

    def destroy(self) -> None:
        """Clean up splash screen resources."""
        # Cancel all pending after callbacks
        for after_id in self._after_ids:
            try:
                self._container.after_cancel(after_id)
            except Exception:
                pass
        self._after_ids.clear()

        # Cancel all animations
        if self._animation_controller:
            self._animation_controller.cancel_all()

        # Stop loading dots
        if self._loading_dots:
            self._loading_dots.stop()

        # Destroy container (removes all children)
        if self._container:
            try:
                self._container.destroy()
            except Exception:
                pass

        self._container = None
        self._malcolm_card = None
        self._hedgehog_card = None
        self._title_label = None
        self._loading_dots = None
