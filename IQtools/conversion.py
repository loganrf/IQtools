"""Utility helpers for converting between IQtools data and common instrument formats."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Iterable, Optional, Tuple

import numpy as np


@dataclass
class WaveformMetadata:
    """Metadata describing a waveform on disk."""

    sample_rate: float
    center_frequency: float = 0.0
    ref_scale: float = 1.0
    comment: str = ""
    instrument: str = ""


class RohdeSchwarzWfm:
    """Parser/serializer for Rohde & Schwarz style WFM files.

    The format used here mirrors the textual header + binary payload structure
    produced by recent R&S vector signal generators.  Files start with an ASCII
    header containing key/value pairs, followed by a ``$DATA`` marker and the
    interleaved IQ samples stored as little-endian float32 pairs.
    """

    HEADER_PREFIX = "#"
    DATA_MARKER = "$DATA"

    @classmethod
    def load(cls, path: str) -> Tuple[np.ndarray, WaveformMetadata]:
        with open(path, 'rb') as handle:
            blob = handle.read()
        try:
            header_blob, data_blob = blob.split(cls.DATA_MARKER.encode('ascii'), 1)
        except ValueError as exc:
            raise ValueError('Invalid WFM file: missing $DATA marker') from exc
        header = header_blob.decode('ascii', errors='ignore').splitlines()
        metadata = {}
        for line in header:
            line = line.strip()
            if not line.startswith(cls.HEADER_PREFIX):
                continue
            line = line[1:].strip()
            if not line:
                continue
            if '=' in line:
                key, value = line.split('=', 1)
                metadata[key.strip().lower()] = value.strip()
        payload = data_blob.lstrip().splitlines()
        if not payload:
            return np.array([], dtype=np.complex64), WaveformMetadata(sample_rate=1.0)
        # The first line after $DATA may be empty or contain a newline before the binary block
        binary_data = b"".join(line.encode('latin1') + b"\n" for line in payload)
        # Attempt to read the raw binary payload.  If the text parser is confused, fall back to raw bytes
        try:
            start = blob.index(cls.DATA_MARKER.encode('ascii')) + len(cls.DATA_MARKER)
            # Skip optional newline characters
            while start < len(blob) and blob[start] in (ord('\n'), ord('\r')):
                start += 1
            binary_data = blob[start:]
        except ValueError:
            pass
        if len(binary_data) % 8:
            # Data should be packed as complex64 pairs
            raise ValueError('Unexpected payload length in WFM file')
        samples = np.frombuffer(binary_data, dtype='<f4')
        samples = samples.astype(np.float32)
        iq = samples[0::2] + 1j * samples[1::2]
        sample_rate = float(metadata.get('samplerate', metadata.get('samplingrate', 1.0)))
        center_frequency = float(metadata.get('centerfrequency', 0.0))
        ref_scale = float(metadata.get('scale', metadata.get('refscale', 1.0)))
        if ref_scale == 0:
            ref_scale = 1.0
        comment = metadata.get('comment', '')
        instrument = metadata.get('instrument', 'Rohde&Schwarz')
        return iq.astype(np.complex64), WaveformMetadata(
            sample_rate=sample_rate,
            center_frequency=center_frequency,
            ref_scale=ref_scale,
            comment=comment,
            instrument=instrument
        )

    @classmethod
    def dump(cls, path: str, samples: np.ndarray, metadata: WaveformMetadata) -> None:
        samples = np.asarray(samples, dtype=np.complex64)
        header_lines = [
            '# Rohde&Schwarz Waveform',
            '# FileFormat=WFM',
            f'# SampleRate={metadata.sample_rate}',
            f'# CenterFrequency={metadata.center_frequency}',
            f'# Scale={metadata.ref_scale}',
            f'# Instrument={metadata.instrument or "IQtools"}'
        ]
        if metadata.comment:
            header_lines.append(f'# Comment={metadata.comment}')
        header_blob = '\n'.join(header_lines) + '\n' + cls.DATA_MARKER + '\n'
        interleaved = np.empty(samples.size * 2, dtype='<f4')
        scale = metadata.ref_scale if metadata.ref_scale else 1.0
        interleaved[0::2] = samples.real.astype(np.float32) / scale
        interleaved[1::2] = samples.imag.astype(np.float32) / scale
        with open(path, 'wb') as handle:
            handle.write(header_blob.encode('ascii'))
            handle.write(interleaved.tobytes())


def detect_format(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    if ext == '.wfm':
        return 'wfm'
    if ext in {'.csv', '.txt'}:
        return 'csv'
    return 'unknown'


def load_waveform(path: str, bits: Optional[int] = None) -> Tuple[np.ndarray, WaveformMetadata]:
    fmt = detect_format(path)
    if fmt == 'wfm':
        samples, metadata = RohdeSchwarzWfm.load(path)
        return samples * metadata.ref_scale, metadata
    if fmt == 'csv':
        scale = (2 ** (bits - 1)) if bits else 1.0
        data = np.loadtxt(path, delimiter=',', dtype=float)
        if data.ndim == 1:
            data = data.reshape(-1, 2)
        iq = (data[:, 0] + 1j * data[:, 1]) / scale
        metadata = WaveformMetadata(sample_rate=1.0, ref_scale=1.0, instrument='CSV')
        return iq.astype(np.complex64), metadata
    raise ValueError(f'Unsupported waveform format for path: {path}')


def save_waveform(path: str, samples: np.ndarray, metadata: Optional[WaveformMetadata] = None) -> None:
    if metadata is None:
        metadata = WaveformMetadata(sample_rate=1.0)
    fmt = detect_format(path)
    samples = np.asarray(samples, dtype=np.complex64)
    if fmt == 'wfm':
        RohdeSchwarzWfm.dump(path, samples, metadata)
        return
    if fmt == 'csv':
        scale = (2 ** 15) - 1
        scaled = np.clip(samples, -1, 1) * scale
        stacked = np.column_stack((scaled.real, scaled.imag))
        np.savetxt(path, stacked, fmt='%d', delimiter=',')
        return
    raise ValueError(f'Unsupported waveform format for path: {path}')
