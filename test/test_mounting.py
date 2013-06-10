#!/usr/bin/python
# -*- Coding:utf-8 -*-
#
# Copyright (C) 2013 Red Hat, Inc.  All rights reserved.
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
# Authors: Jan Synacek <jsynacek@redhat.com>


from test_base import StorageTestBase
import unittest
import pywbem

class TestMounting(StorageTestBase):
    def setUp(self):
        super(TestMounting, self).setUp()

        self.service = self.wbemconnection.EnumerateInstanceNames("LMI_MountConfigurationService")[0]
        self.capability = self.wbemconnection.EnumerateInstanceNames("LMI_MountedFileSystemCapabilities")[0]

    def tearDown(self):
        pass

    def _create_setting(self):
        (ret, outparams) = self.wbemconnection.InvokeMethod('CreateSetting', self.capability)
        self.assertEqual(ret, 0)
        return outparams['setting']

    def _mount(self, mnt_point, partition, fstype='ext4'):
        setting_name = self._create_setting()
        assoc_elems = self.wbemconnection.ExecQuery("WQL",
                                                    'select * from LMI_FileSystemSetting where \
                                                    InstanceID="LMI:LMI_FileSystemSetting:%s"' % (partition))
        if not assoc_elems:
            self.fail("No associations with '%s'" % (partition))

        fs_name = self.wbemconnection.AssociatorNames(assoc_elems[0].path)[0]

        (ret, outparams) = self.invoke_async_method(
            "CreateMount",
            self.service,
            int,
            Goal=setting_name,
            FileSystemType=fstype,
            Mode=pywbem.Uint16(32768),
            FileSystem=fs_name,
            MountPoint=mnt_point,
            FileSystemSpec=partition)

        # 0 - Completed with no error
        # 4096 - Method parameters checked, job started
        self.assertIn(ret, (0, 4096))
        # XXX outparams is always {} here, even though mounting was successful. BUG?

    def _modify_mount(self, something):
        # TBI
        pass

    def _umount(self, mnt_point, partition, fstype='ext4'):
        mnt_name = pywbem.CIMInstanceName(classname='LMI_MountedFileSystem',
                                          namespace='root/cimv2',
                                          keybindings={'MountPointPath':mnt_point,
                                                       'FileSystemType':fstype,
                                                       'FileSystemSpec':partition})

        (ret, outparams) = self.invoke_async_method("DeleteMount",
                                                    self.service,
                                                    int,
                                                    Mount=mnt_name,
                                                    Mode=pywbem.Uint16(32769)
                                                    )

        self.assertEqual(ret, 0)
        self.assertEqual(outparams, {})

    def test_simple_mount(self):
        # there is no assertNotRaises...
        try:
            self._mount(self.mnt_dir, self.mnt_partition, self.mnt_fstype)
        except pywbem.CIMError as pe:
            self.fail(pe[1])

    def test_simple_umount(self):
        # there is no assertNotRaises...
        try:
            self._umount(self.mnt_dir, self.mnt_partition, self.mnt_fstype)
        except pywbem.CIMError as pe:
            self.fail(pe[1])

    def test_mount_wrong_dir(self):
        self.assertRaises(pywbem.CIMError,
                          self._mount,
                          '/no/such/dir',
                          self.mnt_partition,
                          self.mnt_fstype
                          )

    def test_umount_wrong_dir(self):
        self.assertRaises(pywbem.CIMError,
                          self._umount,
                          '/no/such/dir',
                          self.mnt_partition,
                          self.mnt_fstype
                          )

    def test_mount_wrong_partition(self):
        self.assertRaisesRegexp(AssertionError,
                                '^No associations with .*$',
                                self._mount,
                                self.mnt_dir,
                                '/no/such/partition',
                                self.mnt_fstype
                                 )

    def test_umount_wrong_partition(self):
        self.assertRaises(pywbem.CIMError,
                          self._umount,
                          self.mnt_dir,
                          '/no/such/partition',
                          self.mnt_fstype
                          )

    def test_mount_wrong_fstype(self):
        self.assertRaises(pywbem.CIMError,
                          self._mount,
                          self.mnt_dir,
                          self.mnt_partition,
                          'no-such-fs'
                          )

    def test_umount_wrong_fstype(self):
        self.assertRaises(pywbem.CIMError,
                          self._umount,
                          self.mnt_dir,
                          self.mnt_partition,
                          'no-such-fs'
                          )

    # def test_mount_own_setting(self):
    #     # TBI
    #     pass

if __name__ == '__main__':
    unittest.main()
