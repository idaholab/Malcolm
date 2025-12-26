#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2025 Battelle Energy Alliance, LLC.  All rights reserved.

"""Welcome splash screen dialog for GUI installer."""

import os
from pathlib import Path
from typing import Optional
import customtkinter
from PIL import Image

from scripts.installer.utils.logger_utils import InstallerLogger


def show_welcome_dialog(parent: Optional[customtkinter.CTk] = None) -> None:
    """Show welcome splash screen with Malcolm logo.

    Args:
        parent: Parent CTk window (can be None for standalone splash)
    """
    dialog = WelcomeDialog(parent)
    dialog.run()


class WelcomeDialog:
    """Welcome splash screen with Malcolm logo and brief intro."""

    def __init__(self, parent: Optional[customtkinter.CTk] = None):
        """Initialize the welcome dialog.

        Args:
            parent: Parent CTk window (can be None)
        """
        self.parent = parent

    def run(self) -> None:
        """Display the welcome splash screen."""
        # Create toplevel or root window
        if self.parent:
            dialog = customtkinter.CTkToplevel(self.parent)
            dialog.transient(self.parent)
        else:
            dialog = customtkinter.CTk()

        dialog.title("Malcolm Installer")
        dialog.geometry("600x400")

        # Remove window decorations for splash effect
        dialog.overrideredirect(True)

        # Center on screen
        dialog.update_idletasks()
        screen_width = dialog.winfo_screenwidth()
        screen_height = dialog.winfo_screenheight()
        x = (screen_width // 2) - (300)
        y = (screen_height // 2) - (200)
        dialog.geometry(f"+{x}+{y}")

        # Main content frame
        content_frame = customtkinter.CTkFrame(
            dialog,
            corner_radius=10,
            border_width=2,
            border_color=("gray70", "gray30")
        )
        content_frame.pack(fill="both", expand=True, padx=0, pady=0)

        # Try to load Malcolm logo/splash
        logo_frame = customtkinter.CTkFrame(content_frame, fg_color="transparent")
        logo_frame.pack(pady=(30, 10))

        logo_loaded = False
        script_dir = Path(__file__).parent.parent.parent.parent.parent

        # Try multiple logo locations
        logo_paths = [
            script_dir / "malcolm-iso/config/bootloaders/grub-pc/splash-malcolm.png",
            script_dir / "docs/images/logo/malcolm_logo.svg",
        ]

        for logo_path in logo_paths:
            if logo_path.exists():
                try:
                    if logo_path.suffix == '.png':
                        logo_image = customtkinter.CTkImage(
                            light_image=Image.open(logo_path),
                            dark_image=Image.open(logo_path),
                            size=(400, 200)
                        )
                        logo_label = customtkinter.CTkLabel(
                            logo_frame,
                            image=logo_image,
                            text=""
                        )
                        logo_label.pack()
                        logo_loaded = True
                        break
                except Exception as e:
                    InstallerLogger.warning(f"Could not load logo from {logo_path}: {e}")
                    continue

        # Fallback to text logo if image couldn't be loaded
        if not logo_loaded:
            title_label = customtkinter.CTkLabel(
                logo_frame,
                text="MALCOLM",
                font=("Helvetica", 48, "bold"),
            )
            title_label.pack()

        # Subtitle
        subtitle_label = customtkinter.CTkLabel(
            content_frame,
            text="Network Traffic Analysis Tool Suite",
            font=("Helvetica", 14),
            text_color="gray",
        )
        subtitle_label.pack(pady=(10, 20))

        # Welcome message
        message_label = customtkinter.CTkLabel(
            content_frame,
            text=(
                "Welcome to the Malcolm Installer!\n\n"
                "This wizard will guide you through configuring and installing Malcolm.\n\n"
                "Click anywhere to continue..."
            ),
            font=("Helvetica", 12),
            wraplength=500,
        )
        message_label.pack(pady=20, padx=40)

        # Version info (optional)
        version_label = customtkinter.CTkLabel(
            content_frame,
            text="Installer v2.0",
            font=("Courier", 10),
            text_color="gray",
        )
        version_label.pack(side="bottom", pady=10)

        # Auto-close after 3 seconds or on click
        def close_dialog(event=None):
            dialog.destroy()

        dialog.bind("<Button-1>", close_dialog)
        dialog.after(3000, close_dialog)

        # Make dialog appear
        dialog.deiconify()
        dialog.lift()
        dialog.attributes('-topmost', True)
        dialog.after(100, lambda: dialog.attributes('-topmost', False))

        # Wait for dialog to close
        if self.parent:
            dialog.wait_window()
        else:
            dialog.mainloop()
