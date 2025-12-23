#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2025 Battelle Energy Alliance, LLC.  All rights reserved.

"""GUI implementation for the Malcolm installer using customtkinter."""

from typing import Optional, TYPE_CHECKING
import customtkinter

from scripts.malcolm_common import UserInterfaceMode
from scripts.installer.utils.logger_utils import InstallerLogger
from scripts.installer.ui.shared.installer_ui import InstallerUI
from scripts.installer.ui.gui.components.dialog import show_error_dialog, show_confirmation_dialog

if TYPE_CHECKING:
    from scripts.installer.core.malcolm_config import MalcolmConfig
    from scripts.installer.platforms.base import BaseInstaller
    from scripts.installer.core.install_context import InstallContext


class GUIInstallerUI(InstallerUI):
    """CustomTkinter-based GUI implementation for Malcolm installer."""

    def __init__(self, ui_mode: UserInterfaceMode = UserInterfaceMode.InteractionGUI):
        """Initialize the GUI interface.

        Args:
            ui_mode: The user interface mode (InteractionGUI for GUI)
        """
        super().__init__(ui_mode)
        customtkinter.set_appearance_mode("dark")
        customtkinter.set_default_color_theme("blue")
        self._root = None

    def _ensure_root(self):
        """Ensure a root window exists for dialogs."""
        if self._root is None:
            self._root = customtkinter.CTk()
            self._root.withdraw()

    def ask_yes_no(self, message: str, default: bool = True, force_interaction: bool = False) -> bool:
        """Ask the user a yes/no question using a GUI dialog.

        Args:
            message: The question to ask the user
            default: Default answer if user just presses enter
            force_interaction: Force user interaction even if in non-interactive mode

        Returns:
            True for yes, False for no
        """
        self._ensure_root()
        return show_confirmation_dialog(
            self._root,
            message,
            title="Confirm",
            ok_text="Yes",
            cancel_text="No",
        )

    def ask_string(self, prompt: str, default: str = "", force_interaction: bool = False) -> Optional[str]:
        """Ask the user for a string input using a GUI dialog.

        Args:
            prompt: The prompt to show the user
            default: Default value if user just presses enter
            force_interaction: Force user interaction even if in non-interactive mode

        Returns:
            The user's input string, or None if cancelled
        """
        self._ensure_root()

        result = [None]

        dialog = customtkinter.CTkToplevel(self._root)
        dialog.title("Input Required")
        dialog.geometry("400x200")
        dialog.grab_set()

        label = customtkinter.CTkLabel(dialog, text=prompt, wraplength=350)
        label.pack(padx=20, pady=20)

        entry_var = customtkinter.StringVar(value=default)
        entry = customtkinter.CTkEntry(dialog, textvariable=entry_var, width=350)
        entry.pack(padx=20, pady=10)
        entry.focus()

        def on_ok():
            result[0] = entry_var.get()
            dialog.destroy()

        def on_cancel():
            dialog.destroy()

        button_frame = customtkinter.CTkFrame(dialog, fg_color="transparent")
        button_frame.pack(padx=20, pady=20, fill="x")

        ok_button = customtkinter.CTkButton(button_frame, text="OK", command=on_ok, width=100)
        ok_button.pack(side="left", padx=(0, 10))

        cancel_button = customtkinter.CTkButton(button_frame, text="Cancel", command=on_cancel, width=100)
        cancel_button.pack(side="right")

        entry.bind("<Return>", lambda e: on_ok())
        entry.bind("<Escape>", lambda e: on_cancel())

        dialog.wait_window()

        return result[0]

    def ask_password(self, prompt: str, default: str = "") -> Optional[str]:
        """Ask the user for a password using a GUI dialog.

        Args:
            prompt: The prompt to show the user
            default: Default value if user just presses enter

        Returns:
            The user's password input, or None if cancelled
        """
        self._ensure_root()

        result = [None]

        dialog = customtkinter.CTkToplevel(self._root)
        dialog.title("Password Required")
        dialog.geometry("400x200")
        dialog.grab_set()

        label = customtkinter.CTkLabel(dialog, text=prompt, wraplength=350)
        label.pack(padx=20, pady=20)

        entry_var = customtkinter.StringVar(value=default)
        entry = customtkinter.CTkEntry(dialog, textvariable=entry_var, show="*", width=350)
        entry.pack(padx=20, pady=10)
        entry.focus()

        def on_ok():
            result[0] = entry_var.get()
            dialog.destroy()

        def on_cancel():
            dialog.destroy()

        button_frame = customtkinter.CTkFrame(dialog, fg_color="transparent")
        button_frame.pack(padx=20, pady=20, fill="x")

        ok_button = customtkinter.CTkButton(button_frame, text="OK", command=on_ok, width=100)
        ok_button.pack(side="left", padx=(0, 10))

        cancel_button = customtkinter.CTkButton(button_frame, text="Cancel", command=on_cancel, width=100)
        cancel_button.pack(side="right")

        entry.bind("<Return>", lambda e: on_ok())
        entry.bind("<Escape>", lambda e: on_cancel())

        dialog.wait_window()

        return result[0]

    def display_message(self, message: str) -> None:
        """Display a message to the user using a GUI dialog.

        Args:
            message: The message to display
        """
        self._ensure_root()
        dialog = customtkinter.CTkToplevel(self._root)
        dialog.title("Information")
        dialog.geometry("400x200")
        dialog.grab_set()

        label = customtkinter.CTkLabel(dialog, text=message, wraplength=350)
        label.pack(padx=20, pady=20, fill="both", expand=True)

        ok_button = customtkinter.CTkButton(dialog, text="OK", command=dialog.destroy, width=100)
        ok_button.pack(pady=10)

        dialog.wait_window()

    def display_error(self, message: str) -> None:
        """Display an error message to the user using a GUI dialog.

        Args:
            message: The error message to display
        """
        self._ensure_root()
        InstallerLogger.error(message)
        show_error_dialog(self._root, message, title="Error")

    def run_configuration_menu(
        self,
        malcolm_config: "MalcolmConfig",
        install_context: "InstallContext",
        main_menu_keys: list[str],
        debug_mode: bool = False,
    ) -> bool:
        """Run the GUI configuration menu with tabs.

        Args:
            malcolm_config: MalcolmConfig instance containing all configuration
            install_context: InstallContext instance for installation decisions
            main_menu_keys: List of main menu configuration keys to display
            debug_mode: Whether to enable debug menu options

        Returns:
            True if user selected to save and continue, False if user cancelled
        """
        # TODO: Implement MainWindow in Phase 3
        from scripts.installer.ui.gui.main_window import MainWindow

        self._ensure_root()
        self._root.deiconify()
        main_window = MainWindow(malcolm_config, install_context, main_menu_keys, debug_mode, root=self._root)
        result = main_window.run()
        self._root = None
        return result

    def gather_install_options(
        self,
        platform: "BaseInstaller",
        malcolm_config: "MalcolmConfig",
        install_context: "InstallContext",
    ) -> Optional["InstallContext"]:
        """Gather installation options from the user using GUI dialog.

        Args:
            platform: The platform-specific installer instance
            malcolm_config: MalcolmConfig instance for accessing configuration
            install_context: Pre-created InstallContext instance to populate

        Returns:
            Updated InstallContext with user's installation choices, or None if cancelled
        """
        from scripts.installer.ui.gui.dialogs.installation_dialog import show_installation_dialog

        self._ensure_root()
        self._root.withdraw()  # Keep root hidden during dialog

        try:
            result = show_installation_dialog(self._root, malcolm_config, install_context)
            return result
        finally:
            if self._root:
                self._root.destroy()
                self._root = None

    def show_final_configuration_summary(
        self,
        malcolm_config: "MalcolmConfig",
        config_dir: str,
        install_context: "InstallContext",
        is_dry_run: bool = False,
    ) -> bool:
        """Show final configuration summary and get user confirmation to proceed.

        Args:
            malcolm_config: MalcolmConfig instance containing all configuration
            config_dir: Configuration directory path where files will be saved
            install_context: The populated InstallContext with installation choices.
            is_dry_run: When True, display summary as a dry-run and adjust prompt wording.

        Returns:
            True if user confirms to proceed with installation, False otherwise
        """
        from scripts.installer.ui.gui.dialogs.summary_dialog import show_summary_dialog

        self._ensure_root()
        self._root.withdraw()  # Keep root hidden during dialog

        try:
            result = show_summary_dialog(
                self._root,
                malcolm_config,
                config_dir,
                install_context,
                is_dry_run
            )
            return result
        finally:
            if self._root:
                self._root.destroy()
                self._root = None
