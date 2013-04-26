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
Module for LMI_DiskPartition class.

LMI_DiskPartition
-----------------

.. autoclass:: LMI_DiskPartition
    :members:

"""

from openlmi.storage.ExtentProvider import ExtentProvider
import blivet
import pywbem
import openlmi.storage.util.storage as storage
import openlmi.common.cmpi_logging as cmpi_logging

class LMI_DiskPartition(ExtentProvider):
    """
        Provider of LMI_DiskPartition class.
    """

    @cmpi_logging.trace_method
    def __init__(self, *args, **kwargs):
        super(LMI_DiskPartition, self).__init__(
                'LMI_DiskPartition', *args, **kwargs)


    @cmpi_logging.trace_method

    def provides_device(self, device):
        """
            Returns True, if this class is provider for given Anaconda
            StorageDevice class.
        """
        if  isinstance(device, blivet.devices.PartitionDevice):
            if device.disk.format.labelType == 'msdos':
                return True
        return False

    @cmpi_logging.trace_method
    def get_base_devices(self, device):
        if device.isPrimary or device.isExtended:
            return super(LMI_DiskPartition, self).get_base_devices(device)

        # logical partitions depend on the extended partition
        parted_ext = device.disk.format.partedDisk.getExtendedPartition()
        if not parted_ext:
            raise pywbem.CIMError(pywbem.CIM_ERR_FAILED,
                    'Cannot find extended partition for device: ' + device.path)

        ext = self.storage.devicetree.getDeviceByPath(parted_ext.path)
        return [ext, ]


    @cmpi_logging.trace_method

    def enumerate_devices(self):
        """
            Enumerate all StorageDevices, that this provider provides.
        """
        for device in self.storage.partitions:
            if self.provides_device(device):
                yield device

    @cmpi_logging.trace_method
    def get_instance(self, env, model, device=None):
        """
            Add partition-specific properties.
        """
        model = super(LMI_DiskPartition, self).get_instance(env, model, device)
        if not device:
            device = self._get_device(model)

        model['PrimaryPartition'] = device.isPrimary
        if device.isPrimary:
            model['PartitionType'] = self.Values.PartitionType.Primary
        if device.isExtended:
            model['PartitionType'] = self.Values.PartitionType.Extended
        if device.isLogical:
            model['PartitionType'] = self.Values.PartitionType.Logical

        return model

    @cmpi_logging.trace_method
    def do_delete_instance(self, device):
        """
            Really delete given Anaconda StorageDevice.
        """
        storage.log_storage_call("DELETE PARTITION",
                {'device': device})
        storage.remove_partition(self.storage, device)

    class Values(ExtentProvider.Values):
        class PartitionType(object):
            Unknown = pywbem.Uint16(0)
            Primary = pywbem.Uint16(1)
            Extended = pywbem.Uint16(2)
            Logical = pywbem.Uint16(3)
