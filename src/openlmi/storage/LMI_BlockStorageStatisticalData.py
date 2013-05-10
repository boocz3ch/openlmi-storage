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
# Authors: Jan Safranek <jsafrane@redhat.com>
# -*- coding: utf-8 -*-
""" Module for LMI_BlockStorageStatisticalData."""

import pywbem
from openlmi.storage.BaseProvider import BaseProvider
import openlmi.common.cmpi_logging as cmpi_logging
import openlmi.storage.util.storage as storage
from openlmi.common import parse_instance_id
import datetime

class LMI_BlockStorageStatisticalData(BaseProvider):
    """
    Provider for LMI_BlockStorageStatisticalData.
    """

    # Expected nr. of columns in /sys/block/xxx/stat
    STAT_ITEM_COUNT = 11
    # Indexes to self._current_stats
    # Number of read I/Os processed
    STAT_READ_COUNT = 0
    # Number of sectors read, in 512 bytes sectors!
    STAT_READ_SECTORS = 2
    # Total wait time for read requests, in milliseconds
    # Beware, this number is multiplied by nr. of waiting requests ->
    # not usable for LMI_BlockStorageStatisticalData.
    STAT_READ_TICKS = 3
    # Number of write I/Os processed
    STAT_WRITE_COUNT = 4
    # Number of sectors written, in 512 bytes sectors!
    STAT_WRITE_SECTORS = 6
    # Total wait time for write requests, in milliseconds
    # Beware, this number is multiplied by nr. of waiting requests ->
    # not usable for LMI_BlockStorageStatisticalData.
    STAT_WRITE_TICKS = 7
    # Total wait time for all requests.
    # This is real time, not multiplied by nr. of requests.
    STAT_ALL_TICKS = 9

    @cmpi_logging.trace_method
    def __init__(self, *args, **kwargs):
        super(LMI_BlockStorageStatisticalData, self).__init__(*args, **kwargs)

    @cmpi_logging.trace_method
    def has_statistics(self, device, broker):
        """
        Determine, if given device should have LMI_BlockStorageStatisticalData
        instance associated.
        :param device: (``StorageDevice``) Device to examine.
        :param broker: (``CIMOMHandle``) CIMOM broker to use, we need to call
            is_subclass().
        """
        devname = self.provider_manager.get_name_for_device(device)
        if not devname:
            return False
        if not broker.is_subclass(
                self.config.namespace,
                "CIM_StorageExtent",
                devname.classname):
            # We provide statistics only for StorageExtents and not Pools
            return False
        return True

    @cmpi_logging.trace_method
    def load_stats(self, device):
        """
        Load statistics from the device.

        :param device; (``StorageDevice``) Device to measure.
        :returns: dictionary property name (string) -> property value.
        """
        statname = "/sys" + device.sysfsPath + "/stat"
        try:
            with open(statname, "rt") as f:
                line = f.readline()
        except IOError:
            # Translate IOError to CIMError to give user more specific message.
            raise pywbem.CIMError(pywbem.CIM_ERR_FAILED,
                    "Cannot read statistics for device %s"
                    % device.path)

        stats = line.split()
        if len(stats) < self.STAT_ITEM_COUNT:
            cmpi_logging.logger.trace_warn(
                    "Cannot parse statistics from %s, got '%s'",
                    statname, line)
            raise pywbem.CIMError(pywbem.CIM_ERR_FAILED,
                    "Cannot parse statistics for device %s"
                    % device.path)

        # Convert the values to integers
        stats = map(int, stats)

        model = pywbem.cim_obj.NocaseDict()
        model['StatisticTime'] = pywbem.CIMDateTime(datetime.datetime.utcnow())
        model['ElementType'] = self.Values.ElementType.Extent

        # Don't forget to convert sectors to KBytes and milliseconds to
        # hundreds of ms.
        model['IOTimeCounter'] = pywbem.Uint64(
                stats[self.STAT_ALL_TICKS] / 100)
        model['KBytesRead'] = pywbem.Uint64(
                stats[self.STAT_READ_SECTORS] / 2)
        model['KBytesWritten'] = pywbem.Uint64(
                stats[self.STAT_WRITE_SECTORS] / 2)
        model['ReadIOs'] = pywbem.Uint64(stats[self.STAT_READ_COUNT])
        model['TotalIOs'] = pywbem.Uint64(
                stats[self.STAT_READ_COUNT]
                + stats[self.STAT_WRITE_COUNT])
        model['WriteIOs'] = pywbem.Uint64(stats[self.STAT_WRITE_COUNT])
        model['KBytesTransferred'] = pywbem.Uint64(
                (stats[self.STAT_READ_SECTORS]
                        + stats[self.STAT_WRITE_SECTORS]) / 2)
        return model

    @cmpi_logging.trace_method
    def enum_instances(self, env, model, keys_only):
        """
            Enumerate instances. Subclasses do not need to override this method,
            as long as enumeration by self.provides_format is sufficient.
        """
        model.path.update({'InstanceID': None})
        broker = env.get_cimom_handle()
        for device in self.storage.devices:
            if not self.has_statistics(device, broker):
                continue
            name = storage.get_persistent_name(device)
            model['InstanceID'] = "LMI:LMI_BlockStorageStatisticalData:" + name

            if keys_only:
                yield model
            else:
                yield self.get_instance(env, model, device)

    @cmpi_logging.trace_method
    def get_device_for_name(self, name):
        """
        Find StorageDevice for given InstanceName. Return None if there is no such
        device.
        :param name: (``CIMInstanceName`` or ``CIMInstance``) InstanceName to
            examine.
        :returns: ``StorageDevice`` Appropriate device or None if the device
            is not found.
        """
        _id = parse_instance_id(
                name['InstanceID'], "LMI_BlockStorageStatisticalData")
        if not _id:
            return None
        device = storage.get_device_for_persistent_name(self.storage, _id)
        return device

    @cmpi_logging.trace_method
    def get_name_for_device(self, device):
        """
        Create CIMInstanceName of LMI_BlockStorageStatisticalData for given
        device.
        :param device: (``StorageDevice`` Device to get name from.
        :returns:  (``CIMInstanceName``) InstanceName, which refers to stats
            of the device.
        """
        name = storage.get_persistent_name(device)
        return pywbem.CIMInstanceName(
                classname="LMI_BlockStorageStatisticalData",
                namespace=self.config.namespace,
                keybindings={
                        'InstanceID':
                            "LMI:LMI_BlockStorageStatisticalData:" + name
                })

    @cmpi_logging.trace_method
    # pylint: disable-msg=W0221
    def get_instance(self, env, model, device=None):
        """
            Get instance.
            Subclasses should override this method, the default implementation
            just check if the instance exists.
        """
        if not device:
            device = self.get_device_for_name(model)
        if not device:
            raise pywbem.CIMError(pywbem.CIM_ERR_NOT_FOUND,
                    "Cannot find device for this InstanceID.")

        model['ElementName'] = device.path
        stats = self.load_stats(device)
        model.update(stats)
        return model

    class Values(object):
        class ElementType(object):
            Computer_System = pywbem.Uint16(2)
            Front_end_Computer_System = pywbem.Uint16(3)
            Peer_Computer_System = pywbem.Uint16(4)
            Back_end_Computer_System = pywbem.Uint16(5)
            Front_end_Port = pywbem.Uint16(6)
            Back_end_Port = pywbem.Uint16(7)
            Volume = pywbem.Uint16(8)
            Extent = pywbem.Uint16(9)
            Disk_Drive = pywbem.Uint16(10)
            Arbitrary_LUs = pywbem.Uint16(11)
            Remote_Replica_Group = pywbem.Uint16(12)
            # DMTF_Reserved = ..
            # Vendor_Specific = 0x8000..

class LMI_StorageElementStatisticalData(BaseProvider):
    """
    Provider for LMI_BlockStorageStatisticalData.
    """
    @cmpi_logging.trace_method
    def __init__(self, block_stat_provider, *args, **kwargs):
        """
        :param block_stat_provider: (``LMI_BlockStorageStatisticalData``)
            Provider instance to use.
        """
        self.block_stat_provider = block_stat_provider
        super(LMI_StorageElementStatisticalData, self).__init__(*args, **kwargs)

    @cmpi_logging.trace_method
    def enum_instances(self, env, model, keys_only):
        """
            Enumerate instances. Subclasses do not need to override this method,
            as long as enumeration by self.provides_format is sufficient.
        """
        model.path.update({'ManagedElement': None, 'Stats': None})
        broker = env.get_cimom_handle()
        for device in self.storage.devices:
            if not self.block_stat_provider.has_statistics(device, broker):
                continue
            model['Stats'] = self.block_stat_provider.get_name_for_device(
                    device)
            model['ManagedElement'] = self.provider_manager.get_name_for_device(
                    device)
            yield model

    @cmpi_logging.trace_method
    # pylint: disable-msg=W0613
    def get_instance(self, env, model):
        """
            Get instance.
            Subclasses should override this method, the default implementation
            just check if the instance exists.
        """
        # Just check that the keys are correct
        device_name = model['ManagedElement']
        device = self.provider_manager.get_device_for_name(device_name)
        if not device:
            raise pywbem.CIMError(pywbem.CIM_ERR_NOT_FOUND,
                    "Cannot find device for ManagedElement.")

        broker = env.get_cimom_handle()
        if not self.block_stat_provider.has_statistics(device, broker):
            raise pywbem.CIMError(pywbem.CIM_ERR_NOT_FOUND,
                    "The ManagedElement has no statistics.")

        device2 = self.block_stat_provider.get_device_for_name(model['Stats'])
        if device != device2:
            raise pywbem.CIMError(pywbem.CIM_ERR_NOT_FOUND,
                    "The ManagedElement is not related to Stats.")
        return model

    @cmpi_logging.trace_method
    def references(self, env, object_name, model, result_class_name, role,
                   result_role, keys_only):
        """Instrument Associations."""
        return self.simple_references(env, object_name, model,
                result_class_name, role, result_role, keys_only,
                "CIM_StorageExtent",
                "LMI_BlockStorageStatisticalData")
