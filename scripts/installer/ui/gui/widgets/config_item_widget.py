#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2025 Battelle Energy Alliance, LLC.  All rights reserved.

from typing import TYPE_CHECKING, Optional
import tkinter as tk
import customtkinter

from scripts.malcolm_constants import WidgetType
from scripts.installer.utils.logger_utils import InstallerLogger
from scripts.installer.ui.gui.components.validation_state import (
    show_validation_error,
    clear_validation_error,
)
from scripts.installer.ui.gui.components.tooltip import add_tooltip, remove_tooltip

if TYPE_CHECKING:
    from scripts.installer.core.malcolm_config import MalcolmConfig
    from scripts.installer.core.config_item import ConfigItem


def _handle_set_value(widget, error_label, key, value, malcolm_config):
    """Handle setting a configuration value with inline error display.

    Args:
        widget: Input widget to mark with error state
        error_label: Label widget to display error message
        key: Configuration item key
        value: New value to set
        malcolm_config: MalcolmConfig instance

    Returns:
        True if value was set successfully, False otherwise
    """
    import traceback

    try:
        malcolm_config.set_value(key, value)
        clear_validation_error(widget, error_label)
        return True
    except (ValueError, TypeError) as e:
        # Expected validation errors - show inline error
        show_validation_error(widget, error_label, str(e))
        return False
    except Exception as e:
        # Unexpected error - log with traceback for debugging
        InstallerLogger.error(f"Unexpected error setting {key} to {value}: {e}")
        InstallerLogger.error(traceback.format_exc())
        show_validation_error(widget, error_label, f"Error: {e}")
        return False


def _setup_visibility_observer(widget, key, malcolm_config):
    """Set up observer to handle widget visibility changes with tooltips.

    Args:
        widget: The input widget to enable/disable
        key: Configuration item key
        malcolm_config: MalcolmConfig instance
    """

    def on_visibility_change(_):
        """Update widget state and tooltip based on visibility."""
        visible = malcolm_config.is_item_visible(key)

        if visible:
            # Enable widget and remove tooltip
            if hasattr(widget, "configure"):
                try:
                    widget.configure(state="normal")
                except ValueError:
                    pass  # Widget doesn't support state
            remove_tooltip(widget)
        else:
            # Disable widget and add tooltip explaining why
            if hasattr(widget, "configure"):
                try:
                    widget.configure(state="disabled")
                except ValueError:
                    pass  # Widget doesn't support state

            # Get dependency info to explain why disabled
            dep_info = malcolm_config.get_dependency_info(key)
            if dep_info.get("has_visibility_rule"):
                depends_on = dep_info.get("visibility_depends_on")
                if isinstance(depends_on, list):
                    depends_str = ", ".join(depends_on)
                else:
                    depends_str = str(depends_on)

                tooltip_text = f"Disabled: depends on {depends_str}"
                add_tooltip(widget, tooltip_text)

    # Only register observer if config object supports it (MalcolmConfig has observe, InstallContext doesn't)
    if hasattr(malcolm_config, 'observe'):
        malcolm_config.observe(key, on_visibility_change)
        # Trigger initial evaluation
        on_visibility_change(None)


def create_config_item_widget(
    parent: customtkinter.CTkFrame,
    key: str,
    item: "ConfigItem",
    malcolm_config: "MalcolmConfig",
    label_override: Optional[str] = None,
) -> Optional[customtkinter.CTkFrame]:
    """Factory function to create appropriate widget for a ConfigItem.

    Creates a container frame with label and input widget, with reactive
    two-way binding to MalcolmConfig.

    Args:
        parent: Parent CTk widget
        key: ConfigItem key
        item: ConfigItem instance
        malcolm_config: MalcolmConfig instance (or InstallContext for installation items)
        label_override: Optional label to use instead of item.label

    Returns:
        Container frame with label and widget, or None if widget type unsupported
    """
    if not item.widget_type:
        return None

    container = customtkinter.CTkFrame(parent, fg_color="transparent")
    container.grid_columnconfigure(0, weight=0)
    container.grid_columnconfigure(1, weight=1)

    label_text = label_override if label_override else item.label
    label = customtkinter.CTkLabel(
        container,
        text=label_text,
        anchor="w",
        width=240
    )
    label.grid(row=0, column=0, sticky="w", padx=(0, 12), pady=2)

    widget_frame = customtkinter.CTkFrame(container, fg_color="transparent")
    widget_frame.grid(row=0, column=1, sticky="ew", pady=2)

    if item.widget_type == WidgetType.TEXT:
        helper_text = item.question
        if helper_text:
            helper_label = customtkinter.CTkLabel(
                container,
                text=helper_text,
                anchor="w",
                text_color=("gray50", "gray70"),
                wraplength=620,
                justify="left",
            )
            helper_label.grid(
                row=1,
                column=0,
                columnspan=2,
                sticky="w",
                padx=(0, 12),
                pady=(0, 6),
            )

    # Create widget and get reference to the actual input element
    input_widget = None
    if item.widget_type == WidgetType.CHECKBOX:
        input_widget = _create_checkbox(widget_frame, key, item, malcolm_config)
    elif item.widget_type == WidgetType.TEXT:
        input_widget = _create_entry(widget_frame, key, item, malcolm_config, is_password=False)
    elif item.widget_type == WidgetType.PASSWORD:
        input_widget = _create_entry(widget_frame, key, item, malcolm_config, is_password=True)
    elif item.widget_type == WidgetType.SELECT:
        input_widget = _create_dropdown(widget_frame, key, item, malcolm_config)
    elif item.widget_type == WidgetType.RADIO:
        input_widget = _create_radio_group(widget_frame, key, item, malcolm_config)
    elif item.widget_type == WidgetType.NUMBER:
        input_widget = _create_number_entry(widget_frame, key, item, malcolm_config)
    elif item.widget_type == WidgetType.DIRECTORY:
        input_widget = _create_directory_entry(widget_frame, key, item, malcolm_config)
    else:
        return None

    # Store reference to the actual input widget on the outer container for focus/validation
    if input_widget:
        container._input_widget = input_widget

    return container


def _create_checkbox(
    parent: customtkinter.CTkFrame,
    key: str,
    item: "ConfigItem",
    malcolm_config: "MalcolmConfig"
):
    """Create checkbox widget with two-way binding and inline error display."""
    container = customtkinter.CTkFrame(parent, fg_color="transparent")

    var = customtkinter.BooleanVar(value=bool(item.get_value()))
    _updating = [False]  # Guard flag to prevent observer loops

    checkbox = customtkinter.CTkCheckBox(
        container,
        text="",
        variable=var,
    )
    checkbox.grid(row=0, column=0, sticky="w")

    # Error label below checkbox
    error_label = customtkinter.CTkLabel(
        container,
        text="",
        font=("", 10),
        anchor="w"
    )
    error_label.grid(row=1, column=0, sticky="w", padx=(5, 0))
    error_label.grid_remove()  # Hidden by default

    def on_change():
        if _updating[0]:
            return
        _handle_set_value(checkbox, error_label, key, var.get(), malcolm_config)

    checkbox.configure(command=on_change)

    # Only register observer if config object supports it (MalcolmConfig has observe, InstallContext doesn't)
    if hasattr(malcolm_config, 'observe'):
        def update_from_model(value):
            _updating[0] = True
            var.set(bool(malcolm_config.get_value(key)))
            _updating[0] = False

        malcolm_config.observe(key, update_from_model)

    # Set up visibility observer with tooltips for disabled state
    _setup_visibility_observer(checkbox, key, malcolm_config)

    container.pack(anchor="w")

    return checkbox


def _create_entry(
    parent: customtkinter.CTkFrame,
    key: str,
    item: "ConfigItem",
    malcolm_config: "MalcolmConfig",
    is_password: bool = False
):
    """Create text entry widget with two-way binding and inline error display."""
    container = customtkinter.CTkFrame(parent, fg_color="transparent")

    var = customtkinter.StringVar(value=str(item.get_value() or ""))
    _updating = [False]  # Guard flag to prevent observer loops
    _debounce_id = [None]  # Track pending debounce timer

    entry = customtkinter.CTkEntry(
        container,
        textvariable=var,
        show="*" if is_password else "",
        width=300
    )
    entry.grid(row=0, column=0, sticky="ew")
    container.grid_columnconfigure(0, weight=1)

    # Error label below entry
    error_label = customtkinter.CTkLabel(
        container,
        text="",
        font=("", 10),
        anchor="w"
    )
    error_label.grid(row=1, column=0, sticky="w", padx=(5, 0))
    error_label.grid_remove()  # Hidden by default

    def do_validation():
        """Actually perform the validation."""
        _debounce_id[0] = None
        if _updating[0]:
            return
        _handle_set_value(entry, error_label, key, var.get(), malcolm_config)

    def on_change_debounced(*args):
        """Debounced change handler - waits for typing to pause before validating."""
        if _updating[0]:
            return
        # Cancel any pending validation
        if _debounce_id[0]:
            try:
                entry.after_cancel(_debounce_id[0])
            except tk.TclError:
                pass  # Timer already fired or widget destroyed
            except Exception as e:
                InstallerLogger.debug(f"Could not cancel debounce timer for {key}: {e}")
        # Schedule new validation after delay (800ms)
        _debounce_id[0] = entry.after(800, do_validation)

    def on_change_immediate(*args):
        """Immediate change handler for focus out and return."""
        # Cancel any pending debounced validation
        if _debounce_id[0]:
            try:
                entry.after_cancel(_debounce_id[0])
            except tk.TclError:
                pass  # Timer already fired or widget destroyed
            except Exception as e:
                InstallerLogger.debug(f"Could not cancel debounce timer for {key}: {e}")
            _debounce_id[0] = None
        do_validation()

    # Debounce validation on keystroke (wait for typing to pause)
    var.trace_add("write", on_change_debounced)

    # Validate immediately on focus out and return
    entry.bind("<FocusOut>", lambda e: on_change_immediate())
    entry.bind("<Return>", lambda e: on_change_immediate())

    # Only register observer if config object supports it
    if hasattr(malcolm_config, 'observe'):
        def update_from_model(value):
            _updating[0] = True
            var.set(str(malcolm_config.get_value(key) or ""))
            _updating[0] = False

        malcolm_config.observe(key, update_from_model)

    # Set up visibility observer with tooltips for disabled state
    _setup_visibility_observer(entry, key, malcolm_config)

    container.pack(fill="x", expand=True)

    return entry


def _create_dropdown(
    parent: customtkinter.CTkFrame,
    key: str,
    item: "ConfigItem",
    malcolm_config: "MalcolmConfig"
):
    """Create dropdown widget with two-way binding and inline error display."""
    if not item.choices:
        return

    container = customtkinter.CTkFrame(parent, fg_color="transparent")

    values = []
    value_map = {}
    current_value = item.get_value()
    initial_display = ""

    for choice in item.choices:
        if isinstance(choice, tuple) and len(choice) == 2:
            internal_value, display_text = choice
            values.append(display_text)
            value_map[display_text] = internal_value

            if internal_value == current_value:
                initial_display = display_text
        else:
            display_text = str(choice)
            values.append(display_text)
            value_map[display_text] = choice

            if choice == current_value:
                initial_display = display_text

    if not initial_display and values:
        initial_display = values[0]

    var = customtkinter.StringVar(value=initial_display)
    _updating = [False]  # Guard flag to prevent observer loops

    dropdown = customtkinter.CTkOptionMenu(
        container,
        values=values,
        variable=var,
        width=300
    )
    dropdown.grid(row=0, column=0, sticky="ew")
    container.grid_columnconfigure(0, weight=1)

    # Error label below dropdown
    error_label = customtkinter.CTkLabel(
        container,
        text="",
        font=("", 10),
        anchor="w"
    )
    error_label.grid(row=1, column=0, sticky="w", padx=(5, 0))
    error_label.grid_remove()  # Hidden by default

    def on_change(selected_display):
        if _updating[0]:
            return
        internal_value = value_map.get(selected_display)
        _handle_set_value(dropdown, error_label, key, internal_value, malcolm_config)

    dropdown.configure(command=on_change)

    # Only register observer if config object supports it
    if hasattr(malcolm_config, 'observe'):
        def update_from_model(value):
            _updating[0] = True
            current_value = malcolm_config.get_value(key)
            for display_text, internal_value in value_map.items():
                if internal_value == current_value:
                    var.set(display_text)
                    dropdown.set(display_text)
                    break
            _updating[0] = False

        malcolm_config.observe(key, update_from_model)

    # Set up visibility observer with tooltips for disabled state
    _setup_visibility_observer(dropdown, key, malcolm_config)

    container.pack(fill="x", expand=True)

    return dropdown


def _create_radio_group(
    parent: customtkinter.CTkFrame,
    key: str,
    item: "ConfigItem",
    malcolm_config: "MalcolmConfig"
):
    """Create radio button group with two-way binding and inline error display."""
    choices = item.choices
    if not choices and isinstance(item.default_value, bool):
        choices = [(True, "Yes"), (False, "No")]

    if not choices:
        return

    container = customtkinter.CTkFrame(parent, fg_color="transparent")

    value_map = {}
    var = customtkinter.StringVar(value=str(item.get_value()))
    _updating = [False]  # Guard flag to prevent observer loops

    # Radio buttons container
    radio_container = customtkinter.CTkFrame(container, fg_color="transparent")
    radio_container.grid(row=0, column=0, sticky="w")

    # Store all radio buttons for visibility control
    radio_buttons = []

    def on_change():
        if _updating[0]:
            return
        selected_key = var.get()
        new_value = value_map.get(selected_key, selected_key)
        _handle_set_value(radio_buttons[0] if radio_buttons else None, error_label, key, new_value, malcolm_config)

    for choice in choices:
        if isinstance(choice, tuple) and len(choice) >= 2:
            raw_value, label = choice[0], choice[1]
        else:
            raw_value, label = choice, str(choice)
        value_map[str(raw_value)] = raw_value
        radio = customtkinter.CTkRadioButton(
            radio_container,
            text=str(label),
            variable=var,
            value=str(raw_value),
            command=on_change,
        )
        radio.pack(side="left", padx=(0, 12))
        radio_buttons.append(radio)

    # Error label below radio group
    error_label = customtkinter.CTkLabel(
        container,
        text="",
        font=("", 10),
        anchor="w"
    )
    error_label.grid(row=1, column=0, sticky="w", padx=(5, 0))
    error_label.grid_remove()  # Hidden by default

    if hasattr(malcolm_config, 'observe'):
        def update_from_model(value):
            _updating[0] = True
            var.set(str(malcolm_config.get_value(key)))
            _updating[0] = False

        malcolm_config.observe(key, update_from_model)

    # Set up visibility observer for entire radio group
    if radio_buttons:
        def on_visibility_change(_):
            """Update state and tooltip for entire radio group."""
            visible = malcolm_config.is_item_visible(key)

            for radio in radio_buttons:
                if visible:
                    # Enable all radio buttons
                    radio.configure(state="normal")
                else:
                    # Disable all radio buttons
                    radio.configure(state="disabled")

            # Tooltip only on first radio button (logical group indicator)
            first_radio = radio_buttons[0]
            if visible:
                remove_tooltip(first_radio)
            else:
                # Get dependency info to explain why disabled
                dep_info = malcolm_config.get_dependency_info(key)
                if dep_info.get("has_visibility_rule"):
                    depends_on = dep_info.get("visibility_depends_on")
                    if isinstance(depends_on, list):
                        depends_str = ", ".join(depends_on)
                    else:
                        depends_str = str(depends_on)

                    tooltip_text = f"Disabled: depends on {depends_str}"
                    add_tooltip(first_radio, tooltip_text)

        if hasattr(malcolm_config, 'observe'):
            malcolm_config.observe(key, on_visibility_change)
            # Trigger initial evaluation
            on_visibility_change(None)

    container.pack(anchor="w")

    # Return first radio button for focus
    return radio_buttons[0] if radio_buttons else None


def _create_number_entry(
    parent: customtkinter.CTkFrame,
    key: str,
    item: "ConfigItem",
    malcolm_config: "MalcolmConfig"
):
    """Create number entry widget with validation and inline error display."""
    container = customtkinter.CTkFrame(parent, fg_color="transparent")

    var = customtkinter.StringVar(value=str(item.get_value() or ""))
    _updating = [False]  # Guard flag to prevent observer loops

    entry = customtkinter.CTkEntry(
        container,
        textvariable=var,
        width=150
    )
    entry.grid(row=0, column=0, sticky="w")

    # Error label below entry
    error_label = customtkinter.CTkLabel(
        container,
        text="",
        font=("", 10),
        anchor="w"
    )
    error_label.grid(row=1, column=0, sticky="w", padx=(5, 0))
    error_label.grid_remove()  # Hidden by default

    def on_change(*args):
        if _updating[0]:
            return
        new_value_str = var.get()

        if not new_value_str.strip():
            if getattr(item, "accept_blank", False):
                _handle_set_value(entry, error_label, key, None, malcolm_config)
            else:
                _handle_set_value(entry, error_label, key, item.default_value, malcolm_config)
            return

        try:
            if '.' in new_value_str:
                new_value = float(new_value_str)
            else:
                new_value = int(new_value_str)
            _handle_set_value(entry, error_label, key, new_value, malcolm_config)
        except ValueError:
            show_validation_error(entry, error_label, "Please enter a valid number")

    # Validate on every keystroke
    var.trace_add("write", on_change)

    # Also validate on focus out and return
    entry.bind("<FocusOut>", lambda e: on_change())
    entry.bind("<Return>", lambda e: on_change())

    # Only register observer if config object supports it
    if hasattr(malcolm_config, 'observe'):
        def update_from_model(value):
            _updating[0] = True
            var.set(str(malcolm_config.get_value(key) or ""))
            _updating[0] = False

        malcolm_config.observe(key, update_from_model)

    # Set up visibility observer with tooltips for disabled state
    _setup_visibility_observer(entry, key, malcolm_config)

    container.pack(anchor="w")

    return entry


def _create_directory_entry(
    parent: customtkinter.CTkFrame,
    key: str,
    item: "ConfigItem",
    malcolm_config: "MalcolmConfig"
):
    """Create directory entry widget with browse button and inline error display."""
    import os
    from tkinter import filedialog

    container = customtkinter.CTkFrame(parent, fg_color="transparent")
    container.grid_columnconfigure(0, weight=1)

    var = customtkinter.StringVar(value=str(item.get_value() or ""))
    _updating = [False]  # Guard flag to prevent observer loops

    # Entry and browse button row
    input_frame = customtkinter.CTkFrame(container, fg_color="transparent")
    input_frame.grid(row=0, column=0, sticky="ew")
    input_frame.grid_columnconfigure(0, weight=1)

    entry = customtkinter.CTkEntry(
        input_frame,
        textvariable=var,
        width=300
    )
    entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))

    browse_button = customtkinter.CTkButton(
        input_frame,
        text="Browse",
        width=80
    )
    browse_button.grid(row=0, column=1, sticky="e")

    # Error label below entry
    error_label = customtkinter.CTkLabel(
        container,
        text="",
        font=("", 10),
        anchor="w"
    )
    error_label.grid(row=1, column=0, sticky="w", padx=(5, 0))
    error_label.grid_remove()  # Hidden by default

    def on_change(*args):
        if _updating[0]:
            return
        _handle_set_value(entry, error_label, key, var.get(), malcolm_config)

    # Validate on every keystroke
    var.trace_add("write", on_change)

    # Also validate on focus out and return
    entry.bind("<FocusOut>", lambda e: on_change())
    entry.bind("<Return>", lambda e: on_change())

    def browse_for_directory():
        initial_dir = var.get().strip()
        if not initial_dir or not os.path.exists(initial_dir):
            initial_dir = os.path.expanduser("~")
        selected = filedialog.askdirectory(initialdir=initial_dir)
        if selected:
            var.set(selected)
            on_change()

    browse_button.configure(command=browse_for_directory)

    if hasattr(malcolm_config, 'observe'):
        def update_from_model(value):
            _updating[0] = True
            var.set(str(malcolm_config.get_value(key) or ""))
            _updating[0] = False

        malcolm_config.observe(key, update_from_model)

    # Set up visibility observer with tooltips for disabled state
    _setup_visibility_observer(entry, key, malcolm_config)

    container.pack(fill="x", expand=True)

    return entry
