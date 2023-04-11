# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.
from IQtools import *
import matplotlib.pyplot as plt
import os
import numpy as np

# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    # Setting up a sample file
    sampleRate = 1e6 # Complex sample rate
    sigFreq = 200e3 # This is the frequency of the sample sinusoid. Should be < sample rate
    sigLen = 0.1 # Length of signal in seconds
    SAMPLE_OVERRIDE = True # If you want to disable regeneration of the sample file every run then set to False
    if((not os.path.isfile('samples.csv')) or SAMPLE_OVERRIDE):
        t = np.arange(0, sigLen, 1/sampleRate) # Creates an array of discrete timepoints for the given sample rate/len
        dataI = 1024*np.sin(t*np.pi*2*sigFreq) # Create the in phase samples
        dataQ = 1024 * np.sin(t * np.pi * 2 * sigFreq-(np.pi/2)) # Create the imaginary samples
        file = open('samples.csv', 'w') # Create a file for the samples
        for i in range(len(t)): # This loop stores all samples in a typical IQ csv format
            file.writelines(str(int(dataI[i]))+', '+str(int(dataQ[i]))+'\n')
        file.close()

    # Example of how to ingest a datafile. Note that bits must be set for accurate dBFS scaling
    data = IQdata('samples.csv', sampleRate, bits=12)
    # Once data has been ingested, pipe it into the signal analyzer object
    sa = SignalAnalyzer(data)
    # From there a scaled spectrum can be obtained by the following line. Note that this returns a tuple
    freq, mag = sa.getSpectrumMag()

    # Plot example
    plt.plot(freq, mag)
    plt.xlabel('Freq (MHz)')
    plt.ylabel('Magnitude (dBFS)')
    plt.title('Sample Sinusoid')
    plt.show()





# See PyCharm help at https://www.jetbrains.com/help/pycharm/
