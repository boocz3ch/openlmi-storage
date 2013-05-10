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
Module for LMI_VGAssociatedComponentExtent class.

LMI_VGAssociatedComponentExtent
-------------------------------

.. autoclass:: LMI_VGAssociatedComponentExtent
    :members:

"""

from openlmi.storage.BaseProvider import BaseProvider
import pywbem
import blivet
import openlmi.common.cmpi_logging as cmpi_logging

class LMI_VGAssociatedComponentExtent(BaseProvider):
    """
        Implementation of LMI_VGAssociatedComponentExtent class.
    """
    @cmpi_logging.trace_method
    def __init__(self, *args, **kwargs):
        super(LMI_VGAssociatedComponentExtent, self).__init__(*args, **kwargs)

    @cmpi_logging.trace_method
    def enum_instances(self, env, model, keys_only):
        """
            Provider implementation of EnumerateInstances intrinsic method.
        """
        model.path.update({'GroupComponent': None, 'PartComponent': None})

        for vg in self.storage.vgs:
            vgprovider = self.provider_manager.get_provider_for_device(vg)
            if not vgprovider:
                raise pywbem.CIMError(pywbem.CIM_ERR_FAILED,
                        "Cannot find provider for device " + vg.path)
            for pv in vg.pvs:
                pvprovider = self.provider_manager.get_provider_for_device(pv)
                if not pvprovider:
                    raise pywbem.CIMError(pywbem.CIM_ERR_FAILED,
                            "Cannot find provider for device " + pv.path)

                model['GroupComponent'] = vgprovider.get_name_for_device(vg)
                model['PartComponent'] = pvprovider.get_name_for_device(pv)
                if keys_only:
                    yield model
                else:
                    yield self.get_instance(env, model, vg, pv)

    @cmpi_logging.trace_method
    # pylint: disable-msg=W0221
    def get_instance(self, env, model, vg=None, pv=None):
        """
            Provider implementation of GetInstance intrinsic method.
            It just checks if GroupComponent and PartComponent are related.
        """
        if not vg:
            vg = self.provider_manager.get_device_for_name(
                    model['GroupComponent'])
        if not vg:
            raise pywbem.CIMError(pywbem.CIM_ERR_NOT_FOUND,
                    "Cannot find GroupComponent device")

        if not pv:
            pv = self.provider_manager.get_device_for_name(
                    model['PartComponent'])
        if not pv:
            raise pywbem.CIMError(pywbem.CIM_ERR_NOT_FOUND,
                    "Cannot find PartComponent device")

        if not isinstance(vg, blivet.devices.LVMVolumeGroupDevice):
            raise pywbem.CIMError(pywbem.CIM_ERR_NOT_FOUND,
                    "GroupComponent device is not volume group: " + vg.path)
        if not (pv in vg.pvs):
            raise pywbem.CIMError(pywbem.CIM_ERR_NOT_FOUND,
                    "GroupComponent is not related to PartComponent device")

        return model

    @cmpi_logging.trace_method
    def references(self, env, object_name, model, result_class_name, role,
                   result_role, keys_only):
        """Instrument Associations."""
        return self.simple_references(env, object_name, model,
                result_class_name, role, result_role, keys_only,
                "CIM_StorageExtent",
                "CIM_StoragePool")
