# Member A: M1 plotting

将本包中的 scripts、figures、results 文件夹合并到 final_project。
绘图脚本读取你已有的 results/m1/main_fixed/*_summary.csv：

```bash
python -m scripts.plot_m1
```

不需要再次下载数据或运行网络计算。包内附图由同一代码实际生成；
在你的电脑运行上述命令，会用你的结果重新生成这些图及数值表。

## 输出

- figures/M1_PS_aggregation.png 与 .pdf：PS 六面板主图。
- figures/M1_CM_aggregation.png 与 .pdf：CM 六面板主图。
- figures/M1_boundary_check.png 与 .pdf：是否纳入末尾不完整窗口的诊断。
- results/m1/plot_tables/PS_main_means.csv、CM_main_means.csv：主图数值。

PNG 适合放演示文稿，PDF 是适合 LaTeX 的矢量图。

## 解读约定

主图每个点为该尺度下完整窗口指标的等权平均，固定全局节点总表、计入孤立节点及空窗口。
横轴为对数尺度；各数据集纵轴按本数据范围显示，不能用图上高度做原始指标跨网络比较。
聚类是各窗口内平均局部聚类的窗口平均；CM 用有向定义。
连通性为 PS 普通连通、CM 弱连通，均不是时间可达性。
N 指固定全局节点数；active nodes 指窗口内至少参与一条边的节点。

主图仅显示均值，不把标准差画成置信区间。原始 summary.csv 保留窗口间 std、min、max、median。
PS 的 24h 点只有一个完整窗口，无法估计窗口间标准差。
密度与平均度在固定 N 下成比例，不能当作两份独立证据。
边界对照纳入的尾窗口比标称宽度短，仍等权计入，仅作诊断，不替代主分析。

初步结果：两个数据集的这些窗口均值中，密度、平均度、聚类和最大分量比例
随窗口变长而上升，分量数下降。这支持 H1 中结构描述依赖聚合尺度的部分。
前后半段结果见 M1_halves_connectivity.pdf 及 results/m1/plot_tables/M1_half_means.csv。
