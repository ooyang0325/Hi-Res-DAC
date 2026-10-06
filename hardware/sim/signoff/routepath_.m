function route = routepath_(trk, pads, legs)
    % legs: rows {refA, padA, net, refB, padB}; shortest routed path per leg, straight across parts
    route = [];
    for k = 1:size(legs,1)
        pa = findpad_(pads, legs{k,1}, legs{k,2}); pb = findpad_(pads, legs{k,4}, legs{k,5});
        sel = trk(strcmp({trk.net}, legs{k,3}));
        P = [reshape([sel.a],2,[])'; reshape([sel.b],2,[])'];
        P = [P; pa.x pa.y; pb.x pb.y];
        [U, ~, ic] = unique(round(P*1e3)/1e3, 'rows');
        n = numel(sel); e1 = ic(1:n); e2 = ic(n+1:2*n);
        wgt = hypot(U(e1,1)-U(e2,1), U(e1,2)-U(e2,2));
        ia = ic(2*n+1); ib = ic(2*n+2);
        % pads join every track end inside their copper
        E = [e1 e2 wgt];
        for q = [ia ib]
            if q == ia, pd = pa; else, pd = pb; end
            in = find(abs(U(:,1)-pd.x) <= pd.sx/2+1e-3 & abs(U(:,2)-pd.y) <= pd.sy/2+1e-3);
            E = [E; repmat(q,numel(in),1) in hypot(U(in,1)-pd.x, U(in,2)-pd.y)]; %#ok<AGROW>
        end
        % layer changes at vias share x,y so they are already one node
        E = E(E(:,1) ~= E(:,2), :);
        G = graph(E(:,1), E(:,2), max(E(:,3), 1e-6), size(U,1));
        pth = shortestpath(G, ia, ib);
        if isempty(pth), error('no routed path for %s', legs{k,3}); end
        route = [route; U(pth,:)]; %#ok<AGROW>
    end
end

function p = findpad_(pads, ref, n)
    p = pads(strcmp({pads.ref}, ref) & strcmp({pads.n}, n)); p = p(1);
end
