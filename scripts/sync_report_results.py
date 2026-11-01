"""Generate measured A/C/D result sections and cross table into a report checkout.

Usage: python scripts/sync_report_results.py --report ../Temporal-Networks-Report
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
these values alone do not establish a universal ranking of network types.
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
including empty windows when their union is nonempty.}\\label{tab:burst}
\\end{table}
'''+figure('c_activity_reproduced','Pooled burstiness and memory relative to 20 P1 samples.','fig:activity-reproduced')
    for ds in ['PS','CM']:
        b=r('c',ds,'m2_burstiness');m=r('c',ds,'m2_memory');life=r('c',ds,'m2_mean_lifetime_s')
        c+=f"In {ds}, $\\Delta B={b.value-b.null_mean:+.4f}$ and $\\Delta M={m.value-m.null_mean:+.4f}$. "
        c+=f"Mean tie lifetime is {life.value/86400:.3f} days, versus {life.null_mean/86400:.3f} days under P1.\n"
    c+='''\\paragraph{Verdict on H2 and H3.}
Burstiness exceeds P1 in both datasets, while pooled positive memory is weaker than P1.
Thus H2 has a mixed verdict. H3 depends on the statistic: real ties are temporally
concentrated, and adjacent overlap is below P1 in PS but above it in CM at the primary widths.
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
P1 preserves the static graph; the real--P1 difference isolates timing conditional on
that graph. P2 also changes topology and cannot isolate timing alone.
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
H7 is conditional on parameters and the reference model. PS peaks later under its
primary setting; CM peaks earlier than P1 across the four tested full-period settings and is close
to P2. The claim that slowing is strongest in CM is therefore not supported.
Peak timing among major outbreaks does not by itself measure population-wide epidemic speed.
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
    labels={'H1':'Density range/mean','H2':'$B-B_{P1}$','H3':'Adjacent Jaccard','H4':'PA $\\alpha$','H5':'Adjacent NMI','H6':'Reach ratio $R$','H7':'Peak ratio vs P1'}
    for h,label in labels.items():
        part=cross[cross.hypothesis==h].set_index('dataset')
        text+=h+' & '+label+' & '+' & '.join(f(part.loc[ds,'effect']) for ds in ['PS','CM','CIT'])+r' \\'+'\n'
    text+=r'''\bottomrule\end{tabular*}
\caption{Measured H1--H7 primary effects; -- means inapplicable. H4 uses PA as its scalar
representative; ageing, densification and predictive diagnostics retain separate verdicts.
H5 uses 15-min PS/7-day CM windows; H7 uses the first parameter setting and major outbreaks.}
\label{tab:cross}\end{table}
H1 is supported as window dependence. H2 separates excess burstiness from weaker-than-null
memory. H3 and H5 depend on network type and window. H6 shows loss of reachable pairs,
with partial ranking disagreement. H7 slowing is supported in primary PS, but not CM.
The window grids, node universes, edge semantics and conditioning must accompany these values.
'''
    text=text.replace(r'\begin{table}[t]\centering\small',
                      r'\begin{center}\begin{minipage}{\columnwidth}\centering\small')
    text=text.replace(r'\caption{Measured H1', r'\captionof{table}{Measured H1')
    text=text.replace(r'\label{tab:cross}\end{table}', r'\label{tab:cross}\end{minipage}\end{center}')
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
\clearpage
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
              ('C','PS','m2_burstiness','H2 $\\Delta B$'),('C','CM','m2_burstiness','H2 $\\Delta B$'),
              ('D','PS','m3a_R_vsP1','H6 $R$'),('D','CM','m3a_R_vsP1','H6 $R$'),
              ('D','PS','m3c_b0.05_D4h_peak_ratio_vsP1','H7 ratio'),('D','CM','m3c_b0.2_D336h_peak_ratio_vsP1','H7 ratio'),
              ('E','PS','m4_adj_nmi_mean','H5 NMI'),('E','CM','m4_adj_nmi_mean','H5 NMI'),
              ('B','CIT','alpha__P3a','H4 $\\alpha$')]
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
values do not depend on null count, while H2 differences and H7 ratios do.}\label{tab:robust-halves}
\end{table}
Primary H7 ratios remain on the same side of one under the 20/60 comparison:
PS changes from 1.160 to 1.161 and CM from 0.888 to 0.884. Both primary half-period
ratios preserve those directions. This does not hold uniformly over parameter settings:
at PS $\beta=.02$, $D=4$ h the full-period ratio moves from 1.0005 (20 nulls) to
0.9992 (60 nulls), so no directional slowing claim is supported there. PS's one-hour
setting peaks earlier than P1 in the first half (ratio 0.874) despite a full-period
ratio above one. In CM's second half, two settings produce no major real outbreaks
and their conditional peak ratios are undefined; these are not treated as zero.
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
