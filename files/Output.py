"""
Contains functions used to show results
Author: William McCallum
Last Updated: 30/6/21
"""

import numpy as np
import matplotlib.pyplot as plt
from bokeh.io import output_notebook
from bokeh.plotting import figure, show
import os


def Square_Wave(sig, nmodes):
    """
    Plots data as a square wave.
    Note that this function assumes points are evenly spaced

    Parameters
    ---------------------------------------------
    sig : SignalQAMGrayCoded
        Signal that is to have its data output
    """
    # get signal data and frequency
    data1 = sig[0]  # x-pol signal data
    if nmodes == 2:
        data2 = sig[1]  # y-pol signal data
        square_data2 = np.zeros(shape=(len(data2)*2)) # array for storing square wave data points
    freq = sig.fb   # signal frequency

    square_data1 = np.zeros(shape=(len(data1)*2)) # array for storing square wave data points

    # doubles up data-points
    for i in range(len(data1)):
        square_data1[2*i] = data1[i]
        square_data1[2*i+1] = data1[i]

    if nmodes == 2:
        for i in range(len(data2)):
            square_data2[2*i] = data1[i]
            square_data2[2*i+1] = data1[i]

    # offsets period by 1/2 and doubles up
    period = 1 / freq
    time_points = np.zeros(shape=len(square_data1))
    time_points[1] = 0.5 * period
    for i in range(1, len(data1)):
        time_points[2*i] = period * (i - 0.5)
        time_points[2 * i + 1] = period * (i + 0.5)

    # plots results
    plt.subplot(2,1,1)
    plt.plot(time_points, square_data1, 'b-')
    plt.xlabel("Time (S)")
    plt.ylabel("Value")
    plt.ylim([-1, 2])
    plt.title("Data represented as square wave")
    if nmodes == 2:
        plt.subplot(2,1,2)
        plt.plot(time_points, square_data2, 'r-')
    plt.show()
    return


def compare_symbols(sym_set1, sym_set2):
    """
    Compares 2 bool matrices of the same size and creates a matrix where 1 means elements match, and 0 means they are different
    """
    bool_arr = np.equal(sym_set1, sym_set2) * 1
    success = np.sum(bool_arr) / np.size(bool_arr)  # gets proportion of bits correctly recovered, 1=complete success
    print("Results")
    print(bool_arr)
    print("Error rate: %e" % (1-success))
    total_err = np.size(bool_arr) - np.sum(bool_arr)    # gets total number of bits with errors, 0 = complete success
    print("Total Errors %d" % total_err)
    return [bool_arr, success]


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

def error_dist(error_arr, snr, M, n_bins=100):
    """
    Shows the distribution of errors in a signal using a histogram

    Parameters
    ---------------------------------------------
    error_arr : numpy array
        Array of bools where 1 indicates a success, and 0 indicates an error in the signal
    n_bins : integer
        how many different bins the historgram is broken up into, if n_bins>len(error_arr), then there is 1 bit for each item in error_arr
    """
    # convert error arrays into error position arrays
    error_idx1 = np.where(error_arr[0,:] == 0)[0]
    error_idx2 = np.where(error_arr[1,:] == 0)[0]
    if n_bins > len(error_idx1):
        n_bins1 = max(len(error_idx1), 1)
    else:
        n_bins1 = n_bins

    if n_bins > len(error_idx2):
        n_bins2 = max(len(error_idx2), 1)
    else:
        n_bins2 = n_bins

    # Separate error array 
    fig, axs = plt.subplots(2, 1, figsize=(10, 5))
    axs[0].hist(error_idx1, n_bins1, density=False)
    axs[1].hist(error_idx2, n_bins2, density=False)
    plt.xlabel("Position")
    plt.ylabel("Error rate")
    plt.title("Error rate for recovered signal with %d-QAM and %d dB SNR" % (snr, M))
    plt.show()
    return 
