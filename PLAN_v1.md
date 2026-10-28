# PC5253 Final Project — 计划草稿

**暂定题目**：How Much Does Time Matter? A Comparative Study of Aggregation, Temporal Patterns and Dynamics in Real-World Temporal Networks

**核心问题**
- RQ（主线）：时间信息如何改变我们对真实网络结构与功能的理解？这种影响在不同类型网络中有何差异？
- RQ（检验）：文献中的若干时序网络假设，在哪些网络中成立、在哪些网络中不成立？

**原则**
- 主线是"时序网络的研究方法"，数据集是应用对象；不发明新模型。
- 每个分析写成"文献假设 → 指标 → 随机化对照（null model）"。
- 跨数据集只比较**归一化的"时间效应"**，不直接比较原始指标。
- 不强求每个数据集都用全部方法；方法与数据的匹配本身要在报告里论证。

---

## 0. 目录结构

```
final_project/
├── PLAN.md                 # 本文件
├── notes/                  # 文献笔记（每篇一段：问题/方法/结论/可用于本项目的点）
├── data/
│   ├── raw/                # 原始下载，只读
│   └── processed/          # 统一格式：events.csv (u, v, t[, duration])
├── src/                    # 可复用代码
│   ├── io.py               # 读取 + 统一格式
│   ├── aggregate.py        # 静态聚合、快照、窗口
│   ├── stats.py            # 增长、turnover、事件间隔、burstiness、持续性
│   ├── paths.py            # 时间可达性、时序中心性
│   ├── nullmodels.py       # 随机化对照
│   ├── spreading.py        # 时序 SI/SIR
│   └── growth.py           # PA kernel、年龄衰减（引用网络）
├── scripts/                # 每张图/表一个脚本，可一键复现
├── results/                # 中间结果 (csv/json)
├── figures/                # 报告用图 (pdf)
└── report/                 # LaTeX 报告（双栏、英文）
```

---

## 1. 文献调研（Related Work 的素材）

按三类问题整理，每类读 2–4 篇核心文献，笔记放在 `notes/`。

- [ ] **综述/框架**：Holme & Saramäki 2012（Phys. Rep.）；Holme 2015（EPJB）；Masuda & Lambiotte《A Guide to Temporal Networks》相关章节；Gauvin et al. 2022（SIAM Review，随机化对照）
- [ ] **主题 A：表示与聚合**：contact sequence / interval graph / snapshot；Krings et al. 2012（窗口大小与位置）；Ribeiro et al. 2013（时间分辨率）
- [ ] **主题 B：时间结构**：Barabási 2005、Goh & Barabási 2008（burstiness、memory）；Saramäki et al. 2014（关系持续性）；Kovanen et al. 2011、Paranjape et al. 2017（temporal motifs，可选）
- [ ] **主题 C：时间对功能的影响**：Holme 2005（可达性）；Pan & Saramäki 2011（时间路径）；Kim & Anderson 2012（时序中心性）；Karsai et al. 2011（burstiness 减慢传播）
- [ ] **演化/增长模型**（回应题目中的节点/连接出现与消失）：Barabási & Albert 1999；Dorogovtsev & Mendes 2000（aging）；Jeong et al. 2003、Newman 2001（测量 PA）；Leskovec et al. 2005（densification）；Wang, Song & Barabási 2013（引用老化）；Moore et al. 2006（含删除的模型）；Perra et al. 2012（activity-driven）
- [ ] 整理一张"文献 → 假设 → 本项目用到的方法"总表（直接作为 Related Work 的表 1）
- [ ] 写出 Related Work 结尾的 gap：已有工作多针对单一数据集或单一方法，缺少"同一框架下不同类型网络对时间信息的敏感度"的横向比较

## 2. 数据集

| 类型 | 数据集 | 来源 | 时间精度 | 用途 |
|---|---|---|---|---|
| 面对面接触 ×2 | SocioPatterns Primary School（Stehlé 2011）、High School 2013（Mastrandrea 2015） | sociopatterns.org | 20 s | 可达性、传播、null model、窗口；两个样本用于检验结论稳健性 |
| 在线通信 | CollegeMsg（Panzarasa 2009）、email-Eu-core-temporal | SNAP | 秒 | 事件间隔、burstiness、可达性、传播 |
| 论文引用 | cit-HepPh（附带 dates 文件） | SNAP | 日 | 增长、densification、PA kernel、老化 |
| 共同作者（可选） | 由 arXiv 元数据（hep-ph）自建 | Kaggle arXiv dataset | 日/月 | 重复合作、持续性、静态与时序排名比较 |

- [ ] 下载数据并记录来源、版本、许可证、下载日期
- [ ] 统一转换为 `events.csv (u, v, t[, duration])`，有向/无向单独标注
- [ ] 每个数据集写一段 data card：节点/事件数、时间跨度、时间精度、缺失与偏差
- [ ] ⚠️ SNAP 上的 `ca-HepPh` **没有时间戳**；合作网络若需要按时间分析，必须自建。若成本过高就放弃，改为加强接触网络的分析
- [ ] 清洗：去掉自环、重复事件，并截取观测窗口的首尾（排除边界效应）

## 3. 方法 × 数据矩阵（只做打 ✓ 的格子）

| 方法组 | 假设（文献） | 指标 | Null model | 接触 | 通信 | 引用 | 合作* |
|---|---|---|---|---|---|---|---|
| **M0 基础描述** | — | N(t), E(t)、活动量时间序列 | — | ✓ | ✓ | ✓ | ✓ |
| **M1 聚合与窗口** | 聚合和窗口选择会扭曲结构结论 | 度、聚类、连通分量、排名随 Δt 的变化 | — | ✓ | ✓ | ✓（年度 vs 累积） | ✓ |
| **M2a 突发性** | 活动是突发的，且有记忆 | 事件间隔分布、B、M | 打乱时间戳 | ✓ | ✓ | | |
| **M2b 持续性/turnover** | 关系重复且持久；网络在不断更替 | 边重复率、存续时间、相邻快照 Jaccard | 打乱时间戳 | ✓ | ✓ | | ✓ |
| **M2c 增长** | PA + 老化；densification | Π(k)∝k^α、年龄衰减、E∝N^a | BA / 无老化模型对照 | | | ✓ | (✓) |
| **M3a 可达性/路径** | 时间顺序限制可达性 | 时间可达比例、最快到达时间 | 打乱时间戳 / 打乱边 | ✓ | ✓ | | |
| **M3b 时序中心性** | 静态排名 ≠ 时序排名 | Kendall τ（静态 vs 时序 closeness） | — | ✓ | ✓ | | ✓ |
| **M3c 传播** | burstiness/时间相关性减慢传播 | SI 到达时间、SIR 最终规模 | 多种随机化 | ✓ | ✓ | | |

*合作网络为可选项。

**统一的"时间效应"指标**（用于跨数据集比较）
- 窗口敏感性：指标随 Δt 变化的相对幅度
- 可达性比值 R = 时间可达对数 / 静态可达对数
- 传播减速比 T_real / T_null（达到 50% 感染所需时间）
- 排名一致性 Kendall τ(static, temporal)
- 持续性：相邻快照的 Jaccard 均值
- 突发性 B 与 null 下 B 的差值

## 4. 实现

- [ ] `io.py` + 数据转换脚本，跑通全部数据集
- [ ] M0/M1：快照与窗口工具；Δt 网格（例如接触：5 min–1 day；通信：1 h–1 month；引用：1 年）
- [ ] M2：事件间隔、B、M；边持续性与 Jaccard
- [ ] M2c：PA kernel（Jeong 2003 方法：按 Δt 内新边的累积分布），老化曲线，densification 拟合
- [ ] M3a：时间可达性（按时间排序后扫描事件，计算 earliest arrival，O(E·N)）
- [ ] M3b：时序 closeness（基于最快到达时间）
- [ ] M3c：时序 SI/SIR（离散事件驱动；种子节点随机、重复 ≥100 次）
- [ ] Null models（按 Gauvin 2022 的命名）：
  - [ ] P[w,t] 打乱时间戳（保留静态图与事件数，破坏时间相关）
  - [ ] 保留每条边的事件序列，随机平移（破坏边之间的时间相关）
  - [ ] 打乱边/配置模型（破坏拓扑，保留时间序列）
- [ ] 每个 null model 生成 ≥20 个样本，报告均值 ± 标准差
- [ ] 小规模单元测试：用手造的小例子验证可达性和 SI 的正确性
- [ ] 固定随机种子，所有图由 `scripts/` 一键生成

工具：Python、`numpy/pandas/networkx/scipy/matplotlib`；需要时用 `teneto` 或 `raphtory` 交叉验证。

## 5. 结果与分析

- [ ] 每个 ✓ 格子产出一张图或一行表
- [ ] 汇总表：数据集 × 时间效应指标（报告的核心表）
- [ ] 稳健性：Δt 的选择、观测区间（前半段/后半段）、两个接触网络样本的对比
- [ ] 每个假设给出结论：支持 / 不支持 / 依赖数据类型或窗口
- [ ] Discussion 围绕四个问题：
  1. 哪些结论用静态网络就能得到？
  2. 哪些结论必须用时间窗口或完整事件顺序？
  3. 为什么不同网络对时间信息的敏感程度不同（结合数据的生成机制、时间尺度）？
  4. 结论是否依赖窗口、观测区间、随机化规则？
- [ ] 局限性：时间精度、观测边界、采样偏差、引用网络的退化性（DAG、无删除）

## 6. 报告写作（`report/`）

- [ ] Abstract（最后写）
- [ ] Introduction：动机、RQ、贡献
- [ ] Related Work：三类问题 + 演化模型 + 文献总表
- [ ] Data
- [ ] Methods：M1–M3 + null models + 时间效应指标
- [ ] Results：按方法组组织，每节末尾给跨数据集比较
- [ ] Discussion & Limitations
- [ ] Conclusion
- [ ] 图：统一配色与字号，单栏宽度为主，关键汇总图跨双栏
- [ ] 检查：引用格式、图表编号、页数要求（⚠️ 待确认老师的页数/格式要求）

## 7. 时间安排（截止日期待确认，按周倒推）

| 阶段 | 内容 | 占比 |
|---|---|---|
| 第 1 周 | 文献笔记 + 数据下载与清洗 + M0 | 20% |
| 第 2 周 | M1、M2 + null models | 30% |
| 第 3 周 | M3（可达性、中心性、传播）+ 稳健性 | 30% |
| 第 4 周 | 汇总、写作、修改 | 20% |

**最小可交付版本**（时间不够时）：接触网络 ×1 + 通信网络 ×1 + 引用网络；只做 M1、M2a、M3a、M3c。

## 8. 风险

- 合作网络自建成本高 → 设为可选
- 传播模拟太慢 → 先在接触网络上跑；通信网络可截取子时间段
- 范围膨胀 → 严格按矩阵执行，新想法放到 Future Work
- 待确认事项：页数限制、是否需要 presentation、是否要求提交代码、截止日期
