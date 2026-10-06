function [names, data, steps] = ltraw(file)
% LTRAW  Read an LTspice ASCII .raw (AC or transient, stepped). data{s}: points x vars (complex for AC).
txt = fileread(file); L = regexp(txt, '\r?\n', 'split');
nv = str2double(regexp(txt, 'No. Variables:\s*(\d+)', 'tokens', 'once'));
iv = find(startsWith(L, 'Variables:')); ival = find(startsWith(L, 'Values:'));
names = cell(1, nv);
for k = 1:nv, t = strsplit(strtrim(L{iv + k}), char(9)); names{k} = t{2}; end
iscx = contains(txt(1:min(end, 2000)), 'complex');
vals = L(ival + 1:end); vals = vals(~cellfun(@isempty, strtrim(vals)));
np = numel(vals) / nv; M = zeros(np, nv);
for p = 1:np
    for k = 1:nv
        s = strtrim(vals{(p-1)*nv + k}); t = strsplit(s, char(9)); s = t{end};
        if iscx, c = sscanf(s, '%f,%f'); M(p, k) = c(1) + 1i * c(2); else, M(p, k) = sscanf(s, '%f'); end
    end
end
x = real(M(:, 1)); br = [1; find(diff(x) < 0) + 1; np + 1];
steps = numel(br) - 1; data = cell(1, steps);
for s = 1:steps, data{s} = M(br(s):br(s+1) - 1, :); end
end
