"""
Example plotting of ultrasound scans

singlePlot produces a plot of the raw against filtered results for a single scan

multPlot enables multiple results to be plotted over each other. To do this,
the figure and subplots are defined in the top-level script. Then each time
multPlot is called, the plotting is applied to these top-level figure/subplot objects.
A label string for the legends are passed to multplot.


FFT plot provides an FFT of the capture. Can be used to identify noise sources
relative to the main signal.

"""

__author__ = "Richard Gold, Kinneir Dufort Design Ltd."
__copyright__ = "Kinneir Dufort Design Ltd., July 2022"
__version__ = "0.1.0"


# 3rd party imports
import matplotlib.pyplot as plt
import numpy as np
import scipy.fftpack


def singlePlot(raw_results,filtered_results,fs):
    

    ##Create matching time array
    time_s=np.arange(0,len(filtered_results)/fs,1/fs)
    
    ##Add the delay offset
    triggerTimeOffset_s=float(raw_results[1][6])
    time_s=time_s+triggerTimeOffset_s;
    time_s=time_s[0:len(raw_results[2:])]
    
    ##Create figure and define size and resolution
    fig1=plt.figure(figsize=(12, 10), dpi=100)

    ##Top plot
    ax1= plt.subplot(2,1,1)
    plt.plot(time_s,raw_results[2:],label='Raw Data')
    plt.xlabel('Time (s)')
    plt.ylabel('Signal (V)')
    plt.title('Raw Signal')
    plt.legend(loc="upper right")
    
    ##Bottom plot
    ax2=plt.subplot(2,1,2,sharex=ax1,sharey=ax1)
    plt.plot(time_s,filtered_results,label='Filt Data')
    plt.xlabel('Time (s)')
    plt.ylabel('Signal (V)')
    plt.title('Filtered Signal')
    plt.legend(loc="upper right")
    
    fig1.tight_layout()
    
    plt.savefig('singlePlotOutput.png')
    
def multPlot(fig,ax1,ax2,raw_results,filtered_results,fs,label_text):
            
    ##Create matching time array
    time_s=np.arange(0,len(filtered_results)/fs,1/fs)
    ##Add the delay offset
    triggerTimeOffset_s=float(raw_results[1][6])
    time_s=time_s+triggerTimeOffset_s;
    time_s=time_s[0:len(raw_results[2:])] ##Ensure they're matched in size

    ##Top plot - raw signal
    ax1.plot(time_s,raw_results[2:],label=label_text)
    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel('Signal (V)')
    ax1.set_title('Raw Signal')
    ax1.legend(loc="upper right")
    
    ##Bottom plot - filtered
    ax2.plot(time_s,filtered_results,label=label_text)
    ax2.set_xlabel('Time (s)')
    ax2.set_ylabel('Signal (V)')
    ax2.set_title('Filtered Signal')
    ax2.legend(loc="upper right")
    
    
##Perform FFT of the acquisition - used for identifying and debugging noise sources
def FFT_plot(raw,filtered,fs):
    y=raw
    N=len(y)
    T=1/fs
   # x = np.linspace(0.0, N*T, N)
    yf = scipy.fftpack.fft(y)
    xf = np.linspace(0.0, 1.0/(2.0*T), N//2)
    fig1=plt.figure(figsize=(12, 10), dpi=100)
    plt.plot(xf, 2.0/N * np.abs(yf[:N//2]),label='Raw FFT',c='blue')
    
    y=filtered
    N=len(y)
    T=1/fs
   # x = np.linspace(0.0, N*T, N)
    yf = scipy.fftpack.fft(y)
    xf = np.linspace(0.0, 1.0/(2.0*T), N//2)
    plt.plot(xf, 2.0/N * np.abs(yf[:N//2]),label='Filtered FFT',c='orange')
    plt.title('FFT Comparison')
    plt.xlabel('Frequency (Hz)')
    plt.ylabel('Magnitude')
    plt.ylim([0,0.02])
    plt.legend(loc="upper right")
    fig1.tight_layout()
    
    plt.savefig('FFT_Comparison.png')