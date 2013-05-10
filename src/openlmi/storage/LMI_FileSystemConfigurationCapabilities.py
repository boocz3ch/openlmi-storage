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
""""
Module for LMI_FileSystemConfigurationCapabilities class.

LMI_FileSystemConfigurationCapabilities
---------------------------------------

.. autoclass:: LMI_FileSystemConfigurationCapabilities
    :members:

"""

from openlmi.storage.CapabilitiesProvider import CapabilitiesProvider
import pywbem
import openlmi.common.cmpi_logging as cmpi_logging

class LMI_FileSystemConfigurationCapabilities(CapabilitiesProvider):
    """
        LMI_FileSystemConfigurationCapabilities provider implementation.
    """

    INSTANCE_ID = "LMI:LMI_FileSystemConfigurationCapabilities:instance"
    @cmpi_logging.trace_method
    def __init__(self, *args, **kwargs):
        super(LMI_FileSystemConfigurationCapabilities, self).__init__(
                "LMI_FileSystemConfigurationCapabilities", *args, **kwargs)

        methods = self.Values.SupportedAsynchronousMethods
        fs = self.Values.SupportedActualFileSystemTypes
        availability = self.Values.InitialAvailability
        self.instances = [
            {
                    'InstanceID': self.INSTANCE_ID,
                    'SupportedActualFileSystemTypes': [
                            fs.EXT2,
                            fs.EXT3,
                            fs.EXT4,
                            fs.XFS, ],
                    'SupportedSynchronousMethods': pywbem.CIMProperty(
                            name='SupportedSynchronousMethods',
                            value=None,
                            type='uint16',
                            array_size=0,
                            is_array=True),
                    'SupportedAsynchronousMethods':
                            [methods.LMI_CreateFileSystem],
                    'InitialAvailability':  availability.Unmounted
            },
    ]


    @cmpi_logging.trace_method
    def enumerate_capabilities(self):
        """
            Return an iterable with all capabilities instances, i.e.
            dictionaries property_name -> value.
            If the capabilities are the default ones, it must have
            '_default' as a property name.
        """

        return self.instances

    class Values(CapabilitiesProvider.Values):
        class SupportedActualFileSystemTypes(object):
            Unknown = pywbem.Uint16(0)
            UFS = pywbem.Uint16(2)
            HFS = pywbem.Uint16(3)
            FAT = pywbem.Uint16(4)
            FAT16 = pywbem.Uint16(5)
            FAT32 = pywbem.Uint16(6)
            NTFS4 = pywbem.Uint16(7)
            NTFS5 = pywbem.Uint16(8)
            XFS = pywbem.Uint16(9)
            AFS = pywbem.Uint16(10)
            EXT2 = pywbem.Uint16(11)
            EXT3 = pywbem.Uint16(12)
            REISERFS = pywbem.Uint16(13)
            EXT4 = pywbem.Uint16(0x8001)
            BTRFS = pywbem.Uint16(0x8002)
            JFS = pywbem.Uint16(0x8003)
            TMPFS = pywbem.Uint16(0x8004)
            VFAT = pywbem.Uint16(0x8005)

        class SupportedAsynchronousMethods(object):
            CreateFileSystem = pywbem.Uint16(2)
            DeleteFileSystem = pywbem.Uint16(3)
            ModifyFileSystem = pywbem.Uint16(4)
            CreateGoal = pywbem.Uint16(5)
            GetRequiredStorageSize = pywbem.Uint16(6)
            # DMTF_Reserved = ..
            LMI_CreateFileSystem = pywbem.Uint16(0x8001)

        class SupportedSynchronousMethods(object):
            CreateFileSystem = pywbem.Uint16(2)
            DeleteFileSystem = pywbem.Uint16(3)
            ModifyFileSystem = pywbem.Uint16(4)
            CreateGoal = pywbem.Uint16(5)
            GetRequiredStorageSize = pywbem.Uint16(6)
            # DMTF_Reserved = ..
            LMI_CreateFileSystem = pywbem.Uint16(0x8001)

        class InitialAvailability(object):
            Unknown = pywbem.Uint16(0)
            Mounted = pywbem.Uint16(2)
            Unmounted = pywbem.Uint16(3)
            # DMTF_Reserved = ..
            # Vendor_Defined = 0x8000..
