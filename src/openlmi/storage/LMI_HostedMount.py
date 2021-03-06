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
# -*- coding: utf-8 -*-
"""Python Provider for LMI_HostedMount

Instruments the CIM class LMI_HostedMount

"""

import pywbem
import blivet
from openlmi.storage.BaseProvider import BaseProvider
import openlmi.common.cmpi_logging as cmpi_logging


class LMI_HostedMount(BaseProvider):
    """Instrument the CIM class LMI_HostedMount

    CIM_Dependency is a generic association used to establish dependency
    relationships between ManagedElements.

    """
    @cmpi_logging.trace_method
    def __init__ (self, *args, **kwargs):
        super(LMI_HostedMount, self).__init__(*args, **kwargs)

    @cmpi_logging.trace_method
    def get_instance(self, env, model):
        """
            Provider implementation of GetInstance intrinsic method.
        """
        system = model['Antecedent']
        if (system['CreationClassName'] != self.config.system_class_name
            or system['Name'] != self.config.system_name):
            raise pywbem.CIMError(pywbem.CIM_ERR_NOT_FOUND,
                                  "Wrong Antecedent keys.")

        spec = model['Dependent']['FileSystemSpec']
        path = model['Dependent']['MountPointPath']

        device = self.storage.devicetree.getDeviceByPath(spec)

        if device is None:
            raise pywbem.CIMError(pywbem.CIM_ERR_FAILED, "No such mounted device: " + spec)
        if path not in blivet.util.get_mount_paths(spec):
            raise pywbem.CIMError(pywbem.CIM_ERR_FAILED, "%s is not mounted here: %s" % (spec, path))

        return model

    @cmpi_logging.trace_method
    def enum_instances(self, env, model, keys_only):
        """Enumerate instances.
        """

        model.path.update({'Dependent': None, 'Antecedent': None})
        for device in self.storage.devices:
            for path in blivet.util.get_mount_paths(device.path):
                model['Antecedent'] = pywbem.CIMInstanceName(
                    classname=self.config.system_class_name,
                    namespace=self.config.namespace,
                    keybindings={
                        'CreationClassName' : self.config.system_class_name,
                        'Name' : self.config.system_name,
                        })
                model['Dependent'] = pywbem.CIMInstanceName(
                    classname='LMI_MountedFileSystem',
                    namespace=self.config.namespace,
                    keybindings={
                        'FileSystemSpec' : device.path,
                        'MountPointPath' : path
                        })

                yield model

    def references(self, env, object_name, model, result_class_name, role,
                   result_role, keys_only):
        return self.simple_references(env, object_name, model,
                                      result_class_name, role, result_role, keys_only,
                                      "LMI_MountedFileSystem",
                                      "CIM_System")
