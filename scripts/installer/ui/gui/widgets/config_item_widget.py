#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2025 Battelle Energy Alliance, LLC.  All rights reserved.

from typing import TYPE_CHECKING, Optional
import customtkinter

from scripts.malcolm_constants import WidgetType

if TYPE_CHECKING:
    from scripts.installer.core.malcolm_config import MalcolmConfig
    from scripts.installer.core.config_item import ConfigItem


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

    if item.widget_type == WidgetType.CHECKBOX:
        _create_checkbox(widget_frame, key, item, malcolm_config)
    elif item.widget_type == WidgetType.TEXT:
        _create_entry(widget_frame, key, item, malcolm_config, is_password=False)
    elif item.widget_type == WidgetType.PASSWORD:
        _create_entry(widget_frame, key, item, malcolm_config, is_password=True)
    elif item.widget_type == WidgetType.SELECT:
        _create_dropdown(widget_frame, key, item, malcolm_config)
    elif item.widget_type == WidgetType.RADIO:
        _create_radio_group(widget_frame, key, item, malcolm_config)
    elif item.widget_type == WidgetType.NUMBER:
        _create_number_entry(widget_frame, key, item, malcolm_config)
    elif item.widget_type == WidgetType.DIRECTORY:
        _create_directory_entry(widget_frame, key, item, malcolm_config)
    else:
        return None

    return container


def _create_checkbox(
    parent: customtkinter.CTkFrame,
    key: str,
    item: "ConfigItem",
    malcolm_config: "MalcolmConfig"
):
    """Create checkbox widget with two-way binding."""
    var = customtkinter.BooleanVar(value=bool(item.get_value()))

    def on_change():
        from scripts.installer.utils.logger_utils import InstallerLogger
        import traceback
        new_value = var.get()
        try:
            malcolm_config.set_value(key, new_value)
        except (ValueError, TypeError) as e:
            # Expected validation errors
            var.set(not new_value)
            _show_error_dialog(parent, str(e))
        except Exception as e:
            # Unexpected error - log with traceback for debugging
            InstallerLogger.error(f"Unexpected error setting {key} to {new_value}: {e}")
            InstallerLogger.error(traceback.format_exc())
            var.set(not new_value)
            _show_error_dialog(parent, f"Error: {e}")

    checkbox = customtkinter.CTkCheckBox(
        parent,
        text="",
        variable=var,
        command=on_change
    )
    checkbox.pack(anchor="w")

    # Only register observer if config object supports it (MalcolmConfig has observe, InstallContext doesn't)
    if hasattr(malcolm_config, 'observe'):
        def update_from_model(value):
            var.set(bool(malcolm_config.get_value(key)))

        malcolm_config.observe(key, update_from_model)


def _create_entry(
    parent: customtkinter.CTkFrame,
    key: str,
    item: "ConfigItem",
    malcolm_config: "MalcolmConfig",
    is_password: bool = False
):
    """Create text entry widget with two-way binding."""
    var = customtkinter.StringVar(value=str(item.get_value() or ""))

    def on_focus_out(_event=None):
        from scripts.installer.utils.logger_utils import InstallerLogger
        import traceback
        new_value = var.get()
        try:
            malcolm_config.set_value(key, new_value)
        except (ValueError, TypeError) as e:
            # Expected validation errors
            var.set(str(item.get_value() or ""))
            _show_error_dialog(parent, str(e))
        except Exception as e:
            # Unexpected error - log with traceback
            InstallerLogger.error(f"Unexpected error setting {key} to {new_value}: {e}")
            InstallerLogger.error(traceback.format_exc())
            var.set(str(item.get_value() or ""))
            _show_error_dialog(parent, f"Error: {e}")

    entry = customtkinter.CTkEntry(
        parent,
        textvariable=var,
        show="*" if is_password else "",
        width=300
    )
    entry.pack(fill="x", expand=True)
    entry.bind("<FocusOut>", on_focus_out)
    entry.bind("<Return>", on_focus_out)

    # Only register observer if config object supports it
    if hasattr(malcolm_config, 'observe'):
        def update_from_model(value):
            var.set(str(malcolm_config.get_value(key) or ""))

        malcolm_config.observe(key, update_from_model)


def _create_dropdown(
    parent: customtkinter.CTkFrame,
    key: str,
    item: "ConfigItem",
    malcolm_config: "MalcolmConfig"
):
    """Create dropdown widget with two-way binding."""
    if not item.choices:
        return

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

    def on_change(selected_display):
        from scripts.installer.utils.logger_utils import InstallerLogger
        import traceback
        internal_value = value_map.get(selected_display)
        try:
            malcolm_config.set_value(key, internal_value)
        except (ValueError, TypeError) as e:
            # Expected validation errors
            var.set(initial_display)
            _show_error_dialog(parent, str(e))
        except Exception as e:
            # Unexpected error - log with traceback
            InstallerLogger.error(f"Unexpected error setting {key} to {internal_value}: {e}")
            InstallerLogger.error(traceback.format_exc())
            var.set(initial_display)
            _show_error_dialog(parent, f"Error: {e}")

    dropdown = customtkinter.CTkOptionMenu(
        parent,
        values=values,
        variable=var,
        command=on_change,
        width=300
    )
    dropdown.pack(fill="x", expand=True)

    # Only register observer if config object supports it
    if hasattr(malcolm_config, 'observe'):
        def update_from_model(value):
            current_value = malcolm_config.get_value(key)
            for display_text, internal_value in value_map.items():
                if internal_value == current_value:
                    var.set(display_text)
                    dropdown.set(display_text)
                    break

        malcolm_config.observe(key, update_from_model)


def _create_radio_group(
    parent: customtkinter.CTkFrame,
    key: str,
    item: "ConfigItem",
    malcolm_config: "MalcolmConfig"
):
    """Create radio button group with two-way binding."""
    from scripts.installer.utils.logger_utils import InstallerLogger
    import traceback

    choices = item.choices
    if not choices and isinstance(item.default_value, bool):
        choices = [(True, "Yes"), (False, "No")]

    if not choices:
        return

    value_map = {}
    var = customtkinter.StringVar(value=str(item.get_value()))

    def on_change():
        selected_key = var.get()
        new_value = value_map.get(selected_key, selected_key)
        try:
            malcolm_config.set_value(key, new_value)
        except (ValueError, TypeError) as e:
            var.set(str(item.get_value()))
            _show_error_dialog(parent, str(e))
        except Exception as e:
            InstallerLogger.error(f"Unexpected error setting {key} to {new_value}: {e}")
            InstallerLogger.error(traceback.format_exc())
            var.set(str(item.get_value()))
            _show_error_dialog(parent, f"Error: {e}")

    for choice in choices:
        if isinstance(choice, tuple) and len(choice) >= 2:
            raw_value, label = choice[0], choice[1]
        else:
            raw_value, label = choice, str(choice)
        value_map[str(raw_value)] = raw_value
        radio = customtkinter.CTkRadioButton(
            parent,
            text=str(label),
            variable=var,
            value=str(raw_value),
            command=on_change,
        )
        radio.pack(side="left", padx=(0, 12))

    if hasattr(malcolm_config, 'observe'):
        def update_from_model(value):
            var.set(str(malcolm_config.get_value(key)))

        malcolm_config.observe(key, update_from_model)


def _create_number_entry(
    parent: customtkinter.CTkFrame,
    key: str,
    item: "ConfigItem",
    malcolm_config: "MalcolmConfig"
):
    """Create number entry widget with validation and two-way binding."""
    var = customtkinter.StringVar(value=str(item.get_value() or ""))

    def on_focus_out(_event=None):
        from scripts.installer.utils.logger_utils import InstallerLogger
        import traceback
        new_value_str = var.get()

        if not new_value_str.strip():
            try:
                malcolm_config.set_value(key, None)
                return
            except (ValueError, TypeError) as e:
                var.set(str(item.get_value() or ""))
                _show_error_dialog(parent, str(e))
                return
            except Exception as e:
                InstallerLogger.error(f"Unexpected error clearing {key}: {e}")
                InstallerLogger.error(traceback.format_exc())
                var.set(str(item.get_value() or ""))
                _show_error_dialog(parent, f"Error: {e}")
                return

        try:
            if '.' in new_value_str:
                new_value = float(new_value_str)
            else:
                new_value = int(new_value_str)

            malcolm_config.set_value(key, new_value)
        except ValueError:
            var.set(str(item.get_value() or ""))
            _show_error_dialog(parent, "Please enter a valid number")
        except TypeError as e:
            var.set(str(item.get_value() or ""))
            _show_error_dialog(parent, str(e))
        except Exception as e:
            InstallerLogger.error(f"Unexpected error setting {key} to {new_value_str}: {e}")
            InstallerLogger.error(traceback.format_exc())
            var.set(str(item.get_value() or ""))
            _show_error_dialog(parent, f"Error: {e}")

    entry = customtkinter.CTkEntry(
        parent,
        textvariable=var,
        width=150
    )
    entry.pack(anchor="w")
    entry.bind("<FocusOut>", on_focus_out)
    entry.bind("<Return>", on_focus_out)

    # Only register observer if config object supports it
    if hasattr(malcolm_config, 'observe'):
        def update_from_model(value):
            var.set(str(malcolm_config.get_value(key) or ""))

        malcolm_config.observe(key, update_from_model)


def _create_directory_entry(
    parent: customtkinter.CTkFrame,
    key: str,
    item: "ConfigItem",
    malcolm_config: "MalcolmConfig"
):
    """Create directory entry widget with browse button and two-way binding."""
    import os
    from tkinter import filedialog

    var = customtkinter.StringVar(value=str(item.get_value() or ""))

    def on_focus_out(_event=None):
        from scripts.installer.utils.logger_utils import InstallerLogger
        import traceback
        new_value = var.get()
        try:
            malcolm_config.set_value(key, new_value)
        except (ValueError, TypeError) as e:
            var.set(str(item.get_value() or ""))
            _show_error_dialog(parent, str(e))
        except Exception as e:
            InstallerLogger.error(f"Unexpected error setting {key} to {new_value}: {e}")
            InstallerLogger.error(traceback.format_exc())
            var.set(str(item.get_value() or ""))
            _show_error_dialog(parent, f"Error: {e}")

    entry = customtkinter.CTkEntry(
        parent,
        textvariable=var,
        width=300
    )
    entry.pack(side="left", fill="x", expand=True)
    entry.bind("<FocusOut>", on_focus_out)
    entry.bind("<Return>", on_focus_out)

    def browse_for_directory():
        initial_dir = var.get().strip()
        if not initial_dir or not os.path.exists(initial_dir):
            initial_dir = os.path.expanduser("~")
        selected = filedialog.askdirectory(initialdir=initial_dir)
        if selected:
            var.set(selected)
            on_focus_out()

    browse_button = customtkinter.CTkButton(
        parent,
        text="Browse",
        command=browse_for_directory,
        width=80
    )
    browse_button.pack(side="left", padx=(10, 0))

    if hasattr(malcolm_config, 'observe'):
        def update_from_model(value):
            var.set(str(malcolm_config.get_value(key) or ""))

        malcolm_config.observe(key, update_from_model)


def _show_error_dialog(parent, message: str):
    """Show error dialog to user."""
    dialog = customtkinter.CTkToplevel(parent)
    dialog.title("Validation Error")
    dialog.geometry("400x150")
    dialog.transient(parent.winfo_toplevel())
    dialog.grab_set()

    label = customtkinter.CTkLabel(
        dialog,
        text=message,
        wraplength=350
    )
    label.pack(pady=20, padx=20)

    button = customtkinter.CTkButton(
        dialog,
        text="OK",
        command=dialog.destroy
    )
    button.pack(pady=10)

    dialog.wait_window()
