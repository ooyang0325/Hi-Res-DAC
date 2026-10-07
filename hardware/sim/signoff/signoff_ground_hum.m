% signoff_ground_hum.m - MATLAB sign-off model: GND network, hum/whine budget, trace parasitics.
%
% Input : board.json (hardware/sim/board_dump.py on the committed board)
% Output: signoff_parasitics.csv, signoff_gnd_transfer.csv, signoff_hum_budget.txt/.png
%
% 1. Trace parasitics per net/layer (Hammerstad-Wheeler microstrip; inner layers as embedded
%    microstrip to the 0.109 mm neighbour for C (conservative) and 0.55 mm core for L).
% 2. Six-layer GND copper as a resistive grid (0.3 and 0.2 mm, convergence check) with vias.
% 3. Transfer resistances audio-reference -> jack sleeve for each ground current source.
% 4. 50/60 Hz magnetic pickup of the real series audio routes. Open-circuit EMF between two
%    nodes = sum over branches of EMF_branch * I_branch(unit current between the nodes)
%    (reciprocity). With uniform B along z, E = -dA/dt, A = B/2*(-y, x): the trace part is
%    w*Int A.dl along the routed path, the plane part w*Sum I_unit,b * A.dl_b.
% Assumptions: 1 oz outer / 0.5 oz inner Cu, JLC 6-layer (L1-L2 0.0994, L3-L4 0.1088, cores
% 0.55 mm), er 4.3, via barrel plating 20 um.

clear; fmt = @(x) sprintf('%.3g', x);
bf = getenv('BOARD'); if isempty(bf), bf = 'board.json'; end
d = jsondecode(fileread(bf));
trk = d.trk; if iscell(trk), trk = cellfun(@(s) rmfieldsafe(s), trk, 'UniformOutput', false); trk = [trk{:}]; end
fp = d.fp; if iscell(fp), fp = [fp{:}]; end
LAY = {'F.Cu', 'GND', 'PWR', 'SIG', 'GND5', 'B.Cu'};
RS = [0.49e-3 0.98e-3 0.98e-3 0.98e-3 0.98e-3 0.49e-3];         % ohm/sq
c0 = 299.792458; er = 4.3;                                        % mm/ns

%% 1. parasitics -------------------------------------------------------------------------------
nets = {'MCLK','N2_X201_OUT','N6_MCK_IN','BCLK','N2_BCLK_SRC','LRCLK','SDATA','DACL','DACLB', ...
        'N4_IVL_P','N4_LP_INN','N4_LP_OUT','LEG_LP','JACK_LP','N4_RN_OUT','LEG_RN','JACK_RN', ...
        'LEG_LN','JACK_LN','LEG_RP','JACK_RP','3V3D','5V_SYS','VPOS','VNEG'};
fid = fopen('signoff_parasitics.csv', 'w');
fprintf(fid, 'net,layer,length_mm,C_pF,L_nH,Z0_ohm,td_ps\n');
P = struct();
for k = 1:numel(nets)
    sel = trk(strcmp({trk.net}, nets{k}));
    tot = [0 0 0];
    for L = LAY([1 3 4 6])
        s = sel(strcmp({sel.l}, L{1}));
        if isempty(s), continue; end
        len = 0; C = 0; Lh = 0;
        for i = 1:numel(s)
            l = hypot(s(i).b(1) - s(i).a(1), s(i).b(2) - s(i).a(2));
            [z, ee] = mstrip(s(i).w, hC(L{1}), er);
            [zl, eel] = mstrip(s(i).w, hL(L{1}), er);
            len = len + l; C = C + l * sqrt(ee) / (c0 * z) * 1e3;   % pF
            Lh = Lh + l * zl * sqrt(eel) / c0;                      % nH
        end
        z = sqrt(Lh / (C * 1e-3)); td = sqrt(Lh * C * 1e-3) * 1e3;
        fprintf(fid, '%s,%s,%.2f,%.3f,%.3f,%.1f,%.1f\n', nets{k}, L{1}, len, C, Lh, z, td);
        tot = tot + [len C Lh];
    end
    P.(matlab.lang.makeValidName(nets{k})) = tot;
    fprintf(fid, '%s,ALL,%.2f,%.3f,%.3f,,\n', nets{k}, tot);
end
fclose(fid);

%% 2. GND network ------------------------------------------------------------------------------
pads = allpads(fp);
global VIAS_ %#ok<GVMIS>
VIAS_ = d.via; if iscell(VIAS_), VIAS_ = [VIAS_{:}]; end
H0 = 0.3; S = gndsolver(d, trk, pads, LAY, RS, H0);
S2 = gndsolver(d, trk, pads, LAY, RS, 0.2);

%% 3. transfer resistances ---------------------------------------------------------------------
scen = { ...
  'MCU+CPLD supply -> USB GND',   [padsof(pads,'U201'), padsof(pads,'U202')], padsof(pads,'J101'); ...
  'DAC U301 supply -> USB GND',   padsof(pads,'U301'), padsof(pads,'J101'); ...
  'LM27762 input -> USB GND',     padsof(pads,'U501'), padsof(pads,'J101'); ...
  'SE load return J702 -> U501',  padsof(pads,'J702'), padsof(pads,'U501'); ...
  'Ground loop J101 -> J702',     padsof(pads,'J101'), padsof(pads,'J702')};
probes = {'R404','2'; 'R408','2'; 'R412','2'; 'R416','2'; 'R432','2'; 'U301','EP'};
fid = fopen('signoff_gnd_transfer.csv', 'w');
fprintf(fid, 'scenario,probe,vs_J702_uohm_0p3,vs_J702_uohm_0p2,vs_J701_uohm_0p3,vs_J701_uohm_0p2\n');
T = zeros(size(scen,1), size(probes,1), 4);
for s = 1:size(scen,1)
    v3 = S.solve(scen{s,2}, scen{s,3}); v2 = S2.solve(scen{s,2}, scen{s,3});
    for p = 1:size(probes,1)
        pr = findpad(pads, probes{p,:});
        r = [v3(S.node(pr)) - v3(S.node(findpad(pads,'J702','1'))), v2(S2.node(pr)) - v2(S2.node(findpad(pads,'J702','1'))), ...
             v3(S.node(pr)) - v3(S.node(findpad(pads,'J701','1'))), v2(S2.node(pr)) - v2(S2.node(findpad(pads,'J701','1')))] * 1e6;
        T(s,p,:) = r;
        if ~strcmp(pr.net, 'GND'), continue; end      % F10: reference pads are on N4_GSENSE
        fprintf(fid, '%s,%s.%s,%.2f,%.2f,%.2f,%.2f\n', scen{s,1}, probes{p,:}, r);
    end
end
fclose(fid);

%% 4. hum / whine budget -----------------------------------------------------------------------
noise = 1.56e-6;                       % V, output noise floor (EMS report / calc package)
w = 2*pi*60;  B = [1e-6 10e-6];
% (a) effective magnetic loop areas of the real routes (mm^2)
seSE  = routepath(trk, pads, {'U401','9','N4_LP_OUT','R417','1'; 'R417','2','LEG_LP','K601','4'; 'K601','6','JACK_LP','J702','4'});
seSEr = routepath(trk, pads, {'U402','9','N4_RP_OUT','R419','1'; 'R419','2','LEG_RP','K603','4'; 'K603','6','JACK_RP','J702','3'});
balP  = routepath(trk, pads, {'U401','9','N4_LP_OUT','R417','1'; 'R417','2','LEG_LP','K601','4'; 'K601','6','JACK_LP','J701','7'});
balN  = routepath(trk, pads, {'U401','7','N4_LN_OUT','R418','1'; 'R418','2','LEG_LN','K602','4'; 'K602','6','JACK_LN','J701','6'});
Aeff = @(route, refpad, slv) S2.fluxA(route, refpad, slv);   % mm^2 = Phi/B
A_SE_L = Aeff(seSE,  findpad(pads,'R404','2'), findpad(pads,'J702','1'));
A_SE_R = Aeff(seSEr, findpad(pads,'R412','2'), findpad(pads,'J702','1'));
% balanced: loop = LP route out, (headphone), LN route back; amp side closed through R404->R408 plane path
balPR = routepath(trk, pads, {'U402','9','N4_RP_OUT','R419','1'; 'R419','2','LEG_RP','K603','4'; 'K603','6','JACK_RP','J701','4'});
balNR = routepath(trk, pads, {'U402','7','N4_RN_OUT','R420','1'; 'R420','2','LEG_RN','K604','4'; 'K604','6','JACK_RN','J701','2'});
balA = @(P, Nn, rp, rn) segA([rp.x rp.y], P(1,:)) + trapA(P) + segA(P(end,:), Nn(end,:)) - trapA(Nn) ...
         + segA(Nn(1,:), [rn.x rn.y]) + S2.planeA(rn, rp);
A_BAL  = balA(balP, balN, findpad(pads,'R404','2'), findpad(pads,'R408','2'));
A_BALR = balA(balPR, balNR, findpad(pads,'R412','2'), findpad(pads,'R416','2'));
if any(strcmp({pads.net}, 'N4_GSENSE'))      % F10: the two references join through the sense route
    balS = @(P, Nn, rp, rn, rt) segA([rp.x rp.y], P(1,:)) + trapA(P) + segA(P(end,:), Nn(end,:)) - trapA(Nn) ...
         + segA(Nn(1,:), [rn.x rn.y]) + trapA(rt);
    rp = findpad(pads,'R404','2'); rn = findpad(pads,'R408','2');
    A_BAL = balS(balP, balN, rp, rn, routepath(trk, pads, {'R408','2','N4_GSENSE','R404','2'}));
    rp = findpad(pads,'R412','2'); rn = findpad(pads,'R416','2');
    A_BALR = balS(balPR, balNR, rp, rn, routepath(trk, pads, {'R416','2','N4_GSENSE','R412','2'}));
end
% I/V outputs -> difference stage (OPA2210 U403/U404 -> R401/R403 ... ): a 60 Hz EMF between the
% P and N routes is a differential input of the difference stage and reaches its output x Gd.
% Loop = P route out, across the input resistors, N route back, across the OPA2210 package.
Gd = 2.00/1.30;                                              % R402/R401 (calc package v1.1)
ivA = @(u, rp, rn, np, nn) ivloopA(routepath(trk, pads, {u,'7',np,rp,'1'}), routepath(trk, pads, {u,'1',nn,rn,'1'}));
A_IV = struct('LP', ivA('U403','R401','R403','N4_IVL_P','N4_IVL_N'), 'LN', ivA('U403','R407','R405','N4_IVL_P','N4_IVL_N'), ...
              'RP', ivA('U404','R409','R411','N4_IVR_P','N4_IVR_N'), 'RN', ivA('U404','R415','R413','N4_IVR_P','N4_IVR_N'));
hum = @(A, k) w * B(k) * A * 1e-6;     % V at field level k
% (b) ground-current terms (V): R404 - sleeve transfer x current
Ivals = [20e-3, 10e-3];               % MCU+CPLD frame-rate p-p, DAC digital p-p (conservative)
rows = {
 'USB frame-rate MCU/CPLD current (20 mA p-p) - 3.5 mm', T(1,1,2)*1e-6*Ivals(1);
 'USB frame-rate MCU/CPLD current (20 mA p-p) - 4.4 mm bal', abs(T(1,1,4)-T(1,2,4))*1e-6*Ivals(1);
 'DAC digital current (10 mA p-p) - 3.5 mm',  T(2,1,2)*1e-6*Ivals(2);
 'DAC digital current (10 mA p-p) - 4.4 mm bal', abs(T(2,1,4)-T(2,2,4))*1e-6*Ivals(2);
 '60 Hz field 1 uT - 3.5 mm L',   hum(abs(A_SE_L),1);
 '60 Hz field 10 uT - 3.5 mm L',  hum(abs(A_SE_L),2);
 '60 Hz field 10 uT - 3.5 mm R',  hum(abs(A_SE_R),2);
 '60 Hz field 1 uT - 3.5 mm R',   hum(abs(A_SE_R),1);
 '60 Hz field 10 uT - 4.4 mm bal L', hum(abs(A_BAL),2);
 '60 Hz field 10 uT - 4.4 mm bal R', hum(abs(A_BALR),2);
 'USB 100/120 Hz ripple (EMS ems_budget.m)', 7.9e-9};
isF10 = any(strcmp({pads.net}, 'N4_GSENSE'));
if isF10
    % ECO F10: SE reference = J702 sleeve via N4_GSENSE. Ground currents reach the output only as
    % common mode of the difference stage (LTspice hp_cmrr.cir worst tolerance corner).
    acm = struct('f60', 10^(-56.44/20), 'f1k', 10^(-56.41/20), 'f8k', 10^(-54.88/20));
    gsP = routepath(trk, pads, {'R448','1','N4_GSENSE','R404','2'});
    gsR = routepath(trk, pads, {'R448','1','N4_GSENSE','R412','2'});
    sl = findpad(pads,'J702','1'); r448 = findpad(pads,'R448','2');
    loopF10 = @(route, gsroute, ref) segA([ref.x ref.y], route(1,:)) + trapA(route) + segA(route(end,:), [sl.x sl.y]) ...
        + segA([sl.x sl.y], [r448.x r448.y]) + segA([r448.x r448.y], gsroute(1,:)) + trapA(gsroute) + segA(gsroute(end,:), [ref.x ref.y]);
    A_SE_L = loopF10(seSE, gsP, findpad(pads,'R404','2')); A_SE_R = loopF10(seSEr, gsR, findpad(pads,'R412','2'));
    Tcm = @(s) max(abs(T(s,5,2)), abs(T(s,6,2)));    % VREF divider / DAC EP vs sleeve (I/V common mode)
    rows = {
     'F10: USB frame-rate MCU/CPLD current (20 mA p-p) - 3.5 mm', Tcm(1)*1e-6*Ivals(1)*acm.f8k;
     'F10: USB frame-rate MCU/CPLD current (20 mA p-p) - 4.4 mm bal', 2*Tcm(1)*1e-6*Ivals(1)*acm.f8k;
     'F10: DAC digital current (10 mA p-p) - 3.5 mm', Tcm(2)*1e-6*Ivals(2)*acm.f8k;
     'F10: DAC digital current (10 mA p-p) - 4.4 mm bal', 2*Tcm(2)*1e-6*Ivals(2)*acm.f8k;
     'F10: 60 Hz field 1 uT - 3.5 mm L', hum(abs(A_SE_L),1);
     'F10: 60 Hz field 10 uT - 3.5 mm L', hum(abs(A_SE_L),2);
     'F10: 60 Hz field 10 uT - 3.5 mm R', hum(abs(A_SE_R),2);
     'F10: 60 Hz field 1 uT - 3.5 mm R', hum(abs(A_SE_R),1);
     '60 Hz field 10 uT - 4.4 mm bal L', hum(abs(A_BAL),2);
     '60 Hz field 10 uT - 4.4 mm bal R', hum(abs(A_BALR),2);
     'USB 100/120 Hz ripple (EMS ems_budget.m)', 7.9e-9};
    rows = [rows(1:end-1,:); {
     'I/V pair x Gd + output loop, 10 uT - 3.5 mm L', hum(abs(A_SE_L) + Gd*abs(A_IV.LP), 2);
     'I/V pair x Gd + output loop, 10 uT - 3.5 mm R', hum(abs(A_SE_R) + Gd*abs(A_IV.RP), 2);
     'I/V pairs x Gd + output loop, 10 uT - 4.4 mm bal L', hum(abs(A_BAL) + Gd*(abs(A_IV.LP) + abs(A_IV.LN)), 2);
     'I/V pairs x Gd + output loop, 10 uT - 4.4 mm bal R', hum(abs(A_BALR) + Gd*(abs(A_IV.RP) + abs(A_IV.RN)), 2);
     }; rows(end,:)];
end
fid = fopen('signoff_hum_budget.txt', 'w');
fprintf(fid, 'DAC-HPA hum/whine sign-off budget (MATLAB %s)\n', version);
fprintf(fid, 'Output noise floor %.2f uV. Grid 0.3/0.2 mm convergence shown in signoff_gnd_transfer.csv\n\n', noise*1e6);
fprintf(fid, 'Board %s (ECO F10 ground sense: %d)\nEffective 60 Hz loop areas (route + %s): SE-L %.1f, SE-R %.1f, BAL-L %.1f, BAL-R %.1f mm2\n', bf, isF10, ternary(isF10, 'N4_GSENSE sense route', 'resistive plane return'), A_SE_L, A_SE_R, A_BAL, A_BALR);
fprintf(fid, 'I/V output pair loops (U403/U404 -> difference-stage inputs, gain %.2f): LP %.1f, LN %.1f, RP %.1f, RN %.1f mm2\n\n', Gd, A_IV.LP, A_IV.LN, A_IV.RP, A_IV.RN);
% audibility: ISO 226:2003 threshold in quiet and masking by the amplifier's own noise in one ERB
fq = [20 25 31.5 40 50 63 80 100 125 160 200 250 315 400 500 630 800 1000 1250 1600 2000 2500 3150 4000 5000 6300 8000 10000 12500];
tq = [78.5 68.7 59.5 51.1 44.0 37.5 31.5 26.5 22.1 17.9 14.4 11.4 8.6 6.2 4.4 3.0 2.2 2.4 3.5 1.7 -1.3 -4.2 -6.0 -5.4 -1.5 6.0 12.6 13.9 12.3];
Sv = 135;                                  % dB SPL/V: ultra-sensitive IEM (115 dB SPL/mW at 16 ohm)
en = [15.7e-9 25.4e-9];                    % V/rtHz at 1 kHz, SE leg / balanced (calc package v1.1)
freq = 1000*ones(1, size(rows,1)); freq(contains(rows(:,1), 'uT')) = 60; freq(contains(rows(:,1), 'ripple')) = 120;
isbal = contains(rows(:,1), 'bal');
fprintf(fid, '%-46s %9s %8s %9s %9s %8s\n', 'term', 'uV', 'dB/noise', 'dBSPL@IEM', 'audib.lim', 'margin');
vals = zeros(size(rows,1),1); marg = vals;
for i = 1:size(rows,1)
    vals(i) = rows{i,2}; f0 = freq(i);
    erb = 24.7 * (4.37 * f0 / 1000 + 1);
    masked = 20*log10(en(1 + isbal(i)) * sqrt(erb)) - 4 + Sv;      % tone at -4 dB re ERB noise is detectable
    lim = max(interp1(log(fq), tq, log(f0)), masked);
    spl = Sv + 20*log10(vals(i)); marg(i) = lim - spl;
    fprintf(fid, '%-46s %9.4f %8.1f %9.1f %9.1f %8.1f\n', rows{i,1}, vals(i)*1e6, 20*log10(vals(i)/noise), spl, lim, marg(i));
end
fprintf(fid, '\nSign-off criterion: every term >= 6 dB below audibility (threshold in quiet or self-noise masking) on a 135 dB SPL/V IEM.\n');
fprintf(fid, 'Smallest margin %.1f dB -> %s\n', min(marg), ternary(min(marg) >= 6, 'PASS', 'REVIEW'));
worst = max(vals);
fprintf(fid, '\nLine-out ground loop (J101->J702, informational): %.1f uohm -> %.2f uV per 10 mA loop current\n', T(5,1,2), T(5,1,2)*1e-6*10e-3*1e6);
fprintf(fid, '\nTrace parasitics used by the LTspice decks: signoff_parasitics.csv\n');
fclose(fid);
type('signoff_hum_budget.txt');

f = figure('Visible','off'); barh(20*log10(vals/noise)); hold on; xline(0,'r-','noise floor'); xline(-6,'k--');
set(gca,'YTick',1:numel(vals),'YTickLabel',rows(:,1),'TickLabelInterpreter','none','FontSize',7);
xlabel('dB re 1.56 \muV output noise'); title('DAC-HPA hum / whine sign-off budget'); grid on;
exportgraphics(f, 'signoff_hum_budget.png', 'Resolution', 150);

%% ---------------------------------------------------------------------------------------------
function s = rmfieldsafe(s), if isfield(s,'arc'), s = rmfield(s,'arc'); end, end
function h = hC(L), if any(strcmp(L,{'F.Cu','B.Cu'})), h = 0.0994; else, h = 0.1088; end, end
function h = hL(L), if any(strcmp(L,{'F.Cu','B.Cu'})), h = 0.0994; else, h = 0.55; end, end
function [z, ee] = mstrip(w, h, er)
    u = w / h; ee = (er+1)/2 + (er-1)/2 / sqrt(1 + 12/u);
    if u <= 1, z = 60/sqrt(ee) * log(8/u + u/4);
    else, z = 120*pi / (sqrt(ee) * (u + 1.393 + 0.667*log(u + 1.444))); end
end
function out = ternary(c, a, b), if c, out = a; else, out = b; end, end
function A = ivloopA(P, N)
% Signed area (mm^2) of P out, P(end) -> N(end), N back, N(1) -> P(1); A.dl with B = 1 along z.
A = trapA(P) + segA(P(end,:), N(end,:)) - trapA(N) + segA(N(1,:), P(1,:));
end
function pads = allpads(fp)
    pads = struct('ref',{},'n',{},'net',{},'x',{},'y',{},'sx',{},'sy',{},'th',{},'lay',{});
    for i = 1:numel(fp)
        pp = fp(i).pads; if iscell(pp), pp = [pp{:}]; end
        for j = 1:numel(pp)
            lay = pp(j).lay; if ischar(lay), lay = {lay}; end
            pads(end+1) = struct('ref',fp(i).ref,'n',pp(j).n,'net',pp(j).net,'x',pp(j).x,'y',pp(j).y, ...
                'sx',pp(j).sx,'sy',pp(j).sy,'th',pp(j).th,'lay',{lay}); %#ok<AGROW>
        end
    end
end
function p = findpad(pads, ref, n)
    p = pads(strcmp({pads.ref}, ref) & strcmp({pads.n}, n)); p = p(1);
end
function p = padsof(pads, ref)
    p = pads(strcmp({pads.ref}, ref) & strcmp({pads.net}, 'GND'));
end
function A = trapA(route)          % integral of (x dy - y dx)/2 along the route polyline (mm^2)
    A = sum((route(1:end-1,1).*route(2:end,2) - route(2:end,1).*route(1:end-1,2)) / 2);
end
function A = segA(p, q), A = (p(1)*q(2) - q(1)*p(2)) / 2; end
function route = routepath(trk, pads, legs)
    % legs: rows {refA, padA, net, refB, padB}; shortest routed path per leg (netgraph: T-junctions,
    % vias, pads), straight across the parts between legs
    global VIAS_ %#ok<GVMIS>
    route = [];
    for k = 1:size(legs,1)
        pa = findpad(pads, legs{k,1}, legs{k,2}); pb = findpad(pads, legs{k,4}, legs{k,5});
        [G, U, ~, ia, ib] = netgraph(trk, pads, VIAS_, legs{k,3}, pa, pb);
        pth = shortestpath(G, ia, ib);
        if isempty(pth), error('no routed path for %s', legs{k,3}); end
        route = [route; pa.x pa.y; U(pth,:); pb.x pb.y]; %#ok<AGROW>
    end
end
