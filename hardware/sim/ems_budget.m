% ems_budget.m -- DAC-HPA home-environment EMS budget (review model, not a test result)
%
% Inputs
%   ems_headphone_rf.raw  LTspice ASCII AC sweep of ems_headphone_rf.cir (4 steps:
%                         FB=0/1 x CL=0/100p), V(inn) = RF at the OPA1622 inverting
%                         input per 1 V of cable common-mode EMF (150 ohm source).
% Outputs (next to this file)
%   ems_rf_demod.png / .csv   demodulated audio-band error at the headphone output
%   ems_budget_summary.txt    tabulated results used in EMS_VERIFICATION_2026-09-30.md
%
% Models and sources
%   * Demodulation: TI EMIRR definition, dVos = Vrf_pk^2 / 100 mV * 10^(-EMIRR/20).
%     EMIRR IN+ curve digitised from the OPA2210 datasheet (SBOS924H Fig. 6-39, lower
%     envelope, resonance spikes ignored). OPA1622 (SBOS727B) publishes no EMIRR, so
%     the OPA2210 curve and a 10 dB-worse case are both evaluated.
%   * Cable pickup: common-mode EMF = sqrt(2) * E * h_eff, h_eff = min(lambda/pi, 0.6 m)
%     (half-wave-dipole effective length, capped for a 1.2 m headphone cable).
%   * Output error = dVos * noise gain (1 + 2.00k/680) of the OPA1622 difference stage.
%   * GSM/TDD burst (217 Hz, duty 1/8) fundamental = (2/pi) sin(pi/8) of the envelope.
%   * Reference: OPA1622 stage output noise 2.8 nV/rtHz * 3.94 * sqrt(20 kHz) = 1.56 uV rms.

here = fileparts(mfilename('fullpath'));
raw = fullfile(here, 'ems_headphone_rf.raw');
[f, H] = read_ltspice_ascii(raw, 'V(inn)');          % f: Nx1, H: N x steps (complex)
labels = {'as built (R417 = 0 \Omega)', 'bead in R417', '100 pF at LEG', 'bead + 100 pF'};

emirr_f  = [10e6 20e6 40e6 100e6 200e6 400e6 600e6 800e6 1.1e9 1.4e9 1.8e9 2.4e9 3.6e9 5e9 6e9];
emirr_db = [42   38   37   36    39    42    45    47    52    47    70    77    100   95  90];
EMIRR = interp1(log10(emirr_f), emirr_db, log10(f), 'linear', 'extrap');

c = 299792458;
heff = min(c ./ f / pi, 0.6);
NG = 1 + 2000/680;
noise_out = 2.8e-9 * NG * sqrt(20e3);
gsm = 2/pi * sin(pi/8);
fields = [3 10 30];                                     % V/m: IEC 61000-4-3 residential, phone ~1 m, ~0.3 m
cmdm_db = -20; % cable common-mode -> tip-to-GND conversion; -20 dB typical, 0 dB = worst case (rerun to compare)

fid = fopen(fullfile(here, 'ems_budget_summary.txt'), 'w');
fprintf(fid, 'Headphone-output RF demodulation (output-referred, OPA2210 EMIRR proxy / proxy-10 dB)\n');
fprintf(fid, 'noise reference %.2f uV rms (20 kHz); CM->DM conversion %d dB; square law invalid above ~0.1 V RF\n', noise_out * 1e6, cmdm_db);
bands = {[30e6 80e6], [88e6 108e6], [150e6 300e6], [380e6 470e6], [790e6 960e6], [1.71e9 1.99e9], [2.4e9 2.5e9], [5.15e9 5.85e9]};
bname = {'VHF 30-80 MHz', 'FM broadcast', 'VHF 150-300 MHz', 'TETRA/433 ISM/DVB-T', 'LTE800/GSM900', 'GSM1800/DECT', 'Wi-Fi 2.4', 'Wi-Fi 5'};
csv = f;
figure('Visible', 'off', 'Position', [0 0 900 560]);
cols = lines(4);
for s = 1:size(H, 2)
    for k = 1:numel(fields)
        vpk = sqrt(2) * fields(k) .* heff .* abs(H(:, s)) * 10^(cmdm_db / 20);
        for worse = [0 10]
            dv = vpk.^2 / 0.1 .* 10.^(-(EMIRR - worse) / 20) * NG;
            if k == 1 && worse == 0
                csv = [csv, dv]; %#ok<AGROW>
                semilogx(f, 20*log10(dv * gsm + eps), 'Color', cols(s, :), 'LineWidth', 1.4); hold on;
            end
            for b = 1:numel(bands)
                m = f >= bands{b}(1) & f <= bands{b}(2);
                fprintf(fid, '%-28s E=%2d V/m %-26s EMIRR-%-2d  worst %8.3g uV  (%+6.1f dB re noise)\n', ...
                    labels{s}, fields(k), bname{b}, worse, max(dv(m)) * gsm * 1e6, ...
                    20*log10(max(dv(m)) * gsm / noise_out));
            end
        end
    end
end
yline(20*log10(noise_out), 'k--', 'output noise 1.56 \muV');
grid on; xlabel('RF carrier frequency (Hz)'); ylabel('217 Hz buzz at headphone output (dBV)');
title({'Demodulated 217 Hz buzz, E = 3 V/m (IEC 61000-4-3 residential), 1.2 m cable, CM\rightarrowDM -20 dB', 'review model: square law, OPA2210 EMIRR proxy for OPA1622'});
legend([labels, {'noise'}], 'Location', 'southwest'); xlim([1e7 6e9]);
exportgraphics(gcf, fullfile(here, 'ems_rf_demod.png'), 'Resolution', 130);
writematrix(csv, fullfile(here, 'ems_rf_demod.csv'));

% Conducted 100/120 Hz ripple from USB VBUS (50 mV p-p assumed poor charger/host)
vr = 0.05 / 2;                                                   % peak
opa1622_psrr = 140; lm_out_neg = 52; lm_out_pos = 65;            % dB at 100 Hz (datasheet curves)
lp5907 = 90; cm_tol = 0.01;                                      % LP5907 at 100 Hz; 1 % resistor match
rail = vr * 10^(-min(lm_out_neg, lm_out_pos) / 20);
hum_rail = rail * 10^(-opa1622_psrr / 20) * NG;
vref = vr * 10^(-lp5907 / 20) * 0.5;                             % VREF = 3V3A / 2
hum_vref = vref * 2 * cm_tol;                                    % common mode -> differential
fprintf(fid, '\nUSB 100 Hz ripple 50 mV p-p -> ±rail %.2f uV pk -> output %.3g nV; via 3V3A/VREF %.3g nV\n', ...
    rail * 1e6, hum_rail * 1e9, hum_vref * 1e9);

% Magnetic 50/60 Hz pickup: loop areas from audit_ems_layout.py if present
audit = fullfile(here, '..', 'INTEGRATED_AUDIO_EMS_AUDIT.json');
if isfile(audit)
    j = jsondecode(fileread(audit));
    loops = j.hum.largest_loops_mm2;
    fprintf(fid, '\nMagnetic pickup (EMF = 2 pi f B A), 60 Hz:\n');
    for i = 1:size(loops, 1)
        a = str2double(string(loops{i}{2}));
        fprintf(fid, '  %-12s %7.2f mm^2   1 uT %6.2f nV   10 uT %6.1f nV\n', string(loops{i}{1}), a, ...
            2*pi*60*1e-6*a*1e-6*1e9, 2*pi*60*10e-6*a*1e-6*1e9);
    end
end
fclose(fid);
type(fullfile(here, 'ems_budget_summary.txt'));

function [f, V] = read_ltspice_ascii(path, name)
% Parse an LTspice ASCII .raw (complex AC, stepped) and return one variable per step.
txt = fileread(path);
nv = str2double(regexp(txt, 'No\. Variables:\s*(\d+)', 'tokens', 'once'));
names = regexp(txt, '\t\d+\t(\S+)\t\S+', 'tokens');
names = cellfun(@(c) c{1}, names, 'UniformOutput', false);
col = find(strcmp(names, name)) - 1;
body = txt(strfind(txt, 'Values:') + 7:end);
nums = sscanf(strrep(body, ',', ' '), '%f');
per = 1 + 2 * nv;                         % point index + nv complex pairs (frequency included)
nums = nums(1:floor(numel(nums) / per) * per);
M = reshape(nums, per, []).';
freq = M(:, 2);
val = complex(M(:, 2 + 2*col), M(:, 3 + 2*col));
starts = [1; find(diff(freq) < 0) + 1];
n = min(diff([starts; numel(freq) + 1]));
f = freq(1:n);
V = zeros(n, numel(starts));
for s = 1:numel(starts)
    V(:, s) = val(starts(s):starts(s) + n - 1);
end
end
