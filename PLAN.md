# PC5253 Final Project — 计划 v3

（旧版见 `PLAN_v1.md`、`PLAN_v2.md`。v3 把数据集从 5 个减到 3 个，实验从 32 个减到 16 个，七个假设全部保留。v3.1 为 B 的引用网络部分补充 3 个实验，总数 19 个：CIT 是唯一的增长型网络，只有 2 个实验撑不起"演化"这一部分的结论。）

**暂定题目**：How Much Does Time Matter? A Comparative Study of Aggregation, Temporal Patterns and Dynamics in Real-World Temporal Networks

## 核心问题

- **RQ1（主线）**：时间信息如何改变我们对真实网络结构与功能的理解？这种影响在不同类型网络中有何差异？
- **RQ2（检验）**：文献中的若干时序网络假设，在哪些网络中成立、在哪些网络中不成立？

## 原则

- 主线是"时序网络的研究方法"，数据集是应用对象；不发明新模型。
- 每个分析写成"文献假设 → 指标 → 随机化对照（null model）"。
- 跨数据集只比较**归一化的"时间效应"**，不直接比较原始指标。
- **每种网络类型只用一个数据集**，三个数据集在时间尺度和生成机制上互不相同（秒级接触、秒级在线消息、年级引用）。
- **有成熟库函数就用库**；每项功能只选一个库。正确性靠手造小例子的单元测试保证。
- 不设独立的案例研究章节；需要深入展示的内容放进对应的 Results 小节。

---

## 缩减记录

**v3 → v3.1（补强 B 的 CIT 部分，不新增数据集、不新增假设）**

| 增加 | 理由 |
|---|---|
| H4 由 1 个实验拆成 4 个（PA kernel、老化、densification + 直径、引用动力学拟合） | H4 是 CIT 上唯一的检验，原来一个实验同时塞 PA、老化、densification 三件事，每件都做不深；拆开后每个机制各有指标和 null，可单独下结论 |
| 新增 null P3（引用目标重抽样） | CIT 没有 P1/P2 可用，H4 缺对照；P3 让"PA 是否存在""老化是否存在"成为可检验的差异，而非只报拟合指数 |
| 引用动力学拟合（Wang–Song–Barabási 2013） | 与 PS/CM 的 H2（突发/记忆）对应：同样问"时间结构是否可由少数参数刻画"，让 CIT 与另两个数据集在汇总表里可以并列 |


**v2 → v3（减半）**

| 去掉 | 理由 |
|---|---|
| Hospital Lyon 接触数据 | 与小学同为 SocioPatterns 面对面接触，同一类型只留一个；小学有班级标签，可作社区真值 |
| AMiner 合作网络 | 年分辨率，只能做 H3、H4、H5 的重复验证；引用网络已经代表"增长型网络" |
| 案例研究章节（Case 2、Case 3） | 只剩一个接触数据集后，案例与主体结果重复；深入分析直接写进 Results |
| M0 作为单独实验 | 基础描述并入 Data 章（数据卡 + 活动量时间序列图） |

**v1/v2 → v2（去掉同质化）**：High School 2013、email-Eu-core、cit-HepPh/HepTh、多子领域对照、"边序列平移" null model、SI 模型（确定传播时等价于可达性）、M1 中的排名分析（与 M3b 重复）、CollegeMsg 案例。

---

## 0. 目录结构

```
final_project/
├── PLAN.md
├── PLAN_v1.md, PLAN_v2.md
├── notes/                  # 文献笔记（每篇：问题/方法/结论/可用点）
├── data/
│   ├── raw/                # 原始下载，只读
│   └── processed/          # events.csv (u, v, t[, duration]) + nodes.csv (id, label)
├── src/
│   ├── io.py               # 读取 + 统一格式
│   ├── aggregate.py        # 静态聚合、快照、窗口
│   ├── stats.py            # 事件间隔、B/M、持续性、turnover
│   ├── paths.py            # 时间可达性、时序中心性
│   ├── nullmodels.py       # 随机化对照 P1、P2
│   ├── spreading.py        # 时序 SIR
│   ├── growth.py           # PA kernel、老化、densification
│   └── community.py        # 动态/静态社区检测与比较
├── scripts/                # 每张图/表一个脚本，一键复现
├── results/                # 中间结果；各人输出 <owner>_summary.csv
├── figures/
└── report/                 # Overleaf 同步的 LaTeX 项目
    ├── main.tex
    └── sections/           # 按章节/部分分文件；段落负责人见第 8 节
```

**共享接口（第 0 天约定）**
- 事件格式：`events.csv`，列 `u, v, t`（整数时间戳，秒或年），有向/无向在数据卡里标注；`nodes.csv` 存节点标签（小学的班级，用作社区真值）。
- null model 函数签名：`f(events: DataFrame, seed: int) -> DataFrame`，输入输出同格式。
- 结果汇总：`results/<owner>_summary.csv`，列 `dataset, metric, value, null_mean, null_std`。

---

## 1. 文献调研

每类 2–4 篇，笔记放 `notes/`。

- [ ] **综述/框架**：Holme & Saramäki 2012；Holme 2015；Masuda & Lambiotte 相关章节；Gauvin et al. 2022（随机化对照）
- [ ] **I 表示与聚合**：Krings 2012；Ribeiro 2013
- [ ] **II 活动模式**：Barabási 2005；Goh & Barabási 2008；Saramäki 2014
- [ ] **III 结构演化**：Barabási & Albert 1999；Dorogovtsev & Mendes 2000；Jeong 2003；Leskovec 2005；Wang, Song & Barabási 2013；动态社区 Mucha 2010、Greene 2010
- [ ] **IV 功能**：Holme 2005；Pan & Saramäki 2011；Kim & Anderson 2012；Karsai 2011
- [ ] 写出 gap：已有工作多针对单一数据集或单一方法，缺少"同一框架下不同类型网络对时间信息的敏感度"的横向比较

## 2. 数据集（3 个）

| 简称 | 类型 | 数据集 | 来源 | 精度 | 标签 |
|---|---|---|---|---|---|
| **PS** | 面对面接触 | SocioPatterns Primary School（Stehlé 2011 / Gemmetto 2014），约 2 天 | sociopatterns.org（CC BY-NC-SA） | 20 s | 班级 |
| **CM** | 在线通信 | CollegeMsg（1,899 节点，59,835 事件，193 天） | SNAP | 1 s | 无 |
| **CIT** | 论文引用 | AMiner DBLP-Citation-network，截取**一个** CS 子领域 | aminer.org/citation（或 Kaggle 镜像） | 1 年 | — |

- [ ] 下载并记录来源、版本、许可证、下载日期
- [ ] 统一转换为 `events.csv` + `nodes.csv`；去自环、去重复、截取观测窗口首尾
- [ ] 每个数据集一段 data card（节点/事件数、跨度、精度、偏差），并画活动量时间序列（原 M0）
- [ ] ⚠️ SocioPatterns 许可 CC BY-NC-SA，报告中标注来源与许可
- [ ] ⚠️ AMiner 文件很大（数 GB～十余 GB 的单个 JSON），需流式解析（`ijson`），先按 venue/fos 截取子领域再建网络；以下载文件自身的统计为准
- [ ] 第 0 天确认三个链接都能下载；AMiner 若第 1 周内解析不顺，退回 SNAP `cit-HepPh`（带日期、体积小，Leskovec 2005 也用过，可直接对照文献）

## 3. 实验矩阵（19 个）

一个"实验" = 一个方法在一个数据集上做一次（含与 null model 的对比）。

| 部分 | 假设 | 方法 | 指标 | Null | PS | CM | CIT | 数量 | 负责人 |
|---|---|---|---|---|---|---|---|---|---|
| I | H1 聚合与窗口改变结构结论 | M1 | 密度、度、聚类、连通分量随 Δt 变化；CIT 为年度 vs 累积 | — | ✓ | ✓ | ✓ | 3 | A（PS、CM）、B（CIT） |
| II | H2 活动突发且有记忆 | M2a | 事件间隔分布、B、M | P1 | ✓ | ✓ | | 2 | C |
| II | H3 关系重复持久、网络不断更替 | M2b | 边重复率、存续时间、相邻快照 Jaccard | P1 | ✓ | ✓ | | 2 | C |
| III | H4a 优先连接（PA） | M2c-1 | 引用概率核 Π(k)∝k^α（Jeong 2003），α 及其置信区间 | P3 | | | ✓ | 1 | B |
| III | H4b 老化：旧论文被引概率衰减 | M2c-2 | 被引概率 vs 论文年龄；对数正态 vs 指数 vs 幂律衰减（AIC）；按发表年代分 cohort 比较 | P3 | | | ✓ | 1 | B |
| III | H4c densification 与直径收缩 | M2c-3 | E∝N^a 的 a；有效直径随年份变化（Leskovec 2005） | P3 | | | ✓ | 1 | B |
| III | H4d 引用动力学可由少数参数刻画 | M2c-4 | 拟合 Wang–Song–Barabási：fitness λ、immediacy μ、longevity σ；坍缩检验；用前 5 年预测最终引用数 | 无老化的 PA 基线 | | | ✓ | 1 | B |
| III | H5 社区随时间重组，静态划分会掩盖 | M4 | 相邻快照 NMI、动态 vs 静态 NMI、与班级真值 NMI | P1 | ✓ | ✓ | | 2 | E |
| IV | H6a 时间顺序限制可达性 | M3a | 可达比值 R、最快到达时间 | P1、P2 | ✓ | ✓ | | 2 | D |
| IV | H6b 静态排名 ≠ 时序排名 | M3b | Kendall τ（静态 vs 时序 closeness） | — | ✓ | ✓ | | 2 | E |
| IV | H7 时间相关性减慢传播 | M3c | SIR：达到峰值时间比 T_real/T_null、最终规模 | P1、P2 | ✓ | ✓ | | 2 | D |
| | | | | | | | | **19** | |

**P3 的定义**（只用于 CIT）：保持每篇论文的发表年份和参考文献数不变，每条引用的目标改为"当时已存在论文"中随机抽取——P3a 均匀抽取（既无 PA 也无老化），P3b 只按论文年龄加权（有老化、无 PA）。P3a 与真实网络之差检验 PA 和老化，P3b 与真实网络之差单独检验 PA。

不做的格子及理由（写进报告）：CIT 是年分辨率的 DAG，没有细粒度事件，不做 M2a/M2b/M3；引用边不消失、没有社区重组的含义，不做 M4；PS 和 CM 没有"新节点持续加入"的增长过程，不做 M2c。

**每个假设一个"时间效应"指标**（用于跨网络汇总表）
- H1 窗口敏感性（指标在 Δt 网格上的相对变化幅度）
- H2 B_real − B_null
- H3 相邻快照 Jaccard 均值
- H4 指数 α（PA）、老化衰减的最佳形式与时间尺度、a（densification）、(λ, μ, σ)
- H5 相邻快照 NMI 均值、动态 vs 静态 NMI
- H6 可达比值 R、Kendall τ
- H7 T_real / T_null

## 4. 库选择（每项功能一个库）

| 功能 | 选用库 | 备注 |
|---|---|---|
| 数据处理、统计、检验 | `pandas`、`numpy`、`scipy` | |
| 静态图、中心性、聚类、连通分量 | `networkx` | |
| 社区检测 | `leidenalg` + `python-igraph`（或 `networkx` Louvain，二选一） | |
| NMI | `scikit-learn` | |
| 动态社区追踪 | `tnetwork` | |
| 时间路径、可达性、时序中心性 | `raphtory` | 备选 `teneto` |
| 时序 SIR | 所选库自带，没有则 `numpy` 自实现事件驱动版本 | |
| 重尾分布拟合 | `powerlaw` | |
| null model、PA kernel | 自实现 | 无公认库 |
| 作图 | `matplotlib` | 统一配色与字号 |

- [ ] 第 0 天：统一 Python 环境，确认以上库可装、可 import
- [ ] 单元测试：手造 5–10 个节点的小例子，验证可达性、SIR、null model 的保持性质

## 5. 五人分工

| 成员 | 实验 | 数 | 另外的工作 | 产出 |
|---|---|---|---|---|
| **A 数据、聚合、汇总** | M1 on PS、CM | 2 | 下载清洗 PS、CM；三个数据集的 data card 与活动量图；跨网络汇总表；全组稳健性检查（前半段 vs 后半段） | `io.py`、`aggregate.py`、`data/processed/`、`scripts/make_summary_table.py`；`data.tex`、`results_aggregation.tex`（PS/CM 段）、`results_cross.tex` |
| **B 引用网络** | M1 on CIT；M2c-1～M2c-4 on CIT | 5 | AMiner 流式解析与子领域截取（或退回 cit-HepPh）；实现 P3 | `cs_data.py`、`growth.py`（含 P3）；`results_aggregation.tex`（CIT 段）、`results_evolution.tex`（增长段） |
| **C null model 与活动模式** | M2a、M2b on PS、CM | 4 | 实现 P1、P2 并测试保持性质（第 1 周交付） | `nullmodels.py`、`stats.py`；`results_activity.tex`、Methods 随机化小节 |
| **D 可达性与传播** | M3a、M3c on PS、CM | 4 | SIR 计算量最大（≥100 种子 × 2 种 null × ≥20 样本） | `paths.py`（可达性部分）、`spreading.py`；`results_function.tex`（可达性、传播段） |
| **E 社区与中心性** | M4、M3b on PS、CM | 4 | 社区跨快照匹配；分辨率参数敏感性 | `community.py`、时序 closeness（调用 D 的 `paths.py`）；`results_evolution.tex`（社区段）、`results_function.tex`（中心性段） |

A 的实验数少，但承担数据整理和汇总；B 的 5 个实验全在同一数据集上，共用同一张引用图，边际成本低于其他人的跨数据集实验。

**共同要求**
- 代码附单元测试；随机种子固定；图由 `scripts/` 一键生成。
- 结果输出 `results/<owner>_summary.csv`（格式见第 0 节）。
- 每人写自己那块的 Methods 和 Results 段落（含图表说明和分析）。

**依赖安排**
- A 第 1 周前 3 天交 `data/processed/`；之前 C、D、E 直接用 SocioPatterns 小学原始文件开发。
- C 第 1 周内交 `nullmodels.py`；之前 D、E 用"打乱时间戳"一行实现占位。
- D 第 1 周内交 `paths.py` 的最快到达时间函数，E 的时序 closeness 依赖它。
- B 完全独立（P3 自己实现，不依赖 C），只需保持 summary 格式一致。

## 6. 实现清单

- [ ] 环境与库验证（第 0 天）
- [ ] `io.py` + 转换脚本，跑通 3 个数据集
- [ ] M1：快照与窗口；Δt 网格（PS 5 min–1 day；CM 1 h–1 month；CIT 1 年）
- [ ] M2a/M2b：事件间隔、B、M；边持续性与 Jaccard
- [x] M2c-1：PA kernel（Jeong 2003），按年份累积"被引前度数 → 新增引用"的计数
- [x] M2c-2：老化曲线与三种衰减形式的拟合比较（`powerlaw` 库的分布比较或自写 AIC）；按 cohort 分组
- [x] M2c-3：densification 拟合 E∝N^a；有效直径（90% 分位）逐年计算，大图用抽样 BFS
- [x] M2c-4：WSB 模型拟合（每篇论文的累积引用曲线，按数据下载自带的年份）；用前 5 年预测最终引用数，与基线（累积引用数线性外推）比较
- [x] P3a/P3b 实现与单元测试：手造小 DAG 验证发表年份、参考文献数不变
- [ ] M3a/M3b/M3c：时间可达性、时序 closeness、事件驱动 SIR（≥100 个随机种子）
- [ ] M4：每快照社区检测 → 跨快照匹配 → 与静态划分、班级真值比较
- [ ] Null models（Gauvin 2022）：P1 打乱时间戳（保留静态图，破坏时间相关）；P2 打乱边（保留事件时间，破坏拓扑）；每个 ≥20 样本，报告均值 ± 标准差

## 7. 结果与分析

- [ ] 19 个实验各产出一张图或一行表
- [ ] 汇总表：H1–H7 × 三个数据集的时间效应指标（核心表）
- [ ] 稳健性：Δt 的选择、观测区间（前半/后半）、null model 的选择、社区分辨率参数
- [ ] 每个假设给结论：支持 / 不支持 / 依赖数据类型或窗口
- [ ] Discussion 四问：
  1. 哪些结论静态网络就能得到？
  2. 哪些必须用时间窗口或完整事件顺序？
  3. 为什么不同网络对时间的敏感度不同（生成机制、时间尺度、边语义）？
  4. 结论是否依赖窗口、观测区间、随机化规则？
- [ ] 局限性：每类只有一个数据集（结论的普遍性有限）、时间精度、观测边界、引用网络的退化性（DAG、无删除）

## 8. 报告结构

全文用同一骨架：四个部分 + 七个假设，在 Related Work、Methods、Results、Discussion 中按同一顺序出现。

| 部分 | 问题 | 假设 | Results 文件（负责人） |
|---|---|---|---|
| I 表示与聚合 | 聚合和窗口会丢失什么？ | H1 | `results_aggregation.tex`（A、B） |
| II 活动模式 | 互动是否突发、重复、持久？ | H2、H3 | `results_activity.tex`（C） |
| III 结构演化 | 网络如何增长、老化、重组？ | H4、H5 | `results_evolution.tex`（B、E） |
| IV 功能 | 时间顺序是否改变可达性、中心性、传播？ | H6、H7 | `results_function.tex`（D、E） |

- 每个 Results 小节结尾写 "Verdict on Hx"；`results_cross.tex` 汇总 H1–H7 × 数据集。
- Methods 的表 `tab:hypotheses` 同时给出文献、方法、null model 和适用数据集。
- 每个 `.tex` 文件用 `% Owner: X` 标出段落负责人；共用文件时只改自己的段落。
- [ ] Abstract（最后写）、Introduction、Related Work、Data、Methods、Results、Discussion & Limitations、Conclusion
- [ ] 检查：引用格式、图表编号、页数（⚠️ 待确认老师的页数/格式要求）

## 9. 时间安排（截止日期待确认，按周倒推）

| 阶段 | A | B | C | D | E |
|---|---|---|---|---|---|
| 第 0 天 | 环境、库验证、数据链接确认、接口约定（全员） | | | | |
| 第 1 周 | PS、CM 下载清洗，data card，交付 `data/processed/` | AMiner 解析与截取，建引用网络 | `nullmodels.py` 实现、测试、交付 | 在 PS 上实现可达性，交付最快到达函数 | 在 PS 上实现快照社区检测与匹配 |
| 第 2 周 | M1 on PS、CM | M1 on CIT；P3；M2c-1、M2c-2 | M2a、M2b on PS、CM | M3a on PS、CM；SIR 实现与测试 | M4 on PS、CM；M3b on PS、CM |
| 第 3 周 | 汇总表脚本；稳健性（前后半段） | M2c-3、M2c-4；稳健性（子领域选择、观测窗口截断、P3 样本数） | 稳健性（null 样本数、Δt） | M3c on PS、CM | 分辨率参数敏感性 |
| 第 4 周 | 各自完成 Results 段落与图表；全组统一整理其余章节与全文 | | | | |

## 10. 风险与对策

- AMiner 解析困难 → 第 1 周末前退回 cit-HepPh
- M2c-4 拟合不收敛或 CIT 论文太少 → 只拟合被引数 ≥ 阈值的论文；仍不行则只保留 M2c-1～M2c-3（总数 18）
- SIR 太慢 → 减少 null 样本数或截取 CM 的子时间段
- `raphtory`/`tnetwork` 功能不足 → 用 `teneto` 或自实现，单元测试兜底
- 每类只有一个数据集 → 在 Discussion 中明确说明，结论表述为"在本数据中"
- 待确认：页数限制、是否需要 presentation、是否要求提交代码、截止日期


## B 完成记录（2026-10-28）

B 的五项实验（M1/CIT、M2c-1～4）已完成；以上勾选表示实验与交付完成，假设结论以实测报告为准。M1 的全组复选框仍待 PS/CM 完成后统一更新。

- 数据：AMiner V14，完整扫描 5,259,858 条记录，数据库 venue 家族子图含 19,150 篇论文、73,269 条严格年份引用。
- 对照：P3a/P3b 各 20 份，保持性质、原始边核算、预测防泄漏审计及 13 项单元测试通过。
- 执行：准备 1500299 与串行主作业 1500361 均退出 0；单次主作业依次完成实验、绘图、校验、归档。
- 结果：`B_RESULTS.md`、`results/b_summary.csv`、`results/b/`、`figures/b_*`。
- 报告：`report/b_report.pdf` 为 8 页 B 独立报告；主报告 B 数据卡、Methods、Results 已填写。
- 实测结论：支持次线性度数偏好和年龄依赖；全期观察到稠密化，但未检测到有效直径收缩；WSB 的紧凑拟合不等于确立其对线性外推的预测优势。
- 保存：本地项目与 HPC 持久目录均已归档；6,079,589,707 字节原始文件的本地、工作与持久副本 SHA-256 一致。详见 `results/b/COMPLETION_AUDIT.md`。
