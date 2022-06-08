"""
The functions in this file are aimed at being able to repeatedly send a signal with some random initial delay, and then recover the original signal
Author: William McCallum
Last Updated: 28/6/21
"""

from qampy import signals, impairments, equalisation, phaserec, helpers
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


def compare_symbols(sym_set1, sym_set2):
    """
    Compares 2 bool matrices of the same size and creates a matrix where 1 means elements match, and 0 means they are different
    """
    bool_arr = np.equal(sym_set1, sym_set2) * 1
    success = np.sum(bool_arr) / np.size(bool_arr)  # gets proportion of bits correctly recovered, 1=complete success
    print("Results")
    print(bool_arr)
    print("Error rate: %.2f" % (1-success))
    return [bool_arr, success]

def copy_sig(sig, n):
    """
    Copies a signal n times and returns the rebuilt signal

    Parameters
    ---------------------------------------------
    sig : SignalQAMGrayCoded
        Signal to have its data copied and then rebuilt
    n : float
        number of times signal should be copied. For full waveform recovery, n>=2

    Output
    ---------------------------------------------
    rebuilt_sig : SignalQAMGrayCoded
        Signal that has the data of sig copied n times
    """
    sig_temp = sig  # gets temporary signal 

    # checks if n is a whole number
    if math.floor(n) == n:
        sig_temp = np.tile(sig_temp, n)

    # not currently working, to be fixed
    else:       # if n is a fraction
        slice = math.floor((n % 1) * len(sig_temp))   # gets how many array elements are in fractional part of n
        frac_temp = sig_temp[:slice]    # gets copy of signal of length equal to fractional part of n
        sig_temp = np.tile(sig_temp, math.floor(n)) # gets floor(n) copies of original signal
        sig_temp = np.append(sig_temp, frac_temp)   # combines fractional and whole copies of signal
        print(sig[0])
        print(frac_temp[0])

    rebuilt_sig = sig.recreate_from_np_array(sig_temp)  # gets rebuilt signal
    return rebuilt_sig


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
    shift = random.randint(1,upsample_mult-1)  # shift by shift spaces
    if random.random() < 0.5:     # 50% chance to shift in -ve direction
        shift *= -1 
    print("Fractional shift: %.3f" % (shift / upsample_mult))
    if nmodes == 1:
        offset_sig = np.roll(sig, shift, axis=0) #single polarization desynchronization
    if nmodes == 2:
        offset_sig = np.roll(sig, shift, axis=1) #dual polarization desynchronization

    # downsample to scope
    offset_sig = offset_sig.resample(scope_f, beta=0.1, renormalise=True)

    return offset_sig


def recover_full_waveform(sig, orig_sig, frac_upscale=0):
    """
    Takes in a signal with multiple copies of a data packet and a delay, and recovers the original waveform

    Parameters
    ---------------------------------------------
    sig : SignalQAMGrayCoded
        Signal to have its data recovered
    orig_sig : SignalQAMGrayCoded
        Original signal to synchronise sig with
    frac_upscale : int
        if 0, no fractional delay. Else, gives how much the signal should be upsampled from the baud rate to make the fractional delay an integer delay, and hence recoverable
        Note that signal data will be returned at the upsampled frequency

    Output
    ---------------------------------------------
    tx_data : array
        recovered waveform synced to original
    rx_data : array
        Original waveform data
    """
    if frac_upscale == 0:   # if there is no fractional delay
         # syncs signals
        [tx_data, rx_data] = sig._sync_and_adjust(sig, orig_sig) 
        recovered_sig  = orig_sig.recreate_from_np_array(tx_data)
        orig_sig  = orig_sig.recreate_from_np_array(rx_data)
        return [recovered_sig, orig_sig]
    else:                   # if there is a fractional delay
        # upscales signals accordingly

        sig = sig.resample(orig_sig.fb*frac_upscale)
        print("signal fb: %d" % sig.fs)
        upsampled_sig = orig_sig.resample(orig_sig.fb*frac_upscale)
        print("original signal fb: %d" % upsampled_sig.fs)
        # syncs signals for fractional delay
        [tx_data, rx_data] = sig._sync_and_adjust(sig, upsampled_sig) 
        # recovers signal
        #upsampled_sig = orig_sig.resample(orig_sig.fb*frac_upscale)     # upsamples original signal to use as base to recover signal waveform from tx data
        recovered_sig = upsampled_sig.recreate_from_np_array(tx_data)
        # lowers signal to baud rate
        orig_sig = orig_sig.resample(orig_sig.fb*2, beta=0.1)
        recovered_sig = recovered_sig.resample(orig_sig.fb*2, beta=0.1)
        # syncs signals for large delay
        [tx_sig, rx_sig] = recover_full_waveform(recovered_sig, orig_sig, 0)
        recovered_sig2 = orig_sig.recreate_from_np_array(tx_sig)
        orig_sig2 = orig_sig.recreate_from_np_array(rx_sig)
        recovered_sig2 = recovered_sig2.resample(orig_sig.fb, beta=0.1)
        return [recovered_sig2, orig_sig2]


def compare_quadrants(sig1, sig2, nmodes=2):
    """
    Finds how many symbols are in the incorrect quadrants
    """
    assert np.shape(sig1) == np.shape(sig2)   # 2 signals need to have the same shape
    test1 = sig1[0]
    test2 = sig1[0][0]
    quad_err = 0
    if nmodes == 1:
        for i in range(len(sig1)):
            if (np.sign(sig1[i].real) != np.sign(sig2[i].real) or np.sign(sig1[i].imag) != np.sign(sig2[i].imag)):
                quad_err += 1
    elif nmodes == 2:
        for i in range(len(sig1[0])):   # check x-pol
            if (np.sign(sig1[0][i].real) != np.sign(sig2[0][i].real) or np.sign(sig1[0][i].imag) != np.sign(sig2[0][i].imag)):
                quad_err += 1
        for i in range(len(sig1[1])):   # check y-pol
            if (np.sign(sig1[1][i].real) != np.sign(sig2[1][i].real) or np.sign(sig1[1][i].imag) != np.sign(sig2[1][i].imag)):
                quad_err += 1
    return quad_err


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


if __name__ == "__main__": # if this is the main file
    # Generate initial signal
    fs = 92*10**9   # sampling frequency (for AWG)
    fb = 40*10**9   # baud rate (symbols / s)
    f_scope = 80*10**9  # scope sample frequency
    M = 64        # QAM order
    N = 2**18       # number of symbols
    nmodes = 2      # number of polarisations
    Ntaps = 11       # number of taps for equalisation
    dumped_edges = 15 # number of edges dumped
    snr = 21        # signal to noise ratio
    upsample_mult=4     # how many times the signal is upsampled to get fractional delay
    orig_sig = signals.SignalQAMGrayCoded(M, N, fb=fb, nmodes=nmodes) # create signal
    print("%d-QAM signal with %d SNR" % (M, snr))

    # copy sig
    copied_sig = copy_sig(orig_sig, n=2)
    
    # Large Delay
    # max_shift = math.floor(fb/copied_sig.fs*N)  # gets maximum possible delay, ie. length of original signal
    max_shift = N  # gets maximum possible delay, ie. length of original signal
    shift = random.randint(-max_shift, max_shift)   # gets a random shift within the range of -max_shift to +max_shift
    print("Max shift: ", end="")
    print(max_shift)
    print("Actual shift", end=": ")
    print(shift)
    delayed_sig = Impairments.delay(copied_sig, shift=shift, nmodes=2)  # applies shift

    # fractional offset
    frac_delay_sig = frac_offset(delayed_sig, f_scope, upsample_mult, nmodes=2)
    frac_delay_sig = Impairments.add_noise(frac_delay_sig, snr)
    # Output.Square_Wave(frac_delay_sig, nmodes)
    # delayed_sig = frac_delay_sig.resample(fb)

    # add edges
    edge_size = int(math.floor((Ntaps-1)/2)) + dumped_edges
    sig = add_edges(frac_delay_sig, edge_size)

    # other impairments
    #copied_sig = Impairments.add_noise(sig, snr)

    # equalisation
    wxy, err = equalisation.equalise_signal(sig, 2e-3, Ntaps=Ntaps, method="mddma")
    equalised_sig = equalisation.apply_filter(sig, wxy)
    equalised_sig, ph = phaserec.bps(equalised_sig, 36, 11)
    equalised_sig = helpers.normalise_and_center(equalised_sig)
    equalised_sig = helpers.dump_edges(equalised_sig, dumped_edges)
    print(equalised_sig.fs)

    # sync signals
    #print("Got up to waveform recovery")
    [recovered_sig, orig_sig2] = recover_full_waveform(equalised_sig, orig_sig, 0)
    #Output.plot_convolution(equalised_sig[0], equalised_sig[1], orig_sig[0], orig_sig[1], M, shift, len(equalised_sig[0]), 0)
    #frac_delay_sig = frac_delay_sig.resample(fb*upsample_mult)
    #upsample_orig_sig = orig_sig.resample(fb*upsample_mult)
    #[tx_sig, rx_sig] = frac_delay_sig._sync_and_adjust(frac_delay_sig, upsample_orig_sig)    # tx and rx reversed for some reason

    # recovers signal
    #upsampled_sig = orig_sig.resample(fb*upsample_mult)     # upsamples original signal to use as base to recover signal waveform from tx data
    #recovered_sig  = upsampled_sig.recreate_from_np_array(tx_sig)
    # recovered_sig = Receive_Signal.recover_signal(recovered_sig)   # reverses noise

    # recovers signal once more
    #[tx_sig, rx_sig] = recover_full_waveform(recovered_sig, orig_sig, 0)
    #recovered_sig2  = orig_sig.recreate_from_np_array(tx_sig)
    #recovered_sig2 = recovered_sig2.resample(fb, beta=0.1)
    Output.plot_constellation(orig_sig, "Original")
    Output.plot_constellation(frac_delay_sig, "Delayed")
    Output.plot_constellation(equalised_sig, "Equalised")
    Output.plot_constellation(recovered_sig, "Recovered")

    # demodulate
    symbols = orig_sig.demodulate(orig_sig) * 1
    symbols3 = recovered_sig.demodulate(recovered_sig) * 1
    symbols4 = delayed_sig.demodulate(delayed_sig) * 1
    #print("Symbols:")
    #print(symbols)
    #print("Recovered Symbols 2:")
    #print(symbols3)
    #print("Offset Symbols:")
    #print(symbols4)

    # compare results
    [compared, success] = Output.compare_symbols(symbols, symbols3)
    print("Bits Matching")
    print(compared)
    print("Success rate:")
    print(success)
    print("SER = ",recovered_sig.cal_ser()[0])
    print("BER = ",recovered_sig.cal_ber()[0])
    # check quadrants
    quad_err = compare_quadrants(recovered_sig, orig_sig, nmodes=2)
    print("Number of symbols with incorrect quadrant: %d" % quad_err)

    # Output.animate_data(orig_sig[0], recovered_sig[0])