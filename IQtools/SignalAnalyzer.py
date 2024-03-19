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
from scipy.signal import get_window
import math
from .IQdata import IQdata

class SignalAnalyzer():
    def __init__(self, data: IQdata, ref_level=0, ref_unit='dBFS'):
        """
        Class requires an IQdata object containing samples and their metadata
        :param data:
        """
        self.window = 'boxcar'
        self.ref_level = ref_level
        self.ref_unit = ref_unit
        self.dataT = data
        self.t = np.arange(0, self.dataT.datalen * (1 / self.dataT.sampleRate), 1 / self.dataT.sampleRate)
        self.getDataF()

    def getDataF(self, windowName='boxcar'):
        self.window = windowName
        window = get_window(windowName, self.dataT.datalen)
        windowedData = self.dataT.samples * window
        self.dataF = np.fft.fft(windowedData) / self.dataT.datalen
        self.f = np.fft.fftfreq(self.dataT.datalen) * (self.dataT.sampleRate)

    def getSpectrumMag(self, frequencyBase_Hz = 1):
        """
        Process spectral data into dBFS magnitude
        TODO: add support for basic manipulation of data scaling/offset
        :rtype: tuple of frequency array and array of dBFS spectrum values
        """
        magData = 20 * np.log10(np.abs(self.dataF)) + self.ref_level
        freqData = self.f/frequencyBase_Hz
        return freqData, magData

    def getPower(self, maxpower=np.inf):
        maglin = np.abs(self.dataF)**2
        maxpowerLin = 10**(maxpower/10)
        maglinFiltered = []
        for val in maglin:
            if(val>maxpowerLin):
                maglinFiltered+=[0]
            else:
                maglinFiltered+=[val]

        power = np.sqrt(sum(maglinFiltered))
        window = get_window(self.window, self.dataT.datalen)

        ecf = 1/np.sqrt(sum(window**2)/self.dataT.datalen)

        power = power*ecf

        return 20*np.log10(power)

    def getSubSpectrumMag(self, left, right, exclusiveLeft = True, exclusiveRight = False):
        # TODO: Implement
        pass


    def getPeakList(self, minpower = -np.inf, frequencyBase_Hz=1):
        f, magData = self.getSpectrumMag(frequencyBase_Hz=frequencyBase_Hz)
        prevSample = minpower
        samples = len(magData)
        peaks = []
        peaks_f = []
        for index in range(samples):
            sample = magData[index]
            if (sample < prevSample) and (prevSample > minpower):
                peaks.append(prevSample)
                peaks_f.append(self.f[index-1]/frequencyBase_Hz)
            prevSample = sample
        return peaks, peaks_f