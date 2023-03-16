"""
Function to perform the SNR measurement of the signal

By entering the times of the noise region (noise_t1 to noise_t2) and the
signal region (signal_t1 to signal_t2) these regions will be used for the 
calculation of the SNR

A plot is generated showing the noise region between red lines, and the signal
region between black lines to confirm the correct regions are set

"""

__author__ = "Richard Gold, Kinneir Dufort Design Ltd."
__copyright__ = "Kinneir Dufort Design Ltd., July 2022"
__version__ = "0.1.0"


# 3rd party imports
import matplotlib.pyplot as plt
import numpy as np
import math


def SNR_measurement(input_signal,noise_t1,noise_t2,signal_t1,signal_t2,fs,toffset,plot):

    print("Perforing SNR analysis")
    #Create time array for plotting
    time_s=np.arange(0,len(input_signal)/fs,1/fs)
    time_s=time_s+toffset;
    time_s=time_s[0:len(input_signal)]
    
    #Convert time in seconds to sample number 
    noise_s1=int((noise_t1-toffset)*fs)
    noise_s2=int((noise_t2-toffset)*fs)
    signal_s1=int((signal_t1-toffset)*fs)
    signal_s2=int((signal_t2-toffset)*fs)
    
    #Calculate peak to peak voltage for signal
    sigMax=max(input_signal[signal_s1:signal_s2])
    sigMin=min(input_signal[signal_s1:signal_s2])
    sig_P2P=sigMax-sigMin

    ##Calculate Noise RMS
    sum_square=0
    count=0    
    for a in range(noise_s1,noise_s2):
        sum_square=sum_square+(input_signal[a])**2
        count=count+1
    noise_RMS=np.sqrt(sum_square/count)
    
    print("Signal Pk-pk Voltage: ", sig_P2P)
    print("Noise RMS Voltage: ", noise_RMS)
    
    SNR_Vratio=sig_P2P/noise_RMS
    print("Signal Vpk-pk / Noise Vrms: ",SNR_Vratio)
    SNR_dB=20*math.log10(SNR_Vratio)
    print("20*log10(Signal Vpk-pk / Noise Vrms): ",SNR_dB)
    
    ###Plot noise and signal sections
    if(plot==1):
        plt.figure(figsize=(12, 10), dpi=100)
    
        plt.plot(list(time_s),input_signal)
        plt.xlabel('Time (s)')
        plt.ylabel('Signal (V)')
        
        #Plot the lines showing noise and signal regions   
        plt.plot([noise_t1,noise_t1],[min(input_signal),max(input_signal)],color='red')
        plt.plot([noise_t2,noise_t2],[min(input_signal),max(input_signal)],color='red') 
        plt.plot([signal_t1,signal_t1],[min(input_signal),max(input_signal)],color='black')
        plt.plot([signal_t2,signal_t2],[min(input_signal),max(input_signal)],color='black')    
                
    return SNR_dB
        
        