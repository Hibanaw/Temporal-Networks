"""Generate measured A/C/D result sections and cross table into a report checkout.

Usage: python scripts/sync_report_results.py  # initialized report/ Git submodule
Optional: --report ../Temporal-Networks-Report for a separate report checkout.
E's delivered result/method sections and figures are copied without re-running M4.
"""
import argparse
import shutil
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--report',type=Path,default=ROOT/'report');args=ap.parse_args()
    report=args.report.resolve(); sec=report/'sections';fig=report/'figures';sec.mkdir(exist_ok=True);fig.mkdir(exist_ok=True)
    tables={o:pd.read_csv(ROOT/f'results/{o}_summary.csv') for o in 'abcde'}
    def r(o,ds,key):
        g=tables[o];return g[(g.dataset==ds)&(g.metric==key)].iloc[0]
    def f(x):return '--' if not np.isfinite(x) else f'{x:.3f}'
    def pm(row):return '$'+f'{row.null_mean:.4f}'+r'\pm'+f'{row.null_std:.4f}'+'$'
    def write(name,text): (sec/name).write_text(text.strip().replace('[t]', '[!htbp]')+'\n')
    def figure(name,caption,label,wide=False):
        env='figure*' if wide else 'figure'
        return '\\begin{'+env+'}[t]\n\\centering\n\\includegraphics[width=\\linewidth]{'+name+'.pdf}\n\\caption{'+caption+'}\n\\label{'+label+'}\n\\end{'+env+'}\n'
    for name in ['results_e_communities.tex','results_e_centrality.tex','methods_e_communities.tex','methods_e_centrality.tex']:
        source=ROOT/'report/sections'/name
        if source.resolve()!=(sec/name).resolve():shutil.copy2(source,sec/name)
    for pattern in ('e_*.pdf','ac_*.pdf','d_*.pdf','c_activity_reproduced.pdf'):
        for source in (ROOT/'figures').glob(pattern):
            if source.resolve()!=(fig/source.name).resolve():shutil.copy2(source,fig/source.name)
    a='''\\subsection{Aggregation and time windows}
\\label{sec:r-aggregation}
% Owner: A; generated from results/a_summary.csv and results/ac/.
\\paragraph{Contact and messaging networks.}
We use nonoverlapping windows anchored at the first observed event, with all nodes
in the selected period retained in every window. Empty windows and the final partial
window are included; overnight inactivity in PS therefore contributes to the average.
CM clustering is measured on the undirected projection; density and total degree
retain message direction. The grids span 5 minutes--1 day (PS) and 1 hour--30 days (CM).
For each metric, sensitivity is the range of its window-averaged values divided by
their mean across grid widths.
\\begin{table}[t]
\\centering\\small
\\begin{tabular*}{\\columnwidth}{@{\\extracolsep{\\fill}}lrr@{}}
\\toprule Metric sensitivity & PS & CM \\\\
\\midrule
'''
    for key,label in [('density','Density'),('mean_total_degree','Mean total degree'),('clustering','Clustering'),('components','Weak components'),('lcc_fraction','Weak LCC fraction')]:
        a+=label+' & '+f(r('a','PS','H1_window_sensitivity_'+key).value)+' & '+f(r('a','CM','H1_window_sensitivity_'+key).value)+r' \\'+'\n'
    a+='''\\bottomrule\\end{tabular*}
\\caption{Measured relative ranges over the stated grids. These are descriptive
sensitivity measures, not temporal-null significance tests.}\\label{tab:a-windows}
\\end{table}
'''+figure('ac_m1_windows','Structural metrics averaged over windows (PS top, CM bottom; separate scales). Dashed lines show full aggregates. The denominator includes inactive nodes.','fig:agg-window',True)+'''
\\input{sections/results_b_aggregation}
\\paragraph{Verdict on H1.}
Supported as a representation effect in all three datasets. Numerical sensitivity
depends on the width grid, alignment, inclusion of inactive nodes and observation span;
these values alone do not establish a ranking of network types. Density and mean
total degree are proportional under the fixed node denominator, so their identical
sensitivity values are one representation effect, not two independent findings.
PS clustering sensitivity changes from 1.628 in the full interval to 0.921 and
0.959 in the halves, demonstrating observation-interval dependence.
'''
    write('results_aggregation.tex',a)
    c='''\\subsection{Activity patterns}\\label{sec:r-activity}
% Owner: C; reconstructed reproducible code in src/stats.py and scripts/run_ac.py.
Inter-event intervals are pooled within dyads. In PS, contiguous 20-second contacts
are merged into episode onsets before burstiness, memory and repeated-tie analysis.
Memory pools adjacent interval pairs within each tie, without joining different ties.
Lifetimes and Jaccard use the original cleaned records. P1 uses seeds 0--19;
coincident events produced by timestamp shuffling are retained to preserve message
counts. Canonical input ordering fixes each seeded realization; null values below
are recomputed rather than copied from earlier rounded report tables.
\\begin{table}[t]\\centering\\small
\\begin{tabular*}{\\columnwidth}{@{\\extracolsep{\\fill}}llrr@{}}
\\toprule Network & Metric & Real & P1 mean $\\pm$ SD \\\\
\\midrule
'''
    for ds in ['PS','CM']:
        for key,label in [('burstiness','$B$'),('memory','$M$'),('repeated_tie_fraction','Repeated ties'),('adjacent_jaccard','Jaccard')]:
            row=r('c',ds,'m2_'+key);c+=ds+' & '+label+' & '+f(row.value)+' & '+pm(row)+r' \\'+'\n'
    c+='''\\bottomrule\\end{tabular*}
\\caption{Measured activity and persistence. Jaccard uses 1-hour PS and 7-day CM windows,
including empty windows when their union is nonempty. The CM repeated-tie row is descriptive only: it is P1-invariant.}\\label{tab:burst}
\\end{table}
'''+figure('c_activity_reproduced','Pooled burstiness and memory relative to 20 P1 samples.','fig:activity-reproduced')
    for ds in ['PS','CM']:
        b=r('c',ds,'m2_burstiness');m=r('c',ds,'m2_memory');life=r('c',ds,'m2_mean_lifetime_s')
        c+=f"In {ds}, $\\Delta B={b.value-b.null_mean:+.4f}$ and $\\Delta M={m.value-m.null_mean:+.4f}$. "
        c+=f"Mean tie lifetime is {life.value/86400:.3f} days, versus {life.null_mean/86400:.3f} days under P1.\n"
    c+='''\\paragraph{Verdict on H2 and H3.}
For PS, H2's excess burstiness is small in absolute terms over the full interval:
$B=0.535$ versus P1 0.518 ($\\Delta B=0.016$), despite being separated from the
small null dispersion. It grows to 0.116 and 0.120 in the two day-length halves
(real/null 0.404/0.288 and 0.395/0.275). The magnitude is therefore interval-dependent;
inter-day inactivity is a plausible contributor, not a separately identified cause.
CM has a larger excess; positive pooled memory remains weaker than P1 in both datasets.
H2 has a mixed, interval-dependent verdict rather than uniform strong support.

CM's H3 overlap contrast reverses with the observation interval: full-period
Jaccard is 0.096 versus P1 0.069 ($+0.027$), but first-half 0.074 versus 0.113
($-0.039$) and second-half 0.118 versus 0.140 ($-0.022$).
\\emph{CM persistence is observation-interval-dependent.} The full-period result
does not support an interval-independent claim of more persistent real ties.
P1 redistributes timestamps across each selected interval; changes in duration,
activity and window composition alter the null baseline. This explanation is
consistent with the comparisons but is not isolated causally by them.

\\paragraph{P1 invariants are descriptive only.}
The raw-record repeated-event fraction in both datasets and CM's repeated-tie
fraction are invariant under P1 by construction. Their near-zero null SDs are
floating-point effects, not strong evidence for H3; they are not used as null-test
evidence. PS's episode-based repeated-tie fraction can change because P1 breaks
contiguous contact episodes.
The PS lifetime is recomputed over canonical undirected dyads; the earlier report's
lifetime value is superseded by this shared-interface calculation. Pooling across
heterogeneous ties and short observation windows limit generalization.
'''
    write('results_activity.tex',c)
    d1='''% Owner: D. Multi-start rerun; supersedes the single-start analysis.
\\paragraph{Temporal reachability (M3a).}\\label{sec:d_reachability}
We average over 16 clock-hour starts in PS and 20 evenly spaced starts in the first
90\\% of the CM interval. Paths require strictly increasing timestamps; unreachable
pairs contribute zero to reachability. Mean latency is averaged over reachable pairs
at each start and then over starts. $R$ divides temporal reachability by static
reachability on the full selected period, with the same nodes and direction.
\\begin{table}[t]\\centering\\small
\\begin{tabular*}{\\columnwidth}{@{\\extracolsep{\\fill}}llrrr@{}}
\\toprule Dataset & Metric & Real & P1 & P2 \\\\
\\midrule
'''
    for ds in ['PS','CM']:
        for key,label in [('reach','Reach'),('R','$R$'),('mean_latency_s','Delay (h)')]:
            p1=r('d',ds,'m3a_'+key+'_vsP1');p2=r('d',ds,'m3a_'+key+'_vsP2');scale=3600 if key=='mean_latency_s' else 1
            d1+=ds+' & '+label+' & '+' & '.join(f(x/scale) for x in [p1.value,p1.null_mean,p2.null_mean])+r' \\'+'\n'
    d1+='''\\bottomrule\\end{tabular*}
\\caption{Multi-start averages; P1/P2 columns average 20 independent networks.
Individual starts and null SDs are retained in the result tables.}\\label{tab:d-reach}
\\end{table}
'''+figure('d_reachability_multistart','Temporal/static reachability ratios; error bars are the null-network SD.','fig:d_reachability')
    d1+='''\\paragraph{Interpretation.}
Both networks lose reachable pairs when observation starts at different times.
The reduction is stronger in CM, where direction and late starts restrict causal paths.
P1 preserves the static graph, but $R$ also depends on how much observation time
remains after each start; later starts have shorter horizons. P1's almost unit PS
reachability reflects contacts spread across the timetable. Thus $R$ is not a pure
topological effect or an observation-boundary-free timing measure. The real--P1
contrast compares timing under this same finite-horizon protocol. P2 also changes
topology and cannot isolate timing alone.
'''
    write('D1.tex',d1)
    d2='''% Owner: D. Event-started SIR; supersedes the observation-start experiment.
\\paragraph{Event-driven SIR (M3c).}\\label{sec:d_sir}
Each network uses 200 seeds at randomly selected events in its first 70\\% of event
positions. CM seeds use the sender; PS randomly selects either endpoint. The selected
seed event itself is excluded by the strict-time convention. Infectious duration is
fixed, transmission probability is per record, and recovered nodes remain immune.
Final size includes the seed. A major outbreak reaches at least 5\\% of period nodes.
Peak delays are averaged over major outbreaks only; $T_{\\rm real}/\\overline T_{\\rm null}$
is a conditional ratio of means. Nulls with no major outbreaks give an undefined peak,
not a zero delay. Simultaneous infections and recoveries are grouped before measuring
prevalence; the earliest maximum is selected.
\\begin{table*}[t]\\centering\\small
\\begin{tabular}{@{}llrrrrrrrr@{}}
\\toprule & & \\multicolumn{3}{c}{Final infected fraction} & \\multicolumn{3}{c}{Major outbreak probability} & \\multicolumn{2}{c}{Peak ratio} \\\\
Dataset & $(\\beta,D)$ & Real & P1 & P2 & Real & P1 & P2 & vs P1 & vs P2 \\\\
\\midrule
'''
    grids={'PS':[(.05,4),(.02,4),(.1,4),(.05,1)],'CM':[(.2,336),(.05,336),(.5,336),(.2,72)]}
    for ds,settings in grids.items():
        for beta,hours in settings:
            tag=f'b{beta:g}_D{hours}h'; vals=[]
            for metric in ['final_size','p_major']:
                p1=r('d',ds,f'm3c_{tag}_{metric}_vsP1');p2=r('d',ds,f'm3c_{tag}_{metric}_vsP2');vals.extend([p1.value,p1.null_mean,p2.null_mean])
            vals.extend(r('d',ds,f'm3c_{tag}_peak_ratio_vs{mode}').value for mode in ['P1','P2'])
            d2+=ds+f' & ({beta:g}, {hours} h) & '+' & '.join(f(v) for v in vals)+r' \\'+'\n'
    d2+='''\\bottomrule\\end{tabular}
\\caption{Four SIR settings per dataset, 200 seeds per network, 20 nulls per family.
The first setting in each dataset is primary. The peak-ratio population is restricted
to major outbreaks and can differ between real and null networks.}\\label{tab:d-sir}
\\end{table*}
'''+figure('d_sir_event_seeds','Primary SIR settings. Peak delay is conditional on major outbreaks; errors describe null-network variation.','fig:d_sir',True)
    d2+='''The revised design produces nontrivial CM outbreaks. Absence of secondary infections
in the earlier run arose from infecting seeds at the observation boundary with an
unsuitable short duration; it is not evidence for an intrinsic property of CM.

\\paragraph{Parameter, null and outcome dependence.}
For PS versus P1, the peak ratio is 1.0005 at $\\beta=.02$ (negligible peak difference),
1.160 at .05 and 1.311 at .10 for a four-hour infectious duration. Final size is
lower than both null families in all four tested settings; at the primary setting
it is 0.629 versus P1 0.776. The qualifying populations also differ: major outbreaks
occur for 0.860 of real seeds versus a mean 0.908 under P1. Conditional peak comparisons
therefore use different seed subsets and are not paired-seed causal slowdowns.

CM peaks earlier than P1 across the full-period settings (ratios 0.72--0.94),
whereas P2 peak ratios are approximately 0.98--1.01. Even the choice of timing
metric matters: at $\\beta=.5$, 14 days, the peak ratio to P1 is 0.924 but the
half-final-size time ratio is 1.061. The latter is time to half of each trajectory's
own final infected count, not time to a common epidemic size. These opposing signs
exclude a general claim that the entire spreading process is faster or slower.
In CM's second half, two weaker settings have no major real outbreaks (undefined
peak ratios); the primary setting still has major-outbreak probability 0.360.

PS's real mean final fraction is 0.629 over the full interval versus 0.821/0.788
in the halves. Uniform sampling from the first 70\\% of each event stream changes
seed identities, start positions and residual observation horizons when the interval
is split. Finite horizons and schedule boundaries may contribute; these CSV comparisons
alone do not identify their contribution separately. These are protocol sensitivities,
not evidence that truncating the data intrinsically strengthens propagation.
'''
    write('D2.tex',d2)
    write('results_function.tex',r'''
\subsection{Paths, centrality and spreading}\label{sec:r-function}
\input{sections/D1}
\input{sections/results_e_centrality}
\input{sections/D2}
\paragraph{Verdict on H6 and H7.}
H6's reachability component is supported under the multi-start protocol in both datasets;
rankings show a partial effect, with correlated rankings but different top nodes.
H7 receives conditional support in PS at its primary setting, with negligible
peak effect at low transmission probability and a reversal for the one-hour setting
in the first half. Lower final size is a separate result from delayed peak timing.
CM does not support the hypothesized slowdown: full-period peak delays are shorter
than P1, approximately unchanged against P2, and can disagree in sign with half-size
timing. Against P2 the primary half-period ratios fall to 0.961/0.877, so even the
near-null full-period comparison is observation-dependent.
The verdict depends on the null, outcome metric, parameters and observation interval.
All peak ratios condition on network-specific major-outbreak seed subsets; they do
not establish a population-wide causal slowing effect. Undefined ratios are not zeros.
''')
    write('results_evolution.tex',r'''
\subsection{Structural evolution}\label{sec:r-evolution}
\input{sections/results_b_growth}
\input{sections/results_e_communities}
''')
    cross=pd.read_csv(ROOT/'results/cross_network_summary.csv')
    text=r'''\subsection{Measured cross-network summary}\label{sec:r-cross}
Each row uses the hypothesis-specific measure shown below. Their units and interpretations
differ, so the table does not define a single overall sensitivity score.
\begin{table}[t]\centering\small
\begin{tabular*}{\columnwidth}{@{\extracolsep{\fill}}llrrr@{}}
\toprule ID & Measure & PS & CM & CIT \\
\midrule
'''
    specifications=[
        ('H1','none','Density sensitivity (descriptive)','value'),
        ('H2','P1',r'$\Delta B$ vs P1','effect'),
        ('H3','P1',r'$\Delta J$ vs P1','effect'),
        ('H4','P3a',r'$\Delta\alpha$ vs P3a','effect'),
        ('H5','P1',r'$\Delta$ adjacent NMI vs P1','effect'),
        ('H6','P1',r'$\Delta R$ vs P1','effect'),
        ('H6','P2',r'$\Delta R$ vs P2','effect'),
        ('H7','P1',r'Peak ratio vs P1 (conditional)','ratio'),
        ('H7','P2',r'Peak ratio vs P2 (conditional)','ratio')]
    for h,reference,label,column in specifications:
        part=cross[(cross.hypothesis==h)&(cross.reference==reference)].set_index('dataset')
        text+=h+' & '+label+' & '+' & '.join(f(part.loc[ds,column]) for ds in ['PS','CM','CIT'])+r' \\'+'\n'
    text+=r"""
\bottomrule\end{tabular*}
\caption{H1 is descriptive; H2--H6 are real minus the named null mean, in their
respective metric units. H7 explicitly reports both primary-setting peak ratios,
conditional on major outbreaks; its CSV effect column instead contains real minus
null peak delay in seconds. -- denotes inapplicability, not a zero effect.
H1 uses different grids/definitions (PS 5 min--1 day, CM 1 h--30 days, CIT trailing
1/2/5/10-year windows); its three values cannot be ranked. Density and mean total
degree sensitivities are algebraically redundant. H4 represents PA only; the other
H4 verdicts remain separate. H5 uses 15-min PS/7-day CM windows.}
\label{tab:cross}\end{table}
A common subtraction operator does not create a common substantive effect scale.
H2's PS excess is small over the full interval and changes in the halves.
CM's positive full-period H3 overlap contrast reverses in both halves; its verdict
is observation-interval-dependent. H5 has dataset-specific structural evidence;
H6 shows lower reachability than both nulls under the finite-horizon protocol.
H7 has conditional primary-setting support in PS and no general slowdown support
in CM; neither choice of null nor the conditioning on major outbreaks may be hidden.
"""
    text=text.replace(r'\begin{table}[t]\centering\small', r'\begin{center}\small')
    text=text.replace(r'{\columnwidth}{@{\extracolsep{\fill}}llrrr@{}}', r'{\textwidth}{@{\extracolsep{\fill}}llrrr@{}}')
    text=text.replace(r'\caption{H1', r'\captionof{table}{H1')
    text=text.replace(r'\label{tab:cross}\end{table}', r'\label{tab:cross}\end{center}')
    text=r'\twocolumn[\begin{@twocolumnfalse}'+"\n"+text+r'\end{@twocolumnfalse}]'+"\n"
    write('results_cross.tex',text)
    # Results preamble is evidence-based, preserving B's diagnostics and section order.
    write('results.tex',r'''
\section{Results}\label{sec:results}
The results follow the four method groups. All primary PS/CM cells now contain
measurements; null comparisons use 20 networks per family. The supplementary
robustness tables retain individual networks and elapsed-time half-window results.
\input{sections/results_aggregation}
\input{sections/results_activity}
\input{sections/results_evolution}
\input{sections/results_function}
\input{sections/results_b_diagnostics}
\input{sections/results_robustness}
\input{sections/results_cross}
''')
    checks=ROOT/'results/robustness/all_checks.csv'
    if checks.exists():
        g=pd.read_csv(checks)
        text=r"""\subsection{Observation and null-count sensitivity}\label{sec:r-robustness}
\begin{table}[!htbp]\centering\small
\begin{tabular*}{\columnwidth}{@{\extracolsep{\fill}}llrrrr@{}}
\toprule & Measure & Full & First & Second & 60 nulls \\
\midrule
"""
        keys=[('A','PS','H1_window_sensitivity_density','H1 density'),('A','CM','H1_window_sensitivity_density','H1 density'),
              ('A','PS','H1_window_sensitivity_clustering','H1 clustering'),
              ('C','PS','m2_burstiness',r'H2 $\Delta B$'),('C','CM','m2_burstiness',r'H2 $\Delta B$'),
              ('C','PS','m2_adjacent_jaccard',r'H3 $\Delta J$'),('C','CM','m2_adjacent_jaccard',r'H3 $\Delta J$'),
              ('D','PS','m3a_R_vsP1','H6 $R$'),('D','CM','m3a_R_vsP1','H6 $R$'),
              ('D','PS','m3c_b0.05_D4h_peak_ratio_vsP1','H7 ratio P1'),('D','CM','m3c_b0.2_D336h_peak_ratio_vsP1','H7 ratio P1'),
              ('D','PS','m3c_b0.05_D4h_peak_ratio_vsP2','H7 ratio P2'),('D','CM','m3c_b0.2_D336h_peak_ratio_vsP2','H7 ratio P2'),
              ('E','PS','m4_adj_nmi_mean','H5 NMI'),('E','CM','m4_adj_nmi_mean','H5 NMI'),
              ('B','CIT','alpha__P3a',r'H4 $\alpha$')]
        for owner,ds,key,label in keys:
            vals=[]
            for period,n in [('full',20),('first',20),('second',20),('full',60)]:
                part=g[(g.owner==owner)&(g.dataset==ds)&(g.metric==key)&(g.period==period)]
                if owner=='A':part=part[part.nulls==0] if n==20 else part.iloc[:0]
                else:part=part[part.nulls==n]
                value=np.nan
                if len(part):
                    rr=part.iloc[0];value=rr.value-rr.null_mean if owner=='C' else rr.value
                vals.append(value)
            text+=ds+' & '+label+' & '+' & '.join(f(v) for v in vals)+r' \\'+'\n'
        text+=r"""\bottomrule\end{tabular*}
\caption{Elapsed-time halves for PS/CM and analysis-year halves for CIT. A uses no null.
The 60-null run nests the first 20; H7 ratios condition on major outbreaks. A and E real
values do not depend on null count, while H2/H3 differences and H7 ratios do. H2/H3 are real minus P1; H5/H6 show observed NMI/$R$, and H7 shows conditional ratios.}\label{tab:robust-halves}
\end{table}
Primary H7 ratios remain on the same side of one under the 20/60 comparison:
PS changes from 1.160 to 1.161 and CM from 0.888 to 0.884. Both primary half-period
ratios preserve those directions. This does not hold uniformly over parameter settings:
at PS $\beta=.02$, $D=4$ h the full-period ratio moves from 1.0005 (20 nulls) to
0.9992 (60 nulls), so no directional slowing claim is supported there. PS's one-hour
setting peaks earlier than P1 in the first half (ratio 0.874) despite a full-period
ratio above one. In CM's second half, two settings produce no major real outbreaks
and their conditional peak ratios are undefined; these are not treated as zero.
The primary CM setting remains defined in that half (major-outbreak probability 0.360).
CM's H3 contrast reverses from $+0.027$ in the full interval to $-0.039/-0.022$
in the halves. PS's H2 excess grows from 0.016 to 0.116/0.120, while its clustering
sensitivity drops from 1.628 to 0.921/0.959. These are substantive interval
sensitivities even when increasing the null ensemble from 20 to 60 changes little.
Individual realizations, sample SDs and 20/60 changes are retained in the supplementary
CSV files. Splitting changes node populations and the time available for paths and
outbreaks, so agreement of signs is more informative than equality of raw effect sizes.
The established E resolution grid is retained. CIT retains its original history for
PA exposure and eligible targets; its diameter is measured on cumulative endpoint
graphs. WSB uses the original age-15 forecast test, additionally stratified by early
and late publication cohorts, rather than being treated as a stationary half-window test.
"""
        write('results_robustness.tex',text)
    else:
        write('results_robustness.tex',r'% Robustness tables are generated after the PBS runs finish.')
    print('Updated measured sections in',report)
if __name__=='__main__':main()
