#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2025 Battelle Energy Alliance, LLC.  All rights reserved.

"""Installation options dialog for GUI installer."""

from typing import Any, Dict, TYPE_CHECKING, Optional
import customtkinter

from scripts.installer.utils.logger_utils import InstallerLogger
from scripts.installer.ui.shared.store_view_model import build_rows_from_items
from scripts.installer.ui.shared.labels import installation_item_display_label
from scripts.installer.ui.gui.widgets.config_item_widget import create_config_item_widget
from scripts.installer.ui.gui.components.scrollable_frame import ScrollableFrame
from scripts.installer.configs.constants.configuration_item_keys import KEY_CONFIG_ITEM_RUNTIME_BIN
from scripts.installer.configs.constants.installation_item_keys import (
    KEY_INSTALLATION_ITEM_AUTO_TWEAKS,
)
from scripts.malcolm_constants import PLATFORM_LINUX
import platform as platform_module

if TYPE_CHECKING:
    from scripts.installer.core.malcolm_config import MalcolmConfig
    from scripts.installer.core.install_context import InstallContext


def show_installation_dialog(
    parent: customtkinter.CTk,
    malcolm_config: "MalcolmConfig",
    install_context: "InstallContext",
) -> Optional["InstallContext"]:
    """Show installation options dialog.

    Args:
        parent: Parent CTk window
        malcolm_config: MalcolmConfig instance (for runtime_bin context)
        install_context: InstallContext instance with installation items

    Returns:
        Modified InstallContext if user clicked Continue, None if cancelled
    """
    dialog = InstallationDialog(parent, malcolm_config, install_context)
    result = dialog.run()
    return result


INDENT_PER_DEPTH = 20


def build_install_options_content(
    parent,
    malcolm_config: "MalcolmConfig",
    install_context: "InstallContext",
) -> Dict[str, Any]:
    """Populate `parent` with the installation-options UI used by the dialog."""
    widget_map: Dict[str, Any] = {}
    _build_installation_items_into(parent, malcolm_config, install_context, widget_map)
    _build_extended_options_into(parent, install_context)
    return widget_map


def _build_installation_items_into(parent, malcolm_config, install_context, widget_map):
    rows = [r for r in build_rows_from_items(install_context.items.items(), install_context) if r.visible]
    if not rows:
        customtkinter.CTkLabel(
            parent,
            text="No installation options available for your platform.",
            font=("Helvetica", 11),
            text_color="gray",
        ).pack(pady=20)
        return

    runtime_bin = malcolm_config.get_value(KEY_CONFIG_ITEM_RUNTIME_BIN) or ""

    for row in rows:
        item = install_context.get_item(row.key)
        if not item:
            continue

        display_label = installation_item_display_label(row.key, item.label or row.key, runtime_bin.lower())
        widget = create_config_item_widget(
            parent,
            row.key,
            item,
            install_context,
            label_override=display_label,
        )
        if not widget:
            continue
        widget_map[row.key] = widget
        left_pad = 15 + row.depth * INDENT_PER_DEPTH
        widget.pack(fill="x", padx=(left_pad, 15), pady=3)


def _build_extended_options_into(parent, install_context):
    extended_frame = customtkinter.CTkFrame(parent, corner_radius=8)
    extended_frame.pack(fill="x", pady=(10, 0))

    customtkinter.CTkLabel(
        extended_frame,
        text="Additional Options",
        font=("Helvetica", 12, "bold"),
    ).pack(anchor="w", padx=15, pady=(10, 5))

    config_only_var = customtkinter.BooleanVar(value=install_context.config_only)
    customtkinter.CTkCheckBox(
        extended_frame,
        text="Configuration Only (skip installation, just save configuration)",
        variable=config_only_var,
        command=lambda: setattr(install_context, 'config_only', config_only_var.get()),
    ).pack(anchor="w", padx=15, pady=(5, 10))


class InstallationDialog:
    """Modal dialog for installation options configuration."""

    def __init__(
        self,
        parent: customtkinter.CTk,
        malcolm_config: "MalcolmConfig",
        install_context: "InstallContext",
    ):
        """Initialize the installation options dialog.

        Args:
            parent: Parent CTk window
            malcolm_config: MalcolmConfig instance
            install_context: InstallContext instance
        """
        self.parent = parent
        self.malcolm_config = malcolm_config
        self.install_context = install_context
        self.result = None
        self.widget_map = {}  # key -> widget mapping

    def run(self) -> Optional["InstallContext"]:
        """Run the installation options dialog.

        Returns:
            Modified InstallContext if user clicked Continue, None if cancelled
        """
        # Create modal dialog
        self.dialog = customtkinter.CTkToplevel(self.parent)
        self.dialog.title("Installation Options")
        self.dialog.geometry("800x600")
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
        """Build the dialog UI with installation options."""
        # Main content frame
        content_frame = customtkinter.CTkFrame(self.dialog, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Title
        title_label = customtkinter.CTkLabel(
            content_frame,
            text="Installation Options",
            font=("Helvetica", 16, "bold"),
        )
        title_label.pack(pady=(0, 5))

        # Subtitle
        subtitle_label = customtkinter.CTkLabel(
            content_frame,
            text="Configure platform-specific installation and system tweak options",
            font=("Helvetica", 11),
            text_color="gray",
        )
        subtitle_label.pack(pady=(0, 15))

        # Scrollable frame for installation items
        scroll_frame = ScrollableFrame(content_frame)
        scroll_frame.pack(fill="both", expand=True, pady=(0, 15))

        # Build installation items UI
        self._build_installation_items(scroll_frame.scrollable_frame)

        # Extended options section (config_only, auto_tweaks)
        self._build_extended_options(content_frame)

        # Buttons
        self._create_button_bar(content_frame)

    def _build_installation_items(self, parent):
        """Build installation items section using build_rows_from_items.

        Args:
            parent: Parent frame for installation items
        """
        # Get rows from InstallContext items
        rows = build_rows_from_items(self.install_context.items.items(), self.install_context)

        if not rows:
            no_items_label = customtkinter.CTkLabel(
                parent,
                text="No installation options available for your platform.",
                font=("Helvetica", 11),
                text_color="gray",
            )
            no_items_label.pack(pady=20)
            return

        # Get runtime_bin for label formatting
        runtime_bin = self.malcolm_config.get_value(KEY_CONFIG_ITEM_RUNTIME_BIN) or ""

        # Group rows by depth and parent to create sections
        current_depth = 0
        current_parent = None
        section_frame = None

        for row in rows:
            if not row.visible:
                continue

            # Skip the auto_tweaks item - we'll show it separately
            if row.key == KEY_INSTALLATION_ITEM_AUTO_TWEAKS:
                continue

            # Create section for depth > 0 (nested items)
            if row.depth > current_depth or row.ui_parent != current_parent:
                if row.depth > 0 and row.ui_parent:
                    # Create bordered section for nested items
                    parent_item = self.install_context.get_item(row.ui_parent)
                    section_label = parent_item.label if parent_item else row.ui_parent

                    section_container = customtkinter.CTkFrame(parent, fg_color="transparent")
                    section_container.pack(fill="x", padx=10, pady=(10, 0))

                    section_title = customtkinter.CTkLabel(
                        section_container,
                        text=section_label,
                        font=("Helvetica", 12, "bold"),
                    )
                    section_title.pack(anchor="w", pady=(0, 5))

                    section_frame = customtkinter.CTkFrame(section_container, corner_radius=8)
                    section_frame.pack(fill="x", padx=10)
                else:
                    # Top-level items (depth == 0) - no border
                    section_frame = parent

                current_depth = row.depth
                current_parent = row.ui_parent

            # Create widget for this item
            item = self.install_context.get_item(row.key)
            if not item:
                continue

            # Use installation_item_display_label for runtime-specific labels
            display_label = installation_item_display_label(row.key, item.label or row.key, runtime_bin.lower())

            widget = create_config_item_widget(
                section_frame,
                row.key,
                item,
                self.install_context,
                label_override=display_label,
            )

            if widget:
                self.widget_map[row.key] = widget
                widget.pack(fill="x", padx=15, pady=5)

                # Setup visibility observer
                def make_visibility_callback(key, w):
                    def callback(value):
                        if self.install_context.is_item_visible(key):
                            w.pack(fill="x", padx=15, pady=5)
                        else:
                            w.pack_forget()
                    return callback

                # Note: InstallContext doesn't have observe() like MalcolmConfig
                # Visibility is static based on platform detection, so no dynamic updates needed

    def _build_extended_options(self, parent):
        """Build extended options section (config_only, auto_tweaks).

        Args:
            parent: Parent frame
        """
        extended_frame = customtkinter.CTkFrame(parent, corner_radius=8)
        extended_frame.pack(fill="x", pady=(10, 0))

        # Section title
        title_label = customtkinter.CTkLabel(
            extended_frame,
            text="Additional Options",
            font=("Helvetica", 12, "bold"),
        )
        title_label.pack(anchor="w", padx=15, pady=(10, 5))

        # config_only checkbox
        self.config_only_var = customtkinter.BooleanVar(value=self.install_context.config_only)

        config_only_cb = customtkinter.CTkCheckBox(
            extended_frame,
            text="Configuration Only (skip installation, just save configuration)",
            variable=self.config_only_var,
            command=lambda: setattr(self.install_context, 'config_only', self.config_only_var.get()),
        )
        config_only_cb.pack(anchor="w", padx=15, pady=5)

        # auto_tweaks checkbox (Linux only)
        if platform_module.system().lower() == PLATFORM_LINUX.lower():
            auto_tweaks_item = self.install_context.get_item(KEY_INSTALLATION_ITEM_AUTO_TWEAKS)
            if auto_tweaks_item:
                self.auto_tweaks_var = customtkinter.BooleanVar(value=auto_tweaks_item.get_value())

                auto_tweaks_cb = customtkinter.CTkCheckBox(
                    extended_frame,
                    text="Auto-apply system tweaks (Linux system optimizations)",
                    variable=self.auto_tweaks_var,
                    command=lambda: self.install_context.set_item_value(
                        KEY_INSTALLATION_ITEM_AUTO_TWEAKS,
                        self.auto_tweaks_var.get()
                    ),
                )
                auto_tweaks_cb.pack(anchor="w", padx=15, pady=(5, 10))

    def _create_button_bar(self, parent):
        """Create bottom button bar with Continue and Cancel buttons.

        Args:
            parent: Parent frame
        """
        button_frame = customtkinter.CTkFrame(parent, fg_color="transparent")
        button_frame.pack(fill="x", pady=(10, 0))

        def on_continue():
            """Handle Continue button click."""
            self.result = self.install_context
            self.dialog.destroy()

        def on_cancel():
            """Handle Cancel button click."""
            self.result = None
            self.dialog.destroy()

        continue_button = customtkinter.CTkButton(
            button_frame,
            text="Continue",
            command=on_continue,
            width=120,
        )
        continue_button.pack(side="left", padx=5)

        cancel_button = customtkinter.CTkButton(
            button_frame,
            text="Cancel",
            command=on_cancel,
            width=120,
            fg_color="gray",
        )
        cancel_button.pack(side="right", padx=5)
