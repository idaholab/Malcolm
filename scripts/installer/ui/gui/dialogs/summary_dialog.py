#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2025 Battelle Energy Alliance, LLC.  All rights reserved.

"""Final configuration summary dialog for GUI installer.

This dialog displays a read-only summary of the user's configuration choices.
It is shown after validation passes in main_window.py, so no validation logic
is needed here - the configuration is already validated before this dialog opens.
"""

from typing import TYPE_CHECKING
import customtkinter

from scripts.installer.utils.logger_utils import InstallerLogger
from scripts.installer.ui.gui.components.styles import CONTAINER_CORNER_RADIUS, INFO_PANEL_BG
from scripts.installer.utils.summary_utils import build_configuration_summary_items
from scripts.installer.ui.shared.menu_builder import ValueFormatter
from scripts.installer.ui.gui.components.scrollable_frame import ScrollableFrame
from scripts.malcolm_constants import PLATFORM_LINUX
import platform as platform_module

if TYPE_CHECKING:
    from scripts.installer.core.malcolm_config import MalcolmConfig
    from scripts.installer.core.install_context import InstallContext


def show_summary_dialog(
    parent: customtkinter.CTk,
    malcolm_config: "MalcolmConfig",
    config_dir: str,
    install_context: "InstallContext",
    is_dry_run: bool = False,
) -> bool:
    """Show final configuration summary dialog.

    Args:
        parent: Parent CTk window
        malcolm_config: MalcolmConfig instance
        config_dir: Configuration directory path
        install_context: InstallContext instance
        is_dry_run: Whether this is a dry run (read-only display)

    Returns:
        True if user clicked Proceed, False if cancelled
    """
    dialog = SummaryDialog(parent, malcolm_config, config_dir, install_context, is_dry_run)
    result = dialog.run()
    return result


class SummaryDialog:
    """Modal dialog for final configuration summary and confirmation."""

    def __init__(
        self,
        parent: customtkinter.CTk,
        malcolm_config: "MalcolmConfig",
        config_dir: str,
        install_context: "InstallContext",
        is_dry_run: bool = False,
    ):
        """Initialize the summary dialog.

        Args:
            parent: Parent CTk window
            malcolm_config: MalcolmConfig instance
            config_dir: Configuration directory path
            install_context: InstallContext instance
            is_dry_run: Whether this is a dry run
        """
        self.parent = parent
        self.malcolm_config = malcolm_config
        self.config_dir = config_dir
        self.install_context = install_context
        self.is_dry_run = is_dry_run
        self.result = False

    def run(self) -> bool:
        """Run the summary dialog.

        Returns:
            True if user clicked Proceed, False if cancelled
        """
        # Create modal dialog
        self.dialog = customtkinter.CTkToplevel(self.parent)
        self.dialog.title("Configuration Summary")
        self.dialog.geometry("900x700")
        self.dialog.transient(self.parent)
        self.dialog.grab_set()

        # Center on parent
        self.dialog.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - (self.dialog.winfo_width() // 2)
        y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")

        self._build_ui()

        # Wait for dialog to close
        self.dialog.wait_window()

        return self.result

    def _build_ui(self):
        """Build the dialog UI with configuration summary."""
        # Main content frame
        content_frame = customtkinter.CTkFrame(self.dialog, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Title
        title_label = customtkinter.CTkLabel(
            content_frame,
            text="Configuration Summary",
            font=("Helvetica", 16, "bold"),
        )
        title_label.pack(pady=(0, 5))

        # Subtitle
        subtitle_text = "Review your configuration before proceeding with installation"
        if self.is_dry_run:
            subtitle_text = "Configuration preview (dry run mode - no changes will be made)"

        subtitle_label = customtkinter.CTkLabel(
            content_frame,
            text=subtitle_text,
            font=("Helvetica", 11),
            text_color="gray",
        )
        subtitle_label.pack(pady=(0, 15))

        # Scrollable text widget for summary
        summary_frame = customtkinter.CTkFrame(content_frame, corner_radius=8)
        summary_frame.pack(fill="both", expand=True, pady=(0, 15))

        summary_text = customtkinter.CTkTextbox(
            summary_frame,
            font=("Courier", 11),
            wrap="word",
        )
        summary_text.pack(fill="both", expand=True, padx=10, pady=10)

        # Build and display summary
        self._build_summary_content(summary_text)

        # Make text read-only
        summary_text.configure(state="disabled")

        # Extended options display (config_only, auto_tweaks, dry_run)
        self._build_extended_options_display(content_frame)

        # Buttons
        self._create_button_bar(content_frame)

    def _build_summary_content(self, text_widget):
        """Build and insert summary content into text widget.

        Args:
            text_widget: CTkTextbox widget
        """
        # Get summary items from shared utility
        summary_items = build_configuration_summary_items(self.malcolm_config, self.config_dir)

        # Build formatted summary text
        summary_lines = []
        summary_lines.append("=" * 80)
        summary_lines.append("MALCOLM CONFIGURATION SUMMARY")
        summary_lines.append("=" * 80)
        summary_lines.append("")

        # Group items by section (optional - for now just list all)
        for label, value in summary_items:
            display_value = ValueFormatter.format_summary_value(label, value)
            formatted_line = f"{label:.<50} {display_value}"
            summary_lines.append(formatted_line)

        summary_lines.append("")
        summary_lines.append("=" * 80)
        summary_lines.append(f"Configuration Directory: {self.config_dir}")
        summary_lines.append("=" * 80)

        # Insert into text widget
        text_widget.insert("1.0", "\n".join(summary_lines))

    def _build_extended_options_display(self, parent):
        """Build read-only display of extended options.

        Args:
            parent: Parent frame
        """
        # Only show this section if any extended options are active
        show_section = False
        options_text = []

        if self.install_context.config_only:
            show_section = True
            options_text.append("⚠ Configuration Only Mode: Installation will be skipped, only configuration files will be saved")

        if platform_module.system().lower() == PLATFORM_LINUX.lower():
            if self.install_context.auto_tweaks:
                show_section = True
                options_text.append("✓ Auto-apply system tweaks: Linux system optimizations will be applied automatically")

        if self.is_dry_run:
            show_section = True
            options_text.append("ℹ Dry Run Mode: No changes will be made to the system")

        if show_section:
            options_frame = customtkinter.CTkFrame(
                parent,
                corner_radius=CONTAINER_CORNER_RADIUS,
                fg_color=INFO_PANEL_BG,
            )
            options_frame.pack(fill="x", pady=(0, 10))

            for option_text in options_text:
                option_label = customtkinter.CTkLabel(
                    options_frame,
                    text=option_text,
                    font=("Helvetica", 11),
                    anchor="w",
                )
                option_label.pack(anchor="w", padx=15, pady=5)

    def _create_button_bar(self, parent):
        """Create bottom button bar with Proceed and Cancel buttons.

        Args:
            parent: Parent frame
        """
        button_frame = customtkinter.CTkFrame(parent, fg_color="transparent")
        button_frame.pack(fill="x", pady=(10, 0))

        def on_proceed():
            """Handle Proceed button click.

            Note: Validation is already done in main_window.py before this dialog is shown.
            """
            self.result = True
            self.dialog.destroy()

        def on_cancel():
            """Handle Cancel button click."""
            self.result = False
            self.dialog.destroy()

        # Button text changes based on mode
        if self.is_dry_run:
            proceed_text = "Close"
        elif self.install_context.config_only:
            proceed_text = "Save Configuration"
        else:
            proceed_text = "Proceed with Installation"

        proceed_button = customtkinter.CTkButton(
            button_frame,
            text=proceed_text,
            command=on_proceed,
            width=180,
        )
        proceed_button.pack(side="left", padx=5)

        cancel_button = customtkinter.CTkButton(
            button_frame,
            text="Cancel",
            command=on_cancel,
            width=120,
            fg_color="gray",
        )
        cancel_button.pack(side="right", padx=5)
