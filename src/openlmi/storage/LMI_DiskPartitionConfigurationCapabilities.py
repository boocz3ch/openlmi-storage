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
Module for LMI_DiskPartitionConfigurationCapabilities class.

LMI_DiskPartitionConfigurationCapabilities
------------------------------------------

.. autoclass:: LMI_DiskPartitionConfigurationCapabilities
    :members:

"""

from openlmi.storage.CapabilitiesProvider import CapabilitiesProvider
from openlmi.storage.LMI_DiskPartitionConfigurationSetting \
        import LMI_DiskPartitionConfigurationSetting
from openlmi.storage.SettingManager import Setting
import pywbem
import blivet.formats
import parted
import openlmi.common.cmpi_logging as cmpi_logging
import openlmi.storage.util.units as units

class LMI_DiskPartitionConfigurationCapabilities(CapabilitiesProvider):
    """
        LMI_DiskPartitionConfigurationCapabilities provider implementation.
    """

    INSTANCE_ID_MBR = "LMI:LMI_DiskPartitionConfigurationCapabilities:MBR"
    INSTANCE_ID_EMBR = "LMI:LMI_DiskPartitionConfigurationCapabilities:EMBR"
    INSTANCE_ID_GPT = "LMI:LMI_DiskPartitionConfigurationCapabilities:GPT"

    @cmpi_logging.trace_method
    def __init__(self, *args, **kwargs):
        super(LMI_DiskPartitionConfigurationCapabilities, self).__init__(
                "LMI_DiskPartitionConfigurationCapabilities", *args, **kwargs)

        sync_actions = self.Values.SupportedSynchronousActions
        self.instances = [
            {
                    'InstanceID': self.INSTANCE_ID_MBR,
                    'SupportedSettings': [
                            self.Values.SupportedSettings.Partition_Type,
                            self.Values.SupportedSettings.Bootable],
                    'PartitionTableSize': pywbem.Uint32(1),
                    'PartitionStyle': self.Values.PartitionStyle.MBR,
                    'ValidSubPartitionStyles': [
                            self.Values.ValidSubPartitionStyles.EMBR],
                    'MaxNumberOfPartitions': pywbem.Uint16(4),
                    'SupportedSynchronousActions': [
                            sync_actions.CreateOrModifyPartition,
                            sync_actions.SetPartitionStyle],
                    'Caption': "Capabilities of MSDOS style primary " \
                                "partitions.",
                    'MaxCapacity': pywbem.Uint64(units.MAXINT64),
                    'ElementName': 'MBRCapabilities',
                    'OverlapAllowed' : False,
                    # TODO: add Hidden flag? It seems it does not work
                    # on MBR partitions
            },
            {
                    'InstanceID': self.INSTANCE_ID_EMBR,
                    'SupportedSettings': [
                            self.Values.SupportedSettings.Bootable],
                    'PartitionTableSize': pywbem.Uint32(1),
                    'PartitionStyle': self.Values.PartitionStyle.EMBR,
                    'ValidSubPartitionStyles': pywbem.CIMProperty(
                            name='ValidSubPartitionStyles',
                            value=None,
                            type='uint16',
                            array_size=0,
                            is_array=True),
                    'MaxNumberOfPartitions': pywbem.Uint16(2 << 15 - 1),
                    'SupportedSynchronousActions': [
                            sync_actions.CreateOrModifyPartition,
                            sync_actions.SetPartitionStyle],
                    'Caption':
                            "Capabilities of MS-DOS style logical partitions.",
                    'MaxCapacity': pywbem.Uint64(units.MAXINT64),
                    'ElementName': 'EMBRCapabilities',
                    'OverlapAllowed' : False,
            },
            {
                    'InstanceID': self.INSTANCE_ID_GPT,
                    'SupportedSettings': [
                            self.Values.SupportedSettings.Bootable, ],
                    'PartitionTableSize': pywbem.Uint32(68),
                    'PartitionStyle': self.Values.PartitionStyle.GPT,
                    'ValidSubPartitionStyles': pywbem.CIMProperty(
                            name='ValidSubPartitionStyles',
                            value=None,
                            type='uint16',
                            array_size=0,
                            is_array=True),
                    'MaxNumberOfPartitions': pywbem.Uint16(128),
                    'SupportedSynchronousActions': [
                            sync_actions.CreateOrModifyPartition,
                            sync_actions.SetPartitionStyle],
                    'Caption': "Capabilities of GPT partitions.",
                    'MaxCapacity': pywbem.Uint64(units.MAXINT64),
                    'ElementName': 'GPTCapabilities',
                    'OverlapAllowed' : False,
                    CapabilitiesProvider.DEFAULT_CAPABILITY: True,
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

    @cmpi_logging.trace_method
    def create_setting_for_capabilities(self, capabilities):
        """
            Create LMI_*Setting for given capabilities.
            Return CIMInstanceName of the setting or raise CIMError on error.
        """
        setting_id = self.setting_manager.allocate_id(
                'LMI_DiskPartitionConfigurationSetting')
        if not setting_id:
            raise pywbem.CIMError(pywbem.CIM_ERR_FAILED,
                    "Failed to allocate setting InstanceID")

        values = LMI_DiskPartitionConfigurationSetting.Values
        setting = self.setting_manager.create_setting(
                'LMI_DiskPartitionConfigurationSetting',
                Setting.TYPE_TRANSIENT,
                setting_id)
        setting['Bootable'] = False
        setting['ElementName'] = 'CreatedFrom' + capabilities['InstanceID']
        setting['Hidden'] = None
        if (capabilities['PartitionStyle'] == self.Values.PartitionStyle.GPT
                or capabilities['PartitionStyle'] ==
                        self.Values.PartitionStyle.MBR):
            setting['PartitionType'] = values.PartitionType.Primary
        else:
            setting['PartitionType'] = values.PartitionType.Logical

        self.setting_manager.set_setting(
                'LMI_DiskPartitionConfigurationSetting', setting)

        return pywbem.CIMInstanceName(
                classname='LMI_DiskPartitionConfigurationSetting',
                namespace=self.config.namespace,
                keybindings={'InstanceID': setting_id})

    @cmpi_logging.trace_method
    def cim_method_getalignment(self, env, object_name,
                                param_extent=None):
        """
        Implements LMI_DiskPartitionConfigurationCapabilities.GetAlignment()

        Return allignment unit for given StorageExtent (in blocks). New
        partitions and metadata sectors should be aligned to this unit.
        """
        capabilities = self.get_capabilities_for_id(object_name['InstanceID'])
        if not capabilities:
            raise pywbem.CIMError(pywbem.CIM_ERR_NOT_FOUND,
                    "Capabilities not found.")

        if not param_extent:
            raise pywbem.CIMError(pywbem.CIM_ERR_INVALID_PARAMETER,
                    "Parameter Extent must be provided.")
        device = self.provider_manager.get_device_for_name(param_extent)
        if not device:
            raise pywbem.CIMError(pywbem.CIM_ERR_NOT_FOUND,
                    "Extent not found.")
        self.check_capabilities_for_device(device, capabilities)

        if capabilities['PartitionStyle'] == self.Values.PartitionStyle.EMBR:
            device = device.parents[0]

        alignment = device.partedDevice.optimumAlignment.grainSize

        out_params = [pywbem.CIMParameter('alignment', type='uint64',
                value=pywbem.Uint64(alignment))]
        retval = self.Values.GetAlignment.Success
        return (retval, out_params)

    @cmpi_logging.trace_method
    def get_capabilities_for_device(self, device):
        """
            Return capabilities for given StorageDevice
            Return None if it does not have any partition capabilities.
        """

        if isinstance(device, blivet.devices.PartitionDevice):
            if device.isExtended:
                return self.get_capabilities_for_id(self.INSTANCE_ID_EMBR)
            return None

        fmt_class = blivet.formats.disklabel.DiskLabel
        if (not device.format) or (not isinstance(device.format, fmt_class)):
            return None

        if device.format.labelType == "msdos":
            return self.get_capabilities_for_id(self.INSTANCE_ID_MBR)
        if device.format.labelType == "gpt":
            return self.get_capabilities_for_id(self.INSTANCE_ID_GPT)

    @cmpi_logging.trace_method
    def check_capabilities_for_device(self, device, capabilities):
        """
            Check if the capabilities are the right one for the device and
            raise exception if something is wrong.
        """
        if capabilities['PartitionStyle'] == self.Values.PartitionStyle.MBR:
            if (not device.format or not isinstance(
                            device.format,
                            blivet.formats.disklabel.DiskLabel)):
                raise pywbem.CIMError(pywbem.CIM_ERR_INVALID_PARAMETER,
                        "There is no partition table on the Extent.")
            if device.format.labelType != "msdos":
                raise pywbem.CIMError(pywbem.CIM_ERR_INVALID_PARAMETER,
                        "Partition table does not have given Capabilities.")

        elif capabilities['PartitionStyle'] == self.Values.PartitionStyle.GPT:
            if (not device.format or not isinstance(
                            device.format,
                            blivet.formats.disklabel.DiskLabel)):
                raise pywbem.CIMError(pywbem.CIM_ERR_INVALID_PARAMETER,
                        "There is no partition table on the Extent.")
            if device.format.labelType != "gpt":
                raise pywbem.CIMError(pywbem.CIM_ERR_INVALID_PARAMETER,
                        "Partition table does not have given Capabilities.")

        else:
            # the device must be extended partition, find its disk
            if not isinstance(
                    device, blivet.devices.PartitionDevice):
                raise pywbem.CIMError(pywbem.CIM_ERR_INVALID_PARAMETER,
                        "The extent is not an partition.")
            if not device.isExtended:
                raise pywbem.CIMError(pywbem.CIM_ERR_INVALID_PARAMETER,
                        "The extent is not an extended partition.")

        return True

    @cmpi_logging.trace_method
    def cim_method_findpartitionlocation(self, env, object_name,
                                         param_extent=None,
                                         param_size=None):
        """
        Implements LMI_DiskPartitionConfigurationCapabilities
        .FindPartitionLocation()

        This method finds the best place for partition of given size.
        """
        capabilities = self.get_capabilities_for_id(object_name['InstanceID'])
        if not capabilities:
            raise pywbem.CIMError(pywbem.CIM_ERR_NOT_FOUND,
                    "Capabilities not found.")

        # Check parameters
        if not param_extent:
            raise pywbem.CIMError(pywbem.CIM_ERR_INVALID_PARAMETER,
                    "Parameter Extent must be provided.")
        device = self.provider_manager.get_device_for_name(param_extent)
        if not device:
            raise pywbem.CIMError(pywbem.CIM_ERR_NOT_FOUND,
                    "Extent not found.")

        # Check device vs capabilities
        self.check_capabilities_for_device(device, capabilities)

        if capabilities['PartitionStyle'] == self.Values.PartitionStyle.EMBR:
            device = device.parents[0]
            part_type = parted.PARTITION_LOGICAL
        else:
            part_type = parted.PARTITION_NORMAL

        if not param_size:
            grow = True
            size = 1.0
        else:
            grow = False
            size = param_size / (units.MEGABYTE * 1.0)

        # Find the best place
        geometry = blivet.partitioning.getBestFreeSpaceRegion(
                disk=device.format.partedDisk,
                part_type=part_type,
                req_size=size,
                grow=grow)

        if not geometry:
            # No place found
            retval = self.Values.FindPartitionLocation.Not_Enough_Free_Space
            out_params = [pywbem.CIMParameter('size', type='uint64',
                    value=pywbem.Uint64(0))]
            return (retval, out_params)

        retval = self.Values.FindPartitionLocation.Success

        sector_size = device.partedDevice.sectorSize
        new_size = geometry.length * device.partedDevice.sectorSize

        # anaconda returns the whole region size, we should make it smaller
        # to adjust to requested size
        if not grow and new_size > param_size:
            # truncate the end to start + size
            geometry.end = geometry.start + (param_size / sector_size)
            if param_size % sector_size > 0:
                geometry.end = geometry.end + 1
        new_size = (geometry.end - geometry.start) * sector_size

        out_params = [pywbem.CIMParameter('size', type='uint64',
                value=pywbem.Uint64(new_size))]
        out_params += [pywbem.CIMParameter('startingaddress', type='uint64',
                value=pywbem.Uint64(geometry.start))]
        out_params += [pywbem.CIMParameter('endingaddress', type='uint64',
                value=pywbem.Uint64(geometry.end))]
        return (retval, out_params)


    class Values(CapabilitiesProvider.Values):
        class SupportedSettings(object):
            Partition_Type = pywbem.Uint16(1)
            Bootable = pywbem.Uint16(2)
            Hidden = pywbem.Uint16(3)

        class ValidSubPartitionStyles(object):
            Other = pywbem.Uint16(1)
            MBR = pywbem.Uint16(2)
            VTOC = pywbem.Uint16(3)
            GPT = pywbem.Uint16(4)
            EMBR = pywbem.Uint16(4100)

        class SupportedSynchronousActions(object):
            SetPartitionStyle = pywbem.Uint16(2)
            CreateOrModifyPartition = pywbem.Uint16(3)
            # DMTF_Reserved = ..
            # Vendor_Reserved = 0x8000..

        class PartitionStyle(object):
            MBR = pywbem.Uint16(2)
            GPT = pywbem.Uint16(3)
            VTOC = pywbem.Uint16(4)
            PC98 = pywbem.Uint16(4097)
            SUN = pywbem.Uint16(4098)
            MAC = pywbem.Uint16(4099)
            EMBR = pywbem.Uint16(4100)

        class GetAlignment(object):
            Success = pywbem.Uint32(0)
            Not_Supported = pywbem.Uint32(1)
            Failed = pywbem.Uint32(4)

        class FindPartitionLocation(object):
            Success = pywbem.Uint32(0)
            Not_Supported = pywbem.Uint32(1)
            Failed = pywbem.Uint32(4)
            Not_Enough_Free_Space = pywbem.Uint32(100)
