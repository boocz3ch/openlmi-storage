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

""" Module for BaseProvider class. """

from pywbem.cim_provider2 import CIMProvider2
import openlmi.common.cmpi_logging as cmpi_logging

class BaseProvider(CIMProvider2):
    """
        CIM Provider for LMI. It adds access to ProviderManager, configuration
        and blivet.Blivet instance.

        In addition to CIM provider methods, this class and its subclasses
        can convert CIM InstanceName to Anaconda's StorageDevice instance
        and a vice versa.
    """
    @cmpi_logging.trace_method
    def __init__(self, storage, config, provider_manager, setting_manager,
            job_manager, *args, **kwargs):
        """
            Initialize the provider.
            Store reference to blivet.Blivet.
            Store reference to StorageConfiguration.
            Register at given ProviderManager.
        """
        super(BaseProvider, self).__init__(*args, **kwargs)
        self.storage = storage
        self.config = config
        self.provider_manager = provider_manager
        self.setting_manager = setting_manager
        self.job_manager = job_manager

    @cmpi_logging.trace_method
    # The method has too many arguments, but that's because of
    # CIMProvider2.references
    # pylint: disable-msg=R0913
    def simple_references(self, env, object_name, model, result_class_name,
            role, result_role, keys_only, first_class, second_class):
        """
            Implementation of basic associations. This method can be used by
            all subclasses, which implement association provider.

            It has the same arguments as references() method of CIMProvider2,
            additional 'first_class' and 'second_class' should contain
            string with CIM class names of the associated classes.

            All four association-related operations (Associators, AssociatorNames,
            References, ReferenceNames) are mapped to this method.
            This method is a python generator

            Keyword arguments:
            env -- Provider Environment (pycimmb.ProviderEnvironment)
            object_name -- A pywbem.CIMInstanceName that defines the source
                CIM Object whose associated Objects are to be returned.
            model -- A template pywbem.CIMInstance to serve as a model
                of the objects to be returned.  Only properties present on this
                model need to be set.
            result_class_name -- If not empty, this string acts as a filter on
                the returned set of Instances by mandating that each returned
                Instances MUST represent an association between object_name
                and an Instance of a Class whose name matches this parameter
                or a subclass.
            role -- If not empty, MUST be a valid Property name. It acts as a
                filter on the returned set of Instances by mandating that each
                returned Instance MUST refer to object_name via a Property
                whose name matches the value of this parameter.
            result_role -- If not empty, MUST be a valid Property name. It acts
                as a filter on the returned set of Instances by mandating that
                each returned Instance MUST represent associations of
                object_name to other Instances, where the other Instances play
                the specified result_role in the association (i.e. the
                name of the Property in the Association Class that refers to
                the Object related to object_name MUST match the value of this
                parameter).
            keys_only -- A boolean.  True if only the key properties should be
                set on the generated instances.

            The following diagram may be helpful in understanding the role,
            result_role, and result_class_name parameters.
            +------------------------+                    +-------------------+
            | object_name.classname  |                    | result_class_name |
            | ~~~~~~~~~~~~~~~~~~~~~  |                    | ~~~~~~~~~~~~~~~~~ |
            +------------------------+                    +-------------------+
               |              +-----------------------------------+      |
               |              |  [Association] model.classname    |      |
               | object_name  |  ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~    |      |
               +--------------+ object_name.classname REF role    |      |
            (CIMInstanceName) | result_class_name REF result_role +------+
                              |                                   |(CIMInstanceName)
                              +-----------------------------------+

            Possible Errors:
            CIM_ERR_ACCESS_DENIED
            CIM_ERR_NOT_SUPPORTED
            CIM_ERR_INVALID_NAMESPACE
            CIM_ERR_INVALID_PARAMETER (including missing, duplicate, unrecognized
                or otherwise incorrect parameters)
            CIM_ERR_FAILED (some other unspecified error occurred)
        """

        cimom = env.get_cimom_handle()
        if cimom.is_subclass(object_name.namespace,
                  sub=object_name.classname,
                  super=first_class) or \
                  cimom.is_subclass(object_name.namespace,
                       sub=object_name.classname,
                       super=second_class):
            return self.simple_refs(env, object_name, model,
                      result_class_name, role, result_role, keys_only)


