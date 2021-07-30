"""
Modules for testing and correcting errors and bugs in the main code
Author: William McCallum
Last Updated: 17/7/21
"""

from qampy import signals, impairments, equalisation, phaserec, helpers, theory
from qampy.core import io
import numpy as np
import math
from bokeh.io import output_notebook
from bokeh.plotting import figure, show
import os
import random
import Generate_Signal
import Receive_Signal
import Impairments
import Output

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


if __name__ == "__main__":
    # Generate initial signal
    fs = 92*10**9   # sampling frequency (for AWG)
    fb = 40*10**9   # baud rate (symbols / s)
    f_scope = 80*10**9  # scope sample frequency
    M = 4**2        # QAM order
    N = 2**18       # number of symbols
    nmodes = 2      # number of polarisations
    snr = 23        # signal to noise ratio
    upsample_mult=4     # how many times the signal is upsampled to get fractional delay
    Ntaps = 5      # how many taps are used in signal equalisation function
    orig_sig = signals.SignalQAMGrayCoded(M, N, fb=fb, nmodes=nmodes) # create signal
    dumped_edges = 15   # how many edges are going to be dumped from either side of the signal
    Output.plot_constellation(orig_sig, "Original signal")
    print("SNR: %d" % snr)
    print("QAM: %d" % M)
    print("Original signal shape: ", end="")
    print(orig_sig.shape)

    # adds 0's to signal
    edge_size = int(math.floor((Ntaps-1)/2)) + dumped_edges
    sig = add_edges(orig_sig, edge_size)
    print("edges added signal shape: ", end="")
    print(sig.shape)


    # apply noise
    noisy_sig = impairments.change_snr(sig, snr)     # adds noise to signal
    Output.plot_constellation(noisy_sig, "Noisy signal")
    print("Noisy signal shape: ", end="")
    print(noisy_sig.shape)

    # applies phase noise

    # recovery
    # test for different step size/signal frequencies
    # test for multiple iterations
    # applying filters removes Ntaps-1 symbols from the signal -> need to add (Ntaps-1)/2 0's to either side of signal
    wxy, err = equalisation.equalise_signal(noisy_sig, 2e-3, Ntaps=Ntaps, method="mddma")    # gets wx and wy filter 
    recovered_sig = equalisation.apply_filter(noisy_sig, wxy)    # applies filter taps to equalise signal
    Output.plot_constellation(recovered_sig, "Recovered signal")
    print("Recovered signal shape: ", end="")
    print(recovered_sig.shape)

    #phase recovery
    recovered_sig, ph = phaserec.bps(recovered_sig, 36, 11) # what are good values for #test angles and block length?
    print("Phase Recovered signal shape: ", end="")
    print(recovered_sig.shape)
    
    # recovery part 3
    recovered_sig = helpers.normalise_and_center(recovered_sig)
    print("Recovered signal 2 shape: ", end="")
    print(recovered_sig.shape)
    recovered_sig = helpers.dump_edges(recovered_sig, dumped_edges)     # check if errors are concentrated at edges
    print("Dump edges", end="")
    print(recovered_sig.shape)
    print("Recovered signal 3 shape: ", end="")
    print(recovered_sig.shape)
    Output.plot_constellation(recovered_sig, "Fully Recovered signal")

    # check BER, SER
    print("SER = ",recovered_sig.cal_ser())
    print("BER = ",recovered_sig.cal_ber())

    # demodulates signals
    orig_data = orig_sig.demodulate(orig_sig) * 1
    recovered_data = recovered_sig.demodulate(recovered_sig) * 1

    # compare signal lengths and frequencies
    print("Original data:")
    print(orig_data)
    print("Recovered data:")
    print(recovered_data)
    [err_arr, success] = Output.compare_symbols(orig_data, recovered_data)
    BER = theory.ber_vs_es_over_n0_qam(snr, M)  # gets theoretical BER
    print("Predicted BER: %e" % BER)
    Output.error_dist(err_arr, snr, M)