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

import IQtools
import matplotlib.pyplot as plt

if __name__ == '__main__':
    # Create a signal generator instance to creat an IQ file. Use a 10MSps complex sample rate, 12 bit signed ints and
    # a 0.1s duration
    sg = IQtools.SignalGenerator(10E6, 12, 0.1)

    # Add 3 sinusoids to the signal at -1MHz, 2MHz, and 2.5MHz. Amplitude is defined in terms of FS range (0-1)
    sg.addSinusoid(0.5, -1E6)
    sg.addSinusoid(0.3, 2E6)
    sg.addSinusoid(0.1, 2.5E6)

    # Export IQ samples from signal to a csv
    sg.saveToFile('test.csv')

    # Pull the generated IQ files back into IQTools with an appropriate sample rate/bitness
    generatedData = IQtools.IQdata('test.csv', 10E6, 12)

    # Generate a signal analyzer instance
    sa = IQtools.SignalAnalyzer(generatedData)
    # Generate spectrum
    f, mag = sa.getSpectrumMag(frequencyBase_Hz=1E6)
    # Get total inband power
    totalPower = sa.getPower()
    # Get a list of peaks greater than -30dBFS
    peaks, peaksF = sa.getPeakList(minpower=-30, frequencyBase_Hz=1E6)

    # Plot everything generated above

    plt.plot(f, mag)
    plt.text(-4.95, -10, 'Total Power: {power: .2f} dBFS'.format(power=totalPower))
    peakList = 'Peak List:\n'
    for peak, freq in zip(peaks, peaksF):
        peakList+='{peakLevel: .2f} dBFS @ {freqPoint: .2f} MHz\n'.format(peakLevel=peak, freqPoint=freq)
    plt.text(-4.95, -35, peakList)

    plt.ylabel('Amplitude (dBFS)')
    plt.xlabel('Frequency (MHz)')
    plt.title('Sample IQ Data Plot')
    plt.grid()
    plt.ylim((-100,0))
    plt.show()



