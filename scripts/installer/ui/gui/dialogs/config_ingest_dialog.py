#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2025 Battelle Energy Alliance, LLC.  All rights reserved.

"""Config ingestion dialog for GUI installer."""

import os
from typing import TYPE_CHECKING, Optional, Tuple
import customtkinter
from tkinter import filedialog

from scripts.installer.utils.logger_utils import InstallerLogger
from scripts.installer.ui.gui.components.dialog import show_message_dialog, show_confirmation_dialog

if TYPE_CHECKING:
    from scripts.installer.core.malcolm_config import MalcolmConfig


def show_config_ingest_dialog(
    parent: customtkinter.CTk,
    malcolm_config: "MalcolmConfig",
    default_config_dir: str,
) -> Tuple[bool, Optional[str], Optional[str]]:
    """Show config ingestion dialog to select and load configuration directory.

    Args:
        parent: Parent CTk window
        malcolm_config: MalcolmConfig instance
        default_config_dir: Default configuration directory path

    Returns:
        Tuple of (success, input_dir, output_dir)
        - success: True if user completed the flow, False if cancelled
        - input_dir: Selected input configuration directory (or None if cancelled)
        - output_dir: Selected output configuration directory (or None if cancelled)
    """
    dialog = ConfigIngestDialog(parent, malcolm_config, default_config_dir)
    result = dialog.run()
    return result


class ConfigIngestDialog:
    """Modal dialog for configuration directory selection and ingestion."""

    def __init__(
        self,
        parent: customtkinter.CTk,
        malcolm_config: "MalcolmConfig",
        default_config_dir: str,
    ):
        """Initialize the config ingestion dialog.

        Args:
            parent: Parent CTk window
            malcolm_config: MalcolmConfig instance
            default_config_dir: Default configuration directory path
        """
        self.parent = parent
        self.malcolm_config = malcolm_config
        self.default_config_dir = default_config_dir
        self.result = (False, None, None)

    def run(self) -> Tuple[bool, Optional[str], Optional[str]]:
        """Run the config ingestion flow.

        Returns:
            Tuple of (success, input_dir, output_dir)
        """
        # Create modal dialog
        dialog = customtkinter.CTkToplevel(self.parent)
        dialog.title("Configuration Import")
        dialog.geometry("500x250")
        dialog.transient(self.parent)
        dialog.grab_set()
        dialog.focus_force()

        # Center on screen (since parent is withdrawn)
        dialog.update_idletasks()
        screen_width = dialog.winfo_screenwidth()
        screen_height = dialog.winfo_screenheight()
        x = (screen_width // 2) - (dialog.winfo_width() // 2)
        y = (screen_height // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")

        # Make sure dialog appears
        dialog.deiconify()
        dialog.lift()
        dialog.attributes('-topmost', True)
        dialog.after(100, lambda: dialog.attributes('-topmost', False))

        # Store dialog reference
        self.dialog = dialog

        # Main content
        content_frame = customtkinter.CTkFrame(dialog, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Title
        title_label = customtkinter.CTkLabel(
            content_frame,
            text="Import Existing Configuration?",
            font=("Helvetica", 16, "bold"),
        )
        title_label.pack(pady=(0, 10))

        # Description
        desc_label = customtkinter.CTkLabel(
            content_frame,
            text=(
                "You can import settings from an existing Malcolm configuration directory\n"
                "or start with a fresh configuration using default values."
            ),
            wraplength=450,
        )
        desc_label.pack(pady=(0, 20))

        # Default directory info
        default_info = customtkinter.CTkLabel(
            content_frame,
            text=f"Default directory: {self.default_config_dir}",
            font=("Courier", 10),
            text_color="gray",
        )
        default_info.pack(pady=(0, 20))

        # Buttons
        button_frame = customtkinter.CTkFrame(content_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(10, 0))

        def on_browse():
            """Handle Browse button click - supports both directories and tarballs."""
            # First try directory selection
            config_path = filedialog.askdirectory(
                parent=dialog,
                title="Select Malcolm Configuration Directory (or Cancel to select tarball)",
                initialdir=self.default_config_dir,
            )

            # If user cancelled directory selection, offer to select tarball
            if not config_path:
                from scripts.installer.ui.gui.components.dialog import show_confirmation_dialog
                select_tarball = show_confirmation_dialog(
                    dialog,
                    "No directory selected. Do you want to select a Malcolm tarball (.tar.gz) instead?",
                    title="Select Tarball?",
                    ok_text="Yes, Select Tarball",
                    cancel_text="Cancel"
                )

                if select_tarball:
                    config_path = filedialog.askopenfilename(
                        parent=dialog,
                        title="Select Malcolm Tarball",
                        initialdir=self.default_config_dir,
                        filetypes=[("Malcolm Tarballs", "*.tar.gz"), ("All Files", "*.*")]
                    )

                if not config_path:
                    return  # User cancelled

            if config_path:
                success, input_dir, output_dir = self._handle_selected_path(dialog, config_path)
                if success:
                    self.result = (True, input_dir, output_dir)
                    dialog.destroy()
                # If validation failed, dialog stays open for user to try again

        def on_use_default():
            """Handle Use Default button click."""
            success, input_dir, output_dir = self._validate_and_load_config(dialog, self.default_config_dir)
            if success:
                self.result = (True, input_dir, output_dir)
                dialog.destroy()

        def on_cancel():
            """Handle Cancel button click."""
            self.result = (False, None, None)
            dialog.destroy()

        browse_button = customtkinter.CTkButton(
            button_frame,
            text="Browse...",
            command=on_browse,
            width=120,
        )
        browse_button.pack(side="left", padx=5)

        default_button = customtkinter.CTkButton(
            button_frame,
            text="Use Default",
            command=on_use_default,
            width=120,
        )
        default_button.pack(side="left", padx=5)

        cancel_button = customtkinter.CTkButton(
            button_frame,
            text="Cancel",
            command=on_cancel,
            width=120,
            fg_color="gray",
        )
        cancel_button.pack(side="right", padx=5)

        # Wait for dialog to close
        dialog.wait_window()

        return self.result

    def _handle_selected_path(
        self,
        dialog: customtkinter.CTkToplevel,
        path: str,
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """Handle selected path - could be directory or tarball.

        Args:
            dialog: The dialog window
            path: Path to directory or tarball file

        Returns:
            Tuple of (success, input_dir, output_dir)
        """
        from scripts.installer.utils.file_utils import validate_malcolm_tarball, extract_malcolm_tarball
        from scripts.installer.ui.gui.components.dialog import show_confirmation_dialog

        # Check if it's a tarball file
        if os.path.isfile(path):
            # Validate tarball
            is_valid, error_msg = validate_malcolm_tarball(path)
            if not is_valid:
                show_message_dialog(
                    dialog,
                    f"Invalid Malcolm tarball:\\n{error_msg}",
                    title="Invalid Tarball",
                    message_type="error",
                )
                return (False, None, None)

            # Ask user where to extract
            extract_confirmed = show_confirmation_dialog(
                dialog,
                f"Found valid Malcolm tarball:\\n{path}\\n\\nExtract to default directory?",
                title="Extract Tarball",
                ok_text="Yes, Extract",
                cancel_text="Cancel"
            )

            if not extract_confirmed:
                return (False, None, None)

            # Extract tarball
            extract_dir = self.default_config_dir
            success, config_dir = extract_malcolm_tarball(path, extract_dir)

            if not success:
                show_message_dialog(
                    dialog,
                    f"Failed to extract tarball to:\\n{extract_dir}",
                    title="Extraction Failed",
                    message_type="error",
                )
                return (False, None, None)

            # Validate and load the extracted directory
            return self._validate_and_load_config(dialog, config_dir)

        # It's a directory
        elif os.path.isdir(path):
            return self._validate_and_load_config(dialog, path)

        # Unknown path type
        else:
            show_message_dialog(
                dialog,
                f"Path is neither a file nor directory:\\n{path}",
                title="Invalid Path",
                message_type="error",
            )
            return (False, None, None)

    def _validate_and_load_config(
        self,
        dialog: customtkinter.CTkToplevel,
        config_dir: str,
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """Validate config directory and optionally load existing .env files.

        Args:
            dialog: The dialog window
            config_dir: Configuration directory path to validate

        Returns:
            Tuple of (success, input_dir, output_dir)
        """
        # 1. Check if directory exists
        if not os.path.exists(config_dir):
            show_message_dialog(
                dialog,
                f"Directory does not exist:\n{config_dir}",
                title="Invalid Directory",
                message_type="error",
            )
            return (False, None, None)

        if not os.path.isdir(config_dir):
            show_message_dialog(
                dialog,
                f"Path is not a directory:\n{config_dir}",
                title="Invalid Directory",
                message_type="error",
            )
            return (False, None, None)

        # 2. Validate directory has .env.example template files
        try:
            files = os.listdir(config_dir)
            example_files = [f for f in files if f.endswith(".env.example")]

            if not example_files:
                show_message_dialog(
                    dialog,
                    (
                        f"Directory does not contain .env.example template files:\n{config_dir}\n\n"
                        "Please select a valid Malcolm configuration directory."
                    ),
                    title="Invalid Configuration Directory",
                    message_type="error",
                )
                return (False, None, None)

        except Exception as e:
            show_message_dialog(
                dialog,
                f"Error reading directory:\n{config_dir}\n\nError: {e}",
                title="Directory Read Error",
                message_type="error",
            )
            return (False, None, None)

        # 3. Check for existing .env files
        env_files = [f for f in files if f.endswith(".env") and not f.endswith(".example")]

        if env_files:
            # Ask user if they want to load existing .env files
            load_existing = show_confirmation_dialog(
                dialog,
                (
                    f"Found {len(env_files)} existing .env file(s) in:\n{config_dir}\n\n"
                    "Do you want to load settings from these files?"
                ),
                title="Load Existing Configuration",
                ok_text="Yes, Load Settings",
                cancel_text="No, Use Defaults",
            )

            if load_existing:
                try:
                    self.malcolm_config.load_from_env_files(config_dir)
                    InstallerLogger.info(f"Loaded existing .env files from: {config_dir}")

                    # Also try to load from orchestration file (docker-compose.yml)
                    from scripts.malcolm_constants import OrchestrationFramework
                    from scripts.installer.configs.constants.configuration_item_keys import (
                        KEY_CONFIG_ITEM_DOCKER_ORCHESTRATION_MODE,
                    )

                    orch_mode = self.malcolm_config.get_value(KEY_CONFIG_ITEM_DOCKER_ORCHESTRATION_MODE)
                    if orch_mode != OrchestrationFramework.KUBERNETES:
                        try:
                            loaded_from_orch = self.malcolm_config.load_from_orchestration_file(
                                config_dir, None  # malcolm_orchestration_file = None (auto-detect)
                            )
                            if loaded_from_orch:
                                InstallerLogger.info(f"Loaded config from: {loaded_from_orch}")
                        except Exception as e:
                            # Not fatal - just log the error
                            InstallerLogger.warning(f"Could not load from orchestration file: {e}")

                except Exception as e:
                    show_message_dialog(
                        dialog,
                        f"Error loading .env files:\n{e}",
                        title="Load Error",
                        message_type="error",
                    )
                    return (False, None, None)
            else:
                InstallerLogger.info("User chose to use default values instead of loading existing .env files")
        else:
            InstallerLogger.info(f"No existing .env files found in {config_dir}. Using default values.")

        # Success - use same directory for both input and output
        return (True, config_dir, config_dir)
