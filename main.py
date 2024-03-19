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

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    sg = IQtools.SignalGenerator(10E6, 12, 0.1)
    sg.addSinusoid(0.5, 1E6)
    sg.addSinusoid(0.3, 2E6)
    sg.addSinusoid(0.1, 2.5E6)

    sg.saveToFile('test.csv')

    generatedData = IQtools.IQdata('test.csv', 10E6, 12)

    sa = IQtools.SignalAnalyzer(generatedData)
    f, mag = sa.getSpectrumMag(frequencyBase_Hz=1E6)
    totalPower = sa.getPower()
    peaks, peaksF = sa.getPeakList(minpower=-30, frequencyBase_Hz=1E6)

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



# See PyCharm help at https://www.jetbrains.com/help/pycharm/
