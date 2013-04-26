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
Module for DeviceProvider class.

DeviceProvider
--------------

.. autoclass:: DeviceProvider
    :members:

"""

from openlmi.storage.BaseProvider import BaseProvider
import pywbem
import openlmi.common.cmpi_logging as cmpi_logging

class DeviceProvider(BaseProvider):
    """
        CIM Provider which provides CIM StorageExtent or CIM_StoragePool
        of a Anaconda device.

        In addition to CIM provider methods, this class and its subclasses
        can convert CIM InstanceName to Anaconda's StorageDevice instance
        and a vice versa.
    """
    @cmpi_logging.trace_method
    def __init__(self, *args, **kwargs):
        """
            Initialize the provider.
            Store reference to blivet.Blivet.
            Store reference to StorageConfiguration.
            Register at given ProviderManager.
        """
        super(DeviceProvider, self).__init__(*args, **kwargs)
        self.provider_manager.add_device_provider(self)

    @cmpi_logging.trace_method
    # pylint: disable-msg=W0613
    def provides_name(self, object_name):
        """
            Returns True, if this class is provider for given CIM InstanceName.
        """
        return False

    @cmpi_logging.trace_method
    # pylint: disable-msg=W0613
    def provides_device(self, device):
        """
            Returns True, if this class is provider for given Anaconda
            StorageDevice class.
        """
        return False

    @cmpi_logging.trace_method
    # pylint: disable-msg=W0613
    def get_device_for_name(self, object_name):
        """
            Returns Anaconda StorageDevice for given CIM InstanceName or
            None if no device is found.
        """
        return None

    @cmpi_logging.trace_method
    # pylint: disable-msg=W0613
    def get_name_for_device(self, device):
        """
            Returns CIM InstanceName for given Anaconda StorageDevice.
            None if no device is found.
        """
        return None

    @cmpi_logging.trace_method
    def get_status(self, device):
        """
            Returns OperationalStatus for given Anaconda StorageDevice.
            It combines statuses of all parent devices.
            Subclasses should override this method to provide additional
            statuses.
        """
        status = set()
        parents = self.get_base_devices(device)
        if len(parents) > 0:
            for parent in parents:
                parent_provider = self.provider_manager.get_provider_for_device(
                        parent)
                parent_status = parent_provider.get_status(parent)
                status.update(parent_status)
        else:
            status.add(self.Values.OperationalStatus.OK)
        return list(status)

    @cmpi_logging.trace_method
    def get_base_devices(self, device):
        """
            Return iterable with base devices for given StorageDevice.
            Base devices are StorageDevices, that the given StorageDevice
            depend on, e.g. RAID members of a RAID, physical volumes
            of a Volume Group and Volume Group of Logical Volume.
        """
        if device.parents:
            return device.parents
        return []

    @cmpi_logging.trace_method
    def _find_redundancy(self, device):
        """
            Discover redundancy of given StorageDevice.
            It uses ProviderManager to do so.
        """
        provider = self.provider_manager.get_provider_for_device(device)
        if not provider:
            raise pywbem.CIMError(pywbem.CIM_ERR_FAILED,
                    "Cannot find provider for device " + device.path)
        return provider.get_redundancy(device)

    @cmpi_logging.trace_method
    # pylint: disable-msg=W0613
    def do_delete_instance(self, device):
        """
            Really delete given Anaconda StorageDevice.

            Subclasses must override this method to allow DeleteInstance
            intrinsic method.
        """
        raise pywbem.CIMError(pywbem.CIM_ERR_NOT_SUPPORTED,
                    "Cannot delete this device.")

    @cmpi_logging.trace_method
    def delete_instance(self, env, instance_name):
        """Delete an instance intrinsic method"""
        # just check the instance validity
        device = self.get_device_for_name(instance_name)
        if not device:
            raise pywbem.CIMError(pywbem.CIM_ERR_NOT_FOUND,
                    "Cannot find the device.")
        if self.storage.deviceDeps(device):
            deps = self.storage.deviceDeps(device)
            depnames = [device.path for device in deps]
            cmpi_logging.logger.info("Cannot remove %s, it's used by %s"
                    % (device.path, str(depnames)))
            raise pywbem.CIMError(pywbem.CIM_ERR_FAILED,
                    "The device is in use by %s" % str(depnames))

        self.do_delete_instance(device)

    @cmpi_logging.trace_method
    def get_redundancy(self, device):
        """
            Returns redundancy characteristics for given Anaconda StorageDevice.
        """
        parents = self.get_base_devices(device)
        if len(parents) > 0:
            # find all parents and get their redundancy
            redundancies = [self._find_redundancy(device) for device in parents]
            # iteratively call self.get_common_redundancy(r1, r2), ...
            final_redundancy = self.Redundancy.get_common_redundancy_list(
                    redundancies)
        else:
            # this device has no parents, assume it is simple disk
            final_redundancy = self.Redundancy(
                    no_single_point_of_failure=False,
                    data_redundancy=1,
                    package_redundancy=0,
                    stripe_length=1)
        return final_redundancy

    class Redundancy(object):
        """
            Class representing redundancy characteristics of a StorageExtent
            device, i.e. both StorageExtent and StoragePool
        """

        # constants for RAID levels
        RAID0 = 0
        RAID1 = 1
        RAID4 = 4
        RAID5 = 5
        RAID6 = 6
        RAID10 = 10
        LINEAR = 4096

        # ParityLayout
        PARITY_ROTATED = 2
        PARITY_NON_ROTATED = 1

        @cmpi_logging.trace_method
        def __init__(self, no_single_point_of_failure=False,
                     data_redundancy=1,
                     package_redundancy=0,
                     stripe_length=1,
                     parity_layout=None):
            self.no_single_point_of_failure = no_single_point_of_failure
            self.data_redundancy = data_redundancy
            self.package_redundancy = package_redundancy
            self.stripe_length = stripe_length
            self.parity_layout = parity_layout

        @cmpi_logging.trace_method
        def get_redundancy_raid0(self, second):
            """
                Return the combined data redundancy characteristics for
                two devices combined in RAID0.
            """
            # data is spread on all devices -> DataRedundancy is sum of base
            # DataRedundancies
            # PackageRedundancy is the minimum of PackageRedundancies
            data_redundancy = min(self.data_redundancy, second.data_redundancy)
            package_redundancy = min(self.package_redundancy,
                    second.package_redundancy)
            no_single_point_of_failure = (self.no_single_point_of_failure
                    and second.no_single_point_of_failure)
            stripe_length = self.stripe_length + second.stripe_length

            return DeviceProvider.Redundancy(
                    no_single_point_of_failure=no_single_point_of_failure,
                    data_redundancy=data_redundancy,
                    package_redundancy=package_redundancy,
                    stripe_length=stripe_length)

        @cmpi_logging.trace_method
        def get_redundancy_raid1(self, second):
            """
                Return the combined data redundancy characteristics for
                two devices combined in RAID1.
            """
            data_redundancy = self.data_redundancy + second.data_redundancy
            package_redundancy = (self.package_redundancy
                    + second.package_redundancy)
            no_single_point_of_failure = True
            stripe_length = min(self.stripe_length, second.stripe_length)

            return DeviceProvider.Redundancy(
                    no_single_point_of_failure=no_single_point_of_failure,
                    data_redundancy=data_redundancy,
                    package_redundancy=package_redundancy,
                    stripe_length=stripe_length)

        @cmpi_logging.trace_method
        def get_redundancy_raid5(self, second):
            """
                Return the combined data redundancy characteristics for
                two devices combined in RAID5.
            """
            data_redundancy = min(self.data_redundancy, second.data_redundancy)
            package_redundancy = min(self.package_redundancy,
                    second.package_redundancy)
            no_single_point_of_failure = True
            stripe_length = self.stripe_length + second.stripe_length

            return DeviceProvider.Redundancy(
                    no_single_point_of_failure=no_single_point_of_failure,
                    data_redundancy=data_redundancy,
                    package_redundancy=package_redundancy,
                    stripe_length=stripe_length,
                    parity_layout=self.PARITY_ROTATED)

        @cmpi_logging.trace_method
        def get_redundancy_raid4(self, second):
            """
                Return the combined data redundancy characteristics for
                two devices combined in RAID4.
            """
            redundancy = self.get_redundancy_raid5(second)
            redundancy.parity_layout = self.PARITY_NON_ROTATED
            return redundancy


        @cmpi_logging.trace_method
        def get_redundancy_raid6(self, second):
            """
                Return the combined data redundancy characteristics for
                two devices combined in RAID6.
            """
            data_redundancy = min(self.data_redundancy, second.data_redundancy)
            package_redundancy = min(self.package_redundancy,
                    second.package_redundancy)
            no_single_point_of_failure = True
            stripe_length = self.stripe_length + second.stripe_length

            return DeviceProvider.Redundancy(
                    no_single_point_of_failure=no_single_point_of_failure,
                    data_redundancy=data_redundancy,
                    package_redundancy=package_redundancy,
                    stripe_length=stripe_length,
                    parity_layout=self.PARITY_ROTATED)

        @cmpi_logging.trace_method
        def get_redundancy_raid10(self, second):
            """
                Return the combined data redundancy characteristics for
                two devices combined in RAID10.
            """
            data_redundancy = self.data_redundancy + second.data_redundancy
            package_redundancy = min(self.package_redundancy,
                    second.package_redundancy)
            no_single_point_of_failure = True
            stripe_length = self.stripe_length + second.stripe_length

            return DeviceProvider.Redundancy(
                    no_single_point_of_failure=no_single_point_of_failure,
                    data_redundancy=data_redundancy,
                    package_redundancy=package_redundancy,
                    stripe_length=stripe_length)


        @cmpi_logging.trace_method
        def get_redundancy_linear(self, second):
            """
                Return the combined data redundancy characteristics for
                two devices.
                Linear device is assumed, i.e. the data are either on self or
                on B.
            """
            # assume linear device, i.e. a data is either on A or on B
            # hence data_redundancy is the minimum of both
            data_redundancy = min(self.data_redundancy, second.data_redundancy)
            # assume the worst
            package_redundancy = min(self.package_redundancy,
                    second.package_redundancy)
            # both NoSinglePointOfFailure must be true to be the result true
            no_single_point_of_failure = (self.no_single_point_of_failure
                    and second.no_single_point_of_failure)
            #  we don't know if the data are on A or B, so assume the worst
            stripe_length = min(self.stripe_length, second.stripe_length)
            return DeviceProvider.Redundancy(
                    no_single_point_of_failure=no_single_point_of_failure,
                    data_redundancy=data_redundancy,
                    package_redundancy=package_redundancy,
                    stripe_length=stripe_length)

        @staticmethod
        @cmpi_logging.trace_function
        def get_common_redundancy_list(redundancy_list,
                 raid_level=LINEAR):
            """
                Return common redundancy characteristics for list of devices.
                Linear device is assumed, i.e. the data are either on self or
                on B.

                raid_level: LINEAR = Linear, 0,1,5,6 - raidX
            """
            if raid_level == DeviceProvider.Redundancy.LINEAR:
                redundancy = reduce(
                        lambda a, b: a.get_redundancy_linear(b),
                        redundancy_list)
            elif raid_level == DeviceProvider.Redundancy.RAID0:
                redundancy = reduce(
                        lambda a, b: a.get_redundancy_raid0(b),
                        redundancy_list)
            elif raid_level == DeviceProvider.Redundancy.RAID1:
                redundancy = reduce(
                        lambda a, b: a.get_redundancy_raid1(b),
                        redundancy_list)
                redundancy.package_redundancy = \
                        redundancy.package_redundancy + len(redundancy_list) - 1
            elif raid_level == DeviceProvider.Redundancy.RAID4:
                redundancy = reduce(
                        lambda a, b: a.get_redundancy_raid4(b),
                        redundancy_list)
                redundancy.package_redundancy = \
                    redundancy.package_redundancy + 1
            elif raid_level == DeviceProvider.Redundancy.RAID5:
                redundancy = reduce(
                        lambda a, b: a.get_redundancy_raid5(b),
                        redundancy_list)
                redundancy.package_redundancy = \
                    redundancy.package_redundancy + 1
            elif raid_level == DeviceProvider.Redundancy.RAID6:
                redundancy = reduce(
                        lambda a, b: a.get_redundancy_raid6(b),
                        redundancy_list)
                redundancy.package_redundancy = \
                    redundancy.package_redundancy + 2
            elif raid_level == DeviceProvider.Redundancy.RAID10:
                redundancy = reduce(
                        lambda a, b: a.get_redundancy_raid10(b),
                        redundancy_list)

                # stripe-length needs to be calculated separately
                # nr. of stripes for N=2: 1, N=3: 2, N=4: 2, N=5: 3, ...
                stripes = len(redundancy_list) // 2 + len(redundancy_list) % 2
                stripe_lengths = [x.stripe_length for x in redundancy_list]
                stripe_lengths.sort()
                # final stripe_length = sum of the 'stripes' lowest stripe
                # lengths
                stripe_lengths = stripe_lengths[:stripes]
                redundancy.stripe_length = reduce(
                        lambda a, b: a + b,
                        stripe_lengths)

                # data redundancy needs to be calculated separately
                # it's always 2 (at least for now),
                # i.e. sum of two lowest data redundancies
                data_redundancies = [x.data_redundancy for x in redundancy_list]
                data_redundancies.sort()
                redundancy.data_redundancy = (data_redundancies[0]
                        + data_redundancies[1])

                redundancy.package_redundancy = \
                    redundancy.package_redundancy + 1
            else:
                cmpi_logging.logger.trace_warn(
                        "Unknown raid_level: " + str(raid_level))
                return None
            return redundancy

    class Values(object):
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
