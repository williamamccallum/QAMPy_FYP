"""
Comparison of performance between pilot based modulation and blind recovery
Author: William McCalllum
Last Updated: 25/5/22
"""

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
    snr = np.arange(19, 26)     # snr range to sweep over
    N = 2**19                   # Number of symbols in signal
    M = [16, 64, 256, 1024]     # M-QAM
    fs = 92*10**9               # sampling frequency (for AWG)
    fb = 40*10**9               # baud rate (symbols / s)
    f_scope = 80*10**9          # scope sample frequency
    npols = 2                   # number of polarisations
    Ntaps_blind = 7                  # how many taps are used in signal equalisation function
    Ntaps_pilot = 21
    freq_off = 50e6             # carrier frequency offset
    linewidth = 100e3           # linewidth of the laser
    dumped_edges = 15           # number of symbols dropped from edges of blind signal 
    edge_size = dumped_edges + int(math.floor(Ntaps_blind-1)/2)

    # Pilot signal properties
    pilot_seq_len = 2048*8  # length of the pilot frame
    pilot_ins_ratio = 32    # ratio of data : pilot frames
    nframes = 2             # number of frames

    # arrays for storing results
    blind_est_snr = np.zeros((len(M), len(snr)))
    pilot_est_snr = np.zeros((len(M), len(snr)))

    # Transmitter side ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    for j in range(len(M)):     # for each M-QAM
        print("M: ", end="")
        print(M[j])

        # Create signals
        blind_sig = signals.SignalQAMGrayCoded(M[j], N, fb=fb, nmodes=npols)
        print("Original Blind sig shape: ", end="")
        print(blind_sig.shape)
        blind_sig = Impairments.add_edges(blind_sig, edge_size)
        upsampled_blind_sig = blind_sig.resample(fb*2, beta=0.1)    # resamples blind signal to AWG sampling frequency

        pilot_sig = signals.SignalWithPilots(M[j],N,pilot_seq_len,pilot_ins_ratio,nmodes=npols,Mpilots=4,nframes=nframes,fb=fb)
        pilot_sig_orig_data = pilot_sig.get_data()
        upsampled_pilot_sig = pilot_sig.resample(fb*2, beta=0.1)    # resamples pilot signal to AWG sampling frequency

        for i in range(len(snr)):
            print("SNR: ", end="")
            print(snr[i])

            # Add noise
            # impaired_blind_sig = impairments.simulate_transmission(upsampled_blind_sig,snr=snr[i],dgd=0, freq_off=0,lwdth=0)
            impaired_blind_sig = impairments.change_snr(upsampled_blind_sig, snr[i])
            impaired_pilot_sig = impairments.simulate_transmission(upsampled_pilot_sig,snr=snr[i],dgd=0, freq_off=freq_off,lwdth=linewidth,roll_frame_sync=True)

            # Receiver side -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
            # equalisation
            # recovered_blind_sig, wxy, err = equalisation.dual_mode_equalisation(impaired_blind_sig, (1e-3, 1e-3), Ntaps, methods=("mcma", "sbd"), avoid_cma_sing=(False, False))
            impaired_blind_sig = impaired_blind_sig.resample(fb, beta=0.1)
            wxy, err = equalisation.equalise_signal(impaired_blind_sig, 2e-3, Ntaps=Ntaps_blind, method="mddma")
            recovered_blind_sig = equalisation.apply_filter(impaired_blind_sig, wxy)
            recovered_blind_sig = helpers.normalise_and_center(recovered_blind_sig)
            # recovered_blind_sig, ph = phaserec.bps(recovered_blind_sig, 64, 20)
            recovered_blind_sig = helpers.dump_edges(recovered_blind_sig, dumped_edges)
            #print("Blind sig shape: ", end="")
            #print(recovered_blind_sig.shape)

            impaired_pilot_sig.sync2frame()
            impaired_pilot_sig.corr_foe()
            [taps, recovered_pilot_sig] = equalisation.pilot_equaliser(impaired_pilot_sig,(1e-3,1e-3),Ntaps_pilot, frame=0, foe_comp=False,methods=("mddma","sbd_data"))
            recovered_pilot_sig = phaserec.pilot_cpe(recovered_pilot_sig,N=5,use_seq=False)

            # get Estimated SNR
            blind_est_snr[j, i] = 10*np.log10(recovered_blind_sig.est_snr()[0])
            pilot_est_snr[j, i] = 10*np.log10(recovered_pilot_sig[0].get_data().est_snr()[0])
            print("SNR blind est.: ", end="")
            print(blind_est_snr[j, i])
            print("SNR pilot est.: ", end="")
            print(pilot_est_snr[j, i])

    # Output results ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    # Output.plot_BER_theory(M, np.array([blind_ber, pilot_ber]), snr, labels=["Blind", "Pilot"])
    labels = []
    colours = []
    colour_min = 80 / 255
    colour_max = 255 / 255
    for i in range(len(M)):
        labels.append(("%d-QAM Blind" % M[i]))
        current_colour = colour_min + i*((colour_max - colour_min) / (len(M) - 1))
        colours.append([current_colour, 0, 0])
    for i in range(len(M)):
        labels.append(("%d-QAM Pilot" % M[i]))
        current_colour = colour_min + i*((colour_max - colour_min) / (len(M) - 1))
        colours.append([0, 0, current_colour])
    # Output.plot_est_vs_actual_snr(snr, est_snr=blind_est_snr, title="Est Snr vs. Actual for Blind Signal", labels=labels)
    # Output.plot_est_vs_actual_snr(snr, est_snr=pilot_est_snr, title="Est Snr vs. Actual for Pilot Signal", labels=labels)
    Output.plot_est_vs_actual_snr(snr, est_snr=np.concatenate((blind_est_snr, pilot_est_snr), axis=0), title="Est Snr vs. Actual for Blind & Pilot Signal", labels=labels, colours=colours)
