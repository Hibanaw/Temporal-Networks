"""Create M1 figures from saved results; no experiment is rerun.

Run from the project root: python -m scripts.plot_m1
"""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'results/m1/main_fixed'
FIGURES = ROOT / 'figures'
TABLES = ROOT / 'results/m1/plot_tables'
COLORS = {'PS': '#147d99', 'CM': '#c76b30'}
LABELS = {
    'PS': ['5m', '15m', '30m', '1h', '2h', '4h', '8h', '24h'],
    'CM': ['1h', '3h', '6h', '12h', '1d', '3d', '7d', '30d'],
}
METRICS = ['density', 'mean_degree', 'clustering', 'n_components',
           'largest_component_fraction', 'active_fraction']


def read_summary(dataset):
    source = SOURCE / f'{dataset}_summary.csv'
    if not source.exists():
        raise FileNotFoundError(f'{source}: run python -m scripts.run_m1 first')
    frame = pd.read_csv(source)
    frame = frame.loc[(frame.period == 'full') & (frame.node_basis == 'fixed')]
    if frame.empty:
        raise ValueError(f'{dataset}: full/fixed results are missing')
    if frame.duplicated(['delta_seconds', 'window_policy', 'metric']).any():
        raise ValueError(f'{dataset}: duplicate summary rows')
    widths = np.sort(frame.delta_seconds.unique())
    expected = ([300, 900, 1800, 3600, 7200, 14400, 28800, 86400]
                if dataset == 'PS' else
                [3600, 10800, 21600, 43200, 86400, 259200, 604800, 2592000])
    if list(widths) != expected:
        raise ValueError(f'{dataset}: unexpected window grid; update labels explicitly')
    return frame, widths


def series(frame, metric, widths, policy='complete_only'):
    selected = frame.loc[(frame.metric == metric) & (frame.window_policy == policy)]
    selected = selected.set_index('delta_seconds').reindex(widths)
    if selected['mean'].isna().any() or not np.isfinite(selected['mean']).all():
        raise ValueError(f'Missing/nonfinite means: {metric}, {policy}')
    return selected


def style_axis(ax, widths, labels):
    ax.set_xscale('log')
    ax.set_xticks(widths, labels)
    ax.minorticks_off()
    ax.tick_params(axis='x', labelsize=10)
    ax.set_xlabel('Window width (log scale)')
    ax.grid(axis='y', color='#dce1e6', linewidth=0.7)
    ax.spines[['top', 'right']].set_visible(False)
    ax.set_axisbelow(True)
    ax.yaxis.set_major_locator(MaxNLocator(nbins=5))
    ax.ticklabel_format(axis='y', style='plain', useOffset=False)


def save(fig, stem):
    for extension in ['png', 'pdf']:
        path = FIGURES / f'{stem}.{extension}'
        fig.savefig(path, dpi=200, facecolor='white')
        print(f'Saved {path.relative_to(ROOT)}')
    plt.close(fig)


def main_figure(dataset, frame, widths):
    directed = dataset == 'CM'
    titles = ['Density', 'Mean degree (in + out)' if directed else 'Mean degree',
              'Directed clustering' if directed else 'Mean clustering',
              'Weak components' if directed else 'Connected components',
              'Largest weak component / N' if directed else 'Largest component / N',
              'Active nodes / N']
    fig, axes = plt.subplots(2, 3, figsize=(14, 8.2))
    for ax, metric, title in zip(axes.flat, METRICS, titles):
        values = series(frame, metric, widths)
        ax.plot(widths, values['mean'], '-o', color=COLORS[dataset], lw=2.2, ms=5)
        ax.set_title(title, loc='left', fontsize=11.5, fontweight='bold')
        ax.set_ylabel('Mean across complete windows')
        style_axis(ax, widths, LABELS[dataset])
        ax.set_ylim(bottom=0)
        if metric in ['largest_component_fraction', 'active_fraction']:
            ax.set_ylim(0, 1.05)
    count = series(frame, 'density', widths).n_windows.astype(int).tolist()
    count_text = '   |   '.join(f'{label}: {n}' for label, n in zip(LABELS[dataset], count))
    nodes = 242 if dataset == 'PS' else 1899
    description = 'undirected contacts' if dataset == 'PS' else 'directed messages'
    fig.suptitle(f'{dataset} | How window width changes observed structure',
                 x=0.06, ha='left', fontsize=21, fontweight='bold', y=0.98)
    fig.text(0.06, 0.92, f'{description.capitalize()} | Fixed N = {nodes:,}, including isolates | Empty windows retained', fontsize=12)
    fig.text(0.06, 0.065, 'Complete windows at each scale: ' + count_text, fontsize=10)
    caveat = ('24h has one complete window. Chronological gaps retained; monitoring coverage is not inferred.'
              if dataset == 'PS' else
              '30d means 30 days. Weak connectivity does not imply directed or temporal reachability.')
    fig.text(0.06, 0.035, caveat, fontsize=10, color='#4b5563')
    fig.subplots_adjust(left=0.075, right=0.98, top=0.85, bottom=0.18, wspace=0.34, hspace=0.55)
    save(fig, f'M1_{dataset}_aggregation')


def boundary_figure(data):
    fig, axes = plt.subplots(2, 3, figsize=(14, 8))
    metrics = ['density', 'clustering', 'largest_component_fraction']
    titles = ['Density', 'Clustering', 'Largest (weak) component / N']
    for row, dataset in enumerate(['PS', 'CM']):
        frame, widths = data[dataset]
        for ax, metric, title in zip(axes[row], metrics, titles):
            for policy, linestyle, marker, label in [
                ('complete_only', '-', 'o', 'Complete windows (main)'),
                ('include_partial', '--', 's', 'Including partial tail')]:
                values = series(frame, metric, widths, policy)
                ax.plot(widths, values['mean'], linestyle=linestyle, marker=marker,
                        color=COLORS[dataset] if policy == 'complete_only' else '#596575',
                        ms=4, lw=2, label=label)
            ax.set_title(f'{dataset} | {title}', loc='left', fontsize=12, fontweight='bold')
            ax.set_ylabel('Mean across selected windows')
            style_axis(ax, widths, LABELS[dataset])
            ax.set_ylim(bottom=0)
            if metric == 'largest_component_fraction':
                ax.set_ylim(0, 1.05)
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='upper left', bbox_to_anchor=(0.055, 0.925), ncol=2, frameon=False)
    fig.suptitle('M1 | Sensitivity to the final incomplete window', x=0.06,
                 ha='left', fontsize=21, fontweight='bold', y=0.98)
    fig.text(0.06, 0.055, 'Diagnostic: the partial tail is given the same weight as a complete window; its duration is shorter.', fontsize=11)
    fig.text(0.06, 0.025, 'The main analysis uses complete windows only. Vertical scales are dataset-specific; raw levels are not cross-network effects.', fontsize=10)
    fig.subplots_adjust(left=0.075, right=0.98, top=0.82, bottom=0.16, wspace=0.34, hspace=0.55)
    save(fig, 'M1_boundary_check')


def main():
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 11,
                         'pdf.fonttype': 42, 'ps.fonttype': 42})
    FIGURES.mkdir(parents=True, exist_ok=True)
    TABLES.mkdir(parents=True, exist_ok=True)
    data = {}
    for dataset in ['PS', 'CM']:
        frame, widths = read_summary(dataset)
        data[dataset] = frame, widths
        main_figure(dataset, frame, widths)
        selected = frame.loc[(frame.window_policy == 'complete_only') & frame.metric.isin(METRICS)]
        table = selected.pivot(index='delta_seconds', columns='metric', values='mean').reindex(widths)
        table.insert(0, 'window_label', LABELS[dataset])
        table.insert(1, 'n_complete_windows', series(frame, 'density', widths).n_windows.astype(int))
        table.to_csv(TABLES / f'{dataset}_main_means.csv')
    boundary_figure(data)
    print('Done. Figures use saved experimental results; no network calculations were rerun.')


if __name__ == '__main__':
    main()
