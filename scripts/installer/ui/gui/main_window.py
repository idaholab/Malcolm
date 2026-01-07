#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2025 Battelle Energy Alliance, LLC.  All rights reserved.

"""Main window for the Malcolm GUI installer with tab-based interface."""

from typing import TYPE_CHECKING, Optional
import customtkinter

from scripts.installer.utils.logger_utils import InstallerLogger
from scripts.installer.ui.gui.tabs.base_tab import BaseTab
from scripts.installer.ui.gui.tabs.welcome_tab import WelcomeTab

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
        self.tabs = {}  # menu_key -> BaseTab
        self.tab_labels = {}  # menu_key -> tab_label (for switching tabs)
        self.key_to_tab = {}  # config_key -> menu_key (for finding which tab has a field)

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
        # Add Welcome tab as the first tab
        welcome_frame = self.tab_view.add("Welcome")
        WelcomeTab(welcome_frame)

        # Add configuration tabs
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

            base_tab = BaseTab(tab_frame, self.malcolm_config, menu_key)
            self.tabs[menu_key] = base_tab
            self.tab_labels[menu_key] = tab_label

            # Build reverse mapping: config_key -> menu_key for jump-to-field
            for config_key in base_tab.rendered_items:
                self.key_to_tab[config_key] = menu_key

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
        """Handle Save & Continue button click with validation blocking.

        Validates the entire form before allowing the user to proceed.
        If validation fails, shows a dialog with all issues and highlights invalid fields.
        If validation passes, closes the window and returns True. The summary dialog
        is shown by install.py via show_final_configuration_summary().
        """
        from scripts.installer.core.validation import validate_required

        # Clear any previous error highlighting before re-validating
        self._clear_error_highlighting()

        # Run form-level validation
        issues = validate_required(self.malcolm_config)

        if issues:
            # Validation failed - show issues dialog and highlight fields
            self._highlight_invalid_fields(issues)
            self._show_validation_issues_dialog(issues)
            return  # BLOCK - don't save

        # Validation passed - close window and return True
        # Summary dialog is shown by install.py via show_final_configuration_summary()
        self.result = True
        self.root.destroy()

    def _show_validation_issues_dialog(self, issues):
        """Show all validation issues in scrollable dialog with jump-to-field buttons.

        Args:
            issues: List of ValidationIssue objects
        """
        dialog = customtkinter.CTkToplevel(self.root)
        dialog.title("Configuration Issues")
        dialog.geometry("650x450")
        dialog.transient(self.root)
        dialog.grab_set()

        # Center on parent
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")

        # Header
        header = customtkinter.CTkLabel(
            dialog,
            text="Please fix the following issues before continuing:",
            font=("", 14, "bold"),
        )
        header.pack(pady=(15, 10), padx=20)

        # Scrollable issue list
        scroll_frame = customtkinter.CTkScrollableFrame(dialog, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=15, pady=10)

        for idx, issue in enumerate(issues):
            # Each issue is a row with details and "Go to field" button
            row = customtkinter.CTkFrame(
                scroll_frame,
                fg_color=("gray90", "gray20"),
                corner_radius=6,
            )
            row.pack(fill="x", pady=4, padx=5)

            # Left side: issue details
            details_frame = customtkinter.CTkFrame(row, fg_color="transparent")
            details_frame.pack(side="left", fill="both", expand=True, padx=10, pady=8)

            # Issue label (bold)
            label = customtkinter.CTkLabel(
                details_frame,
                text=f"{idx + 1}. {issue.label}",
                font=("", 12, "bold"),
                anchor="w",
            )
            label.pack(anchor="w")

            # Issue message (red)
            message = customtkinter.CTkLabel(
                details_frame,
                text=issue.message,
                text_color=("red", "#ff6b6b"),
                anchor="w",
            )
            message.pack(anchor="w", padx=(15, 0))

            # Right side: "Go to field" button
            def make_jump_callback(key):
                return lambda: self._jump_to_field(dialog, key)

            go_button = customtkinter.CTkButton(
                row,
                text="Go to field",
                command=make_jump_callback(issue.key),
                width=100,
                height=28,
            )
            go_button.pack(side="right", padx=10, pady=8)

        # Close button
        close_button = customtkinter.CTkButton(
            dialog,
            text="Close",
            command=dialog.destroy,
            width=120,
        )
        close_button.pack(pady=15)

    def _jump_to_field(self, dialog, key: str):
        """Jump to the tab containing the field, scroll it into view, and focus it.

        Args:
            dialog: The validation issues dialog to close
            key: The configuration item key to jump to
        """
        # Close the dialog
        dialog.destroy()

        # Find which tab contains this key
        menu_key = self.key_to_tab.get(key)
        if not menu_key:
            InstallerLogger.warning(f"Could not find tab for key: {key}")
            return

        tab_label = self.tab_labels.get(menu_key)
        if not tab_label:
            InstallerLogger.warning(f"Could not find tab label for menu_key: {menu_key}")
            return

        # Switch to that tab
        self.tab_view.set(tab_label)

        # Find the widget container
        tab = self.tabs.get(menu_key)
        if not tab:
            return

        container = tab.widgets.get(key)
        if not container:
            return

        # Scroll the widget into view
        self._scroll_widget_into_view(container)

        # Focus the actual input widget (not the container)
        input_widget = getattr(container, '_input_widget', None)
        if input_widget:
            try:
                input_widget.focus_set()
            except Exception:
                pass  # Some widgets don't support focus
        else:
            # Fallback: try focusing the container
            try:
                container.focus_set()
            except Exception:
                pass

    def _scroll_widget_into_view(self, widget):
        """Scroll a widget into view within its scrollable parent.

        Args:
            widget: The widget to scroll into view
        """
        # Find the CTkScrollableFrame parent
        parent = widget.master
        while parent:
            if hasattr(parent, '_parent_canvas'):
                # Found the scrollable frame
                canvas = parent._parent_canvas
                try:
                    # Update to ensure geometry is calculated
                    widget.update_idletasks()
                    canvas.update_idletasks()

                    # Get widget position relative to canvas
                    widget_y = widget.winfo_y()
                    widget_height = widget.winfo_height()
                    canvas_height = canvas.winfo_height()

                    # Get current scroll position
                    scroll_top = canvas.canvasy(0)
                    scroll_bottom = scroll_top + canvas_height

                    # Check if widget is outside visible area
                    if widget_y < scroll_top:
                        # Widget is above visible area - scroll up
                        canvas.yview_moveto(widget_y / canvas.bbox("all")[3])
                    elif widget_y + widget_height > scroll_bottom:
                        # Widget is below visible area - scroll down
                        target_top = widget_y + widget_height - canvas_height
                        canvas.yview_moveto(target_top / canvas.bbox("all")[3])
                except Exception:
                    pass  # Scrolling failed, widget may still be partially visible
                break
            parent = getattr(parent, 'master', None)

    def _highlight_invalid_fields(self, issues):
        """Add red borders to all invalid fields.

        Args:
            issues: List of ValidationIssue objects
        """
        for issue in issues:
            # Find the widget for this key
            menu_key = self.key_to_tab.get(issue.key)
            if not menu_key:
                continue

            tab = self.tabs.get(menu_key)
            if not tab:
                continue

            widget = tab.widgets.get(issue.key)
            if widget:
                self._apply_error_style_recursive(widget)

    def _apply_error_style_recursive(self, widget):
        """Apply red border styling to widget and its children that support it.

        Args:
            widget: The widget to style
        """
        # Try to apply red border to this widget
        try:
            widget.configure(border_color="red", border_width=2)
        except (AttributeError, ValueError):
            pass  # Widget doesn't support border configuration

        # Also try children (for container widgets)
        try:
            for child in widget.winfo_children():
                self._apply_error_style_recursive(child)
        except (AttributeError, Exception):
            pass

    def _clear_error_highlighting(self):
        """Clear red border styling from all widgets across all tabs.

        Called before re-validation to reset visual state.
        """
        for tab in self.tabs.values():
            for widget in tab.widgets.values():
                self._clear_error_style_recursive(widget)

    def _clear_error_style_recursive(self, widget):
        """Clear error styling from widget and its children.

        Args:
            widget: The widget to clear styling from
        """
        # Try to reset border to default
        try:
            widget.configure(border_color=("gray60", "gray40"), border_width=1)
        except (AttributeError, ValueError):
            pass  # Widget doesn't support border configuration

        # Also try children (for container widgets)
        try:
            for child in widget.winfo_children():
                self._clear_error_style_recursive(child)
        except (AttributeError, Exception):
            pass

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
