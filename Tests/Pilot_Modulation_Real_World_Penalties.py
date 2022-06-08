"""
Simulates transmission of a signal with pilots that has real world penalties applied
    - Fractional delay
    - AWG
    - Receiver frequency not identical to signal
Author: William McCallum
Last Updated: 22/9/21
"""

# import libraries
from qampy import signals, impairments, equalisation, phaserec, helpers, theory
from qampy.core import io, pilotbased_transmitter, pilotbased_receiver, signal_quality
import numpy as np
import math
from bokeh.io import output_notebook
from bokeh.plotting import figure, show
import matplotlib.pyplot as plt
import os
import random
import Generate_Signal
import Receive_Signal
import Impairments
import Output


if __name__ == "__main__":
    # Initial parameters ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    fs = 92*10**9   # sampling frequency (for AWG)
    fb = 40*10**9   # baud rate (symbols / s)
    f_scope = 80*10**9  # scope sample frequency
    M = 4**3        # QAM order
    N = 2**18       # number of symbols
    npols = 2      # number of polarisations
    snr = np.arange(14,25)        # signal to noise ratio
    linewidth = 100e3     # linewidth of the laser
    freq_off = 50e6     # carrier frequency offset
    dgd = 10e-12
    upsample_mult=4     # how many times the signal is upsampled to get fractional delay
    Ntaps = 45      # how many taps are used in signal equalisation function
    dumped_edges = 15   # how many edges are going to be dumped from either side of the signal
    pilot_seq_len = 2048*8 # length of the pilot frame
    pilot_ins_ratio = 32 # ratio of data : pilot frames
    nframes=2           # number of frames

    # Transmitter side ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # Create signal
    test_sig = signals.SignalWithPilots(M,N,pilot_seq_len,pilot_ins_ratio,nmodes=npols,Mpilots=4,nframes=nframes,fb=fb)
    orig_data = test_sig.get_data()

    # Apply noise
    for i in range(len(snr)):
        impaired_sig = impairments.simulate_transmission(test_sig,snr=snr[i],dgd=0, freq_off=0,lwdth=0,roll_frame_sync=True)

        # large delay
        shift = np.random.randint(-N/2, N/2)
        print("Shift amount: %d" % shift)
        impaired_sig = Impairments.delay(impaired_sig, shift, npols)   # shifts signal by a random whole integer amount

        # Frac delay
        impaired_sig = Impairments.frac_offset(impaired_sig, f_scope)   # also resamples to scope frequency

        # Receiver side --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        # equalise signal
        impaired_sig.sync2frame()
        impaired_sig.corr_foe()
        [taps, recovered_pilot_sig] = equalisation.pilot_equaliser(impaired_sig,(1e-3,1e-3),Ntaps, frame=0, foe_comp=False,methods=("mddma","sbd_data"))
        recovered_pilot_sig = phaserec.pilot_cpe(recovered_pilot_sig,N=5,use_seq=False)

        ber = recovered_pilot_sig[0].get_data().cal_ber()[0]
        ser = recovered_pilot_sig[0].get_data().cal_ser()[0]
        e_snr = recovered_pilot_sig[0].est_snr()[0]
        print("Current results for %d-Qam with %d snr" % (M, snr[i]))
        print("Theory BER:", end="")
        print(theory.ber_vs_es_over_n0_qam(10**((snr[i])/10), M))
        print("Actual BER: ", end="")
        print(ber)
        print("BER correction:", end="")
        print(ber/theory.ber_vs_es_over_n0_qam(10**((snr[i])/10), M))
        print("SER: ", end="")
        print(ser)
        print("estimated SNR")
        print(10*np.log10(e_snr))
        print()

    # Output results --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


    #Output.plot_constellation(recovered_pilot_sig[0].get_data(), title=("Recovered Signal with %d snr" % snr[-1]))    

    # Compare original and recovered signal
    recovered_data = recovered_pilot_sig[0].get_data()
    recovered_data = recovered_pilot_sig[0].demodulate(recovered_data) * 1   # demodulates data from 1st part of recovered signal
    orig_data = test_sig.demodulate(orig_data) * 1  # demodulates original data
    A = np.hsplit(orig_data, 2)     # gets 1st frame as A[0]
    print("Recovered data array shape: ", end="")
    print(recovered_data.shape)
    print("Original data array shape: ", end="")
    print(orig_data.shape)

    [bool_arr, success] = Output.compare_symbols(recovered_data, A[0])
    print("Recovery Percentage:")
    print(success)
    print("Bool array shape: ")
    print(bool_arr.shape)
    Output.error_dist(bool_arr, snr, M, n_pols=2)

