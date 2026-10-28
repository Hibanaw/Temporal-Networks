# CIT data acquisition and format

Source: AMiner DBLP-Citation-network V14, dated 2023-01-31.
Archive: https://originalfileserver.aminer.cn/misc/dblp_v14.tar.gz

Original archive size: 6,079,589,707 bytes.
SHA-256: `729cc2c107d8abbe586d9801340246fd94e94d916ba1cebe64dd93a399f0cd28`.
AMiner describes research use; no additional open-data licence is inferred.
Download using `python scripts/download_b.py` from the repository root.

Build with:

```sh
python src/cs_data.py --archive data/raw/dblp_v14.tar.gz --out data/processed/CIT
```

- `events.csv`: directed `(u,v,t)`; citing paper, cited paper, citing publication year.
- `nodes.csv`: `id,original_id,year,venue,title`; contiguous IDs include isolates.
- `same_year_events.csv`: excluded year ties, used only for structural sensitivity.
- `data_card.json`: source, selection, cleaning counts, venue counts and graph metadata.

The parser scans the whole corpus, selects a fixed database-venue whitelist over
1960–2020, removes self-loops and duplicate references, and excludes future-year and
same-year targets from the primary graph. Actual retained years are 1970–2020.
No outcome-based node selection is used for the primary graph.

Only the data card and aggregate scientific outputs are committed. The raw archive,
processed node/edge files and randomized edge datasets remain local. Full verification
requires rebuilding these files and rerunning the experiment pipeline.
