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
Module for LMI_InstalledPartitionTable class.

LMI_InstalledPartitionTable
---------------------------

.. autoclass:: LMI_InstalledPartitionTable
    :members:

"""

import blivet.formats
from openlmi.storage.BaseProvider import BaseProvider
import pywbem
import openlmi.common.cmpi_logging as cmpi_logging

class LMI_InstalledPartitionTable(BaseProvider):
    """
        LMI_InstalledPartitionTable provider implementation.
    """

    @cmpi_logging.trace_method
    def __init__(self, *args, **kwargs):
        super(LMI_InstalledPartitionTable, self).__init__(*args, **kwargs)
        mgr = self.provider_manager
        self.capabilities_provider = mgr.get_capabilities_provider_for_class(
                "LMI_DiskPartitionConfigurationCapabilities")

    @cmpi_logging.trace_method
    def get_instance(self, env, model):
        """
            Provider implementation of GetInstance intrinsic method.
        """
        device = self.provider_manager.get_device_for_name(model['Antecedent'])
        if not device:
            raise pywbem.CIMError(pywbem.CIM_ERR_NOT_FOUND,
                    "Cannot find Antecedent extent.")
        capabilities = self.capabilities_provider.get_capabilities_for_device(
                device)
        if not capabilities:
            raise pywbem.CIMError(pywbem.CIM_ERR_NOT_FOUND,
                    "Cannot find capabilities of the Antecedent extent.")

        if model['Dependent']['InstanceID'] != capabilities['InstanceID']:
            raise pywbem.CIMError(pywbem.CIM_ERR_NOT_FOUND,
                    "Capabilities are not associated to Antecedent extent.")

        return model

    @cmpi_logging.trace_method
    def get_capabilities_name_for_device(self, device):
        """
            Return CIMInstanceName of DiskPartitionConfigurationCapabilities
            for given device
            or None if there is no partition table on the device.
        """
        capabilities = self.capabilities_provider.get_capabilities_for_device(
                device)
        if capabilities:
            return self.capabilities_provider.get_name_for_id(
                    capabilities['InstanceID'])
        return None

    @cmpi_logging.trace_method
    def enum_instances(self, env, model, keys_only):
        """
            Provider implementation of EnumerateInstances intrinsic method.
        """
        model.path.update({'Dependent': None, 'Antecedent': None})

        for device in self.storage.devices:
            fmt_class = blivet.formats.disklabel.DiskLabel
            if device.format and isinstance(device.format, fmt_class):
                model['Antecedent'] = self.provider_manager.get_name_for_device(
                        device)
                model['Dependent'] = self.get_capabilities_name_for_device(
                        device)
                yield model


    @cmpi_logging.trace_method
    def references(self, env, object_name, model, result_class_name, role,
                   result_role, keys_only):
        """Instrument Associations."""
        return self.simple_references(env, object_name, model,
                result_class_name, role, result_role, keys_only,
                "CIM_StorageExtent",
                "CIM_DiskPartitionConfigurationCapabilities")
