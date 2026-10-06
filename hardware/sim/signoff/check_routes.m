% diagnostics for signoff_ground_hum: plot extracted routes, compare plane flux with straight line
d = jsondecode(fileread('board.json'));
trk = d.trk; if iscell(trk), trk = cellfun(@(s) rmfield_if(s), trk, 'UniformOutput', false); trk = [trk{:}]; end
fp = d.fp; if iscell(fp), fp = [fp{:}]; end
run_helpers = true; %#ok<NASGU>
LAY = {'F.Cu','GND','PWR','SIG','GND5','B.Cu'}; RS = [0.49e-3 0.98e-3 0.98e-3 0.98e-3 0.98e-3 0.49e-3];
pads = allpads_(fp);
S = gndsolver(d, trk, pads, LAY, RS, 0.3);
fp_ = @(r,n) pads(strcmp({pads.ref},r) & strcmp({pads.n},n));
legsR = {'U402','9','N4_RP_OUT','R419','1'; 'R419','2','LEG_RP','K603','4'; 'K603','6','JACK_RP','J702','3'};
legsL = {'U401','9','N4_LP_OUT','R417','1'; 'R417','2','LEG_LP','K601','4'; 'K601','6','JACK_LP','J702','4'};
rR = routepath_(trk, pads, legsR); rL = routepath_(trk, pads, legsL);
sl = fp_('J702','1'); s1 = sl(1); r412 = fp_('R412','2'); r404 = fp_('R404','2');
fprintf('route lengths: R %.1f mm, L %.1f mm\n', sum(hypot(diff(rR(:,1)),diff(rR(:,2)))), sum(hypot(diff(rL(:,1)),diff(rL(:,2)))));
fprintf('plane flux sleeve->R412 %.1f vs straight %.1f mm2\n', S.planeA(s1, r412), (s1.x*r412.y - r412.x*s1.y)/2);
fprintf('plane flux sleeve->R404 %.1f vs straight %.1f mm2\n', S.planeA(s1, r404), (s1.x*r404.y - r404.x*s1.y)/2);
% translation invariance of a closed loop: shift origin by recomputing with offset coordinates
f = figure('Visible','off'); hold on; axis equal; set(gca,'YDir','reverse');
plot(rR(:,1), rR(:,2), 'r-', 'LineWidth', 1.5); plot(rL(:,1), rL(:,2), 'b-', 'LineWidth', 1.5);
plot([s1.x r412.x], [s1.y r412.y], 'r:'); plot([s1.x r404.x], [s1.y r404.y], 'b:');
P = {'U401','U402','R417','R419','K601','K603','J702','R404','R412'};
for k = 1:numel(P), q = pads(strcmp({pads.ref}, P{k})); text(mean([q.x]), mean([q.y]), P{k}, 'FontSize', 7); end
xlim([105 160]); ylim([65 120]); grid on; title('SE routes (solid) and straight return (dotted): R red, L blue');
exportgraphics(f, 'check_routes.png', 'Resolution', 130);
function s = rmfield_if(s), if isfield(s,'arc'), s = rmfield(s,'arc'); end, end
