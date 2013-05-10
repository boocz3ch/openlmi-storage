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
from openlmi.storage.ServiceProvider import ServiceProvider
from openlmi.storage.CapabilitiesProvider import CapabilitiesProvider
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
        model['ElementName'] = device.path
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
            EnumerateInstances provider method.
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
            GetInstance method provider.
        """
        if not device:
            device = self.get_device_for_name(model)
        if not device:
            raise pywbem.CIMError(pywbem.CIM_ERR_NOT_FOUND,
                    "Cannot find device for this InstanceID.")

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
            EnumerateInstances provider method.
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
            GetInstance method provider.
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

class LMI_StorageStatisticsCollection(BaseProvider):
    """
    Provider of LMI_StorageStatisticsCollection. There is only one instance
    of LMI_StorageStatisticsCollection on the system.
    """
    INSTANCE_ID = "LMI:LMI_StorageStatisticsCollection:instance"

    @cmpi_logging.trace_method
    def __init__(self, *args, **kwargs):
        super(LMI_StorageStatisticsCollection, self).__init__(*args, **kwargs)

    @cmpi_logging.trace_method
    def enum_instances(self, env, model, keys_only):
        """
            EnumerateInstances provider method.
        """
        model.path.update({'InstanceID': None})
        model['InstanceID'] = self.INSTANCE_ID
        if keys_only:
            yield model
        else:
            yield self.get_instance(env, model)

    @cmpi_logging.trace_method
    # pylint: disable-msg=W0613
    def get_instance(self, env, model):
        """
            GetInstance method provider.
        """
        if model['InstanceID'] != self.INSTANCE_ID:
            raise pywbem.CIMError(pywbem.CIM_ERR_NOT_FOUND,
                    "Unknown InstanceID.")
        # 0 = no fixed sampling interval
        model['SampleInterval'] = pywbem.CIMDateTime(datetime.timedelta(0))
        return model

class LMI_MemberOfStorageStatisticsCollection(BaseProvider):
    @cmpi_logging.trace_method
    def __init__(self, block_stat_provider, *args, **kwargs):
        """
        :param block_stat_provider: (``LMI_BlockStorageStatisticalData``)
            Provider instance to use.
        """
        self.block_stat_provider = block_stat_provider
        super(LMI_MemberOfStorageStatisticsCollection, self).__init__(
                *args, **kwargs)

    @cmpi_logging.trace_method
    def enum_instances(self, env, model, keys_only):
        """
            EnumerateInstances provider method.
        """
        model.path.update({'Collection': None, 'Member': None})
        broker = env.get_cimom_handle()
        for device in self.storage.devices:
            if not self.block_stat_provider.has_statistics(device, broker):
                continue
            model['Collection'] = pywbem.CIMInstanceName(
                    classname="LMI_StorageStatisticsCollection",
                    namespace=self.config.namespace,
                    keybindings={
                        'InstanceID' :
                            LMI_StorageStatisticsCollection.INSTANCE_ID
                    })
            model['Member'] = self.block_stat_provider.get_name_for_device(
                    device)
            yield model

    @cmpi_logging.trace_method
    # pylint: disable-msg=W0613
    def get_instance(self, env, model):
        """
            GetInstance method provider.
        """
        # Just check instance keys
        if model['Collection'] ['InstanceID'] != \
                LMI_StorageStatisticsCollection.INSTANCE_ID:
            raise pywbem.CIMError(pywbem.CIM_ERR_NOT_FOUND,
                    "Unknown Collection InstanceID.")
        device = self.block_stat_provider.get_device_for_name(model['Member'])
        if not device:
            raise pywbem.CIMError(pywbem.CIM_ERR_NOT_FOUND,
                    "Unknown Member.")
        broker = env.get_cimom_handle()
        if not self.block_stat_provider.has_statistics(device, broker):
            raise pywbem.CIMError(pywbem.CIM_ERR_NOT_FOUND,
                    "Member is not part of the Collection.")
        return model

    @cmpi_logging.trace_method
    def references(self, env, object_name, model, result_class_name, role,
                   result_role, keys_only):
        """Instrument Associations."""
        return self.simple_references(env, object_name, model,
                result_class_name, role, result_role, keys_only,
                "LMI_BlockStorageStatisticalData",
                "LMI_StorageStatisticsCollection")

class LMI_HostedStorageStatisticsCollection(BaseProvider):
    """
    Provider of LMI_HostedStorageStatisticsCollection. There is only one instance
    of LMI_HostedStorageStatisticsCollection on the system.
    """

    @cmpi_logging.trace_method
    def __init__(self, *args, **kwargs):
        super(LMI_HostedStorageStatisticsCollection, self).__init__(
                *args, **kwargs)

    @cmpi_logging.trace_method
    def enum_instances(self, env, model, keys_only):
        """
            EnumerateInstances provider method.
        """
        model.path.update({'Antecedent': None, 'Dependent': None})
        model['Antecedent'] = pywbem.CIMInstanceName(
                    classname=self.config.system_class_name,
                    namespace=self.config.namespace,
                    keybindings={
                            'CreationClassName' : self.config.system_class_name,
                            'Name' : self.config.system_name,
                    })

        model['Dependent'] = pywbem.CIMInstanceName(
                    classname="LMI_StorageStatisticsCollection",
                    namespace=self.config.namespace,
                    keybindings={
                        'InstanceID' :
                            LMI_StorageStatisticsCollection.INSTANCE_ID
                    })
        yield model

    @cmpi_logging.trace_method
    # pylint: disable-msg=W0613
    def get_instance(self, env, model):
        """
            GetInstance method provider.
        """
        # just check keys
        system = model['Antecedent']
        if (system['CreationClassName'] != self.config.system_class_name
                or system['Name'] != self.config.system_name):
            raise pywbem.CIMError(pywbem.CIM_ERR_NOT_FOUND,
                    "Wrong Antecedent keys.")
        if model['Dependent'] ['InstanceID'] != \
                LMI_StorageStatisticsCollection.INSTANCE_ID:
            raise pywbem.CIMError(pywbem.CIM_ERR_NOT_FOUND,
                    "Unknown Dependent InstanceID.")
        return model

    @cmpi_logging.trace_method
    def references(self, env, object_name, model, result_class_name, role,
                   result_role, keys_only):
        """Instrument Associations."""
        return self.simple_references(env, object_name, model,
                result_class_name, role, result_role, keys_only,
                "CIM_System",
                "LMI_StorageStatisticsCollection")

class LMI_BlockStatisticsManifestCollection(BaseProvider):
    """
    Provider of LMI_BlockStatisticsManifestCollection. There is only one instance
    of LMI_BlockStatisticsManifestCollection on the system, we don't allow
    user-specified manifests.
    """
    INSTANCE_ID = "LMI:LMI_BlockStatisticsManifestCollection:instance"

    @cmpi_logging.trace_method
    def __init__(self, *args, **kwargs):
        super(LMI_BlockStatisticsManifestCollection, self).__init__(
                *args, **kwargs)

    @cmpi_logging.trace_method
    def enum_instances(self, env, model, keys_only):
        """
            EnumerateInstances provider method.
        """
        model.path.update({'InstanceID': None})
        model['InstanceID'] = self.INSTANCE_ID
        if keys_only:
            yield model
        else:
            yield self.get_instance(env, model)

    @cmpi_logging.trace_method
    # pylint: disable-msg=W0613
    def get_instance(self, env, model):
        """
            GetInstance method provider.
        """
        if model['InstanceID'] != self.INSTANCE_ID:
            raise pywbem.CIMError(pywbem.CIM_ERR_NOT_FOUND,
                    "Unknown InstanceID.")
        model['IsDefault'] = True
        return model

class LMI_BlockStatisticsManifest(BaseProvider):
    """
    Provider of LMI_BlockStatisticsManifest. We don't allow
    user-specified manifests.
    """

    # Sequence of columns in CSV format returned by
    # LMI_BlockStatisticsService.GetStatisticsCollection().
    CSV_SEQUENCE = [
            'InstanceID',
            'ElementType',
            'StatisticTime',
            'IOTimeCounter',
            'KBytesRead',
            'KBytesTransferred',
            'KBytesWritten',
            'ReadIOs',
            'TotalIOs',
            'WriteIOs',
        ]

    @cmpi_logging.trace_method
    def __init__(self, *args, **kwargs):
        super(LMI_BlockStatisticsManifest, self).__init__(
                *args, **kwargs)
        # The manifests are static, we keep them in dictionary
        # InstanceID -> { property name -> property value }
        extent = LMI_BlockStorageStatisticalData.Values.ElementType.Extent
        self.manifests = {
                'LMI:LMI_BlockStatisticsManifest:Extent' : {
                    'ElementType': extent,
                    'IncludeIdleTimeCounter': False,
                    'IncludeIOTimeCounter': True,
                    'IncludeKBytesRead': True,
                    'IncludeKBytesTransferred': True,
                    'IncludeKBytesWritten': True,
                    'IncludeMaintOp': False,
                    'IncludeMaintTimeCounter': False,
                    'IncludeReadHitIOs': False,
                    'IncludeReadHitIOTimeCounter': False,
                    'IncludeReadIOs': True,
                    'IncludeReadIOTimeCounter': False,
                    'IncludeStartStatisticTime': False,
                    'IncludeStatisticTime': True,
                    'IncludeTotalIOs': True,
                    'IncludeWriteHitIOs': False,
                    'IncludeWriteHitIOTimeCounter': False,
                    'IncludeWriteIOs': True,
                    'IncludeWriteIOTimeCounter': False,
                    'CSVSequence': self.CSV_SEQUENCE
                }
        }

    @cmpi_logging.trace_method
    def enum_instances(self, env, model, keys_only):
        """
            EnumerateInstances provider method.
        """
        model.path.update({'InstanceID': None})
        for key in self.manifests.iterkeys():
            model['InstanceID'] = key
            if keys_only:
                yield model
            else:
                yield self.get_instance(env, model)

    @cmpi_logging.trace_method
    # pylint: disable-msg=W0613
    def get_instance(self, env, model):
        """
            GetInstance method provider.
        """
        manifest = self.manifests.get(model['InstanceID'], None)
        if not manifest:
            raise pywbem.CIMError(pywbem.CIM_ERR_NOT_FOUND,
                    "Unknown InstanceID.")
        model.update(manifest)
        return model

class LMI_MemberOfBlockStatisticsManifestCollection(BaseProvider):
    """
    Provider of LMI_MemberOfBlockStatisticsManifestCollection.
    """
    @cmpi_logging.trace_method
    def __init__(self, manifest_provider, *args, **kwargs):
        """
        :param manifest_provider: (``LMI_BlockStatisticsManifest``)
            Provider instance to use.
        """
        self.manifest_provider = manifest_provider
        super(LMI_MemberOfBlockStatisticsManifestCollection, self).__init__(
                *args, **kwargs)

    @cmpi_logging.trace_method
    def enum_instances(self, env, model, keys_only):
        """
            EnumerateInstances provider method.
        """
        model.path.update({'Collection': None, 'Member': None})

        manifest_model = pywbem.CIMInstance(
                classname='LMI_BlockStatisticsManifest',
                path=pywbem.CIMInstanceName(
                        classname='LMI_BlockStatisticsManifest',
                        namespace=self.config.namespace))

        for manifest in self.manifest_provider.enum_instances(
                env, manifest_model, True):
            model['Collection'] = pywbem.CIMInstanceName(
                    classname="LMI_BlockStatisticsManifestCollection",
                    namespace=self.config.namespace,
                    keybindings={
                        'InstanceID' :
                            LMI_BlockStatisticsManifestCollection.INSTANCE_ID
                    })
            model['Member'] = manifest.path
            yield model

    @cmpi_logging.trace_method
    # pylint: disable-msg=W0613
    def get_instance(self, env, model):
        """
            GetInstance method provider.
        """
        # Just check instance keys
        if model['Collection'] ['InstanceID'] != \
                LMI_BlockStatisticsManifestCollection.INSTANCE_ID:
            raise pywbem.CIMError(pywbem.CIM_ERR_NOT_FOUND,
                    "Unknown Collection InstanceID.")
        # get_instance will throw Not Found error if the Member is wrong:
        _manifest_model = self.manifest_provider.get_instance(
                env, model['Member'])
        return model

    @cmpi_logging.trace_method
    def references(self, env, object_name, model, result_class_name, role,
                   result_role, keys_only):
        """Instrument Associations."""
        return self.simple_references(env, object_name, model,
                result_class_name, role, result_role, keys_only,
                "LMI_BlockStatisticsManifestCollection",
                "LMI_BlockStatisticsManifest")

class LMI_AssociatedBlockStatisticsManifestCollection(BaseProvider):
    """
    Provider of LMI_AssociatedBlockStatisticsManifestCollection.
    There should be only one LMI_AssociatedBlockStatisticsManifestCollection
    instance, since we have only one ManifestCollection.
    """
    @cmpi_logging.trace_method
    def __init__(self, *args, **kwargs):
        super(LMI_AssociatedBlockStatisticsManifestCollection, self).__init__(
                *args, **kwargs)

    @cmpi_logging.trace_method
    def enum_instances(self, env, model, keys_only):
        """
            EnumerateInstances provider method.
        """
        model.path.update({'Statistics': None, 'ManifestCollection': None})

        model['ManifestCollection'] = pywbem.CIMInstanceName(
                classname="LMI_BlockStatisticsManifestCollection",
                namespace=self.config.namespace,
                keybindings={
                    'InstanceID' :
                        LMI_BlockStatisticsManifestCollection.INSTANCE_ID
                })
        model['Statistics'] = pywbem.CIMInstanceName(
                    classname="LMI_StorageStatisticsCollection",
                    namespace=self.config.namespace,
                    keybindings={
                        'InstanceID' :
                            LMI_StorageStatisticsCollection.INSTANCE_ID
                    })
        yield model

    @cmpi_logging.trace_method
    # pylint: disable-msg=W0613
    def get_instance(self, env, model):
        """
            GetInstance method provider.
        """
        # Just check instance keys
        if model['Statistics'] ['InstanceID'] != \
                LMI_StorageStatisticsCollection.INSTANCE_ID:
            raise pywbem.CIMError(pywbem.CIM_ERR_NOT_FOUND,
                    "Unknown Dependent InstanceID.")
        if model['ManifestCollection'] ['InstanceID'] != \
                LMI_BlockStatisticsManifestCollection.INSTANCE_ID:
            raise pywbem.CIMError(pywbem.CIM_ERR_NOT_FOUND,
                    "Unknown Dependent InstanceID.")
        return model

    @cmpi_logging.trace_method
    def references(self, env, object_name, model, result_class_name, role,
                   result_role, keys_only):
        """Instrument Associations."""
        return self.simple_references(env, object_name, model,
                result_class_name, role, result_role, keys_only,
                "LMI_BlockStatisticsManifestCollection",
                "LMI_StorageStatisticsCollection")

class LMI_BlockStatisticsService(ServiceProvider):
    """
        LMI_BlockStatisticsService provider implementation.
    """
    # Maximum size of Statistics[] item in GetStatisticsCollection() method.
    # SMI-S says it should be less than 64 kB
    MAXCHUNK = 65535

    @cmpi_logging.trace_method
    def __init__(self, block_stat_provider, *args, **kwargs):
        """
        :param block_stat_provider: (``LMI_BlockStorageStatisticalData``)
            Provider instance to use.
        """
        self.block_stat_provider = block_stat_provider
        super(LMI_BlockStatisticsService, self).__init__(
                "LMI_BlockStatisticsService", *args, **kwargs)

    @cmpi_logging.trace_method
    def _get_statistics_line(self, device):
        """
        Return line for Statistics[] parameter of
        LMI_BlockStatisticsService.GetStatisticsCollection()
        for given device.

        The line is semicolon-separated list of values of properties as listed
        in associated LMI_BlockStatisticsManifest.

        :param device: (``StorageDevice``) Device to examine.
        :returns: ``string`` with device statistics.
        """
        stats = self.block_stat_provider.load_stats(device)
        # Add missing InstanceID property
        name = storage.get_persistent_name(device)
        stats['InstanceID'] = "LMI:LMI_BlockStorageStatisticalData:" + name

        columns = []
        for name in LMI_BlockStatisticsManifest.CSV_SEQUENCE:
            columns.append(str(stats[name]))
        return ";".join(columns)

    @cmpi_logging.trace_method
    def cim_method_getstatisticscollection(self, env, object_name,
                                           param_manifestcollection=None,
                                           param_statisticsformat=None,
                                           param_elementtypes=None,
                                           param_statistics=None):
        """Implements LMI_BlockStatisticsService.GetStatisticsCollection()

        Retrieves statistics in a well-defined bulk format. The collection
        of statistics returned is determined by the list of element types
        passed in to the method and the manifests for those types
        contained in the supplied BlockStatisticsManifestCollection. If
        both the Elements and BlockStatisticsManifestCollection parameters
        are supplied, then the types of elements returned is an
        intersection of the element types listed in the Elements parameter
        and the types for which BlockStatisticsManifest instances exist in
        the supplied BlockStatisticsManifestCollection. The statistics are
        returned through a well-defined array of strings, whose format is
        specified by the StatisticsFormat parameter, that can be parsed to
        retrieve the desired statistics as well as limited information
        about the elements that those metrics describe.

        param_manifestcollection --  The input parameter ManifestCollection (type REF (pywbem.CIMInstanceName(classname='CIM_BlockStatisticsManifestCollection', ...)) 
            The BlockStatisticsManifestCollection that contains the
            manifests that list the metrics to be returned for each
            element type. If not supplied (i.e. parameter is null), then
            all available statistics will be returned unfiltered. Only
            elements that match the element type properties (if
            meaningful) of the BlockStatisticsManifest instances contained
            within the BlockStatisticsManifestCollection will have data
            returned by this method. If the supplied
            BlockStatisticsManifestCollection does not contain any
            BlockStatisticsManifest instances, then no statistics will be
            returned by this method.
        param_statisticsformat --  The input parameter StatisticsFormat (type pywbem.Uint16 self.Values.GetStatisticsCollection.StatisticsFormat) 
            Specifies the format of the Statistics output parameter.  - CSV
            = Comma Separated Values.
        param_elementtypes --  The input parameter ElementTypes (type [pywbem.Uint16,] self.Values.GetStatisticsCollection.ElementTypes) 
            Element types for which statistics should be returned. If not
            supplied (i.e. parameter is null) this parameter is not
            considered when filtering the instances of StatisticalData
            that will populate the Statistics output parameter. If the
            array is not null, but is empty, then no statistics will be
            returned by this method. A client SHOULD NOT specify this
            parameter if it is not meaningful (i.e. the service only
            provides statistics for a single type of element).

        Output parameters:
        Job -- (type REF (pywbem.CIMInstanceName(classname='CIM_ConcreteJob', ...)) 
            Reference to the job (may be null if job completed).

        Statistics -- (type [unicode,]) 
            The statistics for all the elements as determined by the
            Elements, ManifestCollection parameters, and StatisticsFormat
            parameters.
        """
        # check the parameters
        self.check_instance(object_name)
        if param_manifestcollection:
            if (param_manifestcollection['InstanceID'] !=
                    LMI_BlockStatisticsManifestCollection.INSTANCE_ID):
                raise pywbem.CIMError(pywbem.CIM_ERR_NOT_FOUND,
                        "Unknown ManifestCollection.")
        csv = self.Values.GetStatisticsCollection.StatisticsFormat.CSV
        if (param_statisticsformat is not None
                and param_statisticsformat != csv):
            raise pywbem.CIMError(pywbem.CIM_ERR_INVALID_PARAMETER,
                        "Parameter StatisticsFormat must be CSV.")

        extent = self.Values.GetStatisticsCollection.ElementTypes.Extent
        if (param_elementtypes is not None
                and param_elementtypes != [extent]):
            raise pywbem.CIMError(pywbem.CIM_ERR_INVALID_PARAMETER,
                        "Parameter ElementTypes must be [Extent].")

        # Finally, get the statistics.
        broker = env.get_cimom_handle()
        # The output parameter:
        statistics = []
        # Current chunk, candidate to be inserted to statistics[]:
        chunk = ""

        for device in self.storage.devices:
            if not self.block_stat_provider.has_statistics(device, broker):
                continue

            try:
                line = self._get_statistics_line(device)
            except pywbem.CIMError:
                # Ignore any errors, the device may have disappeared
                # -> no line in resulting statistics
                cmpi_logging.logger.trace_warn(
                        "Skipping device %s in statistics.", device.path)
                continue

            if len(line) + len(chunk) + 1 > self.MAXCHUNK:
                statistics.append(chunk)
                chunk = ""
            chunk += line + "\n"

        statistics.append(chunk)
        out_params = []
        out_params += [pywbem.CIMParameter('statistics', type='string',
                           value=statistics)]
        rval = self.Values.GetStatisticsCollection.Job_Completed_with_No_Error
        return (rval, out_params)

    class Values(ServiceProvider.Values):
        class GetStatisticsCollection(object):
            Job_Completed_with_No_Error = pywbem.Uint32(0)
            Not_Supported = pywbem.Uint32(1)
            Unknown = pywbem.Uint32(2)
            Timeout = pywbem.Uint32(3)
            Failed = pywbem.Uint32(4)
            Invalid_Parameter = pywbem.Uint32(5)
            # Method_Reserved = ..
            Method_Parameters_Checked___Job_Started = pywbem.Uint32(4096)
            Element_Not_Supported = pywbem.Uint32(4097)
            Statistics_Format_Not_Supported = pywbem.Uint32(4098)
            # Method_Reserved = 4099..32767
            # Vendor_Specific = 32768..65535
            class StatisticsFormat(object):
                Unknown = pywbem.Uint16(0)
                Other = pywbem.Uint16(1)
                CSV = pywbem.Uint16(2)
                # DMTF_Reserved = ..
                # Vendor_Specific = 0x8000..
            class ElementTypes(object):
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


class LMI_BlockStatisticsCapabilities(CapabilitiesProvider):
    """
    LMI_DiskPartitionConfigurationCapabilities provider implementation.
    """
    @cmpi_logging.trace_method
    def __init__(self, *args, **kwargs):
        super(LMI_BlockStatisticsCapabilities, self).__init__(
                "LMI_BlockStatisticsCapabilities", *args, **kwargs)
        element_types = LMI_BlockStorageStatisticalData.Values.ElementType
        methods = self.Values.SynchronousMethodsSupported
        features = self.Values.SupportedFeatures
        self.instance = {
                'InstanceID': 'LMI:LMI_BlockStatisticsCapabilities:instance',
                'ElementTypesSupported': [pywbem.Uint16(element_types.Extent)],
                'SynchronousMethodsSupported': [
                        methods.GetStatisticsCollection],
                'AsynchronousMethodsSupported': pywbem.CIMProperty(
                            name='AsynchronousMethodsSupported',
                            value=[],
                            type='uint16',
                            array_size=0,
                            is_array=True),
                'ClockTickInterval': pywbem.Uint64(100000),  # 100 milliseconds
                'SupportedFeatures': [features.none],
                'ElementName': "BlockStatisticsCapabilities",
                '_default': True
        }
    @cmpi_logging.trace_method
    def enumerate_capabilities(self):
        """
            Return an iterable with all capabilities instances, i.e.
            dictionaries property_name -> value.
            If the capabilities are the default ones, it must have
            '_default' as a property name.
        """
        return [self.instance]

    @cmpi_logging.trace_method
    def create_setting_for_capabilities(self, capabilities):
        """
            Create LMI_*Setting for given capabilities.
            Return CIMInstanceName of the setting or raise CIMError on error.
        """
        # There is no LMI_BlockStorageStatisticsSetting
        raise pywbem.CIMError(pywbem.CIM_ERR_NOT_SUPPORTED,
                "This method is not supported.")

    class Values:
        class SynchronousMethodsSupported(object):
            Execute_Query = pywbem.Uint16(2)
            Query_Collection = pywbem.Uint16(3)
            GetStatisticsCollection = pywbem.Uint16(4)
            Manifest_Creation = pywbem.Uint16(5)
            Manifest_Modification = pywbem.Uint16(6)
            Manifest_Removal = pywbem.Uint16(7)
        class SupportedFeatures(object):
            none = pywbem.Uint16(2)
            Client_Defined_Sequence = pywbem.Uint16(3)
            # DMTF_Reserved = ..
            # Vendor_Specific = 0x8000..
