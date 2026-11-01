"""Member D: event-driven SIR on a temporal network (M3c).

A node infected at time s is infectious on [s, s + duration). Each event (u, v, t)
whose sender u is infectious and was infected strictly before t (no chains within
one timestamp) infects the susceptible v with probability beta. Undirected events
work in both directions. Recovered nodes stay immune, so only infection times matter.
"""
import numpy as np


def simulate_sir(u, v, t, n_nodes, source, t_start, beta, duration, directed, rng):
    """u, v: int node indices, t: times, all sorted by t. Returns infection times
    (inf = never infected) as an array of length n_nodes."""
    first = np.searchsorted(t, t_start, side="right")
    draws = rng.random(len(t) - first)
    return _sir_kernel(u, v, t, n_nodes, source, t_start, beta, duration, directed, first, draws)


try:
    from numba import njit
except ImportError:
    def njit(**kwargs):
        return lambda fn: fn


@njit(cache=True)
def _sir_kernel(u, v, t, n_nodes, source, t_start, beta, duration, directed, first, draws):
    inf = np.full(n_nodes, np.inf)
    inf[source] = t_start
    for k in range(first, len(t)):
        a, b, tk = u[k], v[k], t[k]
        ia, ib = inf[a], inf[b]
        if ia < tk < ia + duration and ib == np.inf:
            if draws[k - first] < beta:
                inf[b] = tk
        if not directed and ib < tk < ib + duration and inf[a] == np.inf:
            if draws[k - first] < beta:
                inf[a] = tk
    return inf


def outbreak_summary(inf, t_start, duration):
    """Final size (fraction), peak time and half-size time, relative to t_start."""
    infected = inf[np.isfinite(inf)]
    size = len(infected) / len(inf)
    times = np.concatenate([infected, infected + duration])
    delta = np.concatenate([np.ones(len(infected)), -np.ones(len(infected))])
    order = np.argsort(times, kind="stable")
    # Evaluate prevalence after all infections/recoveries at the same timestamp.
    # Infection-before-recovery ordering must not create a fictitious peak.
    ordered_times = times[order]
    unique, first = np.unique(ordered_times, return_index=True)
    prevalence = np.cumsum(np.add.reduceat(delta[order], first))
    peak = float(unique[int(np.argmax(prevalence))] - t_start)
    half = float(np.sort(infected)[int(np.ceil(len(infected) / 2)) - 1] - t_start)
    return size, peak, half
