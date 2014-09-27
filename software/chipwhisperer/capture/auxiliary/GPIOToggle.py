#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2014, NewAE Technology Inc
# All rights reserved.
#
# Authors: Colin O'Flynn
#
# Find this and more at newae.com - this file is part of the chipwhisperer
# project, http://www.assembla.com/spaces/chipwhisperer
#
#    This file is part of chipwhisperer.
#
#    chipwhisperer is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    chipwhisperer is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with chipwhisperer.  If not, see <http://www.gnu.org/licenses/>.
#=================================================
import sys

from PySide.QtCore import *
from PySide.QtGui import *

import time

try:
    from pyqtgraph.parametertree import Parameter
except ImportError:
    print "ERROR: PyQtGraph is required for this program"
    sys.exit()

from chipwhisperer.capture.auxiliary.AuxiliaryTemplate import AuxiliaryTemplate
from openadc.ExtendedParameter import ExtendedParameter

class GPIOToggle(AuxiliaryTemplate):
    paramListUpdated = Signal(list)

    def setupParameters(self):
        ssParams = [
                    {'name':'GPIO Pin', 'type':'list', 'key':'gpiopin', 'values':{'TargetIO1':0, 'TargetIO2':1, 'TargetIO3':2, 'TargetIO4':3}, 'value':2, 'set':self.settingsChanged},
                    {'name':'Standby State', 'type':'list', 'key':'inactive', 'values':{'High':True, 'Low':False}, 'value':False, 'set':self.settingsChanged},
                    {'name':'Toggle Length', 'type':'int', 'key':'togglelength', 'limits':(0, 10E3), 'value':250, 'suffix':'mS', 'set':self.settingsChanged},
                    {'name':'Post-Toggle Delay', 'type':'int', 'key':'toggledelay', 'limits':(0, 10E3), 'value':250, 'suffix':'mS', 'set':self.settingsChanged},
                    {'name':'Trigger', 'type':'list', 'key':'triggerloc', 'values':{'Campaign Init':0, 'Trace Arm':1, 'Trace Done':2, 'Campaign Done':3}, 'value':2, 'set':self.settingsChanged},
                    {'name':'Toggle Now', 'type':'action', 'action':self.trigger}
                    ]
        self.params = Parameter.create(name='GPIO Toggle', type='group', children=ssParams)
        ExtendedParameter.setupExtended(self.params, self)

        self.pin = None
        self.lastPin = None

        self.settingsChanged()

    def settingsChanged(self, ignored=None):
        self.pin = self.findParam('gpiopin').value()
        self.standby = self.findParam('inactive').value()
        self.triglength = self.findParam('togglelength').value() / 1000.0
        self.postdelay = self.findParam('toggledelay').value() / 1000.0
        self.triglocation = self.findParam('triggerloc').value()


    def checkMode(self):
        cwa = self.parent().scope.advancedSettings.cwEXTRA

        if self.pin != self.lastPin:
            # Turn off last used pin
            if self.lastPin:
                cwa.setTargetIOMode(IONumber=self.lastPin, setting=0)

            # Setup new pin
            cwa.setTargetIOMode(IONumber=self.pin, setting=cwa.IOROUTE_GPIOE)

            # Don't do this again
            self.lastPin = self.pin


    def trigger(self):
        self.checkMode()
        self.parent().scope.advancedSettings.cwEXTRA.setGPIOState(state=(not self.standby), IONumber=self.pin)
        time.sleep(self.triglength)
        self.parent().scope.advancedSettings.cwEXTRA.setGPIOState(state=self.standby, IONumber=self.pin)
        time.sleep(self.postdelay)

    def captureInit(self):
        self.checkMode()
        self.parent().scope.advancedSettings.cwEXTRA.setGPIOState(state=self.standby, IONumber=self.pin)

        if self.triglocation == 0:
            self.trigger()

    def captureComplete(self):
        if self.triglocation == 3:
            self.trigger()

    def traceArm(self):
        if self.triglocation == 1:
            self.trigger()

    def traceDone(self):
        if self.triglocation == 2:
            self.trigger()

    def testToggle(self):
        pass


