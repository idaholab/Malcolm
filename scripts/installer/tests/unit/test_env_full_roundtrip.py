#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""Deterministic .env roundtrip tests for installer config."""

import tempfile
import unittest

from scripts.installer.core.malcolm_config import MalcolmConfig
from scripts.installer.configs.constants.configuration_item_keys import (
    KEY_CONFIG_ITEM_DOCKER_ORCHESTRATION_MODE,
    KEY_CONFIG_ITEM_RUNTIME_BIN,
    KEY_CONFIG_ITEM_MALCOLM_PROFILE,
    KEY_CONFIG_ITEM_NETBOX_MODE,
    KEY_CONFIG_ITEM_NETBOX_URL,
    KEY_CONFIG_ITEM_OPENSEARCH_PRIMARY_MODE,
    KEY_CONFIG_ITEM_OPENSEARCH_PRIMARY_URL,
    KEY_CONFIG_ITEM_LOGSTASH_HOST,
    KEY_CONFIG_ITEM_OPEN_PORTS,
    KEY_CONFIG_ITEM_EXPOSE_OPENSEARCH,
)
from scripts.installer.configs.constants.enums import (
    SearchEngineMode,
    NetboxMode,
    OpenPortsChoices,
)
from scripts.malcolm_constants import PROFILE_HEDGEHOG, PROFILE_MALCOLM, OrchestrationFramework


class TestEnvFullRoundtrip(unittest.TestCase):
    """Validate stable write/read behavior for representative scenarios."""

    def _roundtrip_and_assert(self, configure_fn, expected_keys):
        cfg1 = MalcolmConfig()
        configure_fn(cfg1)

        with tempfile.TemporaryDirectory() as td:
            cfg1.generate_env_files(td)
            cfg2 = MalcolmConfig()
            cfg2.load_from_env_files(td)

            for key in expected_keys:
                self.assertEqual(cfg1.get_value(key), cfg2.get_value(key), f"Roundtrip mismatch for {key}")

    def test_defaults_roundtrip(self):
        self._roundtrip_and_assert(
            lambda _cfg: None,
            expected_keys=[
                KEY_CONFIG_ITEM_MALCOLM_PROFILE,
                KEY_CONFIG_ITEM_DOCKER_ORCHESTRATION_MODE,
                KEY_CONFIG_ITEM_RUNTIME_BIN,
                KEY_CONFIG_ITEM_OPENSEARCH_PRIMARY_MODE,
                KEY_CONFIG_ITEM_NETBOX_MODE,
                KEY_CONFIG_ITEM_OPEN_PORTS,
            ],
        )

    def test_malcolm_kubernetes_roundtrip(self):
        def configure(cfg):
            cfg.set_value(KEY_CONFIG_ITEM_MALCOLM_PROFILE, PROFILE_MALCOLM)
            cfg.set_value(KEY_CONFIG_ITEM_DOCKER_ORCHESTRATION_MODE, OrchestrationFramework.KUBERNETES)
            cfg.set_value(KEY_CONFIG_ITEM_RUNTIME_BIN, "kubernetes")
            cfg.set_value(KEY_CONFIG_ITEM_OPENSEARCH_PRIMARY_MODE, SearchEngineMode.OPENSEARCH_LOCAL.value)
            cfg.set_value(KEY_CONFIG_ITEM_OPEN_PORTS, OpenPortsChoices.CUSTOMIZE.value)
            cfg.set_value(KEY_CONFIG_ITEM_EXPOSE_OPENSEARCH, True)

        self._roundtrip_and_assert(
            configure,
            expected_keys=[
                KEY_CONFIG_ITEM_MALCOLM_PROFILE,
                KEY_CONFIG_ITEM_DOCKER_ORCHESTRATION_MODE,
                KEY_CONFIG_ITEM_RUNTIME_BIN,
                KEY_CONFIG_ITEM_OPENSEARCH_PRIMARY_MODE,
                KEY_CONFIG_ITEM_OPEN_PORTS,
                KEY_CONFIG_ITEM_EXPOSE_OPENSEARCH,
            ],
        )

    def test_hedgehog_remote_roundtrip(self):
        def configure(cfg):
            cfg.set_value(KEY_CONFIG_ITEM_MALCOLM_PROFILE, PROFILE_HEDGEHOG)
            cfg.set_value(KEY_CONFIG_ITEM_LOGSTASH_HOST, "192.0.2.1:5044")
            cfg.set_value(KEY_CONFIG_ITEM_OPENSEARCH_PRIMARY_MODE, SearchEngineMode.OPENSEARCH_REMOTE.value)
            cfg.set_value(KEY_CONFIG_ITEM_OPENSEARCH_PRIMARY_URL, "https://remote-os.example:9200")
            cfg.set_value(KEY_CONFIG_ITEM_NETBOX_MODE, NetboxMode.REMOTE.value)
            cfg.set_value(KEY_CONFIG_ITEM_NETBOX_URL, "https://netbox.example")

        self._roundtrip_and_assert(
            configure,
            expected_keys=[
                KEY_CONFIG_ITEM_MALCOLM_PROFILE,
                KEY_CONFIG_ITEM_LOGSTASH_HOST,
                KEY_CONFIG_ITEM_OPENSEARCH_PRIMARY_MODE,
                KEY_CONFIG_ITEM_OPENSEARCH_PRIMARY_URL,
                KEY_CONFIG_ITEM_NETBOX_MODE,
                KEY_CONFIG_ITEM_NETBOX_URL,
            ],
        )


if __name__ == "__main__":
    unittest.main()
