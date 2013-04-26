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
"""Python Provider for LMI_MountedFileSystem

Instruments the CIM class LMI_MountedFileSystem

"""

import pywbem
import blivet
from openlmi.storage.BaseProvider import BaseProvider
from openlmi.storage.SettingHelper import SettingHelper
from openlmi.storage.SettingManager import StorageSetting
from openlmi.storage.SettingProvider import SettingProvider, Setting
import openlmi.common.cmpi_logging as cmpi_logging

class LMI_MountedFileSystem(BaseProvider, SettingHelper):
    """Instrument the CIM class LMI_MountedFileSystem

    Class for representing mounted filesystems. Can be thought of as either
    an entry in /etc/mtab, or in /etc/fstab, according to its associated
    LMI_MountedFileSystemSetting.

    """
    MOUNT_OPTS = {
        'sync'          : ('SynchronousIO', 'True'),
        'dirsync'       : ('SynchronousDirectoryUpdates', 'True'),
        'atime'         : ('UpdateAccessTimes', 'True'),
        'strictatime'   : ('UpdateFullAccessTimes', 'True'),
        'relatime'      : ('UpdateRelativeAccessTimes', 'True'),
        'diratime'      : ('UpdateDirectoryAccessTimes', 'True'),
        'dev'           : ('InterpretDevices', 'True'),
        'mand'          : ('AllowMandatoryLock', 'True'),
        'exec'          : ('AllowExecution', 'True'),
        'suid'          : ('AllowSUID', 'True'),
        'rw'            : ('AllowWrite', 'True'),
        'silent'        : ('Silent', 'True'),
        'auto'          : ('Auto', 'True'),
        'user'          : ('AllowUserMount', 'True'),

        'nosync'        : ('SynchronousIO', 'False'),
        'noatime'       : ('UpdateAccessTimes', 'False'),
        'nostrictatime' : ('UpdateFullAccessTimes', 'False'),
        'norelatime'    : ('UpdateRelativeAccessTimes', 'False'),
        'nodiratime'    : ('UpdateDirectoryAccessTimes', 'False'),
        'nodev'         : ('InterpretDevices', 'False'),
        'nomand'        : ('AllowMandatoryLock', 'False'),
        'noexec'        : ('AllowExecution', 'False'),
        'nosuid'        : ('AllowSUID', 'False'),
        'ro'            : ('AllowWrite', 'False'),
        'loud'          : ('Silent', 'False'),
        'noauto'        : ('Auto', 'False'),
        'nouser'        : ('AllowUserMount', 'False')
    }

    @cmpi_logging.trace_method
    def __init__(self, *args, **kwargs):
        """
            Initialize the provider.
            Store reference to blivet.Blivet.
            Store reference to StorageConfiguration.
            Register at given ProviderManager.
        """
        super(LMI_MountedFileSystem, self).__init__(
            setting_classname='LMI_MountedFileSystemSetting',
            *args, **kwargs)
        self.classname = 'LMI_MountedFileSystem'

    @cmpi_logging.trace_method
    def get_instance(self, env, model):
        """
            Provider implementation of GetInstance intrinsic method.
        """

        spec = model['FileSystemSpec']
        path = model['MountPointPath']
        device = self.storage.devicetree.getDeviceByPath(spec)

        if device is None:
            raise pywbem.CIMError(pywbem.CIM_ERR_FAILED, "No such mounted device: " + spec)
        if path not in blivet.util.get_mount_paths(spec):
            raise pywbem.CIMError(pywbem.CIM_ERR_FAILED, "%s is not mounted here: %s" % (spec, path))

        model['InstanceID'] = self._create_instance_id(self._create_id(spec, path))
        model['FileSystemType'] = device.format.type

        return model

    @cmpi_logging.trace_method
    def enum_instances(self, env, model, keys_only):
        """Enumerate instances.
        """

        # Prime model.path with knowledge of the keys, so key values on
        # the CIMInstanceName (model.path) will automatically be set when
        # we set property values on the model.
        model.path.update({'MountPointPath': None, 'FileSystemSpec': None})

        for device in self.storage.devices:
            for path in blivet.util.get_mount_paths(device.path):
                model['MountPointPath'] = path
                model['FileSystemSpec'] = device.path

                if keys_only:
                    yield model
                else:
                    try:
                        yield self.get_instance(env, model)
                    except pywbem.CIMError, (num, msg):
                        if num not in (pywbem.CIM_ERR_NOT_FOUND,
                                       pywbem.CIM_ERR_ACCESS_DENIED):
                            raise

    def _create_instance_id(self, mountid):
        return 'LMI:' + self.classname + ':' + mountid

    def _create_setting_instance_id(self, mountid):
        return 'LMI:' + self.classname + 'Setting:' + mountid

    def _create_id(self, spec, path):
        return spec + '|' + path

    def _parse_id(self, mountid):
        return mountid.split('|')

    def _get_options_from_name(self, opt):
        if opt in self.MOUNT_OPTS:
            return self.MOUNT_OPTS[opt]
        return (None, None)

    @cmpi_logging.trace_method
    def _get_setting_for_mount(self, spec, path, setting_provider):
        """
        Return setting for given device

        TBI: This method is a half stub... Until blivet can read mount options
        correctly, it will stay that way.
        """
        _id = self._create_setting_instance_id(self._create_id(spec, path))
        setting = self.setting_manager.create_setting(self.setting_classname,
                                                      Setting.TYPE_CONFIGURATION,
                                                      _id)
        setting['ElementName'] = _id
        # TODO blivet can't read mount options correctly yet
        # opts = ['rw', 'nouser', 'relatime', 'auto', 'uid=0', 'gid=1']
        # for opt in opts[:]:
        #     o, v = self._get_options_from_name(opt)
        #     if o:
        #         setting[o] = v
        #         opts.remove(opt)
        # if opts:
        #     setting['OtherOptions'] = str(opts)
        return setting

    @cmpi_logging.trace_method
    # pylint: disable-msg=W0613
    def enumerate_settings(self, setting_provider):
        """
            This method returns iterable with all instances of LMI_*Setting
            as Setting instances.
        """
        for device in self.storage.devices:
            for path in blivet.util.get_mount_paths(device.path):
                yield self._get_setting_for_mount(device.path, path, setting_provider)

    @cmpi_logging.trace_method
    # pylint: disable-msg=W0613
    def get_setting_for_id(self, setting_provider, instance_id):
        """
            Return Setting instance, which corresponds to LMI_*Setting with
            given InstanceID.
            Return None if there is no such instance.

            Subclasses must override this method.
        """
        mountid = setting_provider.parse_setting_id(instance_id)
        if not mountid:
            return None

        spec, path = self._parse_id(mountid)

        device = self.storage.devicetree.getDeviceByPath(spec)
        if device is None:
            return None
        if path not in blivet.util.get_mount_paths(spec):
            return None

        return self._get_setting_for_mount(spec, path, setting_provider)

    @cmpi_logging.trace_method
    # pylint: disable-msg=W0613
    def get_associated_element_name(self, setting_provider, instance_id):
        """
            Return CIMInstanceName of ManagedElement for ElementSettingData
            association for setting with given ID.
            Return None if no such ManagedElement exists.
        """
        mountid = setting_provider.parse_setting_id(instance_id)
        if not mountid:
            return None

        spec, path = self._parse_id(mountid)

        name = pywbem.CIMInstanceName(
            self.classname,
            namespace=self.config.namespace,
            keybindings={
                'FileSystemSpec': spec,
                'MountPointPath': path
                })

        return name

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
        return {
            'AllowExecution'              : SettingProvider.string_to_bool,
            'AllowMandatoryLock'          : SettingProvider.string_to_bool,
            'AllowSUID'                   : SettingProvider.string_to_bool,
            'AllowUserMount'              : SettingProvider.string_to_bool,
            'AllowWrite'                  : SettingProvider.string_to_bool,
            'Auto'                        : SettingProvider.string_to_bool,
            'Caption'                     : str,
            'ChangeableType'              : pywbem.Uint16,
            'ConfigurationName'           : str,
            'Description'                 : str,
            'Dump'                        : SettingProvider.string_to_bool,
            'ElementName'                 : str,
            'FileSystemCheckOrder'        : pywbem.Uint16,
            'Generation'                  : pywbem.Uint64,
            'InterpretDevices'            : SettingProvider.string_to_bool,
            'OtherOptions' : SettingProvider.string_to_string_array,
            'Silent'                      : SettingProvider.string_to_bool,
            'SynchronousDirectoryUpdates' : SettingProvider.string_to_bool,
            'SynchronousIO'               : SettingProvider.string_to_bool,
            'UpdateAccessTimes'           : SettingProvider.string_to_bool,
            'UpdateDirectoryAccessTimes'  : SettingProvider.string_to_bool,
            'UpdateFullAccessTimes'       : SettingProvider.string_to_bool,
            'UpdateRelativeAccessTimes'   : SettingProvider.string_to_bool,
        }
