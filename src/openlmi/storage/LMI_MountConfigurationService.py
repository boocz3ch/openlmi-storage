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
"""
Python Provider for LMI_MountConfigurationService

Instruments the CIM class LMI_MountConfigurationService
"""

import pywbem
import blivet
from openlmi.storage.MountingProvider import MountingProvider
from openlmi.storage.ServiceProvider import ServiceProvider
from openlmi.common.JobManager import Job
import openlmi.common.cmpi_logging as cmpi_logging

class LMI_MountConfigurationService(ServiceProvider, MountingProvider):
    """Instrument the CIM class LMI_MountConfigurationService

    A Service is a LogicalElement that represents the availability of
    functionality that can be managed. This functionality may be provided
    by a seperately modeled entity such as a LogicalDevice or a
    SoftwareFeature, or both. The modeled Service typically provides only
    functionality required for management of itself or the elements it
    affects.

    """

    @cmpi_logging.trace_method
    def __init__ (self, *args, **kwargs):
        super(LMI_MountConfigurationService, self).__init__(
            classname="LMI_MountConfigurationService",
            *args, **kwargs)

    @cmpi_logging.trace_method
    def _check_sane_arguments(self, **kwargs):
        """
        Check for empty parameters. Throw an error if there are any.
        """
        for p, a in kwargs.items():
            if a is None:
                raise pywbem.CIMError(pywbem.CIM_ERR_FAILED,
                                      "Empty paramater: %s." % p)

    @cmpi_logging.trace_method
    def get_mountopts_from_goal(self, goal):
        if goal:
            # XXX fill mountopts; this does not work yet... blivet
            # mountopts = goal.get('OtherOptions', None)
            mountopts = ['rw', 'user', 'relatime'] # for now
        else:
            # use defaults
            mountopts = ['rw', 'suid', 'dev', 'exec', 'auto', 'nouser', 'async']
        return mountopts

    @cmpi_logging.trace_method
    def _parse_goal(self, param_goal, classname):
        """
            Find Setting for given CIMInstanceName and check, that it is
            of given CIM class.
            Return None, if no Goal was given.
            Raise CIMError, if the Goal cannot be found.
        """
        if param_goal:
            instance_id = param_goal['InstanceID']
            goal = self.provider_manager.get_setting_for_id(
                instance_id, classname)
            if not goal:
                raise pywbem.CIMError(pywbem.CIM_ERR_INVALID_PARAMETER,
                    classname + " Goal was not found.")
        else:
            goal = None
        return goal

    @cmpi_logging.trace_method
    def cim_method_createmount(self, env, object_name,
                               param_goal=None,
                               param_filesystemtype=None,
                               param_mode=None,
                               param_filesystem=None,
                               param_mountpoint=None,
                               param_filesystemspec=None):
        """Implements LMI_MountConfigurationService.CreateMount()

        Mounts the specified filesystem to a mountpoint.

        Keyword arguments:
        env -- Provider Environment (pycimmb.ProviderEnvironment)
        object_name -- A pywbem.CIMInstanceName or pywbem.CIMCLassName
            specifying the object on which the method CreateMount()
            should be invoked.
        param_goal --  The input parameter Goal (type REF (pywbem.CIMInstanceName(classname='LMI_MountedFileSystemSetting', ...))
            Desired mount settings. If NULL, defaults will be used. Default
            mount options are 'rw, suid, dev, exec, auto, nouser, async'.

        param_filesystemtype --  The input parameter FileSystemType (type unicode)
            Filesystem type. If NULL, perform a binding mount. If mounting
            a local filesystem, this parameter has to be in agreement with
            the FileSystem.

        param_mode --  The input parameter Mode (type pywbem.Uint16 self.Values.CreateMount.Mode)
            The mode in which the configuration is to be applied to the
            MountedFileSystem. IsNext and IsCurrent are properties of
            LMI_MountedFileSystemElementSettingData, which will be
            created. Meaning of IsNext and IsCurrent is:  IsCurrent = 1:
            The filesystem will be mounted. IsCurrent = 2: The filesystem
            will be unmounted. IsNext = 1: A persistent entry will be
            created (in /etc/fstab).  IsNext = 2: The persistent entry
            will be removed.  Mode 1 - IsNext = 1, IsCurrent = 1. Mode 2 -
            IsNext = 1, IsCurrent not affected. Mode 4 - IsNext = 2,
            IsCurrent = 2. Mode 5 - IsNext = 2, IsCurrent not affected.
            Mode 32768 - IsNext not affected, IsCurrent = 1. Mode 32769 -
            IsNext not affected, IsCurrent = 2.

        param_filesystem --  The input parameter FileSystem (type REF (pywbem.CIMInstanceName(classname='CIM_FileSystem', ...))
            Existing filesystem that should be mounted. If NULL, mount a
            remote filesystem, or mount a non-device filesystem (e.g.
            tmpfs). If not NULL, mount a local filesystem. When mounting a
            local filesystem, the FileSystemType parameter has to agree
            with the type of FileSystem.

        param_mountpoint --  The input parameter MountPoint (type unicode)
            Directory where the mounted filesystem should be attached at.

        param_filesystemspec --  The input parameter FileSystemSpec (type unicode)
            Filesystem specification. Specifies the device that should be
            mounted. Remote filesystems can be specified in their usual
            form (e.g. 'hostname:/share' for NFS, or '//hostname/share'
            for CIFS). Non-device filesystems can also be specified (e.g.
            'tmpfs' or 'sysfs'). When performing a bind mount,
            FileSystemSpec is the path to the source directory.


        Returns a two-tuple containing the return value (type pywbem.Uint32 self.Values.CreateMount)
        and a list of CIMParameter objects representing the output parameters

        Output parameters:
        Mount -- (type REF (pywbem.CIMInstanceName(classname='LMI_MountedFileSystem', ...))
            Reference to the created LMI_MountedFileSystem instance.

        Job -- (type REF (pywbem.CIMInstanceName(classname='CIM_ConcreteJob', ...))
            Reference to the created job.


        Possible Errors:
        CIM_ERR_ACCESS_DENIED
        CIM_ERR_INVALID_PARAMETER (including missing, duplicate,
            unrecognized or otherwise incorrect parameters)
        CIM_ERR_NOT_FOUND (the target CIM Class or instance does not
            exist in the specified namespace)
        CIM_ERR_METHOD_NOT_AVAILABLE (the CIM Server is unable to honor
            the invocation request)
        CIM_ERR_FAILED (some other unspecified error occurred)

        """

        # sanity checks
        self.check_instance(object_name)
        args = {'FileSystem':param_filesystem,
                'Mode':param_mode,
                'MountPoint':param_mountpoint,
                'FileSystemSpec':param_filesystemspec}
        self._check_sane_arguments(**args)
        if param_mode not in [self.MountMethod.Mode.Mode_1,
                              self.MountMethod.Mode.Mode_2,
                              self.MountMethod.Mode.Mode_32768]:
            raise pywbem.CIMError(pywbem.CIM_ERR_INVALID_PARAMETER,
                                  "Mode %d without effect." % param_mode)

        mountopts = self.get_mountopts_from_goal(param_goal)

        if param_filesystem:
            # mount a local filesystem; types and specs have to match
            (device, fmt) = self.get_device_and_format_from_fs(param_filesystem)

            if fmt.type != param_filesystemtype:
                raise pywbem.CIMError(pywbem.CIM_ERR_FAILED,
                                      "Filesystem types don't match.")
            if device.path != param_filesystemspec:
                raise pywbem.CIMError(pywbem.CIM_ERR_FAILED,
                                      "Device paths don't match.")
        else:
            # mount remote/non-device filesystem
            raise pywbem.CIMError(pywbem.CIM_ERR_NOT_SUPPORTED,
                                  "Can't mount remote/non-device filesystems. Yet...")

        # remember input parameters for job
        input_arguments = {
                'Goal' : pywbem.CIMProperty(name='Goal',
                        type='reference',
                        value=param_goal),
                'FileSystemType' : pywbem.CIMProperty(name='FileSystemType',
                        type='string',
                        value=param_filesystemtype),
                'Mode' : pywbem.CIMProperty(name='Mode',
                        type='uint16',
                        value=param_mode),
                'FileSystem' : pywbem.CIMProperty(name='FileSystem',
                        type='reference',
                        value=param_filesystem),
                'MountPoint' : pywbem.CIMProperty(name='MountPoint',
                        type='string',
                        value=param_mountpoint),
                'FileSystemSpec' : pywbem.CIMProperty(name='FileSystemSpec',
                        type='string',
                        value=param_filesystemspec)
                }

        # create Job
        job = Job(job_manager=self.job_manager,
                  job_name="CREATE MOUNT %s %s (t:%s o:%s)"
                           % (param_filesystemspec,
                              param_mountpoint,
                              param_filesystemtype,
                              ",".join(mountopts)),
                  input_arguments=input_arguments,
                  method_name="CreateMount",
                  affected_elements=[param_filesystem],
                  owning_element=self._get_instance_name())
        job.set_execute_action(self._create_mount, job, param_mode,
                               param_filesystemtype, param_filesystemspec,
                               param_mountpoint, mountopts)
        self.job_manager.add_job(job)

        rval = self.RequestStateChange.Method_Parameters_Checked___Job_Started
        outparams = [(pywbem.CIMParameter(
                name='Job',
                type='reference',
                value=job.get_name()))]
        return (rval, outparams)

    @cmpi_logging.trace_method
    def _create_mount(self, job, mode, fstype, fsspec, mountpoint, mountopts):
        """
        Really create mount. All checks have already been done.
        Mode = 1 --> mount and persistent
        Mode = 2 --> persistent
        Mode = 32768 --> mount
        """
        # mount
        if mode == self.MountMethod.Mode.Mode_1 or \
           mode == self.MountMethod.Mode.Mode_32768:
            rc = blivet.util.mount(fsspec, mountpoint, fstype, ",".join(mountopts))

            rval = self.MountMethod.Job_Completed_with_No_Error
            state = Job.STATE_FINISHED_OK
            err = None

            if rc != 0:
                rval = self.MountMethod.Failed
                state = Job.STATE_FAILED
                # XXX it will be nice if blivet also returned a nice error
                # message,provide a meaningful error message so it could be
                # provided here
                err = pywbem.CIMError(pywbem.CIM_ERR_FAILED,
                                      "Mount failed (%d)." % rc)

        # create fstab entry
        if mode == self.MountMethod.Mode.Mode_1 or \
           mode == self.MountMethod.Mode.Mode_2:
            # XXX not supported yet
            raise pywbem.CIMError(pywbem.CIM_ERR_NOT_SUPPORTED,
                                  "Persistent entries not supported. Yet...")

        mfsname = pywbem.CIMInstanceName(
            classname='LMI_MountedFileSystem',
            namespace=self.config.namespace,
            keybindings={
                'FileSystemSpec' : fsspec,
                'MountPointPath' : mountpoint
                })
        outparams = {'Mount' : mfsname}
        job.finish_method(
            state,
            return_value=rval,
            return_type=Job.ReturnValueType.Uint32,
            output_arguments=outparams,
            affected_elements=[mfsname],
            error=err)

    @cmpi_logging.trace_method
    def cim_method_deletemount(self, env, object_name,
                               param_mount=None,
                               param_mode=None):
        """Implements LMI_MountConfigurationService.DeleteMount()

        Unmounts an existing mount.

        Keyword arguments:
        env -- Provider Environment (pycimmb.ProviderEnvironment)
        object_name -- A pywbem.CIMInstanceName or pywbem.CIMCLassName
            specifying the object on which the method DeleteMount()
            should be invoked.
        param_mount --  The input parameter Mount (type REF (pywbem.CIMInstanceName(classname='LMI_MountedFileSystem', ...))
            An existing mount.

        param_mode --  The input parameter Mode (type pywbem.Uint16 self.Values.DeleteMount.Mode)
            The mode in which the configuration is to be applied to the
            MountedFileSystem. Mode 1 - IsNext = 1, IsCurrent = 1. Mode 2
            - IsNext = 1, IsCurrent not affected. Mode 4 - IsNext = 2,
            IsCurrent = 2. Mode 5 - IsNext = 2, IsCurrent not affected.
            Mode 32768 - IsNext not affected, IsCurrent = 1. Mode 32769 -
            IsNext not affected, IsCurrent = 2.


        Returns a two-tuple containing the return value (type pywbem.Uint32 self.Values.DeleteMount)
        and a list of CIMParameter objects representing the output parameters

        Output parameters:
        Job -- (type REF (pywbem.CIMInstanceName(classname='CIM_ConcreteJob', ...))
            Reference to the created job.


        Possible Errors:
        CIM_ERR_ACCESS_DENIED
        CIM_ERR_INVALID_PARAMETER (including missing, duplicate,
            unrecognized or otherwise incorrect parameters)
        CIM_ERR_NOT_FOUND (the target CIM Class or instance does not
            exist in the specified namespace)
        CIM_ERR_METHOD_NOT_AVAILABLE (the CIM Server is unable to honor
            the invocation request)
        CIM_ERR_FAILED (some other unspecified error occurred)

        """

        # sanity checks
        self.check_instance(object_name)
        args = {'Mount':param_mount,
                'Mode':param_mode}
        self._check_sane_arguments(**args)
        if param_mode not in [self.MountMethod.Mode.Mode_4,
                              self.MountMethod.Mode.Mode_5,
                              self.MountMethod.Mode.Mode_32769]:
            raise pywbem.CIMError(pywbem.CIM_ERR_INVALID_PARAMETER,
                                  "Mode %d without effect." % param_mode)

        # remember input parameters for job
        input_arguments = {
                'Mount' : pywbem.CIMProperty(name='Mount',
                        type='reference',
                        value=param_mount),
                'Mode' : pywbem.CIMProperty(name='Mode',
                        type='uint16',
                        value=param_mode)
                }

        # create Job
        job = Job(job_manager=self.job_manager,
                  job_name="DELETE MOUNT %s" % param_mount['MountPointPath'],
                  input_arguments=input_arguments,
                  method_name="DeleteMount",
                  affected_elements=[param_mount],
                  owning_element=self._get_instance_name())
        job.set_execute_action(self._delete_mount, job,
                               param_mode, param_mount['MountPointPath'])
        self.job_manager.add_job(job)

        rval = self.RequestStateChange.Method_Parameters_Checked___Job_Started
        outparams = [(pywbem.CIMParameter(
            name='Job',
            type='reference',
            value=job.get_name()))]
        return (rval, outparams)

    @cmpi_logging.trace_method
    def _delete_mount(self, job, mode, mountpoint):
        """
        Really delete mount. All checks have already been done.
        Mode = 4 --> unmount and remove persistent
        Mode = 5 --> remove persistent
        Mode = 32769 --> unmount
        """
        # unmount
        if mode == self.MountMethod.Mode.Mode_4 or \
           mode == self.MountMethod.Mode.Mode_32769:
            rc = blivet.util.umount(mountpoint)

            rval = self.MountMethod.Job_Completed_with_No_Error
            state = Job.STATE_FINISHED_OK
            err = None

            if rc != 0:
                rval = self.MountMethod.Failed
                state = Job.STATE_FAILED
                # XXX it will be nice if blivet also returned a nice error
                # message,provide a meaningful error message so it could be
                # provided here
                err = pywbem.CIMError(pywbem.CIM_ERR_FAILED,
                                      "Unmount failed (%d)." % rc)

        # delete fstab entry
        if mode == self.MountMethod.Mode.Mode_4 or \
           mode == self.MountMethod.Mode.Mode_5:
            # XXX not supported yet
            raise pywbem.CIMError(pywbem.CIM_ERR_NOT_SUPPORTED,
                                  "Persistent entries not supported. Yet...")

        job.finish_method(
            state,
            return_value=rval,
            return_type=Job.ReturnValueType.Uint32,
            error=err)

    @cmpi_logging.trace_method
    def cim_method_modifymount(self, env, object_name,
                               param_mount=None,
                               param_mode=None,
                               param_goal=None):
        """
        Implements LMI_MountConfigurationService.ModifyMount()

        Modifies (remounts) an existing mount.

        Keyword arguments:
        env -- Provider Environment (pycimmb.ProviderEnvironment)
        object_name -- A pywbem.CIMInstanceName or pywbem.CIMCLassName
            specifying the object on which the method ModifyMount()
            should be invoked.
        param_mount --  The input parameter Mount (type REF (pywbem.CIMInstanceName(classname='LMI_MountedFileSystem', ...))
            Reference to the LMI_Mount instance that is being modified.

        param_mode --  The input parameter Mode (type pywbem.Uint16 self.Values.ModifyMount.Mode)
            The mode in which the configuration is to be applied to the
            MountedFileSystem. Mode 1 - IsNext = 1, IsCurrent = 1. Mode 2
            - IsNext = 1, IsCurrent not affected. Mode 4 - IsNext = 2,
            IsCurrent = 2. Mode 5 - IsNext = 2, IsCurrent not affected.
            Mode 32768 - IsNext not affected, IsCurrent = 1. Mode 32769 -
            IsNext not affected, IsCurrent = 2.

        param_goal --  The input parameter Goal (type REF (pywbem.CIMInstanceName(classname='LMI_MountedFileSystemSetting', ...))
            Desired mount settings. If NULL, the mount options are not
            changed. If mount (or an fstab entry) should be performed
            (created), the appropriate respective MountedFileSystemSetting
            will be created.


        Returns a two-tuple containing the return value (type pywbem.Uint32 self.Values.ModifyMount)
        and a list of CIMParameter objects representing the output parameters

        Output parameters:
        Job -- (type REF (pywbem.CIMInstanceName(classname='CIM_ConcreteJob', ...))
            Reference to the created job.

        Mount -- (type REF (pywbem.CIMInstanceName(classname='LMI_MountedFileSystem', ...))
            Reference to the LMI_Mount instance that is being modified.


        Possible Errors:
        CIM_ERR_ACCESS_DENIED
        CIM_ERR_INVALID_PARAMETER (including missing, duplicate,
            unrecognized or otherwise incorrect parameters)
        CIM_ERR_NOT_FOUND (the target CIM Class or instance does not
            exist in the specified namespace)
        CIM_ERR_METHOD_NOT_AVAILABLE (the CIM Server is unable to honor
            the invocation request)
        CIM_ERR_FAILED (some other unspecified error occurred)

        """
        # sanity checks
        self.check_instance(object_name)
        args = {'Mount':param_mount,
                'Mode':param_mode}
        self._check_sane_arguments(**args)
        if param_mode not in [self.MountMethod.Mode.Mode_1,
                              self.MountMethod.Mode.Mode_2,
                              self.MountMethod.Mode.Mode_32768]:
            raise pywbem.CIMError(pywbem.CIM_ERR_INVALID_PARAMETER,
                                  "Mode %d without effect." % param_mode)

        mountopts = self.get_mountopts_from_goal(param_goal)

        # remember input parameters for job
        input_arguments = {
                'Mount' : pywbem.CIMProperty(name='Mount',
                        type='reference',
                        value=param_mount),
                'Mode' : pywbem.CIMProperty(name='Mode',
                        type='uint16',
                        value=param_mode),
                'Goal' : pywbem.CIMProperty(name='Goal',
                        type='reference',
                        value=param_goal)
                }

        mountpoint = param_mount['MountPointPath']
        fsspec = param_mount['FileSystemSpec']

        # create Job
        job = Job(job_manager=self.job_manager,
                  job_name="MODIFY MOUNT %s %s (o:%s)"
                           % (fsspec, mountpoint, ",".join(mountopts)),
                  input_arguments=input_arguments,
                  method_name="ModifyMount",
                  affected_elements=[param_mount],
                  owning_element=self._get_instance_name())
        job.set_execute_action(self._modify_mount, job,
                               fsspec, mountpoint, mountopts)
        self.job_manager.add_job(job)

        rval = self.RequestStateChange.Method_Parameters_Checked___Job_Started
        outparams.append(pywbem.CIMParameter(
                name='Job',
                type='reference',
                value=job.get_name()))
        return (rval, outparams)

    @cmpi_logging.trace_method
    def _modify_mount(self, job, fsspec, mountpoint, mountopts):
        """
        Really modify mount. All checks have been done.
        """
        # XXX just raise error for now
        # there is now way to use blivet to remount stuff now
        raise pywbem.CIMError(pywbem.CIM_ERR_FAILED,
                              "Modifying mounts not supported yet.")

        rval = self.MountMethod.Job_Completed_with_No_Error
        state = Job.STATE_FINISHED_OK
        err = None

        mfsname = pywbem.CIMInstanceName(
            classname='LMI_MountedFileSystem',
            namespace=self.config.namespace,
            keybindings={
                'FileSystemSpec' : fsspec,
                'MountPointPath' : mountpoint
                })
        outparams = {'Mount' : mfsname}

        job.finish_method(
            state,
            return_value=rval,
            return_type=Job.ReturnValueType.Uint32,
            output_arguments=outparams
            affected_elements=[mfsname],
            error=err)

    class RequestStateChange(object):
        Completed_with_No_Error = pywbem.Uint32(0)
        Not_Supported = pywbem.Uint32(1)
        Unknown_or_Unspecified_Error = pywbem.Uint32(2)
        Cannot_complete_within_Timeout_Period = pywbem.Uint32(3)
        Failed = pywbem.Uint32(4)
        Invalid_Parameter = pywbem.Uint32(5)
        In_Use = pywbem.Uint32(6)
        # DMTF_Reserved = ..
        Method_Parameters_Checked___Job_Started = pywbem.Uint32(4096)
        Invalid_State_Transition = pywbem.Uint32(4097)
        Use_of_Timeout_Parameter_Not_Supported = pywbem.Uint32(4098)
        Busy = pywbem.Uint32(4099)
        # Method_Reserved = 4100..32767
        # Vendor_Specific = 32768..65535

    class MountMethod(object):
        Job_Completed_with_No_Error = pywbem.Uint32(0)
        Not_Supported = pywbem.Uint32(1)
        Unknown = pywbem.Uint32(2)
        Timeout = pywbem.Uint32(3)
        Failed = pywbem.Uint32(4)
        Invalid_Parameter = pywbem.Uint32(5)
        In_Use = pywbem.Uint32(6)
        # DMTF_Reserved = ..
        Method_Parameters_Checked___Job_Started = pywbem.Uint32(4096)
        # Method_Reserved = 4098..32767
        # Vendor_Specific = 32768..65535
        class Mode(object):
            Mode_0 = pywbem.Uint16(0)
            Mode_1 = pywbem.Uint16(1)
            Mode_2 = pywbem.Uint16(2)
            Mode_3 = pywbem.Uint16(3)
            Mode_4 = pywbem.Uint16(4)
            Mode_5 = pywbem.Uint16(5)
            Mode_6 = pywbem.Uint16(6)
            # DMTF_Reserved = ..
            Mode_32768 = pywbem.Uint16(32768)
            Mode_32769 = pywbem.Uint16(32769)
