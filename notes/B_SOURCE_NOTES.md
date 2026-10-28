# B literature / implementation notes

## Jeong, Neda & Barabasi (2003)

Question: does existing degree influence subsequent link acquisition? Use a frozen pre-window degree and normalize incoming hits by the population at each degree, rather than fitting the final degree histogram. Our annual target likelihood additionally conditions on the changing annual citation total. The k+1 offset is an explicitly declared adaptation permitting citations to zero-degree papers. Bootstrap uncertainty resamples citing years, not individual edges. Source: https://www.barabasi.com/media/pub_imports/files/117.pdf

## Leskovec, Kleinberg & Faloutsos (2005)

Question: do edge counts increase superlinearly with graph size, and can effective diameter decrease during growth? We report both quantities separately. The 90th-percentile distance is a sampled weak-LCC statistic; a change in LCC membership can change it. P3 preserves each year's total edges and nodes, so it is not a null test for densification; its diameter distribution is informative. Source: https://www.cs.cmu.edu/~jure/pubs/powergrowth-kdd05.pdf

## Wang, Song & Barabasi (2013)

Equation 3 links cumulative citations to a normal CDF of logarithmic paper age. We use the published functional form, with dataset-specific fixed m from pre-1990 observed reference counts. This is an adaptation to within-database-venue citations, not a replication of the Physical Review corpus analysis. lambda, mu and sigma describe fitness, immediacy and longevity conditional on this m and on bounded fitting. Their numerical values are not directly comparable with global-citation parameters. Collapsing a fitted curve is descriptive; testable predictive evidence comes from held-out years with matched baselines. Source: https://www.barabasi.com/media/pub_imports/files/434.pdf

## WSB critical comment (2014)

An explicit critique motivates avoiding a "good collapse means predictable impact" inference. We retain boundary fits in primary forecast scoring, report their fraction, preserve all individual predictions, and compare against simpler baselines on identical selected papers and horizons. Source: https://arxiv.org/abs/1405.1574

## AMiner V14

The official download and schema are used directly. Selection by publication venue occurs before observing any experiment outcomes. Existing n_citation metadata can include citations not represented by our graph; it is never substituted for cumulative observed in-degree. Source: https://www.aminer.cn/aboutus/en-US/articles/655db2202ab17a072284bc0c
