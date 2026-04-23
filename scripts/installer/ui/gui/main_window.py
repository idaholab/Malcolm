#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2025 Battelle Energy Alliance, LLC.  All rights reserved.

"""Main window for the Malcolm GUI installer with tab-based interface."""

from typing import TYPE_CHECKING, Optional
import customtkinter

from scripts.malcolm_constants import PROFILE_MALCOLM, PROFILE_HEDGEHOG
from scripts.installer.utils.logger_utils import InstallerLogger
from scripts.installer.ui.gui.components.styles import (
    DEFAULT_BORDER_COLOR,
    DEFAULT_BORDER_WIDTH,
    ERROR_BORDER_COLOR,
    ERROR_BORDER_WIDTH,
    ERROR_TEXT_COLOR,
    INFO_PANEL_BG,
    PANEL_CORNER_RADIUS,
)
from scripts.installer.ui.gui.tabs.base_tab import BaseTab
from scripts.installer.ui.gui.components.search_panel import SearchPanel
from scripts.installer.configs.constants.configuration_item_keys import KEY_CONFIG_ITEM_MALCOLM_PROFILE

if TYPE_CHECKING:
    from scripts.installer.core.malcolm_config import MalcolmConfig
    from scripts.installer.core.install_context import InstallContext


# Profile-specific accent colors
ACCENT_COLORS = {
    PROFILE_MALCOLM: {
        "primary": "#EEDD77",      # Gold
        "hover": "#D4C45A",        # Darker gold for hover
        "text": "#1a1a1a",         # Dark text for contrast
    },
    PROFILE_HEDGEHOG: {
        "primary": "#C6B9DB",      # Light purple
        "hover": "#A99BC4",        # Darker purple for hover
        "text": "#1a1a1a",         # Dark text for contrast
    },
}


class MainWindow:
    """Main tabbed window for Malcolm configuration."""

    def __init__(
        self,
        malcolm_config: "MalcolmConfig",
        install_context: "InstallContext",
        main_menu_keys: list[str],
        debug_mode: bool = False,
        root: Optional[customtkinter.CTk] = None,
        selected_profile: Optional[str] = None,
        header_image: Optional[customtkinter.CTkImage] = None,
        build_only: bool = False,
    ):
        """Initialize the main window with tabs.

        Args:
            malcolm_config: MalcolmConfig instance containing all configuration
            install_context: InstallContext instance for installation decisions
            main_menu_keys: List of main menu configuration keys to display as tabs
            debug_mode: Whether to enable debug menu options
            root: Optional existing CTk root window
            selected_profile: Profile selected in splash screen (malcolm or hedgehog)
            header_image: CTkImage for header display from splash screen
            build_only: If True, build UI widgets but don't display them yet.
                        Call display() later to make them visible.
        """
        self.malcolm_config = malcolm_config
        self.install_context = install_context
        self.main_menu_keys = main_menu_keys
        self.debug_mode = debug_mode
        self.result = False
        self.tabs = {}  # menu_key -> BaseTab
        self.tab_labels = {}  # menu_key -> tab_label (for switching tabs)
        self.key_to_tab = {}  # config_key -> menu_key (for finding which tab has a field)

        self.selected_profile = selected_profile or PROFILE_MALCOLM
        self.accent_colors = ACCENT_COLORS.get(self.selected_profile, ACCENT_COLORS[PROFILE_MALCOLM])
        self.header_image = header_image
        self._build_only = build_only
        self._main_frame: Optional[customtkinter.CTkFrame] = None
        self._logo_label: Optional[customtkinter.CTkLabel] = None
        self._button_bar: Optional[customtkinter.CTkFrame] = None
        self._search_panel: Optional[SearchPanel] = None

        self.root = root or customtkinter.CTk()
        profile_display = "Malcolm" if self.selected_profile == PROFILE_MALCOLM else "Hedgehog"
        self.root.title(f"{profile_display} Installer Configuration")
        self.root.geometry("900x700")
        # Minimum size keeps header + tab content + search panel (260) + bottom bar
        # visible even when the user drags the window edges inward.
        self.root.minsize(720, 600)

        self._build_ui()

    def _build_ui(self):
        """Build the main UI with header, tabs, and button bar."""
        self._main_frame = customtkinter.CTkFrame(self.root)
        if not self._build_only:
            self._main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Header bar with profile image and info
        self._create_header(self._main_frame)

        self.tab_view = customtkinter.CTkTabview(
            self._main_frame,
            segmented_button_selected_color=self.accent_colors["primary"],
            segmented_button_selected_hover_color=self.accent_colors["hover"],
            text_color=self.accent_colors["text"],
        )
        self.tab_view.pack(fill="both", expand=True, padx=10, pady=10)

        self._create_tabs()
        self._create_button_bar(self._main_frame)
        self._create_search_panel(self._main_frame)
        self.root.bind_all("<Control-f>", lambda _e: self._focus_search_entry())

    def display(self) -> None:
        """Make the pre-built window visible.

        Call this after building with build_only=True to show the UI.
        """
        if self._build_only and self._main_frame:
            self._main_frame.pack(fill="both", expand=True, padx=10, pady=10)
            self._build_only = False

    def set_header_image(self, header_image: customtkinter.CTkImage) -> None:
        """Set or update the header image after construction.

        Args:
            header_image: CTkImage to display in the header
        """
        self.header_image = header_image
        if self._logo_label:
            self._logo_label.configure(image=header_image)

    def _create_header(self, parent):
        """Create header bar with profile image and appearance toggle.

        Args:
            parent: The parent frame to attach the header to
        """
        header_frame = customtkinter.CTkFrame(parent, height=80, fg_color="transparent")
        header_frame.pack(fill="x", padx=10, pady=(5, 0))
        header_frame.pack_propagate(False)

        # Profile image on left (always pack to reserve position, even if no image yet)
        self._logo_label = customtkinter.CTkLabel(
            header_frame,
            image=self.header_image if self.header_image else None,
            text="",
        )
        self._logo_label.pack(side="left", padx=(10, 15))

        # Profile name and subtitle
        text_frame = customtkinter.CTkFrame(header_frame, fg_color="transparent")
        text_frame.pack(side="left", fill="y", padx=5)

        profile_display = "Malcolm" if self.selected_profile == PROFILE_MALCOLM else "Hedgehog"
        title_label = customtkinter.CTkLabel(
            text_frame,
            text=f"{profile_display} Configuration",
            font=("Helvetica", 18, "bold"),
            anchor="w",
        )
        title_label.pack(anchor="w", pady=(15, 0))

        subtitle_label = customtkinter.CTkLabel(
            text_frame,
            text="Network Traffic Analysis Tool Suite",
            font=("Helvetica", 12),
            text_color="gray",
            anchor="w",
        )
        subtitle_label.pack(anchor="w")

        # Appearance toggle on right
        appearance_frame = customtkinter.CTkFrame(header_frame, fg_color="transparent")
        appearance_frame.pack(side="right", padx=10)

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
            fg_color=self.accent_colors["primary"],
            progress_color=self.accent_colors["hover"],
            button_hover_color=self.accent_colors["hover"],
        )
        appearance_switch.pack(side="left")
        appearance_switch.select() if self._is_dark_mode() else appearance_switch.deselect()

    def _is_dark_mode(self) -> bool:
        """Return True if the current appearance mode is dark."""
        try:
            mode = customtkinter.get_appearance_mode()
            return mode.lower() == "dark" if mode else False
        except AttributeError:
            return False
        except Exception as e:
            InstallerLogger.debug(f"Could not determine appearance mode: {e}")
            return False

    def _toggle_appearance_mode(self):
        """Toggle between light and dark appearance modes."""
        target = "light" if self._is_dark_mode() else "dark"
        customtkinter.set_appearance_mode(target)

    def _create_tabs(self):
        """Create tabs for all MenuItems in main_menu_keys.

        Skips the profile selection tab (profile already chosen in splash screen)
        and skips tabs that are not visible for the selected profile.
        """
        # Add configuration tabs (no Welcome tab - replaced by header)
        for menu_key in self.main_menu_keys:
            # Skip the profile selection tab - profile was already selected in splash
            if menu_key == KEY_CONFIG_ITEM_MALCOLM_PROFILE:
                continue

            # Skip menu items that are not visible for this profile
            if not self.malcolm_config.is_menu_item_visible(menu_key):
                continue

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

            base_tab = BaseTab(tab_frame, self.malcolm_config, menu_key, accent_colors=self.accent_colors)
            self.tabs[menu_key] = base_tab
            self.tab_labels[menu_key] = tab_label

            # Build reverse mapping: config_key -> menu_key for jump-to-field
            for config_key in base_tab.rendered_items:
                self.key_to_tab[config_key] = menu_key

    def _create_button_bar(self, parent):
        """Create bottom bar: [Exit] [-- Search Entry --] [Save & Continue].

        Args:
            parent: The parent frame to attach the button bar to
        """
        button_frame = customtkinter.CTkFrame(parent, fg_color="transparent")
        # side=bottom anchors the bar to the window edge so any later bottom-packed
        # sibling (the SearchPanel) stacks ABOVE it instead of pushing it offscreen.
        button_frame.pack(side="bottom", fill="x", padx=10, pady=10)
        self._button_bar = button_frame

        exit_button = customtkinter.CTkButton(
            button_frame,
            text="Exit",
            command=self._on_exit,
            width=100,
            fg_color=self.accent_colors["primary"],
            hover_color=self.accent_colors["hover"],
            text_color=self.accent_colors["text"],
        )
        exit_button.pack(side="left", padx=(0, 10))

        save_button = customtkinter.CTkButton(
            button_frame,
            text="Save & Continue",
            command=self._on_save,
            width=150,
            fg_color=self.accent_colors["primary"],
            hover_color=self.accent_colors["hover"],
            text_color=self.accent_colors["text"],
        )
        save_button.pack(side="right", padx=(10, 0))

        self._search_entry = customtkinter.CTkEntry(
            button_frame,
            placeholder_text="Search settings and sections (Ctrl+F)",
        )
        self._search_entry.pack(side="left", fill="x", expand=True, padx=5)
        self._search_entry.bind("<KeyRelease>", self._on_search_type)
        self._search_entry.bind("<Down>", self._on_search_down)
        self._search_entry.bind("<Up>", self._on_search_up)
        self._search_entry.bind("<Return>", self._on_search_enter)
        self._search_entry.bind("<Escape>", self._on_search_escape)
        self._search_entry.bind("<FocusIn>", self._on_search_focus_in)

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
        self._shutdown()

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
                fg_color=INFO_PANEL_BG,
                corner_radius=PANEL_CORNER_RADIUS,
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
                text_color=ERROR_TEXT_COLOR,
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
                fg_color=self.accent_colors["primary"],
                hover_color=self.accent_colors["hover"],
                text_color=self.accent_colors["text"],
            )
            go_button.pack(side="right", padx=10, pady=8)

        # Close button
        close_button = customtkinter.CTkButton(
            dialog,
            text="Close",
            command=dialog.destroy,
            width=120,
            fg_color=self.accent_colors["primary"],
            hover_color=self.accent_colors["hover"],
            text_color=self.accent_colors["text"],
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
            widget.configure(border_color=ERROR_BORDER_COLOR, border_width=ERROR_BORDER_WIDTH)
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
            widget.configure(border_color=DEFAULT_BORDER_COLOR, border_width=DEFAULT_BORDER_WIDTH)
        except (AttributeError, ValueError):
            pass  # Widget doesn't support border configuration

        # Also try children (for container widgets)
        try:
            for child in widget.winfo_children():
                self._clear_error_style_recursive(child)
        except (AttributeError, Exception):
            pass

    def _create_search_panel(self, parent):
        """Create the bottom-docked search panel (initially hidden).

        Args:
            parent: The parent frame to attach the search panel to
        """
        self._search_panel = SearchPanel(
            parent,
            malcolm_config=self.malcolm_config,
            on_jump=self._jump_to_item,
            accent_colors=self.accent_colors,
        )

    def _focus_search_entry(self):
        """Focus the search entry; select existing text for easy replacement."""
        if not hasattr(self, "_search_entry"):
            return
        self._search_entry.focus_set()
        if self._search_entry.get():
            self._search_entry.select_range(0, "end")
            # Show results for existing term (if any) without forcing re-query
            self._search_panel.set_term(self._search_entry.get())

    def _on_search_type(self, event=None):
        if event is not None and event.keysym in ("Down", "Up", "Return", "Escape"):
            return
        if self._search_panel is not None:
            self._search_panel.set_term(self._search_entry.get())

    def _on_search_down(self, _event=None):
        if self._search_panel is not None:
            self._search_panel.move_selection(1)
        return "break"

    def _on_search_up(self, _event=None):
        if self._search_panel is not None:
            self._search_panel.move_selection(-1)
        return "break"

    def _on_search_enter(self, _event=None):
        if self._search_panel is not None and self._search_panel.has_results():
            self._search_panel.activate_selection()
        return "break"

    def _on_search_escape(self, _event=None):
        if self._search_panel is not None:
            self._search_panel.hide()
        # Return focus to the main frame so arrow keys don't keep targeting the entry
        if self._main_frame is not None:
            self._main_frame.focus_set()
        return "break"

    def _on_search_focus_in(self, _event=None):
        if self._search_panel is not None and self._search_entry.get().strip():
            self._search_panel.set_term(self._search_entry.get())

    def _jump_to_item(self, key: str) -> None:
        """Switch to the tab containing the given key, scroll it into view, and pulse it.

        Accepts both ConfigItem keys and MenuItem keys. For MenuItem keys, the tab
        itself (or the tab containing the submenu) is selected; for ConfigItem keys,
        the owning tab is selected and the target widget is scrolled and pulsed.
        """
        menu_item = self.malcolm_config.get_menu_item(key)
        if menu_item is not None:
            tab_key = self._resolve_tab_for_menu_item(key)
            if tab_key is None:
                InstallerLogger.debug(f"Search jump: no tab found for menu key '{key}'")
                return
            self._switch_to_tab(tab_key)
            return

        tab_key = self.key_to_tab.get(key)
        if tab_key is None:
            InstallerLogger.debug(f"Search jump: no tab found for config key '{key}'")
            return
        self._switch_to_tab(tab_key)
        base_tab = self.tabs.get(tab_key)
        if base_tab is not None:
            base_tab.scroll_to_item(key)
            base_tab.pulse_item(key)

    def _resolve_tab_for_menu_item(self, menu_key: str) -> Optional[str]:
        """Walk up the MenuItem hierarchy until we find a key that owns a tab."""
        current_key = menu_key
        visited: set = set()
        while current_key and current_key not in visited:
            visited.add(current_key)
            if current_key in self.tab_labels:
                return current_key
            parent_menu = self.malcolm_config.get_menu_item(current_key)
            if parent_menu is None:
                return None
            current_key = parent_menu.ui_parent
        return None

    def _switch_to_tab(self, menu_key: str) -> None:
        tab_label = self.tab_labels.get(menu_key)
        if tab_label:
            self.tab_view.set(tab_label)

    def _on_exit(self):
        """Handle Exit button click."""
        from scripts.installer.ui.gui.components.dialog import show_confirmation_dialog

        if show_confirmation_dialog(
            self.root,
            "Are you sure you want to exit? Any unsaved changes will be lost.",
            title="Confirm Exit",
            ok_text="Yes",
            cancel_text="No",
            accent_colors=self.accent_colors,
        ):
            self.result = False
            self._shutdown()

    def _shutdown(self) -> None:
        """Tear down the window safely for teardown -> next phase transitions.

        Clicking a CTkButton schedules an ~100ms .after() click-animation callback
        against the clicked widget. If we destroy the root synchronously inside
        the command handler, that callback fires against dead widget IDs and
        leaks into the next Tcl interpreter (see install.py's gather_install_options
        creating a fresh CTk root). The cascade surfaces as bgerror and can hang
        the whole process. To avoid it: hide immediately, then after the animation
        window has elapsed, cancel any other pending .after() callbacks and destroy.
        """
        try:
            self.root.withdraw()
        except Exception:
            pass
        self.root.after(150, self._finalize_shutdown)

    def _finalize_shutdown(self) -> None:
        try:
            pending = self.root.tk.call("after", "info") or ()
            for after_id in pending:
                try:
                    self.root.after_cancel(after_id)
                except Exception:
                    pass
        except Exception:
            pass
        try:
            self.root.destroy()
        except Exception:
            pass

    def run(self) -> bool:
        """Run the main window event loop.

        Returns:
            True if user saved and continued, False if user exited
        """
        self.root.mainloop()
        return self.result
