%Alexis Hernandez
%Handy scope measurment for both channels HS5
%University of Bristol
%alexis.hernandez@bristol.ac.uk

%clean previous data
% clc
% clear all 
% close all


%corroborate MATLAB version
if verLessThan('matlab', '8')
    error('Matlab 8.0 (R2012b) or higher is required.');
end


% Open LibTiePie and display library info if not yet opened:
import LibTiePie.Const.*
import LibTiePie.Enum.*

if ~exist('LibTiePie', 'var')
    % Open LibTiePie:
    LibTiePie = LibTiePie.Library
end

% Search for devices:
LibTiePie.DeviceList.update();

% Try to open an oscilloscope with block measurement support and a generator in the same device:
clear scp;
clear gen;


for k = 0 : LibTiePie.DeviceList.Count - 1
    item = LibTiePie.DeviceList.getItemByIndex(k);
    if item.canOpen(DEVICETYPE.OSCILLOSCOPE) && item.canOpen(DEVICETYPE.GENERATOR)
        scp = item.openOscilloscope();
        if ismember(MM.BLOCK, scp.MeasureModes)
            gen = item.openGenerator();
            break;
        else
            clear scp;
        end
    end
end
clear item

%corroborate that there is oscilloscope and generator available
if exist('scp', 'var') && exist('gen', 'var')
    
    % Oscilloscope settings:

    % Set measure mode:
    scp.MeasureMode = MM.BLOCK;

    % Set sample frequency:     
    scp.SampleFrequency = 1e10; % 1 MHz % Maximum sample 1e9

    % Set record length:
    scp.RecordLength = 1e5; % 10000 Samples

    % Set pre sample ratio:
    scp.PreSampleRatio = 0; % 0 %

    % For all channels:
    for ch = scp.Channels
        % Enable channel to measure it:
        ch.Enabled = true;

        % Set range:
        ch.Range = 4; % 8 V

        % Set coupling:
        ch.Coupling = CK.ACV; % DC Volt

        % Release reference:
        clear ch;
    end
    
    
     % Set trigger timeout:
    scp.TriggerTimeOut = 1; % 1 s

    % Disable all channel trigger sources:
    for ch = scp.Channels
        ch.Trigger.Enabled = false;
        clear ch;
    end

    % Locate trigger input:
    triggerInput = scp.getTriggerInputById(TIID.GENERATOR_NEW_PERIOD); 
    % or TIID.GENERATOR_START or TIID.GENERATOR_STOP

    if triggerInput == false
        clear triggerInput;
        clear scp;
        clear gen;
        error('Unknown trigger input!');
    end

    % Enable trigger input:
    triggerInput.Enabled = true;

    % Release reference to trigger input:
    clear triggerInput;
    
    % Generator settings:

    % Set signal type: there are several type of singal, ramp, square,
    % arbitrary etc
    gen.SignalType = ST.SINE;
    
    %Frequency start
    fi=5e6;
    %frequency to finish
    fo=13e6;
    
    %step frequency
    sf=1e4;
    
    % Set amplitude:
    gen.Amplitude = .1; % 2 V

    % Set offset:
    gen.Offset = 0; % 0 V

    % Enable output:
    gen.OutputOn = true;
    % Print oscilloscope info:
    display(scp);
    % Print generator info:
    display(gen);
    
    % Mesaurements settings
 
    % Establish x-values
    time = linspace(0,scp.RecordLength./scp.SampleFrequency,scp.RecordLength);
    dt = time(2)-time(1);
    fft_pts = 2^nextpow2(length(time))+1; fft_pts = 2^nextpow2(fft_pts)+1;
    % build frequency axis
    freq_step = 1/(fft_pts*(dt));
    freqfft = [0 : freq_step : ((freq_step * fft_pts) -freq_step)/2];
    
    j=1; %iteration counter
    
for i=fi:sf:fo
   
    % Set frequency:
    gen.Frequency = i; % 1 kHz

    % Start measurement:
    scp.start();

    % Start signal generation:
    gen.start();
    
    while ~scp.IsDataReady
        pause(1e-3) % 10 ms delay, to save CPU time.
    end
    
    
    % Get data:
    arData = scp.getData();

    % Get all channel data value ranges (which are compensated for probe gain/offset):
    clear darRangeMin;
    clear darRangeMax;
    
    %get the raw data of the oscilloscope
    rawdata1(j,:)=arData(:,1);
    rawdata2(j,:)=arData(:,2);
    
    %get the maximum value of the signal
    max1(j)=max(abs(arData(:,1))*2);
    max2(j)=max(abs(arData(:,2))*2);
    
    %get the average data of the signal
    avgdata1(j)=mean(arData(:,1));
    avgdata2(j)=mean(arData(:,2));

    rms1(j,:)=rms(arData(:,1));
    rms2(j,:)=rms(arData(:,2));
    
    %get an array of frequency
    freq(j)=i;
    
    %plot the signals as oscciloscope
    figure(1);
    title('Oscilloscope')
    
    %Chanel 1
    yyaxis left; 
    plot(time, (arData(:,1)));
    axis([0 5e-6 -2 2]);
    xlabel('Time [s]');
    ylabel('Amplitude in the chanel 1 [V]');
    
    %Chanel 2
    yyaxis right
    plot(time, (arData(:,2)));
    axis([0 5e-6 -2 2]);
    xlabel('Time [s]');
    ylabel('Amplitude in the chanel 2 [V]');
    legend(sprintf('Frequency value = %0.3f',i))
    
    
     % Getting Fourier transform chanel 1.
    t_FT1 = fft(arData(:,1));
    L1 = length(t_FT1);
    P2 = abs(t_FT1 / L1);
    P1 = P2(1 : L1/2 + 1);
    P1(2 : end - 1) = 2 * P1(2 : end - 1);
    t_FFT1 = P2/10;
    t_freq = freq(j) * (0 : (L1 / 2)) / L1;
    magFFT1(j)=max(t_FFT1);
    
    % Getting Fourier transform chanel 2.
    t_FT2 = fft(arData(:,2));
    L2 = length(t_FT2);
    P4 = abs(t_FT2 / L2);
    P3 = P4(1 : L2/2 + 1);
    P3(2 : end - 1) = 2 * P3(2 : end - 1);
    t_FFT2 = P4/10;
    t_freq = freq(j) * (0 : (L2 / 2)) / L2;
    magFFT2(j)=max(t_FFT2);
    
    j=j+1; %increment in the counter
end
   
    %Plot the results maximum value
    figure (2)
    title('RMS voltage')
    yyaxis left
   % plot(freq,(max1),'-','color',rand(1,3));
    plot(freq,(rms1));
    xlabel('Frequency [Hz]');
    ylabel('Amplitude in chanel 1  [V]');
    yyaxis right
   % plot(freq,(max2),'-','color',rand(1,3));
    plot(freq,(rms2));
    xlabel('Frequency [Hz]');
    ylabel('Amplitude in the chanel 2 [V]');
    hold on
    
    %Plot the results fourier transform value
%     figure(3)
%     title('Magnitude FFT')
%     yyaxis left
%     %plot(freq,(magFFT1),'-','color',rand(1,3));
%     plot(freq,(magFFT1));
%     xlabel('Frequency [Hz]');
%     ylabel('Magnitude of the FFT  [V]');
%     yyaxis right
%     %plot(freq,(magFFT2),'-','color',rand(1,3));
%    % plot(freq,(magFFT2));
%     xlabel('Frequency [Hz]');
%     ylabel('Magnitude of the FFT  [V]');
%     hold on
    
    
     % Stop generator:
    gen.stop();

    % Disable output:
    gen.OutputOn = false;

    % Close oscilloscope:
    clear scp;

    % Close generator:
    clear gen;
else
    error('No oscilloscope available with block measurement support or generator available in the same unit!');
end
    
    