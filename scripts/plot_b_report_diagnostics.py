"""Readable two-panel WSB diagnostics for the main manuscript; uses saved fits."""
from pathlib import Path
import shutil
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.special import ndtr

def main():
 root=Path(__file__).resolve().parents[1];out=root/'figures'
 pars=pd.read_csv(root/'results/b/wsb_full_parameters.csv')
 collapse=pd.read_csv(root/'results/b/wsb_collapse.csv')
 plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False,'pdf.fonttype':42})
 fig,axs=plt.subplots(1,2,figsize=(7.2,2.7),constrained_layout=True)
 axs[0].boxplot([pars[k] for k in ['lambda','mu','sigma']],tick_labels=[r'$\lambda$',r'$\mu$',r'$\sigma$'],showfliers=False,patch_artist=True,boxprops={'facecolor':'#c6d8e7'},medianprops={'color':'#173F5F'})
 axs[0].set(ylabel='Fitted parameter',title='Full-history fits (500 papers)')
 axs[1].scatter(collapse.scaled_time,collapse.scaled_citations,s=3,alpha=.1,color='#173F5F',rasterized=True)
 x=np.linspace(-4,4,200);axs[1].plot(x,ndtr(x),color='black',lw=1,label=r'$\Phi(x)$')
 axs[1].set(xlim=(-4,4),ylim=(-.05,1.3),xlabel=r'$(\ln t-\mu)/\sigma$',ylabel=r'$\ln(1+c/m)/\lambda$',title='In-sample collapse')
 axs[1].legend(frameon=False)
 for ext in ['pdf','png']:fig.savefig(out/('b_wsb_fit_diagnostics.'+ext),bbox_inches='tight',dpi=180)
 plt.close(fig)
 report_figures=root/'report/figures';report_figures.mkdir(exist_ok=True)
 for source in out.glob('b_*.pdf'):shutil.copyfile(source,report_figures/source.name)
if __name__=='__main__':main()
