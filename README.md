# IQ Tools

This module is a set of utilities for working with IQ data.

# Build & Installation

## Build Instructions

1. Clone the repo: `git clone git@github.com:loganrf/IQtools.git`
2. Install dependencies: `poetry install`
3. Build: `poetry build`

## Example Run Instructions

1. Follow steps 1/2 from **Build Instructions** above
2. Run `poetry run python main.py`

## Install as CLI Utility

1. Install pipx. `brew install pipx`, `apt install pipx` or check other options [here](https://pipx.pypa.io/stable/installation/).
2. Install iqtools: `pipx install iqtools`
3. You should now be able to run the CLI commands from your normal terminal!

# CLI Guide

## `generateCW`

usage: generateCW [-h] [-p P] [-b B]
                  filename level baseBandFrequency sampleRate duration

Utility for generating a CW IQ signal

**positional arguments:**

  filename           Output File

  level              Output amplitude (0 to 1.0)

  baseBandFrequency  Baseband frequency (must be within Nyquist, +/- Fs/2)

  sampleRate         Complex sample rate of the file

  duration           Duration of sample file in milliseconds

**options:**

  -h, --help         show this help message and exit

  -p P               phase offset (rads)

  -b B               Number of signed bits for the ADC

## `getSpectrum`

usage: getSpectrum [-h] [-f F] [-b B] [-s] filename sampleRate

Utility for generating a frequency spectrum from an IQ data file

**positional arguments:**

  filename    File with IQ data

  sampleRate  Complex sample rate of the file

**options:**

  -h, --help  show this help message and exit

  -f F        Frequency Units

  -b B        Number of signed bits for the ADC

  -s          Save the image to a png instead of showing it

## `getPeaks`

usage: getPeaks [-h] [-f F] [-b B] [-t T] filename sampleRate

Utility for getting peak spectrum values from an IQ data file

**positional arguments:**

  filename    File with IQ data

  sampleRate  Complex sample rate of the file

**options:**

  -h, --help  show this help message and exit

  -f F        Frequency Units

  -b B        Number of signed bits for the ADC

  -t T        Threshold for peak detection (In dBFS by default)
