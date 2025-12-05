#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2025 Battelle Energy Alliance, LLC.  All rights reserved.

"""
Menu Items for the Malcolm installer
====================================

This package contains all of the definitions for menu items (MenuItem).
MenuItems are used for UI grouping and visibility control only - they do not
write configuration values.

All menu item management is handled by the MalcolmConfig class.
"""

from scripts.installer.core.menu_item import MenuItem
from scripts.installer.configs.constants.menu_item_keys import (
    KEY_MENU_ITEM_NETWORK,
    KEY_MENU_ITEM_ANALYSIS,
    KEY_MENU_ITEM_ANALYSIS_LIVE,
    KEY_MENU_ITEM_ANALYSIS_HISTORICAL,
    KEY_MENU_ITEM_STORAGE,
    KEY_MENU_ITEM_ENRICHMENT,
    KEY_MENU_ITEM_ENRICHMENT_NETBOX,
    KEY_MENU_ITEM_RUNTIME_SETTINGS,
    KEY_MENU_ITEM_RUNTIME_CONTAINERS,
    KEY_MENU_ITEM_RUNTIME_RESOURCES,
    KEY_MENU_ITEM_RUNTIME_DOCUMENT_STORE,
    KEY_MENU_ITEM_MALCOLM_OS_PLATFORM,
)

# Menu item definitions
MENU_ITEM_NETWORK = MenuItem(
    key=KEY_MENU_ITEM_NETWORK,
    label="Network Settings",
    sort_priority=10,
)

MENU_ITEM_ANALYSIS = MenuItem(
    key=KEY_MENU_ITEM_ANALYSIS,
    label="Analysis Settings",
    sort_priority=20,
)

MENU_ITEM_ANALYSIS_LIVE = MenuItem(
    key=KEY_MENU_ITEM_ANALYSIS_LIVE,
    label="Live Analysis",
    sort_priority=21,
    ui_parent=KEY_MENU_ITEM_ANALYSIS,
)

MENU_ITEM_ANALYSIS_HISTORICAL = MenuItem(
    key=KEY_MENU_ITEM_ANALYSIS_HISTORICAL,
    label="Historical Analysis",
    sort_priority=22,
    ui_parent=KEY_MENU_ITEM_ANALYSIS,
)

MENU_ITEM_STORAGE = MenuItem(
    key=KEY_MENU_ITEM_STORAGE,
    label="Storage Settings",
    sort_priority=30,
)

MENU_ITEM_ENRICHMENT = MenuItem(
    key=KEY_MENU_ITEM_ENRICHMENT,
    label="Enrichment Settings",
    sort_priority=40,
)

MENU_ITEM_ENRICHMENT_NETBOX = MenuItem(
    key=KEY_MENU_ITEM_ENRICHMENT_NETBOX,
    label="Netbox",
    sort_priority=41,
    ui_parent=KEY_MENU_ITEM_ENRICHMENT,
)

MENU_ITEM_RUNTIME_SETTINGS = MenuItem(
    key=KEY_MENU_ITEM_RUNTIME_SETTINGS,
    label="Runtime Settings",
    sort_priority=50,
)

MENU_ITEM_RUNTIME_CONTAINERS = MenuItem(
    key=KEY_MENU_ITEM_RUNTIME_CONTAINERS,
    label="Containers",
    sort_priority=51,
    ui_parent=KEY_MENU_ITEM_RUNTIME_SETTINGS,
)

MENU_ITEM_RUNTIME_RESOURCES = MenuItem(
    key=KEY_MENU_ITEM_RUNTIME_RESOURCES,
    label="Resources",
    sort_priority=52,
    ui_parent=KEY_MENU_ITEM_RUNTIME_SETTINGS,
)

MENU_ITEM_RUNTIME_DOCUMENT_STORE = MenuItem(
    key=KEY_MENU_ITEM_RUNTIME_DOCUMENT_STORE,
    label="Document Store",
    sort_priority=53,
    ui_parent=KEY_MENU_ITEM_RUNTIME_SETTINGS,
)

MENU_ITEM_MALCOLM_OS_PLATFORM = MenuItem(
    key=KEY_MENU_ITEM_MALCOLM_OS_PLATFORM,
    label="Malcolm OS/Platform",
    sort_priority=100,
    is_visible=False,  # Hidden by default, controlled by SYSTEM_INFO
)

# Dictionary of all menu items
ALL_MENU_ITEMS_DICT = {
    KEY_MENU_ITEM_NETWORK: MENU_ITEM_NETWORK,
    KEY_MENU_ITEM_ANALYSIS: MENU_ITEM_ANALYSIS,
    KEY_MENU_ITEM_ANALYSIS_LIVE: MENU_ITEM_ANALYSIS_LIVE,
    KEY_MENU_ITEM_ANALYSIS_HISTORICAL: MENU_ITEM_ANALYSIS_HISTORICAL,
    KEY_MENU_ITEM_STORAGE: MENU_ITEM_STORAGE,
    KEY_MENU_ITEM_ENRICHMENT: MENU_ITEM_ENRICHMENT,
    KEY_MENU_ITEM_ENRICHMENT_NETBOX: MENU_ITEM_ENRICHMENT_NETBOX,
    KEY_MENU_ITEM_RUNTIME_SETTINGS: MENU_ITEM_RUNTIME_SETTINGS,
    KEY_MENU_ITEM_RUNTIME_CONTAINERS: MENU_ITEM_RUNTIME_CONTAINERS,
    KEY_MENU_ITEM_RUNTIME_RESOURCES: MENU_ITEM_RUNTIME_RESOURCES,
    KEY_MENU_ITEM_RUNTIME_DOCUMENT_STORE: MENU_ITEM_RUNTIME_DOCUMENT_STORE,
    KEY_MENU_ITEM_MALCOLM_OS_PLATFORM: MENU_ITEM_MALCOLM_OS_PLATFORM,
}

