#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (c) 2026 Battelle Energy Alliance, LLC.  All rights reserved.

"""Integration tests for docker-compose update functionality."""

import os
import sys
import tempfile
import shutil
import unittest

# Add the project root directory to the Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, "..", "..", "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from scripts.malcolm_common import DumpYaml, LoadYaml
from scripts.installer.core.malcolm_config import MalcolmConfig
from scripts.installer.actions.shared import update_compose_files
from scripts.installer.core.install_context import InstallContext
from scripts.installer.tests.mock.test_framework import MockPlatform
from scripts.installer.configs.constants.configuration_item_keys import (
    KEY_CONFIG_ITEM_USE_DEFAULT_STORAGE_LOCATIONS,
    KEY_CONFIG_ITEM_CONTAINER_NETWORK_NAME,
    KEY_CONFIG_ITEM_INDEX_DIR,
    KEY_CONFIG_ITEM_INDEX_SNAPSHOT_DIR,
    KEY_CONFIG_ITEM_MALCOLM_RESTART_POLICY,
    KEY_CONFIG_ITEM_PCAP_DIR,
    KEY_CONFIG_ITEM_RUNTIME_BIN,
    KEY_CONFIG_ITEM_SURICATA_LOG_DIR,
    KEY_CONFIG_ITEM_ZEEK_LOG_DIR,
)
from scripts.installer.tests.mock.test_framework import BaseInstallerTest


class TestDockerComposeIntegration(BaseInstallerTest):
    """Integration tests for docker-compose update functionality."""

    def setUp(self):
        """Set up test fixtures."""
        super().setUp()  # Get mock_logger and other utilities
        self.test_dir = tempfile.mkdtemp()
        self.config_dir = os.path.join(self.test_dir, "config")
        os.makedirs(self.config_dir)

        # Create a sample docker-compose.yml file
        self.sample_compose = {
            "services": {
                "opensearch": {
                    "image": "ghcr.io/idaholab/malcolm/opensearch:latest",
                    "restart": "no",
                    "logging": {"driver": "local"},
                    "volumes": ["./opensearch:/usr/share/opensearch/data"],
                },
                "arkime": {
                    "image": "ghcr.io/idaholab/malcolm/arkime:latest",
                    "restart": "no",
                    "logging": {"driver": "local"},
                    "volumes": ["./pcap:/data/pcap"],
                },
                "zeek": {
                    "image": "ghcr.io/idaholab/malcolm/zeek:latest",
                    "restart": "no",
                    "logging": {"driver": "local"},
                    # Use a container path that our remapper supports for the zeek service
                    # (upload directory under the zeek logs root)
                    "volumes": ["./zeek-logs:/zeek/upload"],
                },
            },
            "networks": {"default": {"name": "malcolm_default"}},
        }

        self.compose_file = os.path.join(self.test_dir, "docker-compose.yml")
        DumpYaml(self.sample_compose, self.compose_file)

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.test_dir)

    def test_docker_runtime_updates(self):
        """Test that docker-compose files are updated for Docker runtime."""
        malcolm_config = MalcolmConfig()
        malcolm_config.set_value(KEY_CONFIG_ITEM_RUNTIME_BIN, "docker")
        malcolm_config.set_value(KEY_CONFIG_ITEM_MALCOLM_RESTART_POLICY, "unless-stopped")

        result = update_compose_files(malcolm_config, self.test_dir, None, MockPlatform(), InstallContext())
        self.assertTrue(result)

        # Verify changes
        updated_data = LoadYaml(self.compose_file)

        for service in updated_data["services"]:
            # Docker doesn't use userns_mode
            self.assertNotIn("userns_mode", updated_data["services"][service])
            # Docker uses local logging driver
            self.assertEqual(updated_data["services"][service]["logging"]["driver"], "local")
            # Restart policy should be updated
            self.assertEqual(updated_data["services"][service]["restart"], "unless-stopped")

    def test_podman_runtime_updates(self):
        """Test that docker-compose files are updated for Podman runtime."""
        malcolm_config = MalcolmConfig()
        malcolm_config.set_value(KEY_CONFIG_ITEM_RUNTIME_BIN, "podman")
        malcolm_config.set_value(KEY_CONFIG_ITEM_MALCOLM_RESTART_POLICY, "always")

        result = update_compose_files(malcolm_config, self.test_dir, None, MockPlatform(), InstallContext())
        self.assertTrue(result)

        # Verify changes
        updated_data = LoadYaml(self.compose_file)

        for service in updated_data["services"]:
            # Podman uses userns_mode: keep-id
            self.assertEqual(updated_data["services"][service]["userns_mode"], "keep-id")
            # Podman uses json-file logging driver
            self.assertEqual(updated_data["services"][service]["logging"]["driver"], "json-file")
            # Restart policy should be updated
            self.assertEqual(updated_data["services"][service]["restart"], "always")

    def test_volume_mount_updates(self):
        """Test that volume mounts are updated with custom paths."""
        malcolm_config = MalcolmConfig()

        custom_opensearch = os.path.join(self.test_dir, "os-custom")
        custom_pcap = os.path.join(self.test_dir, "pcap-custom")
        custom_snapshot = os.path.join(self.test_dir, "os-bak-custom")
        custom_suricata = os.path.join(self.test_dir, "suricata-custom")
        custom_zeek = os.path.join(self.test_dir, "zeek-custom")
        for custpath in [custom_opensearch, custom_pcap, custom_snapshot, custom_suricata, custom_zeek]:
            os.makedirs(custpath, exist_ok=True)

        malcolm_config.set_value(KEY_CONFIG_ITEM_USE_DEFAULT_STORAGE_LOCATIONS, False)
        malcolm_config.set_value(KEY_CONFIG_ITEM_INDEX_DIR, custom_opensearch)
        malcolm_config.set_value(KEY_CONFIG_ITEM_INDEX_SNAPSHOT_DIR, custom_snapshot)
        malcolm_config.set_value(KEY_CONFIG_ITEM_PCAP_DIR, custom_pcap)
        malcolm_config.set_value(KEY_CONFIG_ITEM_SURICATA_LOG_DIR, custom_suricata)
        malcolm_config.set_value(KEY_CONFIG_ITEM_ZEEK_LOG_DIR, custom_zeek)

        result = update_compose_files(malcolm_config, self.test_dir, None, MockPlatform(), InstallContext())
        self.assertTrue(result)

        # Verify volume mount updates
        updated_data = LoadYaml(self.compose_file)

        # Spot check volume mounts
        arkime_volumes = updated_data["services"]["arkime"]["volumes"]
        self.assertIn(f"{custom_pcap}:/data/pcap", arkime_volumes)

        # Check zeek log volume mount
        zeek_volumes = updated_data["services"]["zeek"]["volumes"]
        # For zeek, upload directory is remapped to <zeek_dir>/upload
        self.assertIn(f"{os.path.join(custom_zeek, 'upload')}:/zeek/upload", zeek_volumes)

    def test_network_configuration_updates(self):
        """Test that network configuration is updated."""
        malcolm_config = MalcolmConfig()
        malcolm_config.set_value(KEY_CONFIG_ITEM_CONTAINER_NETWORK_NAME, "custom_network")

        result = update_compose_files(malcolm_config, self.test_dir, None, MockPlatform(), InstallContext())
        self.assertTrue(result)

        # Verify network configuration
        updated_data = LoadYaml(self.compose_file)

        networks = updated_data.get("networks", {})
        for network_name in networks:
            network_config = networks[network_name]
            self.assertTrue(network_config.get("external"))
            self.assertEqual(network_config.get("name"), "custom_network")


if __name__ == "__main__":
    unittest.main()
