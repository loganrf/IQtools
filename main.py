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
# Sample Script to demonstrate intended use of the IQtools features
from IQtools import *
import matplotlib.pyplot as plt
import os
import numpy as np

# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    a = DiscreteSignal('Sinusoid', {'freq':100,'phase':30})
    print(a)

    # Setting up a sample file
    sampleRate = 1e6  # Complex sample rate
    sigFreq = 400e3  # This is the frequency of the sample sinusoid. Should be < sample rate
    sigLen = 0.1  # Length of signal in seconds
    SAMPLE_OVERRIDE = True  # If you want to disable regeneration of the sample file every run then set to False
    Bits = 12  # Signed bits to represent sample values
    dBFS = -5 # Set sinusoid amplitude relative to full scale
    codeAmplitude = ((2 ** (Bits - 1)) * (10 ** (dBFS / 20)))
    nbits = 10

    if (not os.path.isfile('samples.csv')) or SAMPLE_OVERRIDE:
        t = np.arange(0, sigLen,
                      1 / sampleRate)  # Creates an array of discrete timepoints for the given sample rate/len
        noiseI = np.random.rand(len(t))*(2**(Bits-nbits))-2**(Bits-nbits-1)
        noiseQ = np.random.rand(len(t))*(2**(Bits-nbits))-2**(Bits-nbits-1)
        dataI = codeAmplitude * np.sin(t * np.pi * 2 * sigFreq) + noiseI # Create the in phase samples
        dataQ = codeAmplitude * np.sin(t * np.pi * 2 * sigFreq - (np.pi / 2)) + noiseQ  # Create the imaginary samples
        file = open('samples.csv', 'w')  # Create a file for the samples
        for i in range(len(t)):  # This loop stores all samples in a typical IQ csv format
            file.writelines(str(int(dataI[i])) + ', ' + str(int(dataQ[i])) + '\n')
        file.close()

    # Example of how to ingest a datafile. Note that bits must be set for accurate dBFS scaling
    data = IQdata('samples.csv', sampleRate, bits=12)
    # Once data has been ingested, pipe it into the signal analyzer object
    sa = SignalAnalyzer(data)
    # From there a scaled spectrum can be obtained by the following line. Note that this returns a tuple
    freq, mag = sa.getSpectrumMag()
    sigpwr = sa.getPower()
    npwr = sa.getPower(maxpower=-100)
    print(npwr)
    print('Signal Power is: ',str(sigpwr)+'dBFS with a SNR of '+str(sigpwr-npwr)+'dB')

    # Plot example
    plt.plot(freq, mag)
    plt.xlabel('Freq (MHz)')
    plt.ylabel('Magnitude (dBFS)')
    plt.title('Sample Sinusoid\nPeak Power: ' + str(int(max(mag))) + 'dBFS')
    plt.grid()
    plt.show()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
