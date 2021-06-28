"""

"""

from qampy import signals, impairments, equalisation, phaserec, helpers
import numpy as np
from bokeh.io import output_notebook
from bokeh.plotting import figure, show
import os


def add_noise(sig, snr, df=100e3):
    """
    Adds noise to signal

    Parameters
    ---------------------------------------------
    sig : SignalQAMGrayCoded
        Signal that is to have noise added to it
    snr : float
        Signal to noise ratio
    df : float
        Combined linewidth of oscillators in the system

    Output
    ---------------------------------------------
    noisy_signal : SignalQAMGrayCoded
        Signal that has had noise added to it
    """
    noisy_signal = impairments.change_snr(sig, snr)     # adds noise to signal
    noisy_signal = noisy_signal.resample(2*noisy_signal.fb, beta=0.1, renormalise=True) # oversample signal
    noisy_signal = impairments.apply_phase_noise(noisy_signal, df)

    return noisy_signal

def Interpolate_Signal(sig):
    """

    """
    return interpolated_sig

def delay(sig, shift, nmodes):  # to do: shift by fraction amount, by first upsampling 16-32x baud rate
    """
    Shifts a given signal by an amount given by shift

    Parameters
    ---------------------------------------------
    sig : SignalQAMGrayCoded
        Signal that is to be shifted
    shift : integer
        How much signal is to be shifted by and in which direction
    nmodes : integer
        Number of polarisations of signal

    Output
    ---------------------------------------------
    sig : SignalQAMGrayCoded
        Signal that has been shifted
    """
    if nmodes == 1:
        sig = np.roll(sig, shift, axis=0) #single polarization desynchronization
    if nmodes == 2:
        sig = np.roll(sig, shift, axis=1) #dual polarization desynchronization

    return sig

def simulate_AWG(sig, upsample_multiplier=4, scope_rate=80e9):
    """
    Simulates the AWG by upsampling the signal, delaying it by a random amount, then downsampling to scope sample rate

    Parameters
    ---------------------------------------------
    sig : SignalQAMGrayCoded
        Signal that is to be simulated by AWG
    upsample_multiplier : float
        How much the sample rate is multiplied by
    scope_rate : 
        Sample rate of the oscilloscope, default 80GS/s

    Output
    ---------------------------------------------
    AWG_sig : SignalQAMGrayCoded
        Signal that has had AWG simulation applied to it
    """
    # upsample to AWG sample rate (92e9)
    sig = sig.resample(sig.fs*upsample_multiplier, beta=0.1, renormalise=True)

    # Delay by random amount
    N = len(sig[0]) + len(sig[1]) # total number of symbols in signal
    shift = np.random.randint(-N/2, N/2, 1) # randomly shift to signal by up to 1/2 signal length in either direction
    AWG_sig = delay(sig, shift, sig.nmodes)
    # interpolate signal here

    # Downsample to oscilloscope sample rate
    AWG_sig = AWG_sig.resample(scope_rate, beta=0.1, renormalise=True)

    return AWG_sig
