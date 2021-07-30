"""
Functions used to receive a signal from a file, remove any impairments, and recover the original signal
Author: William McCallum
Last Updated: 5/7/21
"""

from qampy import signals, impairments, equalisation, phaserec, helpers
from qampy.core import io
import numpy as np
from bokeh.io import output_notebook
from bokeh.plotting import figure, show
import os


def load_base_signal(filename):
    base_sig = io.load_signal(filename)
    return base_sig

def read_sig_data_from_file(filepath="C:/Users/wamcc1/Documents/QAM_sig/sig_data.txt"): # TO DO: read in signal data + noisy E from pickle file, then save E field to rebuilt signal
    """
    opens the file at filepath and reads in the data from it

    """
    fid = open(filepath, 'r' )   # opens file
    # reads in data for both real and imaginary parts for each polarisation
    # note that file is expected to contain 4 lines, with 1st line being real data in x polarisation, 2nd line imag data in x pol, 3rd line real data in y pol, and 4th line imag data in y pol
    x_real_data = fid.readline().split(', ')
    x_imag_data = fid.readline().split(', ')
    y_real_data = fid.readline().split(', ')
    y_imag_data = fid.readline().split(', ')
    fid.close()   # closes file

    # rebuilding signal data
    x_real = np.complex128(x_real_data)
    x_imag = np.complex128(x_imag_data) * 1j
    x = x_real + x_imag
    y_real = np.complex128(y_real_data)
    y_imag = np.complex128(y_imag_data) * 1j
    y = y_real + y_imag
    sig_data = np.complex128([x, y])

    return sig_data


def recreate_signal(data, fs, M, N, fb, nmodes, **kwargs):
    """
    Recreates signal by taking in received signal data and signal parameters

    Parameters
    ---------------------------------------------
    data : numpy array (complex128)
        Data of received signal
    fs : float
       DAC sampling frequency
    M : float
        QAM order
    N : float
        Number of symbols
    fb : float
        baud rate (symbols / s)
    nmodes : float
        number of polarisations

    Output
    ---------------------------------------------
    received_sig : SignalQAMGrayCoded
        signal received by synthesiser
    """
    # creates base carrier signal
    if len(kwargs) != 0:
        sig = signals.SignalQAMGrayCoded(M, N, nmodes, fb, kwargs)
    else:
        sig = signals.SignalQAMGrayCoded(M, N, nmodes, fb)
    sig = sig.resample(fs, beta=0.1, renormalise=True)

    # applies data to signal
    received_sig = sig.recreate_from_np_array(data)
    return received_sig


def fixed_recreate(sig, data):
    """

    """
    recreated_sig = sig.recreate_from_np_array(data)
    return recreated_sig


def recover_signal(sig):
    """
    Attempts to recover original signal at receiver
    """
    print(sig.shape)
    wxy, err = equalisation.equalise_signal(sig, 2e-3, Ntaps=7, method="mddma")

    ## plots estimation of error
    #fig = figure(title="Error", output_backend="webgl")
    #fig.line(np.arange(err[0].shape[0]), abs(err[0]), color='red', alpha=1, legend="X")
    #fig.xaxis[0].axis_label = "symbol"
    #fig.yaxis[0].axis_label = "error"
    #show(fig)

    ## plots equaliser taps for xy polarisations
    #fig = figure(title="Equaliser taps", output_backend="webgl")
    #fig.line(np.arange(wxy[0].shape[1]), wxy[0][0].real, color='red', alpha=1, legend="hxx")
    #fig.line(np.arange(wxy[0].shape[1]), wxy[0][1].real, color='blue', alpha=1, legend="hxy")
    # fig.xaxis[0].axis_label = "tap"
    # fig.yaxis[0].axis_label = "weight"
    #show(fig)
    sig_out = equalisation.apply_filter(sig, wxy)
    print(sig_out.shape)
    # sig_out2, ph = phaserec.viterbiviterbi(sig_out, 11) # find phase recovery for 16-qam
    sig_out2, ph = phaserec.bps(sig_out, 36, 11) # what are good values for #test angles and block length?
    print(sig_out2.shape)
    sig_out2 = helpers.normalise_and_center(sig_out2)
    print(sig_out2.shape)
    sig_out2 = helpers.dump_edges(sig_out2, 10)     # check if errors are concentrated at edges
    print(sig_out2.shape)
    #print("SER = ",sig_out2.cal_ser())
    #print("BER = ", sig_out2.cal_ber())
    return sig_out2