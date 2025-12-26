#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2025 Battelle Energy Alliance, LLC.  All rights reserved.

"""Welcome tab for Malcolm GUI installer."""

import os
from pathlib import Path
import customtkinter
from PIL import Image

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
        # Center content container
        content_frame = customtkinter.CTkFrame(self.parent_frame, fg_color="transparent")
        content_frame.pack(expand=True, fill="both")

        # Center everything vertically and horizontally
        center_frame = customtkinter.CTkFrame(content_frame, fg_color="transparent")
        center_frame.place(relx=0.5, rely=0.5, anchor="center")

        # Try to load Malcolm logo
        logo_loaded = self._load_logo(center_frame)

        # Fallback to text logo if image couldn't be loaded
        if not logo_loaded:
            title_label = customtkinter.CTkLabel(
                center_frame,
                text="MALCOLM",
                font=("Helvetica", 56, "bold"),
            )
            title_label.pack(pady=(0, 10))

        # Subtitle
        subtitle_label = customtkinter.CTkLabel(
            center_frame,
            text="Network Traffic Analysis Tool Suite",
            font=("Helvetica", 16),
            text_color="gray",
        )
        subtitle_label.pack(pady=(10, 30))

        # Welcome message
        message_label = customtkinter.CTkLabel(
            center_frame,
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
        message_label.pack(pady=30, padx=40)

    def _load_logo(self, parent_frame) -> bool:
        """Try to load and display Malcolm logo.

        Args:
            parent_frame: Frame to add logo to

        Returns:
            True if logo was loaded successfully, False otherwise
        """
        script_dir = Path(__file__).parent.parent.parent.parent.parent

        # Try multiple logo locations
        logo_paths = [
            script_dir / "docs/images/logo/Malcolm_outline_banner_dark.png",
            script_dir / "malcolm-iso/config/bootloaders/grub-pc/splash-malcolm.png",
            script_dir / "docs/images/logo/malcolm_logo.png",
        ]

        for logo_path in logo_paths:
            if logo_path.exists():
                try:
                    logo_image = customtkinter.CTkImage(
                        light_image=Image.open(logo_path),
                        dark_image=Image.open(logo_path),
                        size=(500, 150)
                    )
                    logo_label = customtkinter.CTkLabel(
                        parent_frame,
                        image=logo_image,
                        text=""
                    )
                    logo_label.pack(pady=(0, 20))
                    return True
                except Exception as e:
                    InstallerLogger.debug(f"Could not load logo from {logo_path}: {e}")
                    continue

        return False
