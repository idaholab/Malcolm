#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2026 Battelle Energy Alliance, LLC.  All rights reserved.


"""Build and format configuration summaries for UI display."""

from typing import Any, List, Tuple
from enum import Enum


_DISPLAY_STRING_MAPPING = {
    "yes": "Yes",
    "no": "No",
    "always": "Always",
    "unless-stopped": "Unless stopped",
    "customize": "Customize",
    "disabled": "Disabled",
    "enabled": "Enabled",
    "local": "Local",
    "remote": "Remote",
}


def normalize_display_string(value: Any) -> str:
    """Title-case common enum-like strings (yes/no, restart policies, etc.) for UI display."""
    if value is None:
        return "Not set"
    return _DISPLAY_STRING_MAPPING.get(str(value).strip().lower(), value)


def format_scalar(value: Any, *, empty_label: str) -> str:
    """Format primitive, enum, and scalar values consistently for display.

    - bool -> Yes/No
    - Enum -> enum .value (or prettified .name fallback)
    - None/empty -> empty_label
    - other -> normalized string
    """
    try:
        from scripts.installer.core.transform_registry import apply_outbound

        value = apply_outbound("", value)
    except Exception:
        pass

    if value is None or value == "":
        return empty_label
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, Enum):
        try:
            enum_value = value.value
            if isinstance(enum_value, str):
                return normalize_display_string(enum_value)
        except Exception:
            pass
        try:
            name = getattr(value, "name", str(value))
            if isinstance(name, str) and name:
                return normalize_display_string(name.replace("_", " ").strip().title())
        except Exception:
            pass
        return normalize_display_string(str(value))
    return normalize_display_string(str(value))


def _get_restart_policy_display(malcolm_config) -> str:
    """Get the restart policy display value based on auto-restart setting and policy value.

    Args:
        malcolm_config: MalcolmConfig instance

    Returns:
        String representation of the restart policy
    """
    from scripts.installer.configs.constants.configuration_item_keys import (
        KEY_CONFIG_ITEM_MALCOLM_RESTART_POLICY,
    )

    if restart_policy := malcolm_config.get_value(KEY_CONFIG_ITEM_MALCOLM_RESTART_POLICY):
        if isinstance(restart_policy, Enum):
            return normalize_display_string(restart_policy.value)
        return normalize_display_string(str(restart_policy))

    return normalize_display_string("unless-stopped")


def build_configuration_summary_items(malcolm_config, config_dir: str) -> List[Tuple[str, str]]:
    """Build a list of configuration summary items for display.

    Args:
        malcolm_config: MalcolmConfig instance containing all configuration
        config_dir: Configuration directory path where files will be saved

    Returns:
        List of (label, value) tuples representing configuration items
    """
    from scripts.installer.configs.constants.configuration_item_keys import (
        KEY_CONFIG_ITEM_CONTAINER_NETWORK_NAME,
        KEY_CONFIG_ITEM_DOCKER_ORCHESTRATION_MODE,
        KEY_CONFIG_ITEM_MALCOLM_PROFILE,
        KEY_CONFIG_ITEM_MALCOLM_RESTART_POLICY,
        KEY_CONFIG_ITEM_NGINX_SSL,
        KEY_CONFIG_ITEM_PCAP_NODE_NAME,
        KEY_CONFIG_ITEM_PROCESS_GROUP_ID,
        KEY_CONFIG_ITEM_PROCESS_USER_ID,
        KEY_CONFIG_ITEM_RUNTIME_BIN,
        KEY_CONFIG_ITEM_USE_DEFAULT_STORAGE_LOCATIONS,
    )
    from scripts.malcolm_constants import OrchestrationFramework

    used_keys = [
        KEY_CONFIG_ITEM_CONTAINER_NETWORK_NAME,
        KEY_CONFIG_ITEM_DOCKER_ORCHESTRATION_MODE,
        KEY_CONFIG_ITEM_MALCOLM_PROFILE,
        KEY_CONFIG_ITEM_MALCOLM_RESTART_POLICY,
        KEY_CONFIG_ITEM_NGINX_SSL,
        KEY_CONFIG_ITEM_PCAP_NODE_NAME,
        KEY_CONFIG_ITEM_PROCESS_GROUP_ID,
        KEY_CONFIG_ITEM_PROCESS_USER_ID,
        KEY_CONFIG_ITEM_RUNTIME_BIN,
        KEY_CONFIG_ITEM_USE_DEFAULT_STORAGE_LOCATIONS,
    ]

    # determine orchestration to match legacy display behavior
    orch_mode = malcolm_config.get_value(KEY_CONFIG_ITEM_DOCKER_ORCHESTRATION_MODE)

    summary_items = [
        ("Configuration Directory", config_dir),
        ("Container Runtime", malcolm_config.get_value(KEY_CONFIG_ITEM_RUNTIME_BIN)),
        ("Run Profile", malcolm_config.get_value(KEY_CONFIG_ITEM_MALCOLM_PROFILE)),
        (
            "Process UID/GID",
            f"{malcolm_config.get_value(KEY_CONFIG_ITEM_PROCESS_USER_ID)}/{malcolm_config.get_value(KEY_CONFIG_ITEM_PROCESS_GROUP_ID)}",
        ),
    ]

    if orch_mode != OrchestrationFramework.KUBERNETES:
        summary_items.extend(
            [
                ("Container Restart Policy", _get_restart_policy_display(malcolm_config)),
                (
                    "Container Network",
                    malcolm_config.get_value(KEY_CONFIG_ITEM_CONTAINER_NETWORK_NAME) or "default",
                ),
                (
                    "Default Storage Locations",
                    ("Yes" if malcolm_config.get_value(KEY_CONFIG_ITEM_USE_DEFAULT_STORAGE_LOCATIONS) else "No"),
                ),
            ]
        )

    # remaining item(s) are common to both orchestration modes
    summary_items.extend(
        [
            (
                "HTTPS/SSL",
                "Yes" if malcolm_config.get_value(KEY_CONFIG_ITEM_NGINX_SSL) else "No",
            ),
        ]
    )

    summary_items.append(("Node Name", malcolm_config.get_value(KEY_CONFIG_ITEM_PCAP_NODE_NAME)))

    for changed_config_key in malcolm_config.get_all_config_items(modified_only=True):
        if changed_config_key not in used_keys:
            try:
                if item := malcolm_config.get_item(str(changed_config_key)):
                    summary_items.append((item.label, item.get_value()))
                used_keys.append(changed_config_key)
            except Exception:
                pass

    return summary_items


def format_summary_value(label: str, value: Any) -> str:
    """Format a configuration value for summary display, masking password/API-key fields."""
    if value and (("password" in label.lower()) or ("api key" in label.lower())):
        return "********"
    return format_scalar(value, empty_label="Not set")
