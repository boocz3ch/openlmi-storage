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
""" Module for MountingProvider class. """

import pywbem
import blivet
from openlmi.storage.BaseProvider import BaseProvider
import openlmi.common.cmpi_logging as cmpi_logging

class MountingProvider(BaseProvider):
    """
    An auxiliary class that provides some code sharing and a common base for all
    mounting classes.
    """

    @cmpi_logging.trace_method
    def __init__(self, *args, **kwargs):
        """
           init
        """
        super(MountingProvider, self).__init__(*args, **kwargs)

    def get_device_and_format_from_fs(self, fs):
        provider = self.provider_manager.get_provider_for_format_name(fs)

        if provider is None:
            raise pywbem.CIMError(pywbem.CIM_ERR_FAILED, "Could not get provider for %s" % fs['Name'])

        (device, fmt) = provider.get_format_for_name(fs)

        if device is None:
            raise pywbem.CIMError(pywbem.CIM_ERR_FAILED, "No such device: " + fs['Name'])

        return (device, fmt)
