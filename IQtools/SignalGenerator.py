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

import numpy as np
from typing import Optional, Sequence


class DiscreteSignal():
    def __init__(self, description, params: {}):
        self.description = description
        self.params = params

    def __str__(self):
        info = self.description + ' ('
        for p, v in self.params.items():
            info += p + ':' + str(v) + ', '
        info = info[:-2] + ')'
        return info


class SignalGenerator():

    def __init__(self, sampleRate, bits, duration):
        self.sampleRate = sampleRate
        self.bits = bits
        self.duration = duration
        self.t = np.arange(0, self.duration, 1 / self.sampleRate)
        self.s = np.zeros(np.size(self.t), dtype=complex)
        self.FS = (2 ** (self.bits - 1)) - 1

    @staticmethod
    def _coerce_amplitude(amplitude, unit="FS"):
        if unit.upper() == 'DBFS':
            return 10 ** (amplitude / 20)
        return amplitude

    def addSinusoid(self, amplitude_Rel_FS, frequency, phaseRads=0, amplitude_unit='FS'):
        amplitude = self._coerce_amplitude(amplitude_Rel_FS, amplitude_unit)
        newSig = amplitude * (np.cos(frequency * 2 * np.pi * self.t + phaseRads) +
                              1j * np.sin(frequency * 2 * np.pi * self.t + phaseRads))
        self.s = self.s + newSig

    def addBpsk(self, amplitude_Rel_FS, symbol_rate, carrier_frequency=0.0, num_symbols=None,
                data: Optional[Sequence[int]] = None, amplitude_unit='FS'):
        amplitude = self._coerce_amplitude(amplitude_Rel_FS, amplitude_unit)
        if num_symbols is None:
            num_symbols = max(1, int(self.duration * symbol_rate))
        if num_symbols <= 0:
            raise ValueError('Number of symbols must be positive')
        if data is None:
            rng = np.random.default_rng()
            data = rng.integers(0, 2, size=num_symbols)
        symbols = np.array([1 if bit else -1 for bit in data], dtype=float)
        samples_per_symbol = int(round(self.sampleRate / symbol_rate))
        if samples_per_symbol <= 0:
            raise ValueError('Symbol rate must be lower than the sample rate')
        baseband = np.repeat(symbols, samples_per_symbol)
        baseband = baseband[:np.size(self.t)]
        phase = 2 * np.pi * carrier_frequency * self.t
        waveform = amplitude * baseband * np.exp(1j * phase)
        self.s = self.s + waveform

    def addFsk(self, amplitude_Rel_FS, symbol_rate, tone_map: Sequence[float],
               carrier_frequency=0.0, data: Optional[Sequence[int]] = None, amplitude_unit='FS'):
        if not tone_map:
            raise ValueError('tone_map must contain at least one frequency offset')
        amplitude = self._coerce_amplitude(amplitude_Rel_FS, amplitude_unit)
        if data is None:
            num_symbols = max(1, int(self.duration * symbol_rate))
            rng = np.random.default_rng()
            data = rng.integers(0, len(tone_map), size=num_symbols)
        else:
            num_symbols = len(data)
        samples_per_symbol = int(round(self.sampleRate / symbol_rate))
        if samples_per_symbol <= 0:
            raise ValueError('Symbol rate must be lower than the sample rate')
        freq_sequence = np.array([tone_map[sym % len(tone_map)] for sym in data], dtype=float)
        freq_sequence = np.repeat(freq_sequence, samples_per_symbol)
        freq_sequence = freq_sequence[:np.size(self.t)]
        phase = np.cumsum(freq_sequence) * (2 * np.pi / self.sampleRate)
        carrier = np.exp(1j * (2 * np.pi * carrier_frequency * self.t + phase))
        waveform = amplitude * carrier
        self.s = self.s + waveform

    def addQam4(self, amplitude_Rel_FS, symbol_rate, carrier_frequency=0.0, num_symbols=None,
                data: Optional[Sequence[int]] = None, amplitude_unit='FS'):
        amplitude = self._coerce_amplitude(amplitude_Rel_FS, amplitude_unit)
        if num_symbols is None:
            num_symbols = max(1, int(self.duration * symbol_rate))
        if num_symbols <= 0:
            raise ValueError('Number of symbols must be positive')
        if data is None:
            rng = np.random.default_rng()
            data = rng.integers(0, 4, size=num_symbols)
        else:
            data = np.array(data[:num_symbols], dtype=int)
            if data.size < num_symbols:
                data = np.pad(data, (0, num_symbols - data.size), mode='wrap')
        mapping = {
            0: 1 + 1j,
            1: -1 + 1j,
            2: -1 - 1j,
            3: 1 - 1j
        }
        symbols = np.array([mapping[int(sym) % 4] for sym in data], dtype=complex)
        symbols = symbols / np.sqrt(2)
        samples_per_symbol = int(round(self.sampleRate / symbol_rate))
        if samples_per_symbol <= 0:
            raise ValueError('Symbol rate must be lower than the sample rate')
        baseband = np.repeat(symbols, samples_per_symbol)
        baseband = baseband[:np.size(self.t)]
        carrier = np.exp(1j * 2 * np.pi * carrier_frequency * self.t)
        waveform = amplitude * baseband * carrier
        self.s = self.s + waveform

    def clear(self):
        self.s = np.zeros(np.size(self.t), dtype=complex)

    def get_waveform(self):
        return np.clip(self.s, -1.0, 1.0)

    def saveToFile(self, filename):
        scaled = np.clip(self.get_waveform() * self.FS, -self.FS, self.FS)
        with open(filename, 'w') as outPutFile:
            for sample in scaled:
                idata = sample.real
                qdata = sample.imag
                outPutFile.write(str(int(round(idata))) + ',' + str(int(round(qdata))) + '\n')
