#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Settings file roundtrip tests for MalcolmConfig + InstallContext."""

import os
import tempfile
import unittest

from scripts.installer.core.malcolm_config import MalcolmConfig
from scripts.installer.core.install_context import InstallContext
from scripts.installer.utils.settings_file_handler import SettingsFileHandler
from scripts.installer.configs.constants.configuration_item_keys import (
    KEY_CONFIG_ITEM_MALCOLM_PROFILE,
    KEY_CONFIG_ITEM_OPENSEARCH_PRIMARY_MODE,
    KEY_CONFIG_ITEM_OPENSEARCH_PRIMARY_URL,
    KEY_CONFIG_ITEM_NETBOX_MODE,
)
from scripts.installer.configs.constants.enums import (
    SearchEngineMode,
    NetboxMode,
    DockerInstallMethod,
    DockerComposeInstallMethod,
)
from scripts.installer.configs.constants.installation_item_keys import (
    KEY_INSTALLATION_ITEM_AUTO_TWEAKS,
    KEY_INSTALLATION_ITEM_DOCKER_INSTALL_METHOD,
    KEY_INSTALLATION_ITEM_DOCKER_COMPOSE_INSTALL_METHOD,
)
from scripts.malcolm_constants import PROFILE_HEDGEHOG


class TestSettingsFileRoundtrip(unittest.TestCase):
    """Validate YAML/JSON save/load for both config and install contexts."""

    def _make_seeded_state(self):
        cfg = MalcolmConfig()
        ctx = InstallContext()
        ctx.initialize_for_platform("linux")

        # Seed representative non-default values for config serialization.
        cfg.set_value(KEY_CONFIG_ITEM_MALCOLM_PROFILE, PROFILE_HEDGEHOG)
        cfg.set_value(KEY_CONFIG_ITEM_OPENSEARCH_PRIMARY_MODE, SearchEngineMode.OPENSEARCH_REMOTE.value)
        cfg.set_value(KEY_CONFIG_ITEM_OPENSEARCH_PRIMARY_URL, "https://remote-os.example:9200")
        cfg.set_value(KEY_CONFIG_ITEM_NETBOX_MODE, NetboxMode.REMOTE.value)

        # Seed representative install-context values (including enums).
        ctx.set_item_value(KEY_INSTALLATION_ITEM_AUTO_TWEAKS, False)
        ctx.set_item_value(KEY_INSTALLATION_ITEM_DOCKER_INSTALL_METHOD, DockerInstallMethod.CONVENIENCE_SCRIPT)
        ctx.set_item_value(KEY_INSTALLATION_ITEM_DOCKER_COMPOSE_INSTALL_METHOD, DockerComposeInstallMethod.GITHUB)

        return cfg, ctx

    def _assert_roundtrip(self, file_format: str):
        cfg_src, ctx_src = self._make_seeded_state()
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, f"settings.{file_format}")

            SettingsFileHandler(cfg_src, ctx_src).save_to_file(path, file_format=file_format)

            cfg_dst = MalcolmConfig()
            ctx_dst = InstallContext()
            ctx_dst.initialize_for_platform("linux")
            SettingsFileHandler(cfg_dst, ctx_dst).load_from_file(path)

            for key in (
                KEY_CONFIG_ITEM_MALCOLM_PROFILE,
                KEY_CONFIG_ITEM_OPENSEARCH_PRIMARY_MODE,
                KEY_CONFIG_ITEM_OPENSEARCH_PRIMARY_URL,
                KEY_CONFIG_ITEM_NETBOX_MODE,
            ):
                self.assertEqual(cfg_src.get_value(key), cfg_dst.get_value(key), f"{file_format} config mismatch for {key}")

            self.assertEqual(
                ctx_src.get_item_value(KEY_INSTALLATION_ITEM_AUTO_TWEAKS),
                ctx_dst.get_item_value(KEY_INSTALLATION_ITEM_AUTO_TWEAKS),
            )
            self.assertEqual(
                ctx_src.get_item_value(KEY_INSTALLATION_ITEM_DOCKER_INSTALL_METHOD),
                ctx_dst.get_item_value(KEY_INSTALLATION_ITEM_DOCKER_INSTALL_METHOD),
            )
            self.assertEqual(
                ctx_src.get_item_value(KEY_INSTALLATION_ITEM_DOCKER_COMPOSE_INSTALL_METHOD),
                ctx_dst.get_item_value(KEY_INSTALLATION_ITEM_DOCKER_COMPOSE_INSTALL_METHOD),
            )

    def test_yaml_roundtrip(self):
        self._assert_roundtrip("yaml")

    def test_json_roundtrip(self):
        self._assert_roundtrip("json")


if __name__ == "__main__":
    unittest.main()
