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
    print("Shift: %.3f" % (shift / upsample_mult))
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
        recovered_sig  = upsampled_sig.recreate_from_np_array(tx_data)
        # lowers signal to baud rate
        orig_sig = orig_sig.resample(orig_sig.fb, beta=0.1)
        recovered_sig = recovered_sig.resample(orig_sig.fb, beta=0.1)
        # syncs signals for large delay
        [tx_sig, rx_sig] = recover_full_waveform(recovered_sig, orig_sig, 0)
        recovered_sig2  = orig_sig.recreate_from_np_array(tx_sig)
        orig_sig2  = orig_sig.recreate_from_np_array(rx_sig)
        recovered_sig2 = recovered_sig2.resample(fb, beta=0.1)
        return [recovered_sig2, orig_sig2]


if __name__ == "__main__": # if this is the main file
    # Generate initial signal
    fs = 92*10**9   # sampling frequency (for AWG)
    fb = 40*10**9   # baud rate (symbols / s)
    f_scope = 80*10**9  # scope sample frequency
    M = 4**1        # QAM order
    N = 2**3       # number of symbols
    nmodes = 2      # number of polarisations
    snr = 23        # signal to noise ratio
    upsample_mult=4     # how many times the signal is upsampled to get fractional delay
    orig_sig = signals.SignalQAMGrayCoded(M, N, fb=fb, nmodes=nmodes) # create signal
        
    # other impairments
    # impaired_sig = Impairments.add_noise(delayed_sig, snr)

    # copy sig
    copied_sig = copy_sig(orig_sig, n=2)

    # Large Delay
    # max_shift = math.floor(fb/copied_sig.fs*N)  # gets maximum possible delay, ie. length of original signal
    max_shift = N  # gets maximum possible delay, ie. length of original signal
    shift = random.randint(-max_shift, max_shift)   # gets a random shift within the range of -max_shift to +max_shift
    print("Max shift: ", end="")
    print(max_shift)
    print("shift", end=": ")
    print(shift)
    delayed_sig = Impairments.delay(copied_sig, shift=shift, nmodes=2)  # applies shift

    # fractional offset
    frac_delay_sig = frac_offset(delayed_sig, f_scope, upsample_mult, nmodes=2)
    # Output.Square_Wave(frac_delay_sig, nmodes)

    # send and receive signal

    # sync signals
    [recovered_sig, orig_sig2] = recover_full_waveform(frac_delay_sig, orig_sig, upsample_mult)
    #frac_delay_sig = frac_delay_sig.resample(fb*upsample_mult)
    #upsample_orig_sig = orig_sig.resample(fb*upsample_mult)
    #[tx_sig, rx_sig] = frac_delay_sig._sync_and_adjust(frac_delay_sig, upsample_orig_sig)    # tx and rx reversed for some reason

    # recreate and resample to baud rate
    

    # recovers signal
    #upsampled_sig = orig_sig.resample(fb*upsample_mult)     # upsamples original signal to use as base to recover signal waveform from tx data
    #recovered_sig  = upsampled_sig.recreate_from_np_array(tx_sig)
    # recovered_sig = Receive_Signal.recover_signal(recovered_sig)   # reverses noise

    # convert to baud rate
    orig_sig = orig_sig.resample(fb, beta=0.1)
    recovered_sig = recovered_sig.resample(fb, beta=0.1)
    print("Original")
    print(orig_sig)
    print("Original2")
    print(orig_sig2)
    print("Recovered")
    print(recovered_sig)

    # recovers signal once more
    #[tx_sig, rx_sig] = recover_full_waveform(recovered_sig, orig_sig, 0)
    #recovered_sig2  = orig_sig.recreate_from_np_array(tx_sig)
    #recovered_sig2 = recovered_sig2.resample(fb, beta=0.1)

    # demodulate
    symbols = orig_sig.demodulate(orig_sig) * 1
    symbols2 = orig_sig2.demodulate(orig_sig2) * 1
    symbols3 = recovered_sig.demodulate(recovered_sig) * 1
    symbols4 = delayed_sig.demodulate(delayed_sig) * 1
    print("Symbols:")
    print(symbols)
    print("Original Symbols 2:")
    print(symbols2)
    print("Recovered Symbols 2:")
    print(symbols3)
    print("Offset Symbols:")
    print(symbols4)

    # compare results
    # [compared, success] = compare_symbols(symbols, symbols2)
    print("SER = ",recovered_sig.cal_ser())
    print("BER = ",recovered_sig.cal_ber())
