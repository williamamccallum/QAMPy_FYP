"""
Main python file which runs AWG and synthesiser simulation
"""

from qampy import signals, impairments, equalisation, phaserec, helpers
import numpy as np
from bokeh.io import output_notebook
from bokeh.plotting import figure, show
import os
import Generate_Signal
import Receive_Signal
import Impairments

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


if __name__ == "__main__":
     # sets up variables
    fs = 92*10**9   # sampling frequency (for AWG)
    fb = 40*10**9   # baud rate (symbols / s)
    M = 4**2        # QAM order
    N = 2**16       # number of symbols
    nmodes = 2      # number of polarisations
    snr = 23        # signal to noise ratio

    # generates signal and encodes data
    sig = Generate_Signal.generate_AWG_signal(M, N, nmodes, fs, fb)
    plot_constellation(sig, "Initial Signal")

    # adds noise to signal
    noisy_sig = Impairments.add_noise(sig, snr)
    plot_constellation(noisy_sig, "Signal with noise added")

    # writes signal to file
    Generate_Signal.save_sig_data_to_file(noisy_sig)

    # receives signal from file
    read_sig_data = Receive_Signal.read_sig_data_from_file()
    # read_sig = Receive_Signal.recreate_signal(read_sig_data, fs, M, N, fb, nmodes)

    # recovers signal
    # recovered_signal = Receive_Signal.recover_signal(read_sig)
    # plot_constellation(recovered_signal, "Signal with phase recovery")

    #---------------------------------------------------------------------
    # tests pickle compression and recovery
    Generate_Signal.save_base_signal(sig, "Test.txt")
    loaded_sig = Receive_Signal.load_base_signal("Test.txt")
    plot_constellation(sig, "Original signal")
    plot_constellation(loaded_sig, "Signal after pickle compression")

    # Applies received signal data to received base signal
    recreated_sig = Receive_Signal.fixed_recreate(loaded_sig, read_sig_data)
    plot_constellation( recreated_sig, "Signal after data reapplied")
    recovered_signal = Receive_Signal.recover_signal(recreated_sig)
    plot_constellation(recovered_signal, "Signal with phase recovery")

    print("SER = ",recovered_signal.cal_ser())
    print("BER = ",recovered_signal.cal_ber())
