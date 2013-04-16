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
from openlmi.storage.SettingManager import SettingManager, Setting
import openlmi.common.cmpi_logging as cmpi_logging

import logging
import unittest
import os
import shutil

class TestSetting(unittest.TestCase):
    def setUp(self):
        self.directory = os.path.dirname(__file__)
        if not self.directory:
            self.directory = "."

        cmpi_logging.logger = logging.getLogger('openlmi.storage')

        StorageConfiguration.CONFIG_FILE = "/not/existing"
        self.config = StorageConfiguration()

    def test_missing(self):
        """
            Test loading persistent and preconfigured setting when appropriate
            directories are missing.
        """
        self.config.CONFIG_PATH = self.directory + "/configs/missing/etc/"
        self.config.PERSISTENT_PATH = self.directory + "/configs/missing/var/"

        mgr = SettingManager(self.config)
        mgr.load()

        self.assertDictEqual(mgr.classes, {})

    def test_empty(self):
        """
            Test loading persistent and preconfigured setting when appropriate
            directories are empty.
        """
        self.config.CONFIG_PATH = self.directory + "/configs/empty/etc/"
        self.config.PERSISTENT_PATH = self.directory + "/configs/empty/var/"

        mgr = SettingManager(self.config)
        mgr.load()

        self.assertDictEqual(mgr.classes, {})

    def test_full(self):
        """
            Test loading persistent and preconfigured setting when appropriate
            directories are empty.
        """
        self.config.CONFIG_PATH = self.directory + "/configs/full/etc/"
        self.config.PERSISTENT_PATH = self.directory + "/configs/full/var/"

        mgr = SettingManager(self.config)
        mgr.load()

        # check LMI_StorageSetting class loaded OK
        self.assertTrue(mgr.classes.has_key("LMI_StorageSetting"))
        # check it has all instances
        settings = mgr.get_settings("LMI_StorageSetting")
        self.assertIn("LMI:StorageSetting:preconfigured1", settings.keys())
        self.assertIn("LMI:StorageSetting:preconfigured2", settings.keys())
        self.assertIn("LMI:StorageSetting:persistent1", settings.keys())
        self.assertIn("LMI:StorageSetting:persistent2", settings.keys())
        self.assertEqual(len(settings.keys()), 4)

        # check one preconfigured setting
        s1 = settings['LMI:StorageSetting:preconfigured1']
        self.assertEqual(s1.the_id, "LMI:StorageSetting:preconfigured1")
        self.assertEqual(s1.type, Setting.TYPE_PRECONFIGURED)
        self.assertEqual(s1['first'], "1")
        self.assertEqual(s1['second'], "two")
        self.assertEqual(s1['third'], "3.0")

        # check one persistent setting
        s2 = settings['LMI:StorageSetting:persistent2']
        self.assertEqual(s2.the_id, "LMI:StorageSetting:persistent2")
        self.assertEqual(s2.type, Setting.TYPE_PERSISTENT)
        self.assertEqual(s2['first'], "1000")
        self.assertEqual(s2['second'], "two thousand")
        self.assertEqual(s2['third'], "3000.0")

    def test_save_load(self):
        """ Test saving a persistent settings and loading them back."""
        # load the 'full' settings
        self.config.CONFIG_PATH = self.directory + "/configs/full/etc/"
        self.config.PERSISTENT_PATH = self.directory + "/configs/full/var/"

        mgr = SettingManager(self.config)
        mgr.load()

        # dirty hack to save it to different directory...
        self.config.PERSISTENT_PATH = self.directory + "/configs/save_load/var/"

        # add one transient setting
        s = Setting(mgr, 'LMI_StorageSetting',
                Setting.TYPE_TRANSIENT, "LMI:StorageSetting:transient1")
        s['first'] = "111"
        s['second'] = "two two two"
        s['third'] = "333.0"
        mgr.set_setting("LMI_StorageSetting", s)

        # add one preconfigured setting (this should not happen in reality,
        # but let's test it).
        s = Setting(mgr, 'LMI_StorageSetting',
                Setting.TYPE_PRECONFIGURED, "LMI:StorageSetting:preconfigured3")
        s['first'] = "1111"
        s['second'] = "two two two two"
        s['third'] = "3333.0"
        mgr.set_setting("LMI_StorageSetting", s)

        # add one persistent setting
        s = Setting(mgr, 'LMI_StorageSetting',
                Setting.TYPE_PERSISTENT, "LMI:StorageSetting:persistent3")
        s['first'] = "11"
        s['second'] = "two two"
        s['third'] = "33.0"
        mgr.set_setting("LMI_StorageSetting", s)

        # the persistent setting should be saved
        # try to reload the cofig - it should remove the preconfigured one
        mgr.load()

        # check it has all instances and that the preconfigured is gone
        settings = mgr.get_settings("LMI_StorageSetting")
        self.assertIn("LMI:StorageSetting:preconfigured1", settings.keys())
        self.assertIn("LMI:StorageSetting:preconfigured2", settings.keys())
        self.assertIn("LMI:StorageSetting:persistent1", settings.keys())
        self.assertIn("LMI:StorageSetting:persistent2", settings.keys())
        self.assertIn("LMI:StorageSetting:persistent3", settings.keys())
        self.assertIn("LMI:StorageSetting:transient1", settings.keys())
        self.assertEqual(len(settings.keys()), 6)

        # check the transient is ok
        s1 = settings['LMI:StorageSetting:transient1']
        self.assertEqual(s1.the_id, "LMI:StorageSetting:transient1")
        self.assertEqual(s1.type, Setting.TYPE_TRANSIENT)
        self.assertEqual(s1['first'], "111")
        self.assertEqual(s1['second'], "two two two")
        self.assertEqual(s1['third'], "333.0")

        # check the persistent is there
        s2 = settings['LMI:StorageSetting:persistent3']
        self.assertEqual(s2.the_id, "LMI:StorageSetting:persistent3")
        self.assertEqual(s2.type, Setting.TYPE_PERSISTENT)
        self.assertEqual(s2['first'], "11")
        self.assertEqual(s2['second'], "two two")
        self.assertEqual(s2['third'], "33.0")

        # remove one persistent, it should be saved imediatelly
        mgr.delete_setting('LMI_StorageSetting', s2)
        # check it is really removed
        mgr = SettingManager(self.config)
        mgr.load()
        settings = mgr.get_settings("LMI_StorageSetting")
        self.assertNotIn("LMI:StorageSetting:persistent3", settings.keys())

        # change one persistent, it should be saved imediatelly
        s3 = settings['LMI:StorageSetting:persistent2']
        s3['first'] = "-1"
        s3['second'] = "minus one"
        s3['third'] = "-3.0"
        mgr.set_setting('LMI_StorageSetting', s3)
        # check it is really removed
        mgr = SettingManager(self.config)
        mgr.load()
        settings = mgr.get_settings("LMI_StorageSetting")
        s3 = settings['LMI:StorageSetting:persistent2']
        self.assertEqual(s3.the_id, "LMI:StorageSetting:persistent2")
        self.assertEqual(s3.type, Setting.TYPE_PERSISTENT)
        self.assertEqual(s3['first'], "-1")
        self.assertEqual(s3['second'], "minus one")
        self.assertEqual(s3['third'], "-3.0")


    def tearDown(self):
        # remove any files in configs/save_load/var/
        path = self.directory + "/configs/save_load/var/"
        shutil.rmtree(path, ignore_errors=True)



if __name__ == '__main__':
    unittest.main()
