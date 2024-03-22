import argparse

from .IQdata import IQdata
from .SignalAnalyzer import SignalAnalyzer
from .SignalGenerator import SignalGenerator
import matplotlib.pyplot as plt




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
    parser.add_argument('-s', help='Save the image to a png instead of showing it', action='store_true')


    config = parser.parse_args(args)
    bits = config.b
    sampleRate = config.sampleRate
    filename = config.filename
    frequencyUnits = config.f
    data = IQdata(filename, sampleRate, bits)
    saveFig = config.s
    sa = SignalAnalyzer(data)
    f, mag = sa.getSpectrumMag()
    plt.plot(f, mag)
    plt.ylim((-100, 0))
    plt.ylabel('dBFS')
    plt.xlabel('MHz')
    plt.title(filename.split('.')[0])
    plt.grid()
    plt.tight_layout()
    if saveFig:
        plt.savefig(filename.split('.')[0]+'.png')
    else:
        plt.show()
        plt.clf()

def generateCW(args=None):
    parser = argparse.ArgumentParser(description='Utility for generating a CW IQ signal')
    parser.add_argument('filename', help='Output File', type=str)
    parser.add_argument('level', help='Output amplitude (0 to 1.0)', type=float)
    parser.add_argument('baseBandFrequency', help='Baseband frequency (must be within Nyquist, +/- Fs/2)', type=float)
    parser.add_argument('sampleRate', help='Complex sample rate of the file', type=float)
    parser.add_argument('duration', help='Duration of sample file in milliseconds', type=float)
    parser.add_argument('-p', help='phase offset (rads)', type=float, default=0)
    parser.add_argument('-b', help='Number of signed bits for the ADC', type=int, default=12)



    config = parser.parse_args(args)
    bits = config.b
    sampleRate = config.sampleRate
    filename = config.filename
    level = config.level
    duration = config.duration
    phaseOffset = config.p
    bbFreq = config.baseBandFrequency
    sg = SignalGenerator(sampleRate, bits, duration/1000)
    sg.addSinusoid(level, bbFreq, phaseRads=phaseOffset)
    sg.saveToFile(filename)

