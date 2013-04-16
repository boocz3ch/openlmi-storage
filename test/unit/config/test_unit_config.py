# Copyright (C) 2012 Red Hat, Inc.  All rights reserved.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
#
# Authors: Jan Safranek <jsafrane@redhat.com>
# -*- coding: utf-8 -*-

from openlmi.storage.StorageConfiguration import StorageConfiguration
import openlmi.common.cmpi_logging as cmpi_logging
import unittest

import logging
import socket
import os

class TestConfig(unittest.TestCase):
    def setUp(self):
        self.directory = os.path.dirname(__file__)
        if not self.directory:
            self.directory = "."
        cmpi_logging.logger = logging.getLogger('openlmi.storage')

    def test_missing(self):
        """ Test configuration when CONFIG_FILE cannot be found."""

        StorageConfiguration.CONFIG_PATH = self.directory
        StorageConfiguration.CONFIG_FILE = self.directory + "/configs/not-existing.conf"
        cfg = StorageConfiguration()

        # cfg must exists
        self.assertTrue(cfg)

        # cfg must return default values
        self.assertEqual(cfg.namespace, "root/cimv2")
        self.assertEqual(cfg.system_class_name, "Linux_ComputerSystem")
        self.assertEqual(cfg.system_name, socket.getfqdn())

    def test_empty(self):
        """ Test configuration when CONFIG_FILE is empty."""
        StorageConfiguration.CONFIG_PATH = self.directory
        StorageConfiguration.CONFIG_FILE = self.directory + "/configs/empty.conf"
        cfg = StorageConfiguration()

        # cfg must exists
        self.assertTrue(cfg)

        # cfg must return default values
        self.assertEqual(cfg.namespace, "root/cimv2")
        self.assertEqual(cfg.system_class_name, "Linux_ComputerSystem")
        self.assertEqual(cfg.system_name, socket.getfqdn())

    def test_full(self):
        """ Test configuration when CONFIG_FILE is complete."""
        StorageConfiguration.CONFIG_PATH = self.directory
        StorageConfiguration.CONFIG_FILE = self.directory + "/configs/complete.conf"
        cfg = StorageConfiguration()

        # cfg must exists
        self.assertTrue(cfg)

        # cfg must NOT return default values
        self.assertEqual(cfg.namespace, "root/my/namespace")
        self.assertEqual(cfg.system_class_name, "My_ComputerSystem")
        self.assertEqual(cfg.system_name, socket.getfqdn())

    def tearDown(self):
        pass

if __name__ == '__main__':
    unittest.main()
