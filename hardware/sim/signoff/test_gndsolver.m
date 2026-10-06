% unit test for gndsolver flux: uniform 100x80 sheet, symmetric pads -> current centroid on the chord
d.edge = [0 0 100 80];
d.zone = struct('net','GND','l','F.Cu','pri',0,'polys',{{[0 0; 100 0; 100 80; 0 80]}});
d.via = struct('net',{},'x',{},'y',{},'d',{},'drill',{});
trk = struct('net',{},'l',{},'a',{},'b',{},'w',{});
mk = @(r,x,y) struct('ref',r,'n','1','net','GND','x',x,'y',y,'sx',0.5,'sy',0.5,'th',false,'lay',{{'F.Cu'}});
pads = [mk('A',30,40) mk('B',70,40) mk('C',30,6) mk('D',70,6)];
S = gndsolver(d, trk, pads, {'F.Cu'}, 0.49e-3, 0.5);
chord = @(p,q) (p.x*q.y - q.x*p.y)/2;
e1 = S.planeA(pads(1), pads(2)) - chord(pads(1), pads(2));
e2 = S.planeA(pads(3), pads(4)) - chord(pads(3), pads(4));
% analytic resistance check: R between two small contacts in a sheet ~ Rs/pi*ln(D/r) (infinite sheet)
v = S.solve(pads(1), pads(2)); R = v(S.node(pads(1))) - v(S.node(pads(2)));
fprintf('symmetric chord deviation %.2f mm2 (expect ~0)\nedge chord deviation %.2f mm2 (current bows toward interior: expect >0 in y-down coords? sign printed)\n', e1, e2);
fprintf('R = %.3f mOhm, infinite-sheet estimate %.3f mOhm (finite sheet + cell contact: same order)\n', R*1e3, 0.49/pi*log(40/0.28));
assert(abs(e1) < 5, 'symmetric deviation should vanish');
