from enum import Enum
import numpy as np
from scipy.signal import get_window
import math


class DataFormats(Enum):
    IQ = 0
    INTERP = 1
    SEQ = 2


def load_IQ(file, bits):
    samples = []
    scale = (2 ** (bits - 1))
    for line in file:
        splitLine = line.split(',')
        value = (complex(float(splitLine[0].strip())/scale, float(splitLine[1].strip())/scale))
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
        if (self.format == DataFormats.IQ):
            self.samples = load_IQ(file, self.bits)
        else:
            raise ValueError('Unsupported IQ File Format Supplied')


class SignalAnalyzer():
    def __init__(self, data: IQdata):
        """
        Class requires an IQdata object containing samples and their metadata
        :param data:
        """
        self.dataT = data
        self.t = np.arange(0, self.dataT.datalen * (1 / self.dataT.sampleRate), 1 / self.dataT.sampleRate)
        self.getDataF()

    def getDataF(self, windowName='flattop'):
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
        magData = 20 * np.log10(np.abs(self.dataF))+13.32970267796
        freqData = self.f
        return freqData, magData
