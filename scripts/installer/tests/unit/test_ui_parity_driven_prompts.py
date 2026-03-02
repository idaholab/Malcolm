#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Shared prompt contract tests for TUI/DUI choice filtering."""

import unittest
from unittest.mock import patch

from scripts.installer.core.malcolm_config import MalcolmConfig
from scripts.installer.ui.shared.prompt_utils import prompt_config_item_value
from scripts.installer.configs.constants.configuration_item_keys import (
    KEY_CONFIG_ITEM_MALCOLM_PROFILE,
    KEY_CONFIG_ITEM_NETBOX_MODE,
    KEY_CONFIG_ITEM_OPENSEARCH_PRIMARY_MODE,
)
from scripts.malcolm_common import UserInterfaceMode
from scripts.malcolm_constants import PROFILE_HEDGEHOG, PROFILE_MALCOLM


class TestUIPromptChoiceFiltering(unittest.TestCase):
    def _capture_choice_tags(self, ui_mode, config_key, profile_value):
        cfg = MalcolmConfig()
        cfg.set_value(KEY_CONFIG_ITEM_MALCOLM_PROFILE, profile_value)
        item = cfg.get_item(config_key)
        captured = {"tags": []}

        def _fake_choose_one(_prompt, choices=None, **_kwargs):
            captured["tags"] = [c[0] for c in (choices or [])]
            return captured["tags"][0] if captured["tags"] else None

        with patch("scripts.installer.ui.shared.prompt_utils.InstallerChooseOne", side_effect=_fake_choose_one):
            prompt_config_item_value(
                ui_mode=ui_mode,
                config_item=item,
                malcolm_config=cfg,
                show_preamble=False,
            )
        return captured["tags"]

    def test_hedgehog_hides_malcolm_only_netbox_local_choice(self):
        tags_tui = self._capture_choice_tags(
            UserInterfaceMode.InteractionInput, KEY_CONFIG_ITEM_NETBOX_MODE, PROFILE_HEDGEHOG
        )
        tags_dui = self._capture_choice_tags(
            UserInterfaceMode.InteractionDialog, KEY_CONFIG_ITEM_NETBOX_MODE, PROFILE_HEDGEHOG
        )
        self.assertEqual(tags_tui, ["disabled", "remote"])
        self.assertEqual(tags_dui, ["disabled", "remote"])

    def test_hedgehog_hides_opensearch_local_choice(self):
        tags_tui = self._capture_choice_tags(
            UserInterfaceMode.InteractionInput, KEY_CONFIG_ITEM_OPENSEARCH_PRIMARY_MODE, PROFILE_HEDGEHOG
        )
        tags_dui = self._capture_choice_tags(
            UserInterfaceMode.InteractionDialog, KEY_CONFIG_ITEM_OPENSEARCH_PRIMARY_MODE, PROFILE_HEDGEHOG
        )
        self.assertEqual(tags_tui, ["opensearch-remote", "elasticsearch-remote"])
        self.assertEqual(tags_dui, ["opensearch-remote", "elasticsearch-remote"])

    def test_malcolm_keeps_full_choice_set(self):
        tags = self._capture_choice_tags(
            UserInterfaceMode.InteractionInput, KEY_CONFIG_ITEM_NETBOX_MODE, PROFILE_MALCOLM
        )
        self.assertEqual(tags, ["disabled", "local", "remote"])


if __name__ == "__main__":
    unittest.main()
