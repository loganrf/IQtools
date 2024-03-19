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

from enum import Enum


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