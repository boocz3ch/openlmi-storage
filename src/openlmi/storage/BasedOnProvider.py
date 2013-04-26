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
Module for BasedOnProvider class.

BasedOnProvider
---------------

.. autoclass:: BasedOnProvider
    :members:

"""

import pywbem
from openlmi.storage.BaseProvider import BaseProvider
import openlmi.common.cmpi_logging as cmpi_logging

class BasedOnProvider(BaseProvider):
    """
        Base of all BasedOn providers.
        It should handle everything, subclasses just need to override
        enumerate_devices.
    """
    @cmpi_logging.trace_method
    def __init__(self, *args, **kwargs):
        super(BasedOnProvider, self).__init__(*args, **kwargs)

    @cmpi_logging.trace_method
    def enumerate_devices(self):
        """
            Enumerate all devices, which are in this association as
            Dependent ones. The Antecedent ones are found using
            DeviceProvider.get_base_devices of the DependentDevice.
        """
        return []

    @cmpi_logging.trace_method
    def enum_instances(self, env, model, keys_only):
        """
            Provider implementation of EnumerateInstances intrinsic method.
        """
        model.path.update({'Dependent': None, 'Antecedent': None})

        for device in self.enumerate_devices():
            provider = self.provider_manager.get_provider_for_device(device)
            if not provider:
                raise pywbem.CIMError(pywbem.CIM_ERR_FAILED,
                        "Cannot find provider for device " + device.path)
            for base in provider.get_base_devices(device):
                model['Dependent'] = provider.get_name_for_device(device)
                model['Antecedent'] = self.provider_manager.get_name_for_device(
                        base)
                if keys_only:
                    yield model
                else:
                    yield self.get_instance(env, model, device, base)


    # pylint: disable-msg=W0221
    @cmpi_logging.trace_method
    def get_instance(self, env, model, device=None, base=None):
        """
            Provider implementation of GetInstance intrinsic method.
            It just checks if Dependent and Antecedent are related.
        """
        if not device:
            device = self.provider_manager.get_device_for_name(
                    model['Dependent'])
        if not device:
            raise pywbem.CIMError(pywbem.CIM_ERR_NOT_FOUND,
                    "Cannot find Dependent device")

        if not base:
            base = self.provider_manager.get_device_for_name(
                    model['Antecedent'])
        if not base:
            raise pywbem.CIMError(pywbem.CIM_ERR_NOT_FOUND,
                    "Cannot find Antecedent device")

        device_provider = self.provider_manager.get_device_provider_for_name(
                model['Dependent'])
        if not (base in device_provider.get_base_devices(device)):
            raise pywbem.CIMError(pywbem.CIM_ERR_NOT_FOUND,
                    "Antecedent is not related to Dependent device")

        return model

    @cmpi_logging.trace_method
    def references(self, env, object_name, model, result_class_name, role,
                   result_role, keys_only):
        """Instrument Associations."""
        return self.simple_references(env, object_name, model,
                result_class_name, role, result_role, keys_only,
                "CIM_StorageExtent",
                "CIM_StorageExtent")
