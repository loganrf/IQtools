"""
    IQtools - Utilities for IQ data visualization/manipulation in Python
    Copyright (C) 2023  Logan Fagg

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

# Source file for IQtools functions

from enum import Enum
import numpy as np
from .IQdata import IQdata


class DiscreteSignal():
    def __init__(self, description, params: {}):
        self.description = description
        self.params = params

    def __str__(self):
        info = self.description + ' ('
        for p,v in self.params.items():
            info+=p+':'+str(v)+', '
        info = info[:-2]+')'
        return info


class SignalGenerator():

    def __init__(self, sampleRate, bits, duration):
        self.sampleRate = sampleRate
        self.bits = bits
        self.duration = duration
        self.t = np.arange(0, self.duration, 1/self.sampleRate)
        self.s = np.zeros(np.size(self.t))
        self.FS = (2**(self.bits-1))-1

    def addSinusoid(self,amplitude_Rel_FS, frequency, phaseRads = 0):
        newSig = amplitude_Rel_FS*self.FS*(np.cos(frequency*2*3.14159*self.t+phaseRads)+1j*np.sin(frequency*2*3.14159*self.t+phaseRads))
        self.s = self.s + newSig

    def saveToFile(self, filename):
        with open(filename, 'w') as outPutFile:
            for sample in self.s:
                idata = sample.real
                qdata = sample.imag
                outPutFile.write(str(int(idata))+','+str(int(qdata))+'\n')
