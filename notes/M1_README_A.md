# Member A — M1 aggregation implementation

This implements H1/M1 for PS and CM only, within PLAN v3.

## 中文安装与执行

将本增量包中的 `src`、`scripts`、`tests` 目录合并到现有 `final_project`
目录。不会修改原始数据、标准化数据或现有 io.py。

在已启用本项目虚拟环境的终端中执行：

```bash
python -m unittest discover -s tests -v
python -m scripts.run_m1
```

加上原来的 io 测试应共 16 项通过。先测试，测试成功后再运行实验。
主实验结果在 `results/m1/main_fixed/`，共享格式摘要在 `results/m1/A_summary.csv`。
`null_mean` 与 `null_std` 留空，因为 PLAN v3 的 M1 不使用 null model。

后续的前后半段稳健性检查：

```bash
python -m scripts.run_m1 --robustness
```

输出至 `results/m1/robustness_fixed/`，不会覆盖主实验结果。
可选的节点口径诊断使用 `--active-nodes`，输出另一个目录；它不是新增假设。

## 固定的分析口径

- PS 为无向简单图；CM 为有向简单图。窗口内至少发生一次互动即连边。
- 主结果固定全数据节点总表（PS 242、CM 1899）；未出现互动的节点作为孤立节点。
  CM 的总体节点总表不是用户注册时间表，这一口径不等于所有用户始终在平台活跃。
- 保留连续时间轴内的空窗口；不推断 PS 夜间存在完整监测。
- 窗口从所分析区间的首端开始，互不重叠，左闭右开。
- 全观测区间分析边界为首时间戳至末时间戳加一个时间分辨率步长。
  这是明确的计算边界规则，不是额外取得的采集起止元数据。
- PS 保留 interval-end 时间戳；不虚构同一时刻内的先后顺序。
- 末尾不足窗口宽度的数据保存在 `*_windows.csv`，`complete=False`。
  主分析 `complete_only` 仅平均完整窗口；`include_partial` 是单独诊断，不能混用。
- PS 窗口：5、15、30 分钟；1、2、4、8、24 小时。
- CM 窗口：1、3、6、12 小时；1、3、7、30 天。这里一个月固定为 30 天。
- 每个完整窗口等权。均值不是按事件数加权的均值。

## 指标定义（供报告与组员核对）

1. `density`：NetworkX 简单图密度；有向和无向分母分别按各自定义。
2. `mean_degree`：PS 为普通度均值；CM 为入度加出度的均值。
   CM 同时保存 `mean_in_degree` 与 `mean_out_degree`；两者全节点平均值必然相同，
   不能因此声称每个节点的收发行为相同。
3. `clustering`：NetworkX 的无权平均局部聚类，计入零值；CM 使用 Fagiolo 有向定义。
4. `n_components`：PS 普通连通分量数；CM 弱连通分量数；孤立节点各算一个分量。
5. `largest_component_fraction`：最大（弱）连通分量节点数占本图节点数的比例。
6. `component_fraction`：连通分量数除以本图节点数。
7. `active_fraction`：非孤立节点所占比例，辅助解释固定分母的结果。

空的固定节点图依然有节点，所以最大分量大小为 1，而不是 0。
可选 active 口径中，空图的平均值和比例记为 NaN。

窗口敏感性：对某指标在各窗口宽度上的均值，计算
“最大均值减最小均值，再除以这些均值的绝对值平均数”。
这是 PLAN 中“相对变化幅度”的显式实现约定，不是文献中的普适定律或显著性检验。
少于两个有效尺度记为 NaN；全零曲线记为 0。

## 解读限制

- PS 总跨度短，24 小时尺度只有一个完整窗口；不能估计该尺度的窗口间标准差。
- 前后半段都短于 24 小时，所以该尺度半段结果没有完整窗口，必须留空。
- 大尺度会排除更长的末尾片段，改变平均值覆盖的时间；应检查 include_partial
  结果并查看每个尺度的窗口数，不能把边界效应当成普遍规律。
- 同一区间相邻窗口可能相关；std 是描述性窗口间标准差，不是标准误或置信区间。
- 固定节点数时，密度与平均度成比例，不是两项独立的假设证据。
- 弱连通不意味着按消息方向可达，更不意味着遵守时间顺序可达；后者归 Member D。
- 原始指标只在各数据集内部比较；跨网络仅汇总无量纲敏感性，且需注明窗口网格不同。
- 此实验不能检验事件排序对传播/可达性的作用；那是其他成员的实验。
- 主实验、半段检查都保持同一全局节点总表；半段以经过时间切分，不以事件数切分。
- 对比前后半段的敏感性时应只使用双方都有效的相同窗口宽度。

## 数值文件

- `PS_windows.csv` / `CM_windows.csv`：每个窗口的指标和完整性。
- `*_summary.csv`：每个窗口宽度的均值、标准差、范围、样本数。
- `*_sensitivity.csv`：各指标的无量纲窗口敏感性。
- `*_full_aggregate.csv`：整个分析区间的静态聚合指标，作为描述性参考。
- `run_both.json`：参数、输入文件 SHA-256、软件版本和运行时间。

绘图与报告入口见 README.md。

## API 来源

- https://networkx.org/documentation/stable/reference/generated/networkx.classes.function.density.html
- https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.cluster.clustering.html
- https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.components.weakly_connected_components.html

Directed clustering reference: Fagiolo (2007), Physical Review E 76, 026107.
