#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2025 Battelle Energy Alliance, LLC.  All rights reserved.

"""Main window for the Malcolm GUI installer with tab-based interface."""

from typing import TYPE_CHECKING, Optional
import customtkinter

from scripts.installer.utils.logger_utils import InstallerLogger
from scripts.installer.ui.gui.tabs.base_tab import BaseTab

if TYPE_CHECKING:
    from scripts.installer.core.malcolm_config import MalcolmConfig
    from scripts.installer.core.install_context import InstallContext


class MainWindow:
    """Main tabbed window for Malcolm configuration."""

    def __init__(
        self,
        malcolm_config: "MalcolmConfig",
        install_context: "InstallContext",
        main_menu_keys: list[str],
        debug_mode: bool = False,
        root: Optional[customtkinter.CTk] = None,
    ):
        """Initialize the main window with tabs.

        Args:
            malcolm_config: MalcolmConfig instance containing all configuration
            install_context: InstallContext instance for installation decisions
            main_menu_keys: List of main menu configuration keys to display as tabs
            debug_mode: Whether to enable debug menu options
        """
        self.malcolm_config = malcolm_config
        self.install_context = install_context
        self.main_menu_keys = main_menu_keys
        self.debug_mode = debug_mode
        self.result = False
        self.tabs = {}

        self.root = root or customtkinter.CTk()
        self.root.title("Malcolm Installer Configuration")
        self.root.geometry("900x700")

        self._build_ui()

    def _build_ui(self):
        """Build the main UI with tabs and button bar."""
        main_frame = customtkinter.CTkFrame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_view = customtkinter.CTkTabview(main_frame)
        self.tab_view.pack(fill="both", expand=True, padx=10, pady=10)

        self._create_tabs()
        self._create_button_bar(main_frame)

    def _create_tabs(self):
        """Create tabs for all MenuItems in main_menu_keys."""
        for menu_key in self.main_menu_keys:
            menu_item = self.malcolm_config.get_menu_item(menu_key)
            config_item = self.malcolm_config.get_item(menu_key)

            if menu_item:
                tab_label = menu_item.label
            elif config_item:
                tab_label = config_item.label
            else:
                InstallerLogger.warning(f"Menu/config item not found for key: {menu_key}")
                continue

            tab_frame = self.tab_view.add(tab_label)

            self.tabs[menu_key] = BaseTab(tab_frame, self.malcolm_config, menu_key)

    def _create_button_bar(self, parent):
        """Create bottom button bar with Save, Search, Exit buttons.

        Args:
            parent: The parent frame to attach the button bar to
        """
        button_frame = customtkinter.CTkFrame(parent, fg_color="transparent")
        button_frame.pack(fill="x", padx=10, pady=10)

        save_button = customtkinter.CTkButton(
            button_frame,
            text="Save & Continue",
            command=self._on_save,
            width=150,
        )
        save_button.pack(side="left", padx=5)

        search_button = customtkinter.CTkButton(
            button_frame,
            text="Search",
            command=self._on_search,
            width=100,
        )
        search_button.pack(side="left", padx=5)

        exit_button = customtkinter.CTkButton(
            button_frame,
            text="Exit",
            command=self._on_exit,
            width=100,
        )
        exit_button.pack(side="right", padx=5)

    def _on_save(self):
        """Handle Save & Continue button click."""
        self.result = True
        self.root.destroy()

    def _on_search(self):
        """Handle Search button click."""
        # TODO: Phase 5 - Implement search functionality using shared search_utils
        InstallerLogger.info("Search functionality will be implemented in Phase 5")

    def _on_exit(self):
        """Handle Exit button click."""
        from scripts.installer.ui.gui.components.dialog import show_confirmation_dialog

        if show_confirmation_dialog(
            self.root,
            "Are you sure you want to exit? Any unsaved changes will be lost.",
            title="Confirm Exit",
            ok_text="Yes",
            cancel_text="No",
        ):
            self.result = False
            self.root.destroy()

    def run(self) -> bool:
        """Run the main window event loop.

        Returns:
            True if user saved and continued, False if user exited
        """
        self.root.mainloop()
        return self.result
