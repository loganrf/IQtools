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
import pandas


class DataFormats(Enum):
    IQ = 0
    INTERP = 1
    SEQ = 2


def load_IQ(file, bits):
    samples = []
    scale = (2 ** (bits - 1))
    for line in file:
        splitLine = line.split(',')
        value = (complex(float(splitLine[0].strip()) / scale, float(splitLine[1].strip()) / scale))
        samples.append(value)
    return samples


class IQdata:
    def __init__(self, fileName: str, sampleRate: float, bits=0, format=DataFormats.IQ, refOffset=0):
        """
        Initializes a data structure for IQ samples and their metadata
        :param fileName: Source datafile TODO: Add support for nonfile input
        :param sampleRate: Complex samplerate of the data
        :param bits:  Bitness of the data (assumes signed data)
        :param format: Not currently used
        :param refOffset: Not currently used
        """
        self.sampleRate = sampleRate
        self.bits = bits
        self.format = format
        self.refOffset = refOffset
        self.loadData(fileName)
        self.datalen = len(self.samples)

    def loadData(self, fileName: str) -> None:
        """
        Helper function for loading samples from a file
        :param fileName:
        """
        file = open(fileName, 'r')
        if self.format == DataFormats.IQ:
            self.samples = load_IQ(file, self.bits)
        else:
            raise ValueError('Unsupported IQ File Format Supplied')

class PeakSearch():
    def __init__(self, data: (float, float)):
        self.data = [data[0], data[1]]

    def getPeaks(self, xThreshold = (-math.inf, math.inf), yThreshold = (-math.inf, math.inf)):
        pass

class SignalAnalyzer():
    def __init__(self, data: IQdata):
        """
        Class requires an IQdata object containing samples and their metadata
        :param data:
        """
        self.window = 'boxcar'
        self.dataT = data
        self.t = np.arange(0, self.dataT.datalen * (1 / self.dataT.sampleRate), 1 / self.dataT.sampleRate)
        self.getDataF()

    def getDataF(self, windowName='boxcar'):
        self.window = windowName
        window = get_window(windowName, self.dataT.datalen)
        windowedData = self.dataT.samples * window
        self.dataF = np.fft.fft(windowedData) / self.dataT.datalen
        self.f = np.fft.fftfreq(self.dataT.datalen) * (self.dataT.sampleRate)

    def getSpectrumMag(self):
        """
        Process spectral data into dBFS magnitude
        TODO: add support for basic manipulation of data scaling/offset
        :rtype: tuple of frequency array and array of dBFS spectrum values
        """
        magData = 20 * np.log10(np.abs(self.dataF))
        freqData = self.f
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
        signals = []

    def addSinusoid(self, frequency, phaseRads = 0, makeCyclical = False):
        if(makeCyclical):
            pass


