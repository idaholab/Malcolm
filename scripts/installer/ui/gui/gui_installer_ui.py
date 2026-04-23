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
    from scripts.installer.ui.gui.main_window import MainWindow


class GUIInstallerUI(InstallerUI):
    """CustomTkinter-based GUI implementation for Malcolm installer."""

    def __init__(self, ui_mode: UserInterfaceMode = UserInterfaceMode.InteractionGUI):
        """Initialize the GUI interface.

        Args:
            ui_mode: The user interface mode (InteractionGUI for GUI)
        """
        super().__init__(ui_mode)
        customtkinter.set_appearance_mode("system")
        customtkinter.set_default_color_theme("blue")
        self._root = None
        self._main_window: Optional["MainWindow"] = None

    def _ensure_root(self):
        """Ensure a root window exists for dialogs."""
        if self._root is None:
            self._root = customtkinter.CTk()
            self._root.withdraw()
            # Update to ensure window is created before dialogs try to use it
            self._root.update_idletasks()

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

        Shows animated splash screen for profile selection, then displays
        the configuration tabs filtered by the selected profile.

        Args:
            malcolm_config: MalcolmConfig instance containing all configuration
            install_context: InstallContext instance for installation decisions
            main_menu_keys: List of main menu configuration keys to display
            debug_mode: Whether to enable debug menu options

        Returns:
            True if user selected to save and continue, False if user cancelled
        """
        from scripts.installer.ui.gui.main_window import MainWindow
        from scripts.installer.ui.gui.splash.splash_screen import SplashScreen

        self._ensure_root()
        self._root.deiconify()
        self._root.geometry("900x700")

        # State to track splash completion and pre-built main window
        splash_result = {"profile": None, "header_image": None, "complete": False}
        main_window_holder = {"window": None}

        def on_loading_start(profile: str):
            """Called when loading phase starts - build MainWindow in background."""
            main_window_holder["window"] = MainWindow(
                malcolm_config,
                install_context,
                main_menu_keys,
                debug_mode,
                root=self._root,
                selected_profile=profile,
                header_image=None,  # Set later when animation completes
                build_only=True,  # Don't display yet
            )

        def on_splash_complete(profile: str, header_image):
            """Called when splash screen animation completes."""
            splash_result["profile"] = profile
            splash_result["header_image"] = header_image
            splash_result["complete"] = True

        # Show splash screen for profile selection
        splash = SplashScreen(
            self._root,
            malcolm_config,
            on_splash_complete,
            on_loading_start=on_loading_start,
        )
        splash.show()

        # Wait for splash to complete using polling
        def check_splash_complete():
            if splash_result["complete"]:
                # Splash complete - transition to main window
                splash.destroy()
                self._show_main_window(
                    main_window_holder["window"],
                    splash_result["header_image"],
                )
            else:
                # Still waiting, check again
                self._root.after(50, check_splash_complete)

        if self._main_window is None:
            check_splash_complete()
        else:
            self._main_window.load_config_phase(main_menu_keys)

        self._root.mainloop()
        return self._main_window.result if self._main_window else False

    def _show_main_window(
        self,
        main_window: "MainWindow",
        header_image,
    ) -> None:
        """Display the pre-built main configuration window."""
        self._main_window = main_window
        if header_image:
            self._main_window.set_header_image(header_image)
        self._main_window.display()
        self._root.protocol("WM_DELETE_WINDOW", self._main_window._on_exit)

    def gather_install_options(
        self,
        platform: "BaseInstaller",
        malcolm_config: "MalcolmConfig",
        install_context: "InstallContext",
    ) -> Optional["InstallContext"]:
        """Swap the main window into install-options phase and wait for the user."""
        if self._main_window is None:
            return install_context
        self._main_window.load_install_phase(install_context)
        self._root.mainloop()
        return install_context if self._main_window.result else None

    def show_final_configuration_summary(
        self,
        malcolm_config: "MalcolmConfig",
        config_dir: str,
        install_context: "InstallContext",
        is_dry_run: bool = False,
    ) -> bool:
        """Swap the main window into summary phase and wait for the user."""
        if self._main_window is None:
            return False
        self._main_window.load_summary_phase(malcolm_config, config_dir, install_context, is_dry_run)
        self._root.mainloop()
        return bool(self._main_window.result)
