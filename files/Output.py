"""
Contains functions used to show results
Author: William McCallum
Last Updated: 30/6/21
"""

from qampy import signals, impairments, equalisation, phaserec, helpers, theory
import numpy as np
import matplotlib.pyplot as plt
from bokeh.io import output_notebook
from bokeh.plotting import figure, show
import os
import math
from matplotlib.animation import FuncAnimation 


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

def error_dist(error_arr, snr, M, n_bins=100, n_pols=2):
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
    

    if n_pols == 2:
        error_idx1 = np.where(error_arr[0,:] == 0)[0]
        if n_bins > len(error_idx1):
            n_bins1 = max(len(error_idx1), 1)
        else:
            n_bins1 = n_bins
        error_idx2 = np.where(error_arr[1,:] == 0)[0]
        if n_bins > len(error_idx2):
            n_bins2 = max(len(error_idx2), 1)
        else:
            n_bins2 = n_bins
    else:
        error_idx1 = np.where(error_arr[:] == 0)[0]
        if n_bins > len(error_idx1):
            n_bins1 = max(len(error_idx1), 1)
        else:
            n_bins1 = n_bins

    # Separate error array 
    if n_pols == 2:
        fig, axs = plt.subplots(2, 1, figsize=(10, 5))
        axs[0].hist(error_idx1, n_bins1, density=False)
        axs[1].hist(error_idx2, n_bins2, density=False)
    else:
        fig, axs = plt.subplots(1, 1, figsize=(10, 5))
        axs.hist(error_idx1, n_bins1, density=False)
    plt.xlabel("Position")
    plt.ylabel("Error rate")
    plt.title("Error rate for recovered signal with %d-QAM and %d dB SNR" % (M, snr))
    plt.show()
    return 


def init_anim(points1):
    """
    Initializes parameters for animation
    """
    #point.set_data([], [])
    points1.set_offset()
    return points1,


def animate(points1, sig1, sig2, i):
    """
    Steps through animation
    """
    #x1 = sig1[i].real
    #y1 = sig1[i].imag
    #point1.set_data(x1, y1)
    #x2 = sig2[i].real
    #y2 = sig2[i].imag
    #point2.set_data(x2, y2)
    point1.set_offset(i)
    return point1, #point2,


def animate_data(sig1, sig2):
    """
    Function that takes 2 signals and shows symbols in order 1 by 1 to compare the signals

    """
    fig = plt.figure() # initialize figure
    ax = plt.axes(xlim =(-1.5, 1.5), ylim =(-1.5, 1.5)) # get plot limits
    #points1, = ax.scatter([], [], s=2, alpha=0.8, c='#F55E46') # original signal
    #points2, = ax.scatter([], [], s=2, alpha=0.8, c='#2F79F5') # recovered signal
    ax.axhline(y=0, color='k')  # x axis
    ax.axvline(x=0, color='k')  # y axis
    points1 = ax.scatter([], [], s=2)

    anim = FuncAnimation(fig, animate, init_func=init_anim,
                               frames=len(sig1), interval=20, blit=False, fargs=(points1, sig1, sig2))    # animation

    anim.save('sig_comp.gif', writer='imagemagick')
    return

def plot_convolution(Ex, Ey, orig_X, orig_Y, M, delay_offset=-1, corr_search_win=100, sync_start=2001):
    """
    This function aims to plot the convolution between a signal and the same signal after delays and noise applied (not phase noise)
    """
    # normalises signals
    Ex = Ex/math.sqrt(np.mean(abs(Ex)**2))
    Ey = Ey/math.sqrt(np.mean(abs(Ey)**2))
    Ex = Ex*math.sqrt(2/3*(M-1))
    Ey = Ey*math.sqrt(2/3*(M-1))

    syncX = orig_X[sync_start:sync_start+corr_search_win]
    syncY = orig_Y[sync_start:sync_start+corr_search_win]
    indexXX=[];
    indexYY=[];
    indexXY=[];
    indexYX=[];
    pos = np.arange(sync_start,sync_start+corr_search_win)
    
    for k in range(corr_search_win):
        indexXX.append(abs(sum([a*b for a,b in zip(np.conj(syncX), Ex[k:k+corr_search_win])])))
        indexYY.append(abs(sum([a*b for a,b in zip(np.conj(syncY), Ey[k:k+corr_search_win])])))
        indexXY.append(abs(sum([a*b for a,b in zip(np.conj(syncY), Ex[k:k+corr_search_win])])))
        indexYX.append(abs(sum([a*b for a,b in zip(np.conj(syncX), Ey[k:k+corr_search_win])])))

    # gets maximums and their locations
    maxXX = max(indexXX)
    maxXX_idx = indexXX.index(maxXX)
    maxYY = max(indexYY)
    maxYY_idx = indexYY.index(maxYY)
    maxXY = max(indexXY)
    maxXY_idx = indexXY.index(maxXY)
    maxYX = max(indexYX)
    maxYX_idx = indexYX.index(maxYX)

    # plots results
    ax1 = plt.subplot(211)
    ax1.plot(pos, indexXX, 'r', alpha=0.8, label='xx')
    ax1.plot(pos, indexYY, 'b', alpha=0.8, label='yy')
    if delay_offset != -1:
        ax1.plot(abs(delay_offset), maxXX, 'm*', lw=4)
    ax1.set_title("Convolution plot")
    ax1.set_xlabel("Position")
    ax1.set_ylabel("Convolution")
    ax1.legend(loc='best')
    ax2 = plt.subplot(212)
    ax2.plot(pos, indexXY, 'g', alpha=0.8, label='xy')
    ax2.plot(pos, indexYY, 'k', alpha=0.8, label='yx')
    if delay_offset != -1:
        ax2.plot(abs(delay_offset), maxXY, 'm*', lw=4)
    ax2.set_title("Convolution plot")
    ax2.set_xlabel("Position")
    ax2.set_ylabel("Convolution")
    ax2.legend(loc='best')
    plt.show()
    return 

def plot_BER_theory(M, ber_data=[], snr_data=[], labels=['Data'], min_snr=10, max_snr=30):
    steps = max_snr - min_snr + 1
    BER = np.zeros(steps)
    SNR_theory = np.arange(min_snr, max_snr+1)
    for i in range(steps):
        BER[i] = theory.ber_vs_es_over_n0_qam(10**((min_snr+i)/10), M)

    plt.plot(SNR_theory, BER, 'b-', label='Theory')

    if ber_data!=[]:
        if len(ber_data.shape) > 1:
            for i in range(len(ber_data)): # for each set of ber data
                plt.plot(snr_data, ber_data[i], '.', label=(labels[i]))
                plt.legend(loc='best')
        else:
            plt.plot(snr_data, ber_data, 'r.', label=(labels[0]))
            plt.legend(loc='best')
    plt.xlabel("SNR")
    plt.ylabel("BER")
    plt.yscale('log')
    plt.title("SNR vs. BER for %d-QAM" % M)
    plt.show()
    return

def plot_est_vs_actual_snr(snr, est_snr, title="Est Snr vs. Actual", labels=["Signal"]):
    """
    Plots the difference between actual snr of a signal and the est snr based on the BER
    """
    plt.plot(snr, snr, "k-", label="Ideal SNR")
    if len(est_snr.shape) > 1:
            for i in range(len(est_snr)): # for each set of ber data
                plt.plot(snr, est_snr[i], '-', label=(labels[i]))
                plt.legend(loc='best')
    else:
        plt.plot(snr, est_snr, 'r-', label=(labels[0]))
        plt.legend(loc='best')
    plt.title(title)
    plt.xlabel("Actual snr (dB)")
    plt.ylabel("Estimated snr (dB)")
    plt.show()
    return