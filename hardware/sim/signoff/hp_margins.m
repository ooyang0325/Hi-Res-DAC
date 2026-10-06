% loop-gain margins of the OPA1622 leg decks (lt/hp_loop*.raw)
cases = {'relay off, unplugged','relay on, unplugged','16 ohm + 1.2 m cable','32 ohm + 1.2 m cable', ...
         '300 ohm + 3 m cable','300 ohm + 2 nF','16 ohm resistive'};
fid = fopen('signoff_hp_stability.txt', 'w');
fprintf(fid, 'OPA1622 leg loop gain (TI PSpice SBOM958D, LTspice 26.0.2), extracted layout parasitics\n');
for f = {'hp_loop', 'hp_loop_eco', 'hp_loop_f10', 'hp_loop_eco_f10'}
    [n, D, ns] = ltraw(fullfile('lt', [f{1} '.raw']));
    im = find(strcmpi(n, 'V(inm)')); ifb = find(strcmpi(n, 'V(nfb)'));
    fprintf(fid, '\n%s (%s)\n%-24s %10s %8s %8s %10s\n', f{1}, [ternary(contains(f{1},'eco'),'R417 ferrite + 220 pF','as built, R417 0 ohm') ternary(contains(f{1},'f10'),', ECO F10 sense return','')], 'case', 'fc MHz', 'PM deg', 'GM dB', 'f180 MHz');
    for s = 1:ns
        fr = real(D{s}(:,1)); T = -D{s}(:,ifb) ./ D{s}(:,im);
        mag = 20*log10(abs(T)); ph = unwrap(angle(T)) * 180/pi;
        ph = ph - 360 * round(ph(1) / 360);                 % LF phase ~ 0 deg
        k = find(mag(1:end-1) > 0 & mag(2:end) <= 0, 1);
        fc = interp1(mag(k:k+1), fr(k:k+1), 0); pm = 180 + interp1(fr(k:k+1), ph(k:k+1), fc);
        j = find(ph(1:end-1) > -180 & ph(2:end) <= -180, 1);
        if isempty(j), gm = Inf; f180 = NaN; else
            f180 = interp1(ph(j:j+1), fr(j:j+1), -180); gm = -interp1(fr(j:j+1), mag(j:j+1), f180); end
        fprintf(fid, '%-24s %10.2f %8.1f %8.1f %10.1f\n', cases{s}, fc/1e6, pm, gm, f180/1e6);
        R.(f{1})(s,:) = [fc pm gm];
    end
end
pmmin = min(cellfun(@(k) min(R.(k)(:,2)), fieldnames(R))); gmmin = min(cellfun(@(k) min(R.(k)(:,3)), fieldnames(R)));
fprintf(fid, '\nCriterion PM >= 45 deg, GM >= 6 dB in every case: min PM %.1f deg, min GM %.1f dB -> %s\n', pmmin, gmmin, ternary(pmmin >= 45 && gmmin >= 6, 'PASS', 'REVIEW'));
fclose(fid); type('signoff_hp_stability.txt');
function o = ternary(c, a, b), if c, o = a; else, o = b; end, end
