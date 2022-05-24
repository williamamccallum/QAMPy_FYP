"""
Code for adding impairments to a signal, such as delay, noise and simulating hardware.
Author: William McCallum
Last Updated: 24/5/22
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


def delay(sig, shift, nmodes=2):
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

def simulate_AWG(sig, upsample_multiplier=4, scope_rate=80e9, delay_max_offset=1):
    """
    Simulates the AWG by upsampling the signal, delaying it by a random amount, then downsampling to scope sample rate

    Parameters
    ---------------------------------------------
    sig : SignalQAMGrayCoded
        Signal that is to be simulated by AWG
    upsample_multiplier : float
        How much the sample rate is multiplied by
    scope_rate : float
        Sample rate of the oscilloscope, default 80GS/s
    delay_max_offset : float
        Maximum amount that signal is delayed, 1 means that signal can be delayed by up to 1 full signal length

    Output
    ---------------------------------------------
    AWG_sig : SignalQAMGrayCoded
        Signal that has had AWG simulation applied to it
    """
    # upsample to AWG sample rate (92e9)
    sig = sig.resample(sig.fs*upsample_multiplier, beta=0.1, renormalise=True)

    # Delay by random amount
    N = len(sig[0]) + len(sig[1]) # total number of symbols in signal
    shift = np.random.randint(-delay_max_offset*N, delay_max_offset*N, 1) # randomly shift to signal by up to 1/2 signal length in either direction
    AWG_sig = delay(sig, shift, sig.nmodes)
    # interpolate signal here

    # Downsample to oscilloscope sample rate
    AWG_sig = AWG_sig.resample(scope_rate, beta=0.1, renormalise=True)

    return AWG_sig


def add_edges(sig, edge_size, nmodes=2):
    """
    Adds edges to either side of signal filled with 0's of length edge_size

    Parameters
    ---------------------------------------------
    sig : SignalQAMGrayCoded
        Signal that is to have edges added to
    edge_size : integer
        length of edges to be added to each side of signal. Edges are made of 0's

    Output
    ---------------------------------------------
    sig : SignalQAMGrayCoded
        Signal that has had edges added
    """
    sig_temp = sig      # gets temporary signal
    arr_0 = np.zeros((nmodes, edge_size))    # gets array of zeros
    sig_temp = np.concatenate((sig_temp, arr_0), axis=1)   # adds 0's to end of signal
    sig_temp = np.concatenate((arr_0, sig_temp), axis=1)   # adds 0's to start of signal
    out_sig = sig.recreate_from_np_array(sig_temp)  # gets rebuilt signal
    return out_sig

def frac_offset(sig, scope_f, upsample_mult=8, nmodes=2):
    """
    This function takes a signal, then offsets its data by a fraction of a step

    Parameters
    ---------------------------------------------
    sig : SignalQAMGrayCoded
        Signal to have its data offset
    scope_f : float
        frequency of the scope
    upsample_mult : float
        How many times the signal is being upsamples from the baud rate

    Output
    ---------------------------------------------
    offset_sig : SignalQAMGrayCoded
        Signal that has the data of sig offset by a fractional amount
    """
    # large upsample
    sig = sig.resample(sig.fb*upsample_mult, beta=0.1, renormalise=True)

    # random small delay
    shift = np.random.randint(1,upsample_mult-1)  # shift by shift spaces
    if np.random.random() < 0.5:     # 50% chance to shift in -ve direction
        shift *= -1 
    print("Shift: %.3f" % (shift / upsample_mult))
    if nmodes == 1:
        offset_sig = np.roll(sig, shift, axis=0) #single polarization desynchronization
    if nmodes == 2:
        offset_sig = np.roll(sig, shift, axis=1) #dual polarization desynchronization

    # downsample to scope
    offset_sig = offset_sig.resample(scope_f, beta=0.1, renormalise=True)

    return offset_sig
