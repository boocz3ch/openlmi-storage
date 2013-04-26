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
Module for SettingManager and Setting classes.

SettingManager
--------------

.. autoclass:: SettingManager
    :members:

Setting
-------

.. autoclass:: Setting
    :members:

StorageSetting
--------------

.. autoclass:: StorageSetting
    :members:

"""

import os
import ConfigParser
import openlmi.common.cmpi_logging as cmpi_logging

class SettingManager(object):
    """
        Class, which manages all persistent, transient and preconfigured
        LMI_*Setting instances.

        Note: LMI_*Setting instances, which represent actual configuration
        of some element are *not* managed by this class!

        It should be enough to have only one instance of this class.

        Settings must be removed using special methods of this class.

        Preconfigured settings are stored in /etc/openlmi/storage/setting/
        directory. Each LMI_*Setting class has its own file. Name of the
        file is the same as name of the class.
        Each file has ini structure. Each section represents one LMI_*Setting
        instance, with key=value pairs. Name of the ini section is the same
        as InstanceID of the setting.

        Persistent settings have the same structure, but they are stored in
        /var/lib/openlmi-storage/settings/ directory.
    """

    @cmpi_logging.trace_method
    def __init__(self, storage_configuration, timer_manager):
        """
        Create new SettingManager.

        :param storage_configuration: (``StorageConfiguration``) Current
                configuration.
        :param timer_manager: (``TimerManager``) Timer manager instance.
        """
        # hash classname -> settings
        #   settings = hash setting_id -> Setting
        self.classes = {}
        self.config = storage_configuration
        self.timer_manager = timer_manager
        # hash classname -> last generated unique ID (integer)
        self.ids = {}

    @cmpi_logging.trace_method
    def get_settings(self, classname):
        """
            Return dictionary of all instances of given LMI_*Setting class.
        """
        if not self.classes.has_key(classname):
            self.classes[classname] = {}
        return self.classes[classname]

    @cmpi_logging.trace_method
    def clean(self):
        """
            Remove all persistent and preconfigured settings, leaving
            only transient ones.
        """
        for cls in self.classes.values():
            for setting in cls.values():
                if (setting.type == Setting.TYPE_PERSISTENT
                        or setting.type == Setting.TYPE_PRECONFIGURED):
                    del(cls[setting.the_id])

    @cmpi_logging.trace_method
    def load(self):
        """
            Load all persistent and preconfigured settings from configuration
            files.
        """
        self.clean()

        # open all preconfigured config files
        self._load_directory(self.config.CONFIG_PATH
                    + self.config.SETTINGS_DIR, Setting.TYPE_PRECONFIGURED)
        self._load_directory(self.config.PERSISTENT_PATH
                    + self.config.SETTINGS_DIR, Setting.TYPE_PERSISTENT)

    @cmpi_logging.trace_method
    def _load_directory(self, directory, setting_type):
        """ Load all ini files from given directory. """
        if not os.path.isdir(directory):
            return

        for classname in os.listdir(directory):
            ini = ConfigParser.SafeConfigParser()
            ini.optionxform = str  # don't convert to lowercase
            ini.read(directory + classname)
            for sid in ini.sections():
                setting = self.create_setting(classname, setting_type, sid)
                setting.load(ini)
                self._set_setting(classname, setting)

    @cmpi_logging.trace_method
    def _set_setting(self, classname, setting):
        """ Set given setting. """
        if self.classes.has_key(classname):
            stg = self.classes[classname]
            stg[setting.the_id] = setting
        else:
            self.classes[classname] = { setting.the_id : setting}
        setting.touch()

    @cmpi_logging.trace_method
    def set_setting(self, classname, setting):
        """
            Add or set setting. If the setting is (or was) persistent, it will
            be immediately stored to disk.
        """
        was_persistent = False
        settings = self.classes.get(classname, None)
        if settings:
            old_setting = settings.get(setting.the_id, None)
            if old_setting and old_setting.type == Setting.TYPE_PERSISTENT:
                was_persistent = True

        self._set_setting(classname, setting)
        if setting.type == Setting.TYPE_PERSISTENT or was_persistent:
            self._save_class(classname)

    @cmpi_logging.trace_method
    def delete_setting(self, classname, setting):
        """
            Remove a setting. If the setting was persistent, it will
            be immediately removed from disk.
        """
        settings = self.classes.get(classname, None)
        if settings:
            old_setting = settings.get(setting.the_id, None)
            if old_setting:
                del(settings[setting.the_id])
                if old_setting.type == Setting.TYPE_PERSISTENT:
                    self._save_class(classname)

    @cmpi_logging.trace_method
    def save(self):
        """
            Save all persistent settings to configuration files.
            Create the persistent directory if it does not exist.
        """
        for classname in self.classes.keys():
            self._save_class(classname)

    @cmpi_logging.trace_method
    def _save_class(self, classname):
        """ Save all settings of given class to persistent ini file."""
        ini = ConfigParser.SafeConfigParser()
        ini.optionxform = str  # don't convert to lowercase
        for setting in self.classes[classname].values():
            if setting.type != Setting.TYPE_PERSISTENT:
                continue
            setting.save(ini)

        finaldir = self.config.PERSISTENT_PATH + self.config.SETTINGS_DIR
        if not os.path.isdir(finaldir):
            os.makedirs(finaldir)
        with open(finaldir + classname, 'w') as configfile:
            ini.write(configfile)

    @cmpi_logging.trace_method
    def allocate_id(self, classname):
        """
            Return new unique InstanceID for given LMI_*Setting class.
        """
        if not self.ids.has_key(classname):
            self.ids[classname] = 1

        i = self.ids[classname]
        settings = self.get_settings(classname)
        while settings.has_key("LMI:" + classname + ":" + str(i)):
            i = i + 1

        self.ids[classname] = i + 1
        return "LMI:" + classname + ":" + str(i)

    @cmpi_logging.trace_method
    def create_setting(self, classname, setting_type=None, setting_id=None,
            class_to_create=None):
        """
        Create new Setting instance.

        :param classname: (``string``) Name of related CIM LMI_*Setting class.
        :param setting_type: (``Setting.TYPE_*`` constant) Type of the setting
                to create.
        :param setting_id: (``string`` constant) ID of the new setting.
        :param class_to_create: (``Class``) Subclass of Setting, which should
                be instantiated.
        """
        if class_to_create:
            return class_to_create(self, classname, setting_type, setting_id)
        else:
            return Setting(self, classname, setting_type, setting_id)

    @cmpi_logging.trace_method
    def expire_setting(self, classname, the_id):
        """
        Removes expired setting.

        :param classname: (``string``) Name of LMI_*Setting CIM class.
        :param the_id: (``string``) ID of the setting instance, which has
                expired.
        """
        settings = self.get_settings(classname)
        if settings:
            old_setting = settings.get(the_id, None)
            if old_setting:
                if old_setting.type == Setting.TYPE_TRANSIENT:
                    # Remove transient settings only.
                    del(settings[the_id])

class Setting(object):
    """
        This class represents generic LMI_*Setting properties.
        Every instance has name, type and properties (key-value pairs).
        The value must be string!
    """

    # setting with ChangeableType = Persistent
    TYPE_PERSISTENT = 1
    # setting with ChangeableType = Transient
    TYPE_TRANSIENT = 2
    # setting with ChangeableType = Fixed, preconfigured by system admin
    TYPE_PRECONFIGURED = 3
    # setting with ChangeableType = Fixed, current configuration of real
    # managed element, usually associated to it
    TYPE_CONFIGURATION = 4

    # Time of life of transient setting, in seconds.
    TRAINSIENT_SETTING_LIFETIME = 3600

    @cmpi_logging.trace_method
    def __init__(self, setting_manager, classname, setting_type=None, setting_id=None):
        self.type = setting_type
        self.the_id = setting_id
        self.properties = {}
        self.manager = setting_manager
        self.classname = classname

        self.timer = None
        self.touch()

    @cmpi_logging.trace_method
    def load(self, config):
        """
            Load setting with self.the_id from given ini file
            (ConfigParser instance).
        """
        self.properties = {}
        for (key, value) in config.items(self.the_id):
            if value == "":
                value = None
            self.properties[key] = value

    @cmpi_logging.trace_method
    def save(self, config):
        """
            Save setting with self.the_id to given ini file
            (ConfigParser instance).
        """
        config.add_section(self.the_id)
        for (key, value) in self.properties.items():
            if value is None:
                value = ""
            config.set(self.the_id, key, value)

    @cmpi_logging.trace_method
    def __getitem__(self, key):
        return self.properties[key]

    @cmpi_logging.trace_method
    def __setitem__(self, key, value):
        self.properties[key] = value

    @cmpi_logging.trace_method
    def __delitem__(self, key):
        del self.properties[key]

    @cmpi_logging.trace_method
    def __len__(self):
        return len(self.properties)

    @cmpi_logging.trace_method
    def has_key(self, key):
        """ Emulate dict.has_key(). """
        return self.properties.has_key(key)

    @cmpi_logging.trace_method
    def get(self, key, default=None):
        """ Emulate dict.get(). """
        return self.properties.get(key, default)

    @cmpi_logging.trace_method
    def items(self):
        """
            Return all (key, value) properties.
        """
        return self.properties.items()

    @cmpi_logging.trace_method
    def touch(self):
        """
        Reset expiration timer of transient setting.
        """
        if self.timer:
            self.timer.cancel()
        if self.type == self.TYPE_TRANSIENT:
            self.timer = self.manager.timer_manager.create_timer(
                    "Setting " + self.the_id)
            self.timer.set_callback(
                    self.manager.expire_setting,
                    self.classname,
                    self.the_id)
            self.timer.start(self.TRAINSIENT_SETTING_LIFETIME)


class StorageSetting(Setting):
    """
        Setting for LMI_StorageSetting subclasses. It has all the redundancy
        parameters.
    """
    def set_setting(self, redundancy):
        """
            Set setting according to given DeviceProvider.Redundancy.
        """
        self['DataRedundancyGoal'] = redundancy.data_redundancy
        self['DataRedundancyMax'] = redundancy.data_redundancy
        self['DataRedundancyMin'] = redundancy.data_redundancy
        self['ExtentStripeLength'] = redundancy.stripe_length
        self['ExtentStripeLengthMin'] = redundancy.stripe_length
        self['ExtentStripeLengthMax'] = redundancy.stripe_length
        self['NoSinglePointOfFailure'] = redundancy.no_single_point_of_failure
        self['PackageRedundancyGoal'] = redundancy.package_redundancy
        self['PackageRedundancyMax'] = redundancy.package_redundancy
        self['PackageRedundancyMin'] = redundancy.package_redundancy
        self['ParityLayout'] = redundancy.parity_layout
