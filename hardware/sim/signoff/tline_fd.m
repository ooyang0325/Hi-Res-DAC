function r = tline_fd(g)
% 2-D quasi-static finite-difference field solver for L1 microstrip lines over the L2 plane.
% g: struct with w (trace width), s (edge gap; 0 = single line), t (copper), h (dielectric),
%    er (dielectric), tm/erm (conformal solder mask; tm = 0 for none), d (grid step), all mm.
% r: Z0 (single) or Zodd/Zeven/Zdiff/Zcomm (pair), plus eeff, in ohm.
% Method: solve div(eps grad phi) = 0 on a box (plane at y = 0, phi = 0 on the box), once with
% the dielectrics and once in air; per-line capacitance C = 2W/V^2 from the field energy W,
% Z = 1/(c0 sqrt(C Cair)).
c0 = 299792458;
if g.s > 0, modes = {[1 1], [1 -1]}; else, modes = {1}; end
for k = 1:numel(modes)
    C  = cap(g, modes{k}, true);
    Ca = cap(g, modes{k}, false);
    Z(k) = 1 / (c0 * sqrt(C * Ca)); E(k) = C / Ca; %#ok<AGROW>
end
if g.s > 0
    r = struct('Zeven', Z(1), 'Zodd', Z(2), 'Zdiff', 2*Z(2), 'Zcomm', Z(1)/2, 'eeff_odd', E(2));
else
    r = struct('Z0', Z(1), 'eeff', E(1));
end
end

function C = cap(g, v, diel)
e0 = 8.854187817e-12;
d = g.h / round(g.h / g.d);             % grid rows land exactly on the dielectric top
g.t = max(1, round(g.t / d)) * d;        % and on the copper top
W = 2*g.w + g.s + 12*g.h + 1.0;          % box: >= 5 h of dielectric beyond the outer edges
H = g.h + g.t + 1.2;                     % plane at y = 0, lid 1.2 mm above the copper
nx = round(W/d) + 1; ny = round(H/d) + 1;
x = (0:nx-1)*d - W/2; y = (0:ny-1)*d;
[X, Y] = ndgrid(x, y);
% conductors (fixed potential)
fix = false(nx, ny); val = zeros(nx, ny);
if g.s > 0, xc = [-(g.s+g.w)/2, (g.s+g.w)/2]; else, xc = 0; end
cond = false(nx, ny);
for k = 1:numel(xc)
    m = abs(X - xc(k)) <= g.w/2 + 1e-9 & Y >= g.h - 1e-9 & Y <= g.h + g.t + 1e-9;
    fix(m) = true; val(m) = v(k); cond = cond | m;
end
fix(:, 1) = true; fix(:, end) = true; fix(1, :) = true; fix(end, :) = true;   % plane and box at 0 V
% permittivity per cell (cell (i,j) spans nodes i..i+1, j..j+1)
xm = (X(1:end-1,1:end-1) + X(2:end,2:end))/2; ym = (Y(1:end-1,1:end-1) + Y(2:end,2:end))/2;
ep = ones(nx-1, ny-1);
if diel
    ep(ym < g.h) = g.er;
    if g.tm > 0
        near = false(size(xm));
        for k = 1:numel(xc)       % mask over the trace top and sides
            near = near | (abs(xm - xc(k)) <= g.w/2 + g.tm & ym >= g.h & ym <= g.h + g.t + g.tm);
        end
        near = near | (ym >= g.h & ym <= g.h + g.tm);     % mask on the bare laminate
        ep(near) = g.erm;
    end
end
% 5-point stencil with face permittivities (average of the two cells sharing each face)
id = reshape(1:nx*ny, nx, ny);
epad = zeros(nx+1, ny+1); epad(2:end-1, 2:end-1) = ep;
eE = (epad(2:end, 2:end) + epad(2:end, 1:end-1))/2;   % face between node (i,j) and (i+1,j)
eN = (epad(2:end, 2:end) + epad(1:end-1, 2:end))/2;   % face between node (i,j) and (i,j+1)
a1 = id(1:end-1, :); b1 = id(2:end, :); w1 = eE(1:end-1, :);
a2 = id(:, 1:end-1); b2 = id(:, 2:end); w2 = eN(:, 1:end-1);
a = [a1(:); a2(:)]; b = [b1(:); b2(:)]; w = [w1(:); w2(:)];
A = sparse([a; a; b; b], [a; b; b; a], [w; -w; w; -w], nx*ny, nx*ny);
free = ~fix(:);
phi = val(:);
phi(free) = A(free, free) \ (-A(free, ~free) * phi(~free));
P = reshape(phi, nx, ny);
% field energy per unit length (J/m) -> C = 2W/sum(V^2) per line
Ex = diff(P, 1, 1) / (d*1e-3); Ey = diff(P, 1, 2) / (d*1e-3);
Wx = 0.5 * e0 * sum(sum(eE(1:end-1, :) .* Ex.^2)) * (d*1e-3)^2;
Wy = 0.5 * e0 * sum(sum(eN(:, 1:end-1) .* Ey.^2)) * (d*1e-3)^2;
C = 2 * (Wx + Wy) / sum(v.^2);
end
