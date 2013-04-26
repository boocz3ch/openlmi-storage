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
Module for SettingHelper class.

SettingHelper
-------------

.. autoclass:: SettingHelper
    :members:

"""

import openlmi.common.cmpi_logging as cmpi_logging

class SettingHelper(object):
    """
        Abstract interface to help implementation of LMI_*Setting classes.
        LMI_*Setting instances are associated with some managed
        element, let's say LMI_Foo. LMI_Foo has its own provider, which can
        enumerate and provide LMI_Foo instances. If LMI_Foo inherits also
        SettingHelper, it can then enumerate and provider CIM_FooSetting
        instances associated to the managed foos.
    """

    @cmpi_logging.trace_method
    def __init__(self, setting_classname, *args, **kwargs):
        self.setting_classname = setting_classname
        super(SettingHelper, self).__init__(*args, **kwargs)

    @cmpi_logging.trace_method
    # pylint: disable-msg=W0613
    def enumerate_settings(self, setting_provider):
        """
            This method returns iterable with all instances of LMI_*Setting
            as Setting instances.
        """
        return []

    @cmpi_logging.trace_method
    # pylint: disable-msg=W0613
    def get_setting_for_id(self, setting_provider, instance_id):
        """
            Return Setting instance, which corresponds to LMI_*Setting with
            given InstanceID.
            Return None if there is no such instance.

            Subclasses must override this method.
        """
        return None

    @cmpi_logging.trace_method
    # pylint: disable-msg=W0613
    def get_associated_element_name(self, setting_provider, instance_id):
        """
            Return CIMInstanceName of ManagedElement for ElementSettingData
            association for setting with given ID.
            Return None if no such ManagedElement exists.
        """
        return None

    @cmpi_logging.trace_method
    # pylint: disable-msg=W0613
    def get_supported_setting_properties(self, setting_provider):
        """
            Return hash property_name -> constructor.
                constructor is a function which takes string argument
                and returns CIM value. (i.e. pywbem.Uint16
                or bool or string etc).
            This hash will be passed to SettingProvider.__init__
        """
        return {}

    @cmpi_logging.trace_method
    # pylint: disable-msg=W0613
    def get_setting_ignore(self, setting_provider):
        """
            Return hash property_name -> default value.
            If this value of the property is set, the ModifyInstance
            won't complain, but it will silently ignore the value.
            This is useful when someone tries to set default value
            of a property and the provider does not implement it.
        """
        return None

    @cmpi_logging.trace_method
    # pylint: disable-msg=W0613
    def get_setting_validators(self, setting_provider):
        """
            Return hash property_name -> validator
                validator is a function which takes pywbem (Uint32, bool ...)
                value as parameter and returns True, if the value is correct for
                the property. Not all properties do need to have a validator.
        """
        return None
