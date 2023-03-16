from numpy import arange, linspace, exp, pi, fft, zeros
from math import cos, sin, ceil

def fn_nextpow2(x):  
    return 1 if x == 0 else 2**(x - 1).bit_length()

def fn_hanning(time_pts, peak_pos_fract, half_width_fract):
    x = linspace(start = 0, stop = 1, num = time_pts)
    win = zeros(time_pts, dtype = float)
    
    for ii in range(0, time_pts):
        y = 0.5 * (1 + cos((x[ii]-peak_pos_fract) / half_width_fract * pi))
        win[ii] = y * ((x[ii] >= (peak_pos_fract-half_width_fract)) & (x[ii] <= (peak_pos_fract+half_width_fract)))
    
    return win

def fn_create_hanning_burst(pts, centre_freq, time_step, no_cycles, centre_time):
    time = arange(pts) * time_step
    time = time.flatten()
    tmid = max(time) / 2;
    tmax = max(time);
    
    carrier = zeros(pts, dtype = float)
    
    for ii in range(0, pts):
        carrier[ii] = sin(2 * pi * centre_freq * (time[ii] - tmid))
    
    window = fn_hanning(pts, 0.5, (no_cycles/centre_freq/tmax/2));
    time_sig = carrier * window;
    
    # do spectrum
    duration = no_cycles / centre_freq
    min_pts = int(ceil((tmax+(duration/2))/time_step))
    fft_pts = fn_nextpow2(min_pts)
    fstep = 1/(fft_pts*time_step);
    freq = arange(fft_pts/2) * fstep
    in_freq_spec = fft.fft(time_sig, n = fft_pts)
    in_freq_spec = in_freq_spec[0:int(fft_pts / 2)]
    in_freq_spec = in_freq_spec*exp(2*pi*1j*freq*(tmid-centre_time))
    in_time_sig = fft.ifft(in_freq_spec, n = fft_pts) * 2
    in_time_sig = in_time_sig[0:pts]
    sf = 1 / max(abs(in_time_sig))
    in_time_sig = in_time_sig * sf
    in_freq_spec = in_freq_spec * sf
    
    return time, in_time_sig, freq, in_freq_spec, fft_pts