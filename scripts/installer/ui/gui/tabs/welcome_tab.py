#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2025 Battelle Energy Alliance, LLC.  All rights reserved.

"""Welcome tab for Malcolm GUI installer."""

import os
import io
from pathlib import Path
import customtkinter
from PIL import Image

from scripts.malcolm_utils import get_main_script_dir
from scripts.installer.utils.logger_utils import InstallerLogger


class WelcomeTab:
    """Welcome tab with Malcolm logo and introduction."""

    def __init__(self, parent_frame: customtkinter.CTkFrame):
        """Initialize the welcome tab.

        Args:
            parent_frame: Parent frame to build the welcome content in
        """
        self.parent_frame = parent_frame
        self._build_ui()

    def _build_ui(self):
        """Build the welcome tab UI."""
        # Content container
        content_frame = customtkinter.CTkFrame(self.parent_frame, fg_color="transparent")
        content_frame.pack(expand=True, fill="both")

        logo_frame = customtkinter.CTkFrame(content_frame, fg_color="transparent")
        logo_frame.pack(pady=(30, 10))

        logo_loaded = self._load_logo(logo_frame)

        if not logo_loaded:
            title_label = customtkinter.CTkLabel(
                logo_frame,
                text="MALCOLM",
                font=("Helvetica", 56, "bold"),
            )
            title_label.pack(pady=(10, 10))

        # Subtitle
        text_frame = customtkinter.CTkFrame(content_frame, fg_color="transparent")
        text_frame.pack(expand=True)

        subtitle_label = customtkinter.CTkLabel(
            text_frame,
            text="Network Traffic Analysis Tool Suite",
            font=("Helvetica", 16),
            text_color="gray",
        )
        subtitle_label.pack(pady=(10, 20))

        # Welcome message
        message_label = customtkinter.CTkLabel(
            text_frame,
            text=(
                "Welcome to the Malcolm Installer!\n\n"
                "This configuration wizard will guide you through setting up Malcolm.\n\n"
                "Use the tabs above to configure different aspects of your Malcolm deployment.\n\n"
                "When you're done, click 'Save & Continue' to proceed with installation."
            ),
            font=("Helvetica", 14),
            wraplength=650,
            justify="center",
        )
        message_label.pack(pady=(10, 30), padx=40)

        appearance_frame = customtkinter.CTkFrame(text_frame, fg_color="transparent")
        appearance_frame.pack(pady=(0, 20))

        appearance_label = customtkinter.CTkLabel(
            appearance_frame,
            text="Appearance",
            font=("Helvetica", 12),
            text_color="gray",
        )
        appearance_label.pack(side="left", padx=(0, 10))

        appearance_switch = customtkinter.CTkSwitch(
            appearance_frame,
            text="Light/Dark",
            command=self._toggle_appearance_mode,
        )
        appearance_switch.pack(side="left")
        appearance_switch.select() if self._is_dark_mode() else appearance_switch.deselect()

    def _load_logo(self, parent_frame) -> bool:
        """Try to load and display Malcolm logo artwork.

        Args:
            parent_frame: Frame to add logo to

        Returns:
            True if logo was loaded successfully, False otherwise
        """
        base_dir = get_main_script_dir()
        if base_dir:
            script_dir = Path(base_dir).resolve().parent
        else:
            script_dir = Path(__file__).resolve().parent.parent.parent.parent.parent

        logo_paths = [
            script_dir / "docs/images/logo/Malcolm.svg",
            script_dir / "docs/images/logo/Malcolm_outline_banner_dark.png",
            script_dir / "docs/images/logo/Malcolm_outline_banner.png",
        ]

        for logo_path in logo_paths:
            if not logo_path.exists():
                continue
            try:
                image = self._open_logo_image(logo_path)
                if image is None:
                    continue
                self.logo_image = customtkinter.CTkImage(
                    light_image=image,
                    dark_image=image,
                    size=(680, 200),
                )
                logo_label = customtkinter.CTkLabel(
                    parent_frame,
                    image=self.logo_image,
                    text="",
                )
                logo_label.pack()
                return True
            except Exception as e:
                InstallerLogger.debug(f"Could not load logo from {logo_path}: {e}")
                continue

        return False

    def _open_logo_image(self, logo_path: Path):
        """Open logo image, optionally converting SVG if supported."""
        if logo_path.suffix.lower() != ".svg":
            return Image.open(logo_path)

        try:
            import cairosvg
        except ImportError:
            InstallerLogger.debug("cairosvg not available; cannot render SVG logo")
            return None

        try:
            svg_bytes = logo_path.read_bytes()
            png_bytes = cairosvg.svg2png(bytestring=svg_bytes)
            return Image.open(io.BytesIO(png_bytes))
        except Exception as e:
            InstallerLogger.debug(f"Failed to render SVG logo from {logo_path}: {e}")
            return None

    def _is_dark_mode(self) -> bool:
        """Return True if the current appearance mode is dark."""
        try:
            mode = customtkinter.get_appearance_mode()
            return mode.lower() == "dark" if mode else False
        except AttributeError:
            # get_appearance_mode returned None or unexpected type
            return False
        except Exception as e:
            InstallerLogger.debug(f"Could not determine appearance mode: {e}")
            return False

    def _toggle_appearance_mode(self):
        """Toggle between light and dark appearance modes."""
        target = "light" if self._is_dark_mode() else "dark"
        customtkinter.set_appearance_mode(target)
