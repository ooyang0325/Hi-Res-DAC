function S = gndsolver(d, trk, pads, LAY, RS, H)
% GNDSOLVER  Resistive grid model of the GND copper on all layers + vias (grid pitch H mm).
% S.solve(src, snk)       node potentials for 1 A from src pads to snk pads (pad struct arrays)
% S.node(pad)             node index of a pad (F.Cu for SMD/PTH, B.Cu for bottom pads)
% S.planeA(pa, pb)        Sum_b I_b * (A.dl)_b / B for 1 A pa->pb, A = B/2 (-y, x): flux area, mm^2
% S.fluxA(route, ref, slv) closed-loop flux area: ref -> route -> sleeve -> plane back to ref
x0 = d.edge(1); y0 = d.edge(2);
nx = floor((d.edge(3) - x0) / H) + 1; ny = floor((d.edge(4) - y0) / H) + 1;
xs = x0 + H * ((0:nx-1) + 0.5); ys = y0 + H * ((0:ny-1) + 0.5);
N = nx * ny; NL = numel(LAY);
M = false(ny, nx, NL);
zones = d.zone; if iscell(zones), zones = [zones{:}]; end
for k = 1:NL
    for z = zones(:)'
        if ~strcmp(z.net, 'GND') || ~strcmp(z.l, LAY{k}), continue; end
        polys = z.polys; if ~iscell(polys), polys = num2cell(polys, [2 3]); end
        for i = 1:numel(polys)
            p = polys{i}; if iscell(p), continue; end            % holes are not emitted (fractured fills)
            p = squeeze(p); if size(p,2) ~= 2, p = p'; end
            M(:,:,k) = M(:,:,k) | scanfill(p, xs, ys);
        end
    end
    g = trk(strcmp({trk.net}, 'GND') & strcmp({trk.l}, LAY{k}));
    for t = g(:)'
        r = max(t.w/2, H/2);
        ix = find(xs >= min(t.a(1),t.b(1)) - r & xs <= max(t.a(1),t.b(1)) + r);
        iy = find(ys >= min(t.a(2),t.b(2)) - r & ys <= max(t.a(2),t.b(2)) + r);
        [X, Y] = meshgrid(xs(ix), ys(iy));
        M(iy, ix, k) = M(iy, ix, k) | segdist(X, Y, t.a, t.b) <= r;
    end
end
gp = pads(strcmp({pads.net}, 'GND'));
for p = gp(:)'
    if p.th, ks = 1:NL; else, ks = find(ismember(LAY, p.lay)); end
    ix = xs >= p.x - p.sx/2 & xs <= p.x + p.sx/2; iy = ys >= p.y - p.sy/2 & ys <= p.y + p.sy/2;
    if ~any(ix), [~, j] = min(abs(xs - p.x)); ix(j) = true; end
    if ~any(iy), [~, j] = min(abs(ys - p.y)); iy(j) = true; end
    for k = ks, M(iy, ix, k) = true; end
end
cell_ = @(x, y) (min(max(floor((x - x0) / H), 0), nx-1)) * ny + min(max(floor((y - y0) / H), 0), ny-1) + 1;  % column-major
I = []; J = []; V = [];
idx = reshape(1:N, ny, nx);
for k = 1:NL
    m = M(:,:,k); g = 1 / RS(k); b = (k-1) * N;
    h = m(:,1:end-1) & m(:,2:end); a1 = idx(:,1:end-1); a2 = idx(:,2:end);
    I = [I; b + a1(h)]; J = [J; b + a2(h)]; V = [V; g * ones(nnz(h),1)]; %#ok<AGROW>
    v = m(1:end-1,:) & m(2:end,:); a1 = idx(1:end-1,:); a2 = idx(2:end,:);
    I = [I; b + a1(v)]; J = [J; b + a2(v)]; V = [V; g * ones(nnz(v),1)]; %#ok<AGROW>
end
nbr = numel(I);                                                % in-plane branches (for flux sums)
vias = d.via; if iscell(vias), vias = [vias{:}]; end
vg = vias(strcmp({vias.net}, 'GND'));
VX = [[vg.x]'; [gp([gp.th]).x]']; VY = [[vg.y]'; [gp([gp.th]).y]'];
VD = [[vg.drill]'; 0.6 * max([gp([gp.th]).sx; gp([gp.th]).sy])'];
for q = 1:numel(VX)
    c = cell_(VX(q), VY(q)); gv = pi * VD(q) * 20e-6 / (1.72e-8 * 0.3e-3) * 1e-3;  % drill in mm
    filled = find(arrayfun(@(k) M(mod(c-1,ny)+1, floor((c-1)/ny)+1, k), 1:NL));
    for t = 1:numel(filled)-1
        I = [I; (filled(t)-1)*N + c]; J = [J; (filled(t+1)-1)*N + c]; V = [V; gv / (filled(t+1)-filled(t))]; %#ok<AGROW>
    end
end
n = NL * N;
G = sparse([I; J; I; J], [I; J; J; I], [V; V; -V; -V], n, n) + speye(n) * 1e-6;
F = decomposition(G, 'chol');
S.H = H; S.nx = nx; S.ny = ny; S.mask = M; S.N = N;
S.node = @(p) (strcmp(p.lay{1}, 'B.Cu') && ~p.th) * (NL-1) * N + cell_(p.x, p.y);
S.solve = @(src, snk) F \ rhs(src, snk);
    function b = rhs(src, snk)
        b = zeros(n, 1);
        for s_ = src(:)', b(S.node(s_)) = b(S.node(s_)) + 1 / numel(src); end
        for s_ = snk(:)', b(S.node(s_)) = b(S.node(s_)) - 1 / numel(snk); end
    end
% branch midpoints for flux sums
ii = mod(I(1:nbr) - 1, N) + 1; jj = mod(J(1:nbr) - 1, N) + 1;
xi = xs(floor((ii-1)/ny) + 1)'; yi = ys(mod(ii-1, ny) + 1)';
xj = xs(floor((jj-1)/ny) + 1)'; yj = ys(mod(jj-1, ny) + 1)';
S.planeA = @(pa, pb) planeflux(F \ rhs(pa, pb));
    function A = planeflux(v)
        Ib = V(1:nbr) .* (v(I(1:nbr)) - v(J(1:nbr)));            % current i -> j
        xm = (xi + xj) / 2; ym = (yi + yj) / 2;
        A = sum(Ib .* ((-ym / 2) .* (xj - xi) + (xm / 2) .* (yj - yi)));
    end
S.fluxA = @(route, ref, slv) segA([ref.x ref.y], route(1,:)) + trapA(route) + ...
    segA(route(end,:), [slv.x slv.y]) + S.planeA(slv, ref);
fprintf('GND grid %.2f mm: %d x %d x %d nodes, %d vias/PTH\n', H, nx, ny, NL, numel(VX));
end

function m = scanfill(p, xs, ys)
% even-odd scanline fill of polygon p (K x 2, mm) sampled at cell centres xs, ys
m = false(numel(ys), numel(xs));
q = [p; p(1,:)]; x1 = q(1:end-1,1); y1 = q(1:end-1,2); x2 = q(2:end,1); y2 = q(2:end,2);
rows = find(ys >= min(p(:,2)) & ys <= max(p(:,2)));
for r = rows(:)'
    y = ys(r); c = (y1 <= y & y2 > y) | (y2 <= y & y1 > y);
    if ~any(c), continue; end
    xc = sort(x1(c) + (y - y1(c)) .* (x2(c) - x1(c)) ./ (y2(c) - y1(c)));
    for t = 1:2:numel(xc) - 1
        m(r, xs >= xc(t) & xs < xc(t+1)) = true;
    end
end
end
function dd = segdist(X, Y, a, b)
ab = b(:)' - a(:)'; L2 = ab * ab';
if L2 == 0, s = zeros(size(X)); else, s = min(max(((X - a(1)) * ab(1) + (Y - a(2)) * ab(2)) / L2, 0), 1); end
dd = hypot(a(1) + s * ab(1) - X, a(2) + s * ab(2) - Y);
end
function A = trapA(route), A = sum((route(1:end-1,1).*route(2:end,2) - route(2:end,1).*route(1:end-1,2)) / 2); end
function A = segA(p, q), A = (p(1)*q(2) - q(1)*p(2)) / 2; end
