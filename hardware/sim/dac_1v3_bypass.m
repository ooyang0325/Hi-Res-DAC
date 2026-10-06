% ES9018K2M 1V3 passive decoupling sensitivity; assumptions match the
% companion LTspice deck. This is a layout comparison, not board extraction.
% Run from the repository root:
% matlab -batch "run('hardware/sim/dac_1v3_bypass.m')"

freq_hz = logspace(5, log10(80e6), 4001).';
omega = 2*pi*freq_hz;
branches = [100e-9, 0.05, 2e-9; 1e-6, 0.05, 5e-9; ...
            2.2e-6, 0.06, 20e-9];
locations = {"local 5 nH", "remote 20 nH"};
results = zeros(numel(freq_hz), 2);
sample_hz = [100e3, 1e6, 10e6, 80e6];
sample_z = zeros(numel(sample_hz), 2);
for case_index = 1:2
    branch_set = branches;
    if case_index == 2
        branch_set(2,3) = 20e-9;
    end
    admittance = complex(zeros(size(omega)));
    for row = 1:size(branch_set,1)
        c = branch_set(row,1);
        esr = branch_set(row,2);
        l = branch_set(row,3);
        admittance = admittance + 1./(esr + 1i*omega*l + 1./(1i*omega*c));
    end
    results(:,case_index) = abs(1./admittance);
    for point = 1:numel(sample_hz)
        w = 2*pi*sample_hz(point);
        z = branch_set(:,2) + 1i*w*branch_set(:,3) + ...
            1./(1i*w*branch_set(:,1));
        sample_z(point,case_index) = abs(1/sum(1./z));
    end
end

for case_index = 1:2
    [maximum_z, position] = max(results(:,case_index));
    fprintf('%s: max %.6f ohm at %.0f Hz (100 kHz to 80 MHz)\n', ...
        locations{case_index}, maximum_z, freq_hz(position));
end
for point = 1:numel(sample_hz)
    fprintf('%.0f Hz: local %.6f ohm, remote %.6f ohm\n', ...
        sample_hz(point), sample_z(point,1), sample_z(point,2));
end

this_dir = fileparts(mfilename('fullpath'));
table_out = table(freq_hz, results(:,1), results(:,2), ...
    'VariableNames', {'frequency_hz','local_5nH_ohm','remote_20nH_ohm'});
writetable(table_out, fullfile(this_dir, 'dac_1v3_bypass_sweep.csv'));
figure('Visible','off', 'Color','white', 'Position',[100 100 900 520]);
loglog(freq_hz, results(:,1), 'LineWidth', 1.6); hold on;
loglog(freq_hz, results(:,2), 'LineWidth', 1.6);
grid on;
xlabel('Frequency (Hz)'); ylabel('|Z_{1V3}| (ohm)');
title('DAC 1V3 bypass sensitivity to C312 loop inductance');
legend(locations, 'Location','best');
exportgraphics(gcf, fullfile(this_dir, 'dac_1v3_bypass_sweep.png'), 'Resolution', 160);
close(gcf);
