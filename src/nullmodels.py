
import numpy as np

# ---------- Data preprocessing ----------

def prepare_events(events, directed=False, contact_step=None):
    df = events[["u", "v", "t"]].copy()

    if not directed:
        a = np.minimum(df["u"], df["v"])
        b = np.maximum(df["u"], df["v"])
        df["u"], df["v"] = a, b

    df = df.drop_duplicates(["u", "v", "t"])
    df = df.sort_values(["u", "v", "t"])

    if contact_step is not None:
        gaps = df.groupby(["u", "v"])["t"].diff()
        df = df[gaps.isna() | (gaps > contact_step)]

    return df

# P1: Timestamp Shuffling
def timestamp_shuffle(events, seed=42):
    shuffled = events.copy()
    rng = np.random.default_rng(seed)

    shuffled["t"] = rng.permutation(
        shuffled["t"].to_numpy()
    )

    return shuffled


# P2: Edge Randomization
def edge_shuffle(events, seed=42, directed=False, n_swaps=None):
    rng = np.random.default_rng(seed)

    shuffled = events.copy()
    u = shuffled["u"].to_numpy().copy()
    v = shuffled["v"].to_numpy().copy()
    t = shuffled["t"].to_numpy()

    n = len(u)

    if n < 2:
        raise ValueError("At least two events are required")

    if n_swaps is None:
        n_swaps = 5 * n

    if not directed:
        mask = rng.random(n) < 0.5
        u[mask], v[mask] = v[mask].copy(), u[mask].copy()

    def edge_key(i, a, b):
        if directed:
            return (t[i], a, b)
        return (t[i], min(a, b), max(a, b))

    existing = {
        edge_key(i, u[i], v[i])
        for i in range(n)
    }

    if len(existing) != n:
        raise ValueError("Input contains duplicate events")

    if np.any(u == v):
        raise ValueError("Input contains self-loops")

    accepted = 0

    for _ in range(n_swaps):
        i, j = rng.choice(n, size=2, replace=False)

        a, b = u[i], v[i]
        c, d = u[j], v[j]

        if a == d or c == b:
            continue

        old1 = edge_key(i, a, b)
        old2 = edge_key(j, c, d)

        new1 = edge_key(i, a, d)
        new2 = edge_key(j, c, b)

        if new1 == new2:
            continue

        if new1 == old1 and new2 == old2:
            continue

        existing.remove(old1)
        existing.remove(old2)

        if new1 not in existing and new2 not in existing:
            v[i], v[j] = v[j], v[i]

            existing.add(new1)
            existing.add(new2)
            accepted += 1
        else:
            existing.add(old1)
            existing.add(old2)

    shuffled["u"] = u
    shuffled["v"] = v

    return shuffled

if __name__ == "__main__":
    import pandas as pd

    # 测试数据
    events = pd.DataFrame({
        "u": [1, 1, 2, 3, 2, 4],
        "v": [2, 3, 3, 4, 4, 1],
        "t": [100, 200, 300, 400, 500, 600]
    })

    # P1
    p1 = timestamp_shuffle(events, seed=42)

    print("=== P1 Timestamp Shuffling ===")
    print(p1)
    print("Same timestamps:",
          sorted(events["t"]) == sorted(p1["t"]))

    # P2
    p2 = edge_shuffle(events, seed=42, directed=False)

    print("\n=== P2 Edge Randomization ===")
    print(p2)
    print("Same timestamps:", events["t"].equals(p2["t"]))
    print("Self-loops:", (p2["u"] == p2["v"]).sum())