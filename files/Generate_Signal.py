"""
Code for generating a QAM signal and saving it to a file
"""

from qampy import signals, impairments, equalisation, phaserec, helpers
import numpy as np
from bokeh.io import output_notebook
from bokeh.plotting import figure, show
import os

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

def generate_random_data(length):
    """
    Generates a random array of bits of size length
    To be implemented: given a set of symbols, only generate sets of bits that map to symbols in that set
    """
    sample_data = [0,1]
    data = np.random.choice(sample_data, size=length)
    return data


def encode_data(sig, data, data2=[]):
    """
    Encodes the given data onto the given signal
    If 2 sets of data are given, and the given signal has dual polarisation, will encode the each set of data to a separate polarisation.
    Note that if a 2nd set of data is included, but the signal only has a single polarisation, the 2nd set of data will be ignored.
    """
    # encodes data onto 1st polarisation
    encoded_signal = sig.modulate(data)
    #sig[0] = encoded_signal

    # encodes data2 to 2nd polarisation if given
    if data2 != [] and sig.nmodes==2:
        encoded_signal2 = sig.modulate(data2)
        #sig[1] = encoded_signal2       # fix size mismatch issue
        return [sig, encoded_signal, encoded_signal2]
    return [sig, encoded_signal]


def save_sig_data_to_file(sig, path="C:/Users/wamcc1/Documents/QAM_sig", filename="sig_data.txt"):  # TO DO: save original signal data + noisy signal E as pickle
    """
    Saves sig to a txt file with given path and filename. If path and/or does not exist, creates it.

    Parameters
    ---------------------------------------------
    sig : SignalQAMGrayCoded
        Signal that is to be saved to a file
    path : txt
        Path of where file is to be saved
    filename : txt
        Name of file where data is to be saved. If file already exists, overwrites it.

    Output
    ---------------------------------------------
    File at given location with signal data
    """
    # checks if path exists
    if not os.path.isdir(path):
        # creates path if it doesn't exist
        os.makedirs(path)

    # check if file exists, if it does, deletes it to avoid overflow issues
    file_path = os.path.join(path, filename)
    if os.path.isfile(file_path):
        os.remove(file_path)

    # converts sig data to string to be save
    x_data_real = ", ".join(str(x) for x in sig[0].real)   # needs to be byte-like, not string
    x_data_imag = ", ".join(str(x) for x in sig[0].imag)
    y_data_real = ", ".join(str(x) for x in sig[1].real)
    y_data_imag = ", ".join(str(x) for x in sig[1].imag)

    # writes data to file
    fid = os.open(file_path, os.O_WRONLY|os.O_CREAT) # opens file to write to it, and creates file if it doesn't already exist
    os.write(fid, x_data_real.encode('utf-8'))
    os.write(fid, "\n".encode('utf-8'))
    os.write(fid, x_data_imag.encode('utf-8'))
    os.write(fid, "\n".encode('utf-8'))
    os.write(fid, y_data_real.encode('utf-8'))
    os.write(fid, "\n".encode('utf-8'))
    os.write(fid, y_data_imag.encode('utf-8'))
    
    os.close(fid)   # closes file
    return

def generate_AWG_signal(M, N, nmodes=2, fs=1, fb=1, shift=0, **kwargs):
    """
    Generates a signal that gets resampled at the output DAC

    Parameters
    ---------------------------------------------
    M : Integer
        QAM-order, should be a power of 2, ie. M=2^x for x being some integer
    N : Integer
        Path of where file is to be saved
    nmodes : Integer
        Number of polarisations, 1=single polarisation, 2=dual polarisation
    fs : Integer
        Sampling frequency of output DAC
    fb : Integer
        Baud rate of AWG (symbols/s)
    shift : 

    Output
    ---------------------------------------------
    signal_to_be_transmitted : SignalQAMGrayCoded
        Generated signal
    """
    if "beta" in kwargs:
        beta = kwargs.pop("beta")
    else:
        beta = 0.1

    sig = signals.SignalQAMGrayCoded(M, N, fb=fb, nmodes=nmodes)
    plot_constellation(sig, "Initial signal")

    # resample signal at output DAC
    signal_to_be_transmitted = sig.resample(fs, beta=beta)

    return signal_to_be_transmitted 

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

def plot_constellation(E, title="QPSK signal constellation"):
    """
    Plots signal in a constellation diagram
    """
    fig = figure(title=title, output_backend="webgl")
    fig.scatter(E[0].real, E[0].imag, color='red', alpha=0.3)
    fig.scatter(E[1].real, E[1].imag, color='blue', alpha=0.3)
    fig.xaxis[0].axis_label = "In-Phase"
    fig.yaxis[0].axis_label = "Quadrature"
    show(fig)