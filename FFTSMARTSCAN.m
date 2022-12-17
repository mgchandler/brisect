import LibTiePie.Const.*
import LibTiePie.Enum.*
if ~exist('LibTiePie', 'var')
    % Open LibTiePie:
    LibTiePie = LibTiePie.Library;
end
% Search for devices:
LibTiePie.DeviceList.update();
% Try to open an oscilloscope with block measurement support and a generator in the same device:
clear scp; clear gen;
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
% Oscilloscope settings:
    scp.MeasureMode = MM.BLOCK;% Set measure mode:
    scp.SampleFrequency = 1e10; % 1 MHz % Maximum sample 1e9% Set sample frequency:   
    scp.RecordLength =1e6; % length array % Set record length:
    scp.PreSampleRatio = 0; % 0 %% Set pre sample ratio:
    scp.Resolution = 12;          % Scope bit depth. Can be 8, 12, 14, 16.
    sample= scp.SampleFrequency;
% For all channels:
    for ch = scp.Channels(1)
        % Enable channel to measure it:
        ch.Enabled = true;
        % Set range:
        ch.Range =8; % 8 V
        % Set coupling
        ch.Coupling = CK.ACV; % DC Volt
        % Release reference:
        clear ch;
    end
    % For all channels:
    for ch = scp.Channels(2)
         % Enable channel to measure it:
        ch.Enabled = false;
        % Set range:
        ch.Range =14; % 8 V
        % Set coupling
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

   % gen.SignalType = ST.SINE;

   % gen.Frequency = 500e3; % 500 kHz

     figure(123)
    %set(gcf, 'Position', [100 100 1000 600]);
    a1 = subplot(2,2,1); 
    h1a = plot(NaN, NaN); ylabel('V_{1}, [V]'); hold on; 
    % yyaxis left; h1c = plot(NaN, NaN);
    %xlim([0 100./scp.SampleFrequency]./1e-6); xlabel('Time, [\mu s]');
    title('Waveform');
      a2 = subplot(2,2,2); h2a = plot(NaN, NaN); hold on; h2b = plot(NaN, NaN);
    xlabel('Frequency, [MHz]'); ylabel('Magnitude, [dim.]');
    title('Spectrum')
    
    a3 = subplot(2,2,3);
    h3a = plot(NaN, NaN); 
    ylabel('Magnitude V');
    title('Waveform from HS5')
    
    a4 = subplot(2,2,4); 
    h4a = plot(NaN, NaN,'*');
    xlabel('Frequency, [MHz]'); ylabel('Magnitude, [dim.]');
    title('Spectrum from HS5')
  %  hold on;

 gen.SignalType = ST.ARBITRARY;
   


 Fs = scp.SampleFrequency;            % Sampling frequency                    
T = 1/Fs;             % Sampling period       
L = 1e6;             % Length of signal
t = (0:L-1)*T;        % Time vector

%S = 0.7*sin(2*pi*2e6*t) + sin(2*pi*1.5e6*t);
S = .1*sin(2*pi*11e6*t) +.1*sin(2*pi*12e6*t)+.1*sin(2*pi*13e6*t);
%S=2*sin(2*pi*1e6*t);

amp=max(S);
gen.Amplitude = amp; % 2 V
data=S;
gen.setData(data);
   % Set frequency:
   gen.Frequency = 1./max(t); %1e3; % 1 kHz
    
    % Enable output:
    gen.OutputOn = true;
  
    
    % Set amplitude:
    gen.Amplitude = amp; % 2 V

    % Set offset:
    gen.Offset = 0; % 0 V



Y = fft(S);
P2 = abs(Y/L);
P1 = P2(1:L/2+1);
P1(2:end-1) = 2*P1(2:end-1);
f = Fs*(0:(L/2))/L;
cont=1;
var=[];
    while(1)
        scp.start();

    % Start signal generation:
    gen.start();
    
        
    while ~scp.IsDataReady
        pause(1e-3) % 10 ms delay, to save CPU time.
    end
    arData = scp.getData();

    % Get all channel data value ranges (which are compensated for probe gain/offset):
    clear darRangeMin;
    clear darRangeMax;

   
    %get the raw data of the oscilloscope
    rawdata1(1,:)=arData(:,1);
    rawdata2(1,:)=arData(:,2);
    
    rmsvalue(1,:)=rms(arData(:,1));
    rms2(1,:)=rms(arData(:,2));

         %frequency=2e6;

Fs = scp.SampleFrequency;            % Sampling frequency                    
T = 1/Fs;             % Sampling period       
L = scp.RecordLength;             % Length of signal
t1 = (0:L-1)*T;        % Time vector

S1 = rawdata1;

Y = fft(S1);
P22 = abs(Y/L);
P11 = P22(1:L/2+1);
P11(2:end-1) = 2*P11(2:end-1);
f1 = Fs*(0:(L/2))/L;

  


     axes(a1); 
     set(h1a, 'XData', 1000*t(1:100000), 'YData', S(1:100000));
     xlim([0 10e-3])
     ylim([-amp*1.2 amp*1.2])

    axes(a2); 
    set(h2a, 'XData', f, 'YData', P1);
    xlim([10e6 14e6])
    ylim([0 .1])

     axes(a3); 
     set(h3a, 'XData', 1000*t1(1:100000), 'YData', S1(1:100000));
     xlim([0 10e-3])
  ylim([-10 10])
var(cont)=rms(S1);
xdata(cont)=cont;

dd=findpeaks(P11,'MinPeakProminence',.05);
magf1(cont)=dd(1);
magf2(cont)=dd(2);
magf3(cont)=dd(3);
      axes(a4);
      %axes('NextPlot','add')
%       %set(h4a, 'XData', f1, 'YData', P11);
%           xlim([0 2e6])
%            ylim([0 amp*1.2])
    set(h4a, 'XData', xdata, 'YData', magf1); 
    xlim([0 cont+10])
     ylim([0 1])
    
   
     %drawnow;

     cont=cont+1;
    end

         % Stop generator:
    gen.stop();

    % Disable output:
    gen.OutputOn = false;

    % Close oscilloscope:
   clear scp;

    % Close generator:
   clear gen;