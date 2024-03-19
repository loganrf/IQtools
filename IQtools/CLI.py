import argparse

from .IQdata import IQdata
from .SignalAnalyzer import SignalAnalyzer
from .SignalGenerator import SignalGenerator
import numpy as np
def configureSpectrumParser():
    parser = argparse.ArgumentParser(prog='IQT: get_spectrum', description='Processes IQ data into plots and allows for measurements of spectral content')
    parser.add_argument('filename', help='IQ file to process')
    return parser

def get_spectrum(args=None):
    parser = configureSpectrumParser()
    args = parser.parse_args(args)
    print('Processing '+args.filename)
