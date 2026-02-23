"""Interactive PyQt6 utility for exploring IQ waveforms in time/frequency domains."""

from __future__ import annotations

from typing import Optional, Sequence, Tuple

import numpy as np
from PyQt6 import QtCore, QtWidgets
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib.widgets import SpanSelector

from .SignalGenerator import SignalGenerator
from .conversion import WaveformMetadata, detect_format, load_waveform


class WaveformCanvas(FigureCanvasQTAgg):
    """Matplotlib canvas responsible for rendering time/frequency plots."""

    def __init__(self):
        self.figure = Figure(figsize=(8, 6))
        super().__init__(self.figure)
        self.time_ax = self.figure.add_subplot(211)
        self.freq_ax = self.figure.add_subplot(212)
        self.figure.tight_layout()
        self.samples = np.array([], dtype=np.complex64)
        self.sample_rate = 1.0
        self.selection: Optional[Tuple[float, float]] = None
        self.selection_callback = None
        self._span = SpanSelector(
            self.time_ax,
            self._on_select,
            'horizontal',
            useblit=True,
            interactive=True,
            props=dict(alpha=0.2, facecolor='tab:blue')
        )

    def set_selection_callback(self, callback):
        self.selection_callback = callback

    def _on_select(self, xmin, xmax):
        if xmin == xmax:
            self.selection = None
        else:
            self.selection = (min(xmin, xmax), max(xmin, xmax))
        if self.selection_callback:
            self.selection_callback(self.selection)
        self.draw_idle()

    def clear_selection(self):
        self.selection = None
        self._span.clear()
        self.draw_idle()

    def update_display(self, samples: np.ndarray, sample_rate: float,
                       selection: Optional[Tuple[float, float]], amplitude_unit: str):
        self.samples = samples
        self.sample_rate = sample_rate
        self.selection = selection
        self.time_ax.cla()
        self.freq_ax.cla()
        if samples.size == 0:
            self.time_ax.set_title('Time Domain')
            self.freq_ax.set_title('Frequency Domain')
            self.draw_idle()
            return
        time_axis = np.arange(samples.size) / sample_rate
        if amplitude_unit.upper() == 'FS':
            self.time_ax.plot(time_axis, samples.real, label='I (FS)')
            self.time_ax.plot(time_axis, samples.imag, label='Q (FS)')
            self.time_ax.plot(time_axis, np.abs(samples), label='|IQ| (FS)', linestyle='--', alpha=0.6)
            self.time_ax.set_ylabel('Amplitude (FS)')
        else:
            mag = np.abs(samples)
            mag_db = np.where(mag > 0, 20 * np.log10(mag), -200)
            self.time_ax.plot(time_axis, mag_db, label='|IQ| (dBFS)')
            self.time_ax.set_ylabel('Amplitude (dBFS)')
        if selection:
            self.time_ax.axvspan(selection[0], selection[1], color='tab:blue', alpha=0.1)
        self.time_ax.set_xlabel('Time (s)')
        self.time_ax.set_title('Time Domain')
        self.time_ax.grid(True)
        self.time_ax.legend(loc='upper right')

        selected_samples = self._get_selected_samples(selection)
        if selected_samples.size:
            window = np.hanning(selected_samples.size)
            windowed = selected_samples * window
            spectrum = np.fft.fftshift(np.fft.fft(windowed))
            freqs = np.fft.fftshift(np.fft.fftfreq(selected_samples.size, d=1 / sample_rate))
            magnitude = np.abs(spectrum) / selected_samples.size
        else:
            freqs = np.array([0.0])
            magnitude = np.array([0.0])
        if amplitude_unit.upper() == 'DBFS':
            magnitude = np.where(magnitude > 0, 20 * np.log10(magnitude), -200)
            self.freq_ax.set_ylabel('Magnitude (dBFS)')
        else:
            self.freq_ax.set_ylabel('Magnitude (FS)')
        self.freq_ax.plot(freqs, magnitude)
        self.freq_ax.set_xlabel('Frequency (Hz)')
        self.freq_ax.set_title('Frequency Domain')
        self.freq_ax.grid(True)
        self.figure.tight_layout()
        self.draw_idle()

    def _get_selected_samples(self, selection):
        if selection is None or self.samples.size == 0:
            return self.samples
        start = max(0, int(selection[0] * self.sample_rate))
        stop = min(self.samples.size, int(selection[1] * self.sample_rate))
        if stop <= start:
            return self.samples
        return self.samples[start:stop]


class WaveformBuilderWidget(QtWidgets.QWidget):
    """Widget that allows synthesis of simple waveforms."""

    waveformGenerated = QtCore.pyqtSignal(object, float, object)

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent)
        self.generator: Optional[SignalGenerator] = None
        self.bits = 16
        self.sample_rate_spin = QtWidgets.QDoubleSpinBox()
        self.sample_rate_spin.setRange(1.0, 100e9)
        self.sample_rate_spin.setValue(10e6)
        self.sample_rate_spin.setSuffix(' Sa/s')
        self.sample_rate_spin.setDecimals(3)
        self.sample_rate_spin.valueChanged.connect(self.reset_generator)
        self.duration_spin = QtWidgets.QDoubleSpinBox()
        self.duration_spin.setRange(1e-6, 60.0)
        self.duration_spin.setValue(1e-3)
        self.duration_spin.setSuffix(' s')
        self.duration_spin.setDecimals(6)
        self.duration_spin.valueChanged.connect(self.reset_generator)
        self.component_list = QtWidgets.QListWidget()

        layout = QtWidgets.QVBoxLayout(self)
        form = QtWidgets.QFormLayout()
        form.addRow('Sample rate:', self.sample_rate_spin)
        form.addRow('Duration:', self.duration_spin)
        layout.addLayout(form)

        reset_button = QtWidgets.QPushButton('Reset Waveform')
        reset_button.clicked.connect(self.reset_generator)
        layout.addWidget(reset_button)
        layout.addWidget(QtWidgets.QLabel('Components:'))
        layout.addWidget(self.component_list)

        layout.addWidget(self._sinusoid_box())
        layout.addWidget(self._bpsk_box())
        layout.addWidget(self._fsk_box())
        layout.addWidget(self._qam_box())

        generate_button = QtWidgets.QPushButton('Generate Waveform')
        generate_button.clicked.connect(self._emit_waveform)
        layout.addWidget(generate_button)
        layout.addStretch(1)

        self.reset_generator()

    def reset_generator(self):
        self.generator = SignalGenerator(self.sample_rate_spin.value(), self.bits, self.duration_spin.value())
        self.generator.clear()
        self.component_list.clear()

    def _sinusoid_box(self):
        box = QtWidgets.QGroupBox('Add Sinusoid')
        layout = QtWidgets.QFormLayout(box)
        self.sin_amplitude = QtWidgets.QDoubleSpinBox()
        self.sin_amplitude.setRange(-120.0, 0.0)
        self.sin_amplitude.setValue(-6.0)
        self.sin_unit = QtWidgets.QComboBox()
        self.sin_unit.addItems(['dBFS', 'FS'])
        self.sin_frequency = QtWidgets.QDoubleSpinBox()
        self.sin_frequency.setRange(-100e9, 100e9)
        self.sin_frequency.setDecimals(3)
        self.sin_frequency.setSuffix(' Hz')
        self.sin_phase = QtWidgets.QDoubleSpinBox()
        self.sin_phase.setRange(-360.0, 360.0)
        self.sin_phase.setSuffix(' °')
        add_button = QtWidgets.QPushButton('Add')
        add_button.clicked.connect(self._add_sinusoid)
        layout.addRow('Amplitude:', self.sin_amplitude)
        layout.addRow('Amplitude unit:', self.sin_unit)
        layout.addRow('Frequency:', self.sin_frequency)
        layout.addRow('Phase:', self.sin_phase)
        layout.addRow(add_button)
        return box

    def _bpsk_box(self):
        box = QtWidgets.QGroupBox('Add BPSK')
        layout = QtWidgets.QFormLayout(box)
        self.bpsk_amplitude = QtWidgets.QDoubleSpinBox()
        self.bpsk_amplitude.setRange(-120.0, 0.0)
        self.bpsk_amplitude.setValue(-3.0)
        self.bpsk_unit = QtWidgets.QComboBox()
        self.bpsk_unit.addItems(['dBFS', 'FS'])
        self.bpsk_symbol_rate = QtWidgets.QDoubleSpinBox()
        self.bpsk_symbol_rate.setRange(1.0, 10e9)
        self.bpsk_symbol_rate.setDecimals(3)
        self.bpsk_symbol_rate.setValue(1e5)
        self.bpsk_symbol_rate.setSuffix(' sym/s')
        self.bpsk_carrier = QtWidgets.QDoubleSpinBox()
        self.bpsk_carrier.setRange(-100e9, 100e9)
        self.bpsk_carrier.setDecimals(3)
        self.bpsk_carrier.setSuffix(' Hz')
        self.bpsk_symbols = QtWidgets.QSpinBox()
        self.bpsk_symbols.setRange(1, 1_000_000)
        self.bpsk_symbols.setValue(1000)
        add_button = QtWidgets.QPushButton('Add')
        add_button.clicked.connect(self._add_bpsk)
        layout.addRow('Amplitude:', self.bpsk_amplitude)
        layout.addRow('Amplitude unit:', self.bpsk_unit)
        layout.addRow('Symbol rate:', self.bpsk_symbol_rate)
        layout.addRow('Carrier frequency:', self.bpsk_carrier)
        layout.addRow('Symbols:', self.bpsk_symbols)
        layout.addRow(add_button)
        return box

    def _fsk_box(self):
        box = QtWidgets.QGroupBox('Add Multi-tone FSK')
        layout = QtWidgets.QFormLayout(box)
        self.fsk_amplitude = QtWidgets.QDoubleSpinBox()
        self.fsk_amplitude.setRange(-120.0, 0.0)
        self.fsk_amplitude.setValue(-6.0)
        self.fsk_unit = QtWidgets.QComboBox()
        self.fsk_unit.addItems(['dBFS', 'FS'])
        self.fsk_symbol_rate = QtWidgets.QDoubleSpinBox()
        self.fsk_symbol_rate.setRange(1.0, 10e9)
        self.fsk_symbol_rate.setDecimals(3)
        self.fsk_symbol_rate.setValue(1e5)
        self.fsk_symbol_rate.setSuffix(' sym/s')
        self.fsk_carrier = QtWidgets.QDoubleSpinBox()
        self.fsk_carrier.setRange(-100e9, 100e9)
        self.fsk_carrier.setDecimals(3)
        self.fsk_carrier.setSuffix(' Hz')
        self.fsk_tones = QtWidgets.QLineEdit('0, 1000, -1000')
        self.fsk_data = QtWidgets.QLineEdit('0,1,2,1')
        add_button = QtWidgets.QPushButton('Add')
        add_button.clicked.connect(self._add_fsk)
        layout.addRow('Amplitude:', self.fsk_amplitude)
        layout.addRow('Amplitude unit:', self.fsk_unit)
        layout.addRow('Symbol rate:', self.fsk_symbol_rate)
        layout.addRow('Carrier frequency:', self.fsk_carrier)
        layout.addRow('Tone offsets (Hz):', self.fsk_tones)
        layout.addRow('Symbol sequence:', self.fsk_data)
        layout.addRow(add_button)
        return box

    def _qam_box(self):
        box = QtWidgets.QGroupBox('Add 4-QAM')
        layout = QtWidgets.QFormLayout(box)
        self.qam_amplitude = QtWidgets.QDoubleSpinBox()
        self.qam_amplitude.setRange(-120.0, 0.0)
        self.qam_amplitude.setValue(-3.0)
        self.qam_unit = QtWidgets.QComboBox()
        self.qam_unit.addItems(['dBFS', 'FS'])
        self.qam_symbol_rate = QtWidgets.QDoubleSpinBox()
        self.qam_symbol_rate.setRange(1.0, 10e9)
        self.qam_symbol_rate.setDecimals(3)
        self.qam_symbol_rate.setValue(1e5)
        self.qam_symbol_rate.setSuffix(' sym/s')
        self.qam_carrier = QtWidgets.QDoubleSpinBox()
        self.qam_carrier.setRange(-100e9, 100e9)
        self.qam_carrier.setDecimals(3)
        self.qam_carrier.setSuffix(' Hz')
        self.qam_symbols = QtWidgets.QSpinBox()
        self.qam_symbols.setRange(1, 1_000_000)
        self.qam_symbols.setValue(1000)
        add_button = QtWidgets.QPushButton('Add')
        add_button.clicked.connect(self._add_qam)
        layout.addRow('Amplitude:', self.qam_amplitude)
        layout.addRow('Amplitude unit:', self.qam_unit)
        layout.addRow('Symbol rate:', self.qam_symbol_rate)
        layout.addRow('Carrier frequency:', self.qam_carrier)
        layout.addRow('Symbols:', self.qam_symbols)
        layout.addRow(add_button)
        return box

    def _parse_sequence(self, text: str) -> Sequence[float]:
        parts = [p.strip() for p in text.split(',') if p.strip()]
        return [float(part) for part in parts]

    def _parse_int_sequence(self, text: str) -> Sequence[int]:
        parts = [p.strip() for p in text.split(',') if p.strip()]
        return [int(part) for part in parts]

    def _add_sinusoid(self):
        if not self.generator:
            return
        amplitude = self.sin_amplitude.value()
        unit = self.sin_unit.currentText()
        frequency = self.sin_frequency.value()
        phase = np.deg2rad(self.sin_phase.value())
        try:
            self.generator.addSinusoid(amplitude, frequency, phaseRads=phase, amplitude_unit=unit)
        except ValueError as exc:
            QtWidgets.QMessageBox.warning(self, 'Invalid sinusoid', str(exc))
            return
        self.component_list.addItem(f'Sinusoid {frequency:.3f} Hz, {amplitude:.2f} {unit}')

    def _add_bpsk(self):
        if not self.generator:
            return
        amplitude = self.bpsk_amplitude.value()
        unit = self.bpsk_unit.currentText()
        symbol_rate = self.bpsk_symbol_rate.value()
        carrier = self.bpsk_carrier.value()
        symbols = self.bpsk_symbols.value()
        try:
            self.generator.addBpsk(amplitude, symbol_rate, carrier_frequency=carrier,
                                   num_symbols=symbols, amplitude_unit=unit)
        except ValueError as exc:
            QtWidgets.QMessageBox.warning(self, 'Invalid BPSK settings', str(exc))
            return
        self.component_list.addItem(f'BPSK {symbol_rate:.3f} sym/s @ {carrier:.3f} Hz')

    def _add_fsk(self):
        if not self.generator:
            return
        amplitude = self.fsk_amplitude.value()
        unit = self.fsk_unit.currentText()
        symbol_rate = self.fsk_symbol_rate.value()
        carrier = self.fsk_carrier.value()
        try:
            tones = self._parse_sequence(self.fsk_tones.text())
            data = self._parse_int_sequence(self.fsk_data.text()) if self.fsk_data.text().strip() else None
            self.generator.addFsk(amplitude, symbol_rate, tones, carrier_frequency=carrier,
                                  data=data, amplitude_unit=unit)
        except ValueError as exc:
            QtWidgets.QMessageBox.warning(self, 'Invalid FSK settings', str(exc))
            return
        self.component_list.addItem(f'M-FSK tones={len(tones)} @ {carrier:.3f} Hz')

    def _add_qam(self):
        if not self.generator:
            return
        amplitude = self.qam_amplitude.value()
        unit = self.qam_unit.currentText()
        symbol_rate = self.qam_symbol_rate.value()
        carrier = self.qam_carrier.value()
        symbols = self.qam_symbols.value()
        try:
            self.generator.addQam4(amplitude, symbol_rate, carrier_frequency=carrier,
                                   num_symbols=symbols, amplitude_unit=unit)
        except ValueError as exc:
            QtWidgets.QMessageBox.warning(self, 'Invalid 4-QAM settings', str(exc))
            return
        self.component_list.addItem(f'4-QAM {symbol_rate:.3f} sym/s @ {carrier:.3f} Hz')

    def _emit_waveform(self):
        if not self.generator:
            return
        waveform = self.generator.get_waveform()
        metadata = WaveformMetadata(sample_rate=self.generator.sampleRate, ref_scale=1.0,
                                    instrument='SignalGenerator')
        self.waveformGenerated.emit(waveform, self.generator.sampleRate, metadata)


class WaveformExplorer(QtWidgets.QMainWindow):
    """Main window for the interactive spectrum analyzer/oscilloscope."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle('IQtools Spectrum Explorer')
        self.resize(1200, 800)
        self.samples = np.array([], dtype=np.complex64)
        self.sample_rate = 1.0
        self.metadata: Optional[WaveformMetadata] = None
        self.selection: Optional[Tuple[float, float]] = None

        self.canvas = WaveformCanvas()
        self.canvas.set_selection_callback(self._on_selection_changed)

        self.amplitude_combo = QtWidgets.QComboBox()
        self.amplitude_combo.addItems(['FS', 'dBFS'])
        self.amplitude_combo.currentTextChanged.connect(self._refresh_plots)

        load_button = QtWidgets.QPushButton('Load Waveform…')
        load_button.clicked.connect(self._open_waveform)
        reset_selection_button = QtWidgets.QPushButton('Reset Selection')
        reset_selection_button.clicked.connect(self._reset_selection)

        self.selection_label = QtWidgets.QLabel('Selection: entire signal')

        controls = QtWidgets.QWidget()
        controls_layout = QtWidgets.QVBoxLayout(controls)
        controls_layout.addWidget(load_button)
        controls_layout.addWidget(QtWidgets.QLabel('Amplitude units:'))
        controls_layout.addWidget(self.amplitude_combo)
        controls_layout.addWidget(reset_selection_button)
        controls_layout.addWidget(self.selection_label)

        self.builder = WaveformBuilderWidget()
        self.builder.waveformGenerated.connect(self._accept_generated_waveform)
        controls_layout.addWidget(self.builder)
        controls_layout.addStretch(1)

        splitter = QtWidgets.QSplitter()
        splitter.addWidget(controls)
        splitter.addWidget(self.canvas)
        splitter.setStretchFactor(1, 1)
        self.setCentralWidget(splitter)

    def _refresh_plots(self):
        self.canvas.update_display(self.samples, self.sample_rate, self.selection,
                                   self.amplitude_combo.currentText())

    def _on_selection_changed(self, selection: Optional[Tuple[float, float]]):
        self.selection = selection
        if selection is None:
            self.selection_label.setText('Selection: entire signal')
        else:
            self.selection_label.setText(f'Selection: {selection[0]:.6f}s – {selection[1]:.6f}s')
        self._refresh_plots()

    def _reset_selection(self):
        self.selection = None
        self.canvas.clear_selection()
        self.selection_label.setText('Selection: entire signal')
        self._refresh_plots()

    def _ensure_sample_rate(self, metadata: Optional[WaveformMetadata], fallback: float = 1.0) -> float:
        if metadata and metadata.sample_rate:
            return metadata.sample_rate
        value, ok = QtWidgets.QInputDialog.getDouble(self, 'Sample rate',
                                                     'Enter sample rate (Sa/s):', fallback, 1.0, 1e12, 3)
        if not ok:
            raise RuntimeError('Sample rate required to continue')
        return value

    def _open_waveform(self):
        options = QtWidgets.QFileDialog.Options()
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            'Open waveform file',
            '',
            'Waveforms (*.wfm *.csv *.txt);;All files (*.*)',
            options=options
        )
        if not file_path:
            return
        fmt = detect_format(file_path)
        bits = None
        if fmt == 'csv':
            bits, ok = QtWidgets.QInputDialog.getInt(self, 'Bit depth',
                                                     'Enter bit depth for CSV waveform:', 16, 1, 32)
            if not ok:
                return
        try:
            samples, metadata = load_waveform(file_path, bits=bits)
        except Exception as exc:  # pragma: no cover - interactive message box
            QtWidgets.QMessageBox.critical(self, 'Failed to load waveform', str(exc))
            return
        try:
            sample_rate = self._ensure_sample_rate(metadata, fallback=self.sample_rate)
        except RuntimeError:
            return
        self.samples = np.asarray(samples, dtype=np.complex64)
        self.sample_rate = sample_rate
        self.metadata = metadata
        self.selection = None
        self.canvas.clear_selection()
        self.selection_label.setText('Selection: entire signal')
        self._refresh_plots()

    def _accept_generated_waveform(self, samples: np.ndarray, sample_rate: float, metadata: WaveformMetadata):
        self.samples = samples.astype(np.complex64)
        self.sample_rate = sample_rate
        self.metadata = metadata
        self.selection = None
        self.canvas.clear_selection()
        self.selection_label.setText('Selection: generated signal')
        self._refresh_plots()


def main():
    import sys

    app = QtWidgets.QApplication(sys.argv)
    window = WaveformExplorer()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
