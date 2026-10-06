% extract U504 regulator-to-capacitor paths on the old and new boards
fid = fopen('signoff_ldo_paths.txt', 'w');
for b = {'board_old.json', 'board.json'}
    d = jsondecode(fileread(b{1}));
    trk = d.trk; if iscell(trk), trk = cellfun(@(s) rmf(s), trk, 'UniformOutput', false); trk = [trk{:}]; end
    fp = d.fp; if iscell(fp), fp = [fp{:}]; end
    pads = allpads_(fp);
    [Lo, Ro, lo, vo] = pathLC(trk, pads, d.via, 'U504', '1', '3V3D', 'C512', '1');
    [Li, Ri, li, vi] = pathLC(trk, pads, d.via, 'U504', '6', '5V_SYS', 'C501', '1');
    fprintf(fid, '%s: U504.OUT->C512 %.1f mm, %d layer changes, %.2f nH, %.1f mOhm | U504.IN->C501 %.1f mm, %d layer changes, %.2f nH, %.1f mOhm\n', ...
        b{1}, lo, vo, Lo, Ro*1e3, li, vi, Li, Ri*1e3);
end
fclose(fid); type('signoff_ldo_paths.txt');
function s = rmf(s), if isfield(s,'arc'), s = rmfield(s,'arc'); end, end
