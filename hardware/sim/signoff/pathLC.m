function [L, R, len, nvia] = pathLC(trk, pads, vias, refA, pA, net, refB, pB)
% PATHLC  Series inductance (nH) and resistance (ohm) of the routed path between two pads of one net.
% Segments: microstrip/embedded L' (Hammerstad, h = 0.0994 outer, 0.55 inner), R' = rho/(w t);
% each via on the path: 0.4 nH (1.6 mm barrel, Goldfarb) and 1 mOhm.
pa = pads(strcmp({pads.ref}, refA) & strcmp({pads.n}, pA)); pa = pa(1);
pb = pads(strcmp({pads.ref}, refB) & strcmp({pads.n}, pB)); pb = pb(1);
sel = trk(strcmp({trk.net}, net));
vs = vias; if iscell(vs), vs = [vs{:}]; end
[G, ~, segOf, ia, ib] = netgraph(trk, pads, vs, net, pa, pb);
[pth, ~, ep] = shortestpath(G, ia, ib);
if isempty(pth), error('pathLC: %s not connected between %s.%s and %s.%s', net, refA, pA, refB, pB); end
% map graph edges back to track indices via endpoints
L = 0; R = 0; len = 0; lays = {};
for e = ep(:)'
    k = segOf(e); if k == 0, continue; end
    s = sel(k); l = G.Edges.Weight(e);
    outer = any(strcmp(s.l, {'F.Cu', 'B.Cu'}));
    h = 0.0994 * outer + 0.55 * ~outer; t = 0.035 * outer + 0.0175 * ~outer;
    [z, ee] = ms(s.w, h); L = L + l * z * sqrt(ee) / 299.792458;
    R = R + 1.72e-8 * l * 1e-3 / (s.w * 1e-3 * t * 1e-3); len = len + l; lays{end+1} = s.l; %#ok<AGROW>
end
nvia = sum(~strcmp(lays(1:end-1), lays(2:end)));
L = L + 0.4 * nvia; R = R + 1e-3 * nvia;
end
function [z, ee] = ms(w, h)
u = w / h; ee = (4.3+1)/2 + (4.3-1)/2 / sqrt(1 + 12/u);
if u <= 1, z = 60/sqrt(ee) * log(8/u + u/4); else, z = 120*pi / (sqrt(ee) * (u + 1.393 + 0.667*log(u + 1.444))); end
end
