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

from BasedOnProvider import BasedOnProvider
import pywbem

class LMI_MDRAIDBasedOn(BasedOnProvider):
    """
        Implementation of BasedOn class.
    """
    def __init__(self, *args, **kwargs):
        super(LMI_MDRAIDBasedOn, self).__init__(*args, **kwargs)


    def enumerateDevices(self):
        """
            Enumerate all devices, which are in this association as
            Dependent ones, i.e. all devices, which do not have any
            specialized BasedOn class
        """
        return self.storage.mdarrays
    
    def get_instance(self, env, model, device=None, base=None):
        model = super(LMI_MDRAIDBasedOn, self).get_instance(env, model, device, base)
        
        if not device:
            device = self.manager.getDeviceForName(model['Dependent'])
        if not base:
            base = self.manager.getDeviceForName(model['Antecedent'])
        
        model['OrderIndex'] = pywbem.Uint16(device.parents.index(base) + 1)
        
        return model
            
        
        
