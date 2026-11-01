"""Build an auditable H1-H7 x PS/CM/CIT long table, never fabricate missing cells.

H4 is represented by PA alpha (its primary scalar); supporting H4a-d remain
in b_summary.csv. H6 uses R; ranking tau is retained as a supplementary row.
H7 peak ratio is conditional on >=5% outbreaks, primary setting, P1.
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]


def main():
    frames=[]
    for owner in 'abcde':
        p=ROOT/f'results/{owner}_summary.csv'
        if p.exists():
            g=pd.read_csv(p); g['source']=str(p.relative_to(ROOT)); frames.append(g)
    allrows=pd.concat(frames,ignore_index=True)
    allrows.to_csv(ROOT/'results/all_summary.csv',index=False)
    keys={'H1':'H1_window_sensitivity_density','H2':'m2_burstiness','H3':'m2_adjacent_jaccard',
          'H4':'pa_alpha__P3a','H5':'m4_adj_nmi_mean_', 'H6':'m3a_R_vsP1','H7':'peak_ratio_vsP1'}
    rows=[]
    for h,key in keys.items():
        for ds in ['PS','CM','CIT']:
            applicable=(h in ('H1','H4')) if ds=='CIT' else h!='H4'
            part=allrows[allrows.dataset==ds]
            if h=='H1' and ds=='CIT': key1=key+'_directed'
            elif h=='H5': key1=key+('w15min_g1' if ds=='PS' else 'w7D_g1')
            elif h=='H7': key1='m3c_'+('b0.05_D4h' if ds=='PS' else 'b0.2_D336h')+'_'+key
            else: key1=key
            found=part[part.metric==key1]
            row=dict(hypothesis=h,dataset=ds,metric=key1,status='missing' if applicable else 'inapplicable',
                     value=np.nan,null_mean=np.nan,null_std=np.nan,effect=np.nan,source='')
            if applicable and len(found):
                f=found.iloc[-1]; value=f.value
                effect=value-f.null_mean if h=='H2' else value
                row.update(status='measured' if np.isfinite(value) else 'undefined',value=value,
                           null_mean=f.null_mean,null_std=f.null_std,effect=effect,source=f.source)
            rows.append(row)
    out=pd.DataFrame(rows); out.to_csv(ROOT/'results/cross_network_summary.csv',index=False)
    display=out.pivot(index='hypothesis',columns='dataset',values='effect').reindex(columns=['PS','CM','CIT'])
    (ROOT/'results/cross_network_summary.md').write_text(display.fillna('--').to_markdown()+'\n\nH2 = real minus P1; H7 = ratio conditional on major outbreaks.\n')
    print(out.to_string(index=False))
if __name__=='__main__': main()
