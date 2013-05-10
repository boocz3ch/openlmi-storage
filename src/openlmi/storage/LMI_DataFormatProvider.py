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
""""
Module for FormatProvider.

LMI_DataFormatProvider
----------------------

.. autoclass:: LMI_DataFormatProvider
    :members:

"""

from openlmi.storage.FormatProvider import FormatProvider
import blivet.formats
import openlmi.common.cmpi_logging as cmpi_logging

class LMI_DataFormatProvider(FormatProvider):
    """
        Provider of generic LMI_DataFormat.
        It provides all DeviceFormats, which do not have any special provider
        (like MDRAIDFormat or PVFormat) and are not filesystems.
    """
    @cmpi_logging.trace_method
    def __init__(self, *args, **kwargs):
        super(LMI_DataFormatProvider, self).__init__(
                "LMI_DataFormat",
                None,
                *args, **kwargs)

    @cmpi_logging.trace_method
    def provides_format(self, device, fmt):
        if fmt is None:
            return False
        if isinstance(fmt, blivet.formats.mdraid.MDRaidMember):
            return False
        if isinstance(fmt, blivet.formats.lvmpv.LVMPhysicalVolume):
            return False
        if isinstance(fmt, blivet.formats.fs.FS):
            return False

        # skip 'Unknown' format
        if fmt.type is None:
            return False
        # skip partition tables
        if isinstance(fmt, blivet.formats.disklabel.DiskLabel):
            return False

        return True
