# Cura Storage Provider
#
# Copyright (C) 2012 Red Hat, Inc.  All rights reserved.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Python Provider for LMI_PartitionBasedOnPartition

Instruments the CIM class LMI_PartitionBasedOnPartition

"""

from wrapper.common import *
import pywbem
from pywbem.cim_provider2 import CIMProvider2
import pyanaconda.storage.devices
import util.partitioning

class LMI_PartitionBasedOnPartition(CIMProvider2):
    """Instrument the CIM class LMI_PartitionBasedOnPartition 

    Association between logical partitions and its extended partition.
    
    """

    def __init__ (self, env):
        logger = env.get_logger()
        logger.log_debug('Initializing provider %s from %s' \
                % (self.__class__.__name__, __file__))

    def get_instance(self, env, model):
        """Return an instance.

        Keyword arguments:
        env -- Provider Environment (pycimmb.ProviderEnvironment)
        model -- A template of the pywbem.CIMInstance to be returned.  The 
            key properties are set on this instance to correspond to the 
            instanceName that was requested.  The properties of the model
            are already filtered according to the PropertyList from the 
            request.  Only properties present in the model need to be
            given values.  If you prefer, you can set all of the 
            values, and the instance will be filtered for you. 

        Possible Errors:
        CIM_ERR_ACCESS_DENIED
        CIM_ERR_INVALID_PARAMETER (including missing, duplicate, unrecognized 
            or otherwise incorrect parameters)
        CIM_ERR_NOT_FOUND (the CIM Class does exist, but the requested CIM 
            Instance does not exist in the specified namespace)
        CIM_ERR_FAILED (some other unspecified error occurred)

        """
        
        logger = env.get_logger()
        logger.log_debug('Entering %s.get_instance()' \
                % self.__class__.__name__)
        
        # TODO: checking
        
        path = model['Dependent']['DeviceID']
        partition = storage.devicetree.getDeviceByPath(path)
        if not isinstance(partition, pyanaconda.storage.devices.PartitionDevice):
            raise pywbem.CIMError(pywbem.CIM_ERR_NOT_FOUND, 'Wrong Dependent InstanceID')

        path = model['Antecedent']['DeviceID']
        extended = storage.devicetree.getDeviceByPath(path)
        if not isinstance(partition, pyanaconda.storage.devices.PartitionDevice):
            raise pywbem.CIMError(pywbem.CIM_ERR_NOT_FOUND, 'Wrong Antecedent InstanceID')

        pstart = util.partitioning.getLogicalPartitionStart(partition)
        pend = partition.partedPartition.geometry.end
        estart = extended.partedPartition.geometry.start
        
        model['EndingAddress'] = pywbem.Uint64(pend - estart)
        model['OrderIndex'] = pywbem.Uint16(partition.partedPartition.number) 
        model['StartingAddress'] = pywbem.Uint64(pstart - estart)
        return model

    def enum_instances(self, env, model, keys_only):
        """Enumerate instances.

        The WBEM operations EnumerateInstances and EnumerateInstanceNames
        are both mapped to this method. 
        This method is a python generator

        Keyword arguments:
        env -- Provider Environment (pycimmb.ProviderEnvironment)
        model -- A template of the pywbem.CIMInstances to be generated.  
            The properties of the model are already filtered according to 
            the PropertyList from the request.  Only properties present in 
            the model need to be given values.  If you prefer, you can 
            always set all of the values, and the instance will be filtered 
            for you. 
        keys_only -- A boolean.  True if only the key properties should be
            set on the generated instances.

        Possible Errors:
        CIM_ERR_FAILED (some other unspecified error occurred)

        """

        logger = env.get_logger()
        logger.log_debug('Entering %s.enum_instances()' \
                % self.__class__.__name__)
                
        # Prime model.path with knowledge of the keys, so key values on
        # the CIMInstanceName (model.path) will automatically be set when
        # we set property values on the model. 
        model.path.update({'Dependent': None, 'Antecedent': None})
        
        for partition in storage.partitions:
            if not partition.isLogical:
                continue
            extendedPath = partition.partedPartition.disk.getExtendedPartition().path
            extended = storage.devicetree.getDeviceByPath(extendedPath)
            
            model['Dependent'] = pywbem.CIMInstanceName(classname='LMI_DiskPartition',
                    namespace=LMI_NAMESPACE,
                    keybindings={'CreationClassName': 'LMI_DiskPartition',
                                 'DeviceID': partition.path,
                                 'SystemCreationClassName': LMI_SYSTEM_CLASS_NAME,
                                 'SystemName': LMI_SYSTEM_NAME
                    })
            model['Antecedent'] = pywbem.CIMInstanceName(classname='LMI_DiskPartition',
                    namespace=LMI_NAMESPACE,
                    keybindings={'CreationClassName': 'LMI_DiskPartition',
                                 'DeviceID': extended.path,
                                 'SystemCreationClassName': LMI_SYSTEM_CLASS_NAME,
                                 'SystemName': LMI_SYSTEM_NAME
                    })
            if keys_only:
                yield model
            else:
                try:
                    yield self.get_instance(env, model)
                except pywbem.CIMError, (num, msg):
                    if num not in (pywbem.CIM_ERR_NOT_FOUND, 
                                   pywbem.CIM_ERR_ACCESS_DENIED):
                        raise

    def set_instance(self, env, instance, modify_existing):
        """Return a newly created or modified instance.

        Keyword arguments:
        env -- Provider Environment (pycimmb.ProviderEnvironment)
        instance -- The new pywbem.CIMInstance.  If modifying an existing 
            instance, the properties on this instance have been filtered by 
            the PropertyList from the request.
        modify_existing -- True if ModifyInstance, False if CreateInstance

        Return the new instance.  The keys must be set on the new instance. 

        Possible Errors:
        CIM_ERR_ACCESS_DENIED
        CIM_ERR_NOT_SUPPORTED
        CIM_ERR_INVALID_PARAMETER (including missing, duplicate, unrecognized 
            or otherwise incorrect parameters)
        CIM_ERR_ALREADY_EXISTS (the CIM Instance already exists -- only 
            valid if modify_existing is False, indicating that the operation
            was CreateInstance)
        CIM_ERR_NOT_FOUND (the CIM Instance does not exist -- only valid 
            if modify_existing is True, indicating that the operation
            was ModifyInstance)
        CIM_ERR_FAILED (some other unspecified error occurred)

        """

        logger = env.get_logger()
        logger.log_debug('Entering %s.set_instance()' \
                % self.__class__.__name__)
        # TODO create or modify the instance
        raise pywbem.CIMError(pywbem.CIM_ERR_NOT_SUPPORTED) # Remove to implement
        return instance

    def delete_instance(self, env, instance_name):
        """Delete an instance.

        Keyword arguments:
        env -- Provider Environment (pycimmb.ProviderEnvironment)
        instance_name -- A pywbem.CIMInstanceName specifying the instance 
            to delete.

        Possible Errors:
        CIM_ERR_ACCESS_DENIED
        CIM_ERR_NOT_SUPPORTED
        CIM_ERR_INVALID_NAMESPACE
        CIM_ERR_INVALID_PARAMETER (including missing, duplicate, unrecognized 
            or otherwise incorrect parameters)
        CIM_ERR_INVALID_CLASS (the CIM Class does not exist in the specified 
            namespace)
        CIM_ERR_NOT_FOUND (the CIM Class does exist, but the requested CIM 
            Instance does not exist in the specified namespace)
        CIM_ERR_FAILED (some other unspecified error occurred)

        """ 

        logger = env.get_logger()
        logger.log_debug('Entering %s.delete_instance()' \
                % self.__class__.__name__)

        # TODO delete the resource
        raise pywbem.CIMError(pywbem.CIM_ERR_NOT_SUPPORTED) # Remove to implement
        
    def references(self, env, object_name, model, result_class_name, role,
                   result_role, keys_only):
        """Instrument Associations.

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

        logger = env.get_logger()
        logger.log_debug('Entering %s.references()' \
                % self.__class__.__name__)
        ch = env.get_cimom_handle()

        # If you want to get references for free, implemented in terms 
        # of enum_instances, just leave the code below unaltered.
        if ch.is_subclass(object_name.namespace, 
                          sub=object_name.classname,
                          super='CIM_StorageExtent') or \
                ch.is_subclass(object_name.namespace,
                               sub=object_name.classname,
                               super='CIM_StorageExtent'):
            return self.simple_refs(env, object_name, model,
                          result_class_name, role, result_role, keys_only)
                          
## end of class LMI_PartitionBasedOnPartitionProvider
    
## get_providers() for associating CIM Class Name to python provider class name
    
def get_providers(env): 
    initAnaconda(False)
    LMI_partitionbasedonpartition_prov = LMI_PartitionBasedOnPartition(env)  
    return {'LMI_PartitionBasedOnPartition': LMI_partitionbasedonpartition_prov} 