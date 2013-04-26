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
""" Module for LMI_LocalFilesystem."""

from openlmi.storage.LocalFileSystemProvider import LocalFileSystemProvider
import openlmi.common.cmpi_logging as cmpi_logging
import blivet.formats
import pywbem
import os

class LMI_TransientFileSystem(LocalFileSystemProvider):
    """
        Generic file system provider for filesystems which do not have
        it's own provider and device.
    """
    @cmpi_logging.trace_method
    def __init__(self, *args, **kwargs):
        super(LMI_TransientFileSystem, self).__init__(
                classname="LMI_TransientFileSystem",
                device_type=None,
                setting_classname=None,
                *args, **kwargs)

    @cmpi_logging.trace_method
    def provides_format(self, device, fmt):
        if fmt is None:
            return False

        # Skip all non-filesystems
        if not isinstance(fmt, blivet.formats.fs.FS):
            return False

        # Skip 'Unknown' format
        if fmt.type is None:
            return False

        # Skip not mounted filesystems, there is no unique ID which we can
        # use to reference them.
        if fmt.mountpoint is None:
            return False

        if  isinstance(device, blivet.devices.NoDevice):
            return True

        return False

    def get_instance(self, env, model, fmt=None):
        model = super(LMI_TransientFileSystem, self).get_instance(env, model, fmt)

        if not fmt:
            (_device, fmt) = self.get_format_for_name(model)
        else:
            _device = self.storage.devicetree.getDeviceByPath(fmt.device)
        if not fmt:
            raise pywbem.CIMError(pywbem.CIM_ERR_NOT_FOUND,
                    "Cannot find the format.")

        model['PersistenceType'] = self.Values.PersistenceType.Temporary
        return model

    def get_format_id(self, device, fmt):
        return "PATH=" + fmt.mountpoint

    def get_format_for_id(self, name):
        if name.startswith("PATH="):
            (_unused, mountpoint) = name.split("=")
            for (path, device) in self.storage.mountpoints.iteritems():
                if path == mountpoint:
                    return (device, device.format)
        return (None, None)
