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

# PS and CM data acquisition

Download with `python scripts/download_e.py`, which prints each file's size and SHA-256.

- Primary School (PS): SocioPatterns, https://www.sociopatterns.org/datasets/primary-school-temporal-network-data/
  (`primaryschool.csv.gz`, `primaryschool_metadata.txt`). Licence CC BY-NC-SA 4.0; cite
  Stehlé et al. (2011) and Gemmetto et al. (2014). The old `wp-content` links return 404.
  Columns: `t i j Ci Cj`, tab-separated; `t` is seconds from midnight of the first day,
  in 20-s steps. Contacts are undirected.
- CollegeMsg (CM): SNAP, https://snap.stanford.edu/data/CollegeMsg.html
  (`CollegeMsg.txt.gz`). Columns `SRC DST UNIXTS`, space-separated; messages are directed.

E's loaders (`src/e_datasets.py`) remove self-loops and duplicate events and store PS
pairs as `u < v`. They will be replaced by A's `io.py` once `data/processed/` exists.
Raw files are not committed.