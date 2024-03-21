import argparse

from .IQdata import IQdata
from .SignalAnalyzer import SignalAnalyzer
from .SignalGenerator import SignalGenerator
import numpy as np




def getPeaks(args=None):
    parser = argparse.ArgumentParser(description='Utility for getting peak spectrum values from an IQ data file')
    parser.add_argument('filename', help='File with IQ data', type=str)
    parser.add_argument('sampleRate', help='Complex sample rate of the file', type=float)
    parser.add_argument('-f', help='Frequency Units', type=float, default=1E6)
    parser.add_argument('-b', help='Number of signed bits for the ADC', type=int, default=12)
    parser.add_argument('-t', help='Threshold for peak detection (In dBFS by default)', type=float, default=-float('inf'))

    config = parser.parse_args(args)

    bits = config.b
    sampleRate = config.sampleRate
    filename = config.filename
    threshold = config.t
    frequencyUnits = config.f
    data = IQdata(filename, sampleRate, bits)
    sa = SignalAnalyzer(data)
    totalPower = sa.getPower()
    peaks, peaksF = sa.getPeakList(minpower=threshold, frequencyBase_Hz=frequencyUnits)
    print('Total Power: {0:.2f} dBFS'.format(totalPower))
    peaksFound = len(peaks)
    for index, peak, frequency in zip(range(peaksFound), peaks, peaksF):
        print('{index}: {peak:.2f} dBFS @ {frequency: 0.2f} MHz'.format(index=index, peak=peak, frequency=frequency))

def getSpectrum(args=None):
    parser = argparse.ArgumentParser(description='Utility for generating a frequency spectrum from an IQ data file')
    parser.add_argument('filename', help='File with IQ data', type=str)
    parser.add_argument('sampleRate', help='Complex sample rate of the file', type=float)
    parser.add_argument('-f', help='Frequency Units', type=float, default=1E6)
    parser.add_argument('-b', help='Number of signed bits for the ADC', type=int, default=12)
    parser.add_argument('-i', help='Generate a png of the spectrum instead of an ASCII plot', action='store_true')

    config = parser.parse_args(args)
    bits = config.b
    sampleRate = config.sampleRate
    filename = config.filename
    frequencyUnits = config.f
    data = IQdata(filename, sampleRate, bits)
    sa = SignalAnalyzer(data)
