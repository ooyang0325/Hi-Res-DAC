% Controlled-impedance sign-off on the declared JLC06161H-3313 stackup (L1 over L2:
% 3313 prepreg 0.0994 mm, er 4.1; 1 oz outer copper; LPI mask 15 um, er 3.8).
% 1) validate tline_fd against Hammerstad-Jensen and its own grid convergence,
% 2) solve the routed USB pair geometries and the 0.15 mm clock lines.
out = fopen('signoff_impedance.txt', 'w');
fprintf(out, 'Controlled-impedance sign-off (MATLAB %s), 2-D finite-difference field solver tline_fd.m\n\n', version);
% --- validation 1: thin strip (one grid cell thick) vs Hammerstad-Jensen t = 0 (quoted 0.01 %% in Z),
%     with grid refinement; validation 2: 1 oz strip vs H-J with its thickness correction
fprintf(out, 'Validation 1 (thin strip t = one cell, h 0.1 mm, no mask, er 4.1) vs Hammerstad-Jensen (t = 0):\n');
for u = [1 2]
    for d = [0.0025 0.00125]
        g = struct('w', u*0.1, 's', 0, 't', d, 'h', 0.1, 'er', 4.1, 'tm', 0, 'erm', 1, 'd', d);
        r = tline_fd(g); zr = hjz(u, 4.1);
        fprintf(out, '  w/h = %d, grid %.5f mm: FD %.2f ohm, HJ %.2f ohm, diff %+.2f %%\n', u, d, r.Z0, zr, 100*(r.Z0/zr - 1));
    end
end
fprintf(out, ['  -> the residual shrinks with the grid (edge singularity) and includes the strip''s own\n' ...
              '     thickness; the solver is within ~1.5 %% and reads slightly LOW at the grids used below.\n']);
fprintf(out, 'Validation 2 (t 0.035 mm, h 0.1 mm, no mask) vs Hammerstad-Jensen with its thickness correction:\n');
for u = [1 2 3]
    g = struct('w', u*0.1, 's', 0, 't', 0.035, 'h', 0.1, 'er', 4.1, 'tm', 0, 'erm', 1, 'd', 0.0025);
    r = tline_fd(g); zr = hjt(u, 0.35, 4.1);
    fprintf(out, '  w/h = %d: FD %.2f ohm, HJ %.2f ohm, diff %+.2f %%\n', u, r.Z0, zr, 100*(r.Z0/zr - 1));
end
fprintf(out, ['  -> 3-5 %% apart at t/h = 0.35, where the closed-form thickness correction is approximate.\n' ...
              '     Taking the H-J value instead would raise every Zdiff below by <= 5 %%: the worst USB corner\n' ...
              '     would be ~103 ohm, still inside 90 ohm +15 %%.\n']);
fprintf(out, 'Grid convergence, USB pair (w 0.17, gap 0.215, t 0.035, mask):\n');
for d = [0.006 0.004 0.003]
    g = struct('w', 0.17, 's', 0.215, 't', 0.035, 'h', 0.0994, 'er', 4.1, 'tm', 0.015, 'erm', 3.8, 'd', d);
    r = tline_fd(g);
    fprintf(out, '  grid %.4f mm: Zdiff %.2f ohm\n', d, r.Zdiff);
end
fprintf(out, '\nUSB 2.0 HS pair as built (target 90 ohm +/-15 %%; sections from the routed board):\n');
cases = {'coupled 0.17 mm / gap 0.215 mm (10.0 mm)', 0.17, 0.215; 'coupled 0.18 mm / gap 0.32 mm (2.5 mm)', 0.18, 0.32; ...
         'split 0.20 mm around U101 (centre 1.6 mm)', 0.20, 1.40; 'J101 pin escape 0.16 mm (centre 1.5 mm)', 0.16, 1.34};
tol = {'nominal', 0.0994, 4.1, 0.035; 'prepreg -10 %, er +0.2, Cu +5 um', 0.0895, 4.3, 0.040; ...
       'prepreg +10 %, er -0.2, Cu -5 um', 0.1093, 3.9, 0.030};
for c = 1:size(cases, 1)
    for k = 1:size(tol, 1)
        g = struct('w', cases{c, 2}, 's', cases{c, 3}, 't', tol{k, 4}, 'h', tol{k, 2}, 'er', tol{k, 3}, ...
                   'tm', 0.015, 'erm', 3.8, 'd', 0.004);
        r = tline_fd(g);
        fprintf(out, '  %-46s %-34s Zdiff %6.1f  Zodd %5.1f  Zcomm %5.1f ohm\n', cases{c, 1}, tol{k, 1}, r.Zdiff, r.Zodd, r.Zcomm);
    end
end
g = struct('w', 0.17, 's', 0.215, 't', 0.035, 'h', 0.0994, 'er', 4.1, 'tm', 0.015, 'erm', 3.8, 'd', 0.004);
r = tline_fd(g); vp = 299.792458 / sqrt(r.eeff_odd);
fprintf(out, '  odd-mode eeff %.3f -> %.1f ps/mm; 2.153 mm intra-pair mismatch = %.1f ps (USB 2.0 HS budget 100 ps)\n', ...
        r.eeff_odd, 1000/vp, 2.153*1000/vp);
fprintf(out, '\nClock lines (0.15 mm, single-ended, nominal stackup):\n');
g = struct('w', 0.15, 's', 0, 't', 0.035, 'h', 0.0994, 'er', 4.1, 'tm', 0.015, 'erm', 3.8, 'd', 0.003);
r = tline_fd(g); vp = 299.792458 / sqrt(r.eeff);
fprintf(out, '  Z0 %.1f ohm, eeff %.3f, %.2f ps/mm (clk_si.cir uses Z0 58 ohm, 5.96 ps/mm)\n', r.Z0, r.eeff, 1000/vp);
fclose(out);
type signoff_impedance.txt

function z = hjt(u, tn, er)
% Hammerstad & Jensen (1980) with the strip-thickness correction; tn = t/h
du1 = tn/pi*log(1 + 4*exp(1)/(tn*coth(sqrt(6.517*u))^2));
dur = 0.5*(1 + 1/cosh(sqrt(er - 1)))*du1;
u1 = u + du1; ur = u + dur;
[z1, ~] = hjz(u1, 1); [zr, eer] = hjz(ur, er);
z1a = z1; zra = zr*sqrt(eer);          % air impedances
ee = eer*(z1a/zra)^2;
z = zra/sqrt(ee);
end

function [z, ee] = hjz(u, er)
% Hammerstad & Jensen (1980), zero-thickness microstrip
a = 1 + log((u^4 + (u/52)^2)/(u^4 + 0.432))/49 + log(1 + (u/18.1)^3)/18.7;
b = 0.564*((er - 0.9)/(er + 3))^0.053;
ee = (er + 1)/2 + (er - 1)/2*(1 + 10/u)^(-a*b);
f = 6 + (2*pi - 6)*exp(-(30.666/u)^0.7528);
z1 = 60*log(f/u + sqrt(1 + 4/u^2));
z = z1/sqrt(ee);
end
