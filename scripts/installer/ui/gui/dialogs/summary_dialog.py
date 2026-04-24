#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2025 Battelle Energy Alliance, LLC.  All rights reserved.

"""Read-only configuration summary content for the GUI installer's summary phase."""

from typing import TYPE_CHECKING
import customtkinter

from scripts.installer.ui.gui.components.styles import CONTAINER_CORNER_RADIUS, INFO_PANEL_BG
from scripts.installer.utils.summary_utils import build_configuration_summary_items, format_summary_value
from scripts.malcolm_constants import PLATFORM_LINUX
import platform as platform_module

if TYPE_CHECKING:
    from scripts.installer.core.malcolm_config import MalcolmConfig
    from scripts.installer.core.install_context import InstallContext


def build_summary_content(
    parent,
    malcolm_config: "MalcolmConfig",
    config_dir: str,
    install_context: "InstallContext",
    is_dry_run: bool = False,
) -> None:
    """Populate `parent` with the read-only configuration summary."""
    subtitle_text = (
        "Configuration preview (dry run mode - no changes will be made)"
        if is_dry_run
        else "Review your configuration before proceeding with installation"
    )
    customtkinter.CTkLabel(
        parent,
        text=subtitle_text,
        font=("Helvetica", 11),
        text_color="gray",
    ).pack(pady=(0, 10))

    summary_frame = customtkinter.CTkFrame(parent, corner_radius=8)
    summary_frame.pack(fill="both", expand=True, pady=(0, 15))

    summary_text = customtkinter.CTkTextbox(
        summary_frame,
        font=("Courier", 11),
        wrap="word",
    )
    summary_text.pack(fill="both", expand=True, padx=10, pady=10)

    summary_items = build_configuration_summary_items(malcolm_config, config_dir)
    lines = [
        "=" * 80,
        "MALCOLM CONFIGURATION SUMMARY",
        "=" * 80,
        "",
    ]
    for label, value in summary_items:
        display_value = format_summary_value(label, value)
        lines.append(f"{label:.<50} {display_value}")
    lines.extend(["", "=" * 80, f"Configuration Directory: {config_dir}", "=" * 80])
    summary_text.insert("1.0", "\n".join(lines))
    summary_text.configure(state="disabled")

    notes = []
    if install_context.config_only:
        notes.append("⚠ Configuration Only Mode: Installation will be skipped, only configuration files will be saved")
    if platform_module.system().lower() == PLATFORM_LINUX.lower() and getattr(install_context, "auto_tweaks", False):
        notes.append("✓ Auto-apply system tweaks: Linux system optimizations will be applied automatically")
    if is_dry_run:
        notes.append("ℹ Dry Run Mode: No changes will be made to the system")

    if notes:
        options_frame = customtkinter.CTkFrame(
            parent,
            corner_radius=CONTAINER_CORNER_RADIUS,
            fg_color=INFO_PANEL_BG,
        )
        options_frame.pack(fill="x", pady=(0, 10))
        for note in notes:
            customtkinter.CTkLabel(
                options_frame,
                text=note,
                font=("Helvetica", 11),
                anchor="w",
            ).pack(anchor="w", padx=15, pady=5)
