function [G, U, segOf, ia, ib] = netgraph(trk, pads, vias, net, pa, pb)
% NETGRAPH  Graph of one net's copper: track ends, T-junctions (end on another track's body),
% vias (ends within the via pad) and the two terminal pads. Edge weight = length (mm).
% segOf(e) = track index for track edges (0 for joins).
sel = trk(strcmp({trk.net}, net)); n = numel(sel);
A = reshape([sel.a], 2, [])'; B = reshape([sel.b], 2, [])';
vs = vias(strcmp({vias.net}, net)); V = [[vs.x]' [vs.y]']; vr = [vs.d]' / 2;
P = [A; B; V; pa.x pa.y; pb.x pb.y];
[U, ~, ic] = unique(round(P * 1e3) / 1e3, 'rows');
ea = ic(1:n); eb = ic(n+1:2*n); ev = ic(2*n+1:2*n+numel(vs)); ia = ic(end-1); ib = ic(end);
len = hypot(B(:,1) - A(:,1), B(:,2) - A(:,2));
E = [ea eb len (1:n)'];
ends = [ea; eb]; XY = U(ends, :); elay = [{sel.l} {sel.l}]';
for k = 1:n                                    % T-junctions: an end lying on track k's body
    ab = B(k,:) - A(k,:); L2 = ab * ab'; if L2 == 0, continue; end
    s = ((XY(:,1) - A(k,1)) * ab(1) + (XY(:,2) - A(k,2)) * ab(2)) / L2;
    dd = hypot(A(k,1) + s * ab(1) - XY(:,1), A(k,2) + s * ab(2) - XY(:,2));
    hit = find(s > 1e-6 & s < 1 - 1e-6 & dd <= sel(k).w / 2 + 1e-3 & strcmp(elay, sel(k).l));
    for h = hit'
        E = [E; ends(h) ea(k) s(h) * len(k) k; ends(h) eb(k) (1 - s(h)) * len(k) k]; %#ok<AGROW>
    end
end
for q = 1:numel(vs)                            % ends inside a via pad join the via node
    in = find(hypot(XY(:,1) - V(q,1), XY(:,2) - V(q,2)) <= vr(q) + 1e-3);
    E = [E; repmat(ev(q), numel(in), 1) ends(in) zeros(numel(in), 1) zeros(numel(in), 1)]; %#ok<AGROW>
end
for t = [1 2]                                  % terminal pads join every end inside their copper
    if t == 1, pd = pa; q = ia; else, pd = pb; q = ib; end
    in = find(abs(U(:,1) - pd.x) <= pd.sx/2 + 1e-3 & abs(U(:,2) - pd.y) <= pd.sy/2 + 1e-3);
    E = [E; repmat(q, numel(in), 1) in zeros(numel(in), 1) zeros(numel(in), 1)]; %#ok<AGROW>
end
other = pads(strcmp({pads.net}, net));         % pass-through pads of the net join the ends inside them
for pd = other(:)'
    in = find(abs(XY(:,1) - pd.x) <= pd.sx/2 + 1e-3 & abs(XY(:,2) - pd.y) <= pd.sy/2 + 1e-3);
    for t = 2:numel(in)
        E = [E; ends(in(1)) ends(in(t)) 0 0]; %#ok<AGROW>
    end
end
E = E(E(:,1) ~= E(:,2), :);
G = graph(E(:,1), E(:,2), max(E(:,3), 1e-9), size(U, 1));
segOf = zeros(numnodes(G) * 0 + numedges(G), 1);
% recover track ids per graph edge (graph() may reorder edges)
[~, loc] = ismember(sort(G.Edges.EndNodes, 2), sort(E(:,1:2), 2), 'rows');
segOf(:) = E(loc, 4);
end
