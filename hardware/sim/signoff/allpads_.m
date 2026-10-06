function pads = allpads_(fp)
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