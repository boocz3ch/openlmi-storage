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
"""
Python Provider for LMI_MountedFileSystemCapabilities

Instruments the CIM class LMI_MountedFileSystemCapabilities
"""

import pywbem
import blivet
from openlmi.storage.MountingProvider import MountingProvider
from openlmi.storage.CapabilitiesProvider import CapabilitiesProvider
from openlmi.storage.SettingManager import Setting
import openlmi.common.cmpi_logging as cmpi_logging

class LMI_MountedFileSystemCapabilities(CapabilitiesProvider):
    """
    LMI_MountedFileSystemCapabilities provider implementation.
    """

    @cmpi_logging.trace_method
    def __init__ (self, *args, **kwargs):
        super(LMI_MountedFileSystemCapabilities, self).__init__(
            classname="LMI_MountedFileSystemCapabilities",
            *args, **kwargs)
        self.instances = [
            {
                'InstanceID':'LMI:LMI_MountedFileSystemCapabilities:1',
                'SupportedAsynchronousMethods':[self.Values.SupportedAsynchronousMethods.CreateMount,
                                                self.Values.SupportedAsynchronousMethods.ModifyMount,
                                                self.Values.SupportedAsynchronousMethods.DeleteMount]
                }
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

    # pylint: disable-msg=W0613
    @cmpi_logging.trace_method
    def create_setting_for_capabilities(self, capabilities):
        """
            Create LMI_*Setting for given capabilities.
            Return CIMInstanceName of the setting or raise CIMError on error.
        """
        setting_name = 'LMI_MountedFileSystemSetting'
        setting_id = self.setting_manager.allocate_id(setting_name)
        if not setting_id:
            raise pywbem.CIMError(pywbem.CIM_ERR_FAILED,
                                  "Failed to allocate setting InstanceID.")

        setting = self.setting_manager.create_setting(setting_name,
                                                      Setting.TYPE_TRANSIENT,
                                                      setting_id)

        setting['ElementName'] = 'CreatedFrom' + capabilities['InstanceID']
        # default settings: rw, suid, dev, exec, auto, nouser, and async.
        setting['AllowWrite'] = True
        setting['AllowSuid'] = True
        setting['InterpretDevices'] = True
        setting['AllowExecution'] = True
        setting['Auto'] = True
        setting['AllowUserMount'] = False
        setting['SynchronousIO'] = False
        self.setting_manager.set_setting(setting_name, setting)

        return pywbem.CIMInstanceName(
                classname=setting_name,
                namespace=self.config.namespace,
                keybindings={'InstanceID': setting_id})

    class Values(object):
        class SupportedAsynchronousMethods(object):
            CreateMount = pywbem.Uint16(0)
            ModifyMount = pywbem.Uint16(1)
            DeleteMount = pywbem.Uint16(2)

        class CreateSetting(object):
            Success = pywbem.Uint32(0)
            Not_Supported = pywbem.Uint32(1)
            Unspecified_Error = pywbem.Uint32(2)
            Timeout = pywbem.Uint32(3)
            Failed = pywbem.Uint32(4)
            Invalid_Parameter = pywbem.Uint32(5)
