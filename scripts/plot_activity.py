"""Reproduce the PS/CM activity figure in the report from canonical cleaned events.

Run from the repository root with python -m scripts.plot_activity.
"""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
from src.io import load

ROOT = Path(__file__).resolve().parents[1]


def main():
    plt.rcParams.update({'font.size': 11, 'axes.spines.top': False,
                         'axes.spines.right': False, 'pdf.fonttype': 42})
    fig, axes = plt.subplots(2, 1, figsize=(10, 7.4), layout='constrained')
    (ROOT / 'results').mkdir(exist_ok=True)
    for dataset, ax, width, color in [('PS', axes[0], 600, '#167D9A'),
                                      ('CM', axes[1], 86400, '#C76C35')]:
        events = load(dataset).events
        first, last = int(events.t.min() // width), int(events.t.max() // width)
        counts = (events.groupby(events.t // width).size()
                  .reindex(range(first, last + 1), fill_value=0))
        table = pd.DataFrame({'bin_start': counts.index.to_numpy() * width,
                              'bin_end': (counts.index.to_numpy() + 1) * width,
                              'events': counts.to_numpy()})
        table.to_csv(ROOT / 'results' / f'{dataset}_activity.csv', index=False)
        if dataset == 'PS':
            ax.bar(table.bin_start / 3600, table.events, width=width/3600,
                   align='edge', color=color, linewidth=0)
            ax.set(xlabel='Hours from the source time origin', ylabel='Contact records / 10 min',
                   title='PS | Two school days of face-to-face contacts')
            ax.text(.99, .96, 'Each record represents 20 seconds of contact',
                    transform=ax.transAxes, ha='right', va='top', fontsize=9)
        else:
            dates = pd.to_datetime(table.bin_start, unit='s', utc=True)
            ax.bar(dates, table.events, width=1, align='edge', color=color, linewidth=0)
            ax.set(xlabel='Date (UTC)', ylabel='Messages / day',
                   title='CM | Online private messages (after exact-triple deduplication)')
        ax.grid(axis='y', alpha=.18)
        ax.set_axisbelow(True)
    fig.suptitle('Observed activity over time', fontsize=17, fontweight='bold')
    out = ROOT / 'figures'
    out.mkdir(exist_ok=True)
    fig.savefig(out / 'activity_PS_CM.png', dpi=180)
    fig.savefig(out / 'activity_PS_CM.pdf')
    plt.close(fig)
    print('Saved activity_PS_CM.png and .pdf; activity bin tables in results/')


if __name__ == '__main__':
    main()
