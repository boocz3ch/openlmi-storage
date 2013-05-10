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
Module for ServiceProvider class.

ServiceProvider
---------------

.. autoclass:: ServiceProvider
    :members:

"""

from openlmi.storage.BaseProvider import BaseProvider
import pywbem
import openlmi.common.cmpi_logging as cmpi_logging

class ServiceProvider(BaseProvider):
    """
        Base class for every LMI_*Service providers.
        It implements get_instance and enum_instances methods.
    """

    @cmpi_logging.trace_method
    def __init__(self, classname, *args, **kwargs):
        super(ServiceProvider, self).__init__(*args, **kwargs)
        self.classname = classname


    @cmpi_logging.trace_method
    def check_instance(self, model):
        """
            Check if the model represents real instance of this class.
            Throw an error if not.
        """
        if (model['SystemCreationClassName'] != self.config.system_class_name
                or model['SystemName'] != self.config.system_name
                or model['CreationClassName'] != self.classname
                or model['Name'] != self.classname):
            raise pywbem.CIMError(pywbem.CIM_ERR_NOT_FOUND, "Wrong keys.")

    @cmpi_logging.trace_method
    def get_instance(self, env, model):
        """
            Provider implementation of GetInstance intrinsic method.
        """
        self.check_instance(model)

        model['EnabledDefault'] = self.Values.EnabledDefault.Enabled
        model['EnabledState'] = self.Values.EnabledState.Enabled
        model['HealthState'] = self.Values.HealthState.OK
        model['OperationalStatus'] = [self.Values.OperationalStatus.OK, ]
        model['PrimaryStatus'] = self.Values.PrimaryStatus.OK
        model['Started'] = True
        model['StartMode'] = self.Values.StartMode.Automatic
        return model

    @cmpi_logging.trace_method
    def enum_instances(self, env, model, keys_only):
        """
            Provider implementation of EnumerateInstances intrinsic method.
        """
        model.path.update({'CreationClassName': None, 'SystemName': None,
            'Name': None, 'SystemCreationClassName': None})
        model['SystemName'] = self.config.system_name
        model['SystemCreationClassName'] = self.config.system_class_name
        model['CreationClassName'] = self.classname
        model['Name'] = self.classname
        if keys_only:
            yield model
        else:
            yield self.get_instance(env, model)

    @cmpi_logging.trace_method
    def _get_instance_name(self):
        """ Return CIMInstanceName of the service singleton."""
        name = pywbem.CIMInstanceName(
                classname=self.classname,
                namespace=self.config.namespace,
                keybindings={
                    'SystemName': self.config.system_name,
                    'SystemCreationClassName': self.config.system_class_name,
                    'CreationClassName': self.classname,
                    'Name': self.classname})
        return name

    class Values(object):
        class EnabledDefault(object):
            Enabled = pywbem.Uint16(2)
            Disabled = pywbem.Uint16(3)
            Not_Applicable = pywbem.Uint16(5)
            Enabled_but_Offline = pywbem.Uint16(6)
            No_Default = pywbem.Uint16(7)
            Quiesce = pywbem.Uint16(9)
            # DMTF_Reserved = ..
            # Vendor_Reserved = 32768..65535

        class EnabledState(object):
            Unknown = pywbem.Uint16(0)
            Other = pywbem.Uint16(1)
            Enabled = pywbem.Uint16(2)
            Disabled = pywbem.Uint16(3)
            Shutting_Down = pywbem.Uint16(4)
            Not_Applicable = pywbem.Uint16(5)
            Enabled_but_Offline = pywbem.Uint16(6)
            In_Test = pywbem.Uint16(7)
            Deferred = pywbem.Uint16(8)
            Quiesce = pywbem.Uint16(9)
            Starting = pywbem.Uint16(10)
            # DMTF_Reserved = 11..32767
            # Vendor_Reserved = 32768..65535

        class HealthState(object):
            Unknown = pywbem.Uint16(0)
            OK = pywbem.Uint16(5)
            Degraded_Warning = pywbem.Uint16(10)
            Minor_failure = pywbem.Uint16(15)
            Major_failure = pywbem.Uint16(20)
            Critical_failure = pywbem.Uint16(25)
            Non_recoverable_error = pywbem.Uint16(30)
            # DMTF_Reserved = ..
            # Vendor_Specific = 32768..65535

        class OperationalStatus(object):
            Unknown = pywbem.Uint16(0)
            Other = pywbem.Uint16(1)
            OK = pywbem.Uint16(2)
            Degraded = pywbem.Uint16(3)
            Stressed = pywbem.Uint16(4)
            Predictive_Failure = pywbem.Uint16(5)
            Error = pywbem.Uint16(6)
            Non_Recoverable_Error = pywbem.Uint16(7)
            Starting = pywbem.Uint16(8)
            Stopping = pywbem.Uint16(9)
            Stopped = pywbem.Uint16(10)
            In_Service = pywbem.Uint16(11)
            No_Contact = pywbem.Uint16(12)
            Lost_Communication = pywbem.Uint16(13)
            Aborted = pywbem.Uint16(14)
            Dormant = pywbem.Uint16(15)
            Supporting_Entity_in_Error = pywbem.Uint16(16)
            Completed = pywbem.Uint16(17)
            Power_Mode = pywbem.Uint16(18)
            Relocating = pywbem.Uint16(19)
            # DMTF_Reserved = ..
            # Vendor_Reserved = 0x8000..

        class PrimaryStatus(object):
            Unknown = pywbem.Uint16(0)
            OK = pywbem.Uint16(1)
            Degraded = pywbem.Uint16(2)
            Error = pywbem.Uint16(3)
            # DMTF_Reserved = ..
            # Vendor_Reserved = 0x8000..

        class StartMode(object):
            Automatic = 'Automatic'
            Manual = 'Manual'
