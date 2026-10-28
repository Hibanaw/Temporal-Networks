# PC5253 Final Project — 计划 v2（已被 PLAN.md v3 取代）

（旧版见 `PLAN_v1.md`）

**暂定题目**：How Much Does Time Matter? A Comparative Study of Aggregation, Temporal Patterns and Dynamics in Real-World Temporal Networks

## 核心问题

- **RQ1（主线）**：时间信息如何改变我们对真实网络结构与功能的理解？这种影响在不同类型网络中有何差异？
- **RQ2（检验）**：文献中的若干时序网络假设，在哪些网络中成立、在哪些网络中不成立？

## 原则

- 主线是"时序网络的研究方法"，数据集是应用对象；不发明新模型。
- 每个分析写成"文献假设 → 指标 → 随机化对照（null model）"。
- 跨数据集只比较**归一化的"时间效应"**，不直接比较原始指标。
- 方法尽量通用，能跑在所有适用数据集上；不适用的格子要在报告里说明理由。
- **有成熟库函数就用库**；每项功能只选一个库，不做多工具交叉验证。正确性靠手造小例子的单元测试保证。
- 两个案例研究（Case 2/3）作为主体结果之后的深度展示，回扣主线问题。
- 同质化的实验不做：每种设定只保留一个代表（见下方"缩减记录"）。

---

## 缩减记录（去掉同质化实验）

| 去掉 | 理由 | 保留的代表 |
|---|---|---|
| High School 2013 | 与小学同为学校、同为班级标签，结论高度重复 | Primary School（学校）+ Hospital（不同场景、角色标签） |
| email-Eu-core-temporal | 与 CollegeMsg 同为在线消息，且缺部门标签 | CollegeMsg |
| cit-HepPh / cit-HepTh 物理对照 | 与 AMiner 引用网络方法、问题相同 | AMiner CS 引用 |
| 多个 CS 子领域对照 | 同一数据同一方法重复跑 | 一个子领域 |
| null model P2"每条边事件序列平移" | 与"打乱时间戳"破坏的都是时间相关，结果相近 | P1 打乱时间戳 + P2 打乱边（原 P3），一个破坏时间、一个破坏拓扑 |
| SI 模型 | 确定传播的 SI 等价于 M3a 时间可达性 | SIR（联系课程内容） |
| M1 中的"中心性排名随 Δt" | 与 M3b 的静态/时序排名比较重复 | M3b |
| 合作网络上的 M3b（原可选） | 年分辨率下时序路径意义弱 | 接触、通信上的 M3b |
| Case 1（CollegeMsg 演化） | CollegeMsg 是唯一通信数据，主体结果已全面覆盖 | Case 2、Case 3 |

## 0. 目录结构

```
final_project/
├── PLAN.md
├── PLAN_v1.md
├── notes/                  # 文献笔记（每篇：问题/方法/结论/可用点）
├── data/
│   ├── raw/                # 原始下载，只读
│   └── processed/          # events.csv (u, v, t[, duration]) + nodes.csv (id, label)
├── src/
│   ├── io.py               # 读取 + 统一格式
│   ├── aggregate.py        # 静态聚合、快照、窗口
│   ├── stats.py            # 增长、turnover、事件间隔、B/M、持续性
│   ├── paths.py            # 时间可达性、时序中心性
│   ├── nullmodels.py       # 随机化对照
│   ├── spreading.py        # 时序 SIR
│   ├── growth.py           # PA kernel、老化、densification
│   └── community.py        # 动态/静态社区检测与比较
├── scripts/                # 每张图/表一个脚本，一键复现
├── results/                # 中间结果；各人输出 xxx_summary.csv
├── figures/
└── report/
    ├── main.tex
    └── sections/           # 按章节/部分分文件，用 \input 合入；段落负责人见第 9 节
```

**共享接口（第 0 天约定，之后各自独立）**
- 事件格式：`events.csv`，列 `u, v, t`（整数时间戳，秒或天），有向/无向在数据卡里标注；`nodes.csv` 存节点标签（班级、角色、部门等，用作社区真值）。
- null model 函数签名：`f(events: DataFrame, seed: int) -> DataFrame`，输入输出同格式。
- 结果汇总：`results/<owner>_summary.csv`，列 `dataset, metric, value, null_mean, null_std`。

---

## 1. 文献调研

按三类问题加演化与社区，每类 2–4 篇，笔记放 `notes/`。

- [ ] **综述/框架**：Holme & Saramäki 2012；Holme 2015；Masuda & Lambiotte 相关章节；Gauvin et al. 2022（随机化对照）
- [ ] **A 表示与聚合**：Krings 2012；Ribeiro 2013
- [ ] **B 时间结构**：Barabási 2005；Goh & Barabási 2008；Saramäki 2014；Kovanen 2011 / Paranjape 2017（可选）
- [ ] **C 时间对功能的影响**：Holme 2005；Pan & Saramäki 2011；Kim & Anderson 2012；Karsai 2011
- [ ] **D 演化/增长**：Barabási & Albert 1999；Dorogovtsev & Mendes 2000；Jeong 2003；Newman 2001；Leskovec 2005；Wang, Song & Barabási 2013；Moore 2006；Perra 2012
- [ ] **E 动态社区（新增）**：Mucha et al. 2010（多层模块度）；Greene et al. 2010 或 Rosvall & Bergstrom 2010（动态社区追踪）；Cazabet & Rossetti 综述（与所用库配套）
- [ ] 整理"文献 → 假设 → 方法"总表（Related Work 表 1）
- [ ] 写出 gap：已有工作多针对单一数据集或单一方法，缺少"同一框架下不同类型网络对时间信息的敏感度"的横向比较

## 2. 数据集

| 类型 | 数据集 | 来源 | 精度 | 标签（真值） |
|---|---|---|---|---|
| 面对面接触 ×2 | SocioPatterns Primary School（Gemmetto 2014 / Stehlé 2011）、Hospital Lyon（Vanhems 2013） | sociopatterns.org/datasets.html（CC BY-NC-SA） | 20 s | 班级 / 角色（NUR, PAT, MED, ADM） |
| 在线通信 | CollegeMsg（1899 节点, 59,835 事件, 193 天） | SNAP | 秒 | 无 |
| 计算机领域论文（主）| AMiner DBLP-Citation-network（V18：6,733,427 篇、73,702,758 条引用，2025-07-14；V14 为 5,259,858 / 36,630,661）。一份数据同时得到**引用网络**（references）和**合作网络**（authors + year），并带 venue、fos 可按子领域截取 | aminer.org/citation（另有 Kaggle 镜像 dblp.v12.json） | 年 | venue / fos（可作社区真值，可选）|
| 计算机领域合作（备选）| DBLP 官方 XML（dblp.xml.gz，CC0）自己解析；或 KONECT `dblp_coauthor`（边带发表日期；新版 1,824,701 节点 / 29,487,744 边，旧版 1,314,050 / 18,986,618，注意版本差异） | dblp.org/xml/release、konect.cc | 年 | — |

- [ ] 下载并记录来源、版本、许可证、下载日期
- [ ] 统一转换为 `events.csv` + `nodes.csv`
- [ ] 每个数据集一段 data card：节点/事件数、跨度、精度、偏差
- [ ] ⚠️ SNAP 的 `ca-HepPh` 没有时间戳，不要用
- [ ] ⚠️ SocioPatterns 许可是 CC BY-NC-SA（非商业、相同方式共享）；课程作业可用，但报告里要标注来源与许可。Hospital 的角色信息在接触文件里（NUR/PAT/MED/ADM），不是单独元数据文件；Primary School 有单独 metadata 文件
- [ ] ⚠️ AMiner 文件很大（单个 JSON，Kaggle 上 V12 标注为数 GB～12.5 GB），需流式解析（如 `ijson`）并先按 venue/fos 截取**一个** CS 子领域（例如数据库、网络、机器学习中的某一方向）再建网络。V17 页面上的引用数（5,103,745）与相邻版本量级不符，疑似页面笔误，**请以下载文件自身为准**
- [ ] 计算机领域数据的时间精度是**年**：适用 M0、M1、M2b（年度重复合作）、M2c、M4；不适用 M2a、M3（没有细粒度事件）
- [ ] 清洗：去自环、去重复事件、截取观测窗口首尾
- [ ] 第 0 天确认所有数据链接可下载；合作网络若 1 天内找不到合适来源，降级为可选

## 3. 方法 × 数据矩阵

| 方法组 | 假设（文献） | 指标 | Null model | 接触 | 通信 | 引用 | 合作 |
|---|---|---|---|---|---|---|---|
| **M0 基础描述** | — | N(t)、E(t)、活动量 | — | ✓ | ✓ | ✓ | ✓ |
| **M1 聚合与窗口** | 聚合与窗口选择扭曲结构结论 | 密度、度、聚类、连通分量随 Δt 变化（排名交给 M3b） | — | ✓ | ✓ | ✓（年度 vs 累积） | ✓ |
| **M2a 突发性** | 活动突发且有记忆 | 事件间隔分布、B、M | 打乱时间戳 | ✓ | ✓ | | |
| **M2b 持续性/turnover** | 关系重复持久、网络不断更替 | 边重复率、存续时间、相邻快照 Jaccard | 打乱时间戳 | ✓ | ✓ | | ✓ |
| **M2c 增长** | PA + 老化；densification | Π(k)∝k^α、年龄衰减、E∝N^a | 无老化 / BA 对照 | | | ✓ | ✓ |
| **M3a 可达性/路径** | 时间顺序限制可达性 | 时间可达比例、最快到达时间 | 打乱时间戳 / 打乱边 | ✓ | ✓ | | |
| **M3b 时序中心性** | 静态排名 ≠ 时序排名 | Kendall τ（静态 vs 时序 closeness） | — | ✓ | ✓ | | |
| **M3c 传播** | burstiness/时间相关性减慢传播 | SI 到达时间、SIR 最终规模 | 多种随机化 | ✓ | ✓ | | |
| **M4 动态社区** | 社区随时间形成/合并/拆分，静态划分会掩盖 | 快照模块度、社区数、相邻快照 NMI、动态 vs 静态 NMI、与真值 NMI | 打乱时间戳 | ✓ | ✓ | ✗（DAG，无意义） | ✓ |

**统一的"时间效应"指标**
- 窗口敏感性：指标随 Δt 变化的相对幅度
- 可达性比值 R = 时间可达对数 / 静态可达对数
- 传播减速比 T_real / T_null（达到 50% 感染所需时间）
- Kendall τ(static, temporal)
- 相邻快照 Jaccard 均值；相邻快照社区 NMI 均值
- B_real − B_null
- 动态社区与静态社区的 NMI

## 4. 库选择（每项功能一个库）

| 功能 | 选用库 | 备注 |
|---|---|---|
| 数据处理、统计、检验 | `pandas`、`numpy`、`scipy`（`kendalltau` 等） | |
| 静态图、中心性、聚类、连通分量 | `networkx` | |
| 社区检测（静态与每个快照） | `networkx.community`（Louvain）或 `leidenalg` + `python-igraph` | 二选一 |
| NMI / ARI | `scikit-learn` | `normalized_mutual_info_score` |
| 动态社区追踪与评估 | `tnetwork` | 提供快照图、动态社区算法与匹配 |
| 时间路径、可达性、时序中心性 | `raphtory`（PyPI 最新 0.17.0，已确认可用 `pip` 解析于 Python 3.13） | 备选 `teneto`（0.5.3）。**`pathpy3` 在 PyPI 上已无可装版本**，其继任者 `pathpyG` 需从 GitHub 安装且依赖 torch / torch-geometric，不建议；`tnetwork` 1.2 在 PyPI 可用 |
| 时序 SIR | 优先复用上面所选库自带功能，没有则用 `numpy` 自实现事件驱动版本 | 单元测试验证 |
| 重尾分布拟合（事件间隔、度、引用） | `powerlaw` | |
| null model | 自实现（按 Gauvin 2022，两种） | 无公认库 |
| PA kernel、老化曲线 | 自实现（Jeong 2003 方法） | 无公认库 |
| 作图 | `matplotlib`（可加 `seaborn`） | 统一配色与字号 |

- [ ] 第 0 天：建 conda/venv 环境，确认以上库在团队统一的 Python 版本上可装、可 import
- [ ] 单元测试：手造 5–10 个节点的小例子，验证可达性、SI、null model 的保持性质

## 5. 案例研究（回扣主线）

- **Case 2：动态社区演化（Primary School）** — 群体如何形成/变化/重组，对比静态与动态社区检测，用班级标签作真值；回答"静态结构是否掩盖了重组"。
- **Case 3：时间是否改变可达性（Hospital）** — 静态可达为 baseline，对比 time-respecting paths；回答"忽略时间顺序会高估多少传播范围"。

每个案例 0.5–1 页，主体结果放在前面，案例放在 Results 后半部分。

## 6. 五人分工（只安排实验与结果分析；摘要、引言、相关工作、讨论、结论等纯写作不在此安排）

每人负责一块**从数据到结果图表再到本块分析文字**的完整链路，代码、结果、报告小节都在自己名下，互不修改。

| 成员 | 实验模块 | 方法 | 数据 | 要回答的分析问题 | 产出（代码 / 结果 / 报告） |
|---|---|---|---|---|---|
| **A 接触与通信数据、聚合、汇总与稳健性** | 下载清洗并统一格式 3 个数据集（接触×2、通信×1）；基础描述；快照与窗口；跨网络汇总表；全组稳健性检查（前后半段） | M0、M1（接触、通信）；汇总表；稳健性 | 小学、Hospital、CollegeMsg | 聚合与窗口选择会改变哪些结论（密度、聚类、连通分量）？结论在哪个 Δt 范围内稳定？各假设的结论在前半段和后半段是否一致？ | `io.py`、`aggregate.py`、`data/processed/`、`a_summary.csv`、`scripts/make_summary_table.py`；`results_aggregation.tex`（接触/通信段）、`results_cross.tex`、Data 章数据卡 |
| **B 计算机领域论文数据（引用 + 合作）** | 解析 AMiner DBLP-Citation（流式），按 CS 子领域截取；构建引用网络与合作网络；增长与老化 | M0、M1（年度 vs 累积）、M2b（合作重复）、M2c；| AMiner CS 数据（一个子领域） | 优先连接是否成立（α 多大）？引用是否老化？网络是否 densification（指数 a）？合作关系的重复率与更替如何？ | `growth.py`、`cs_data.py`、`b_summary.csv`；`results_aggregation.tex`（论文网络段）、`results_activity.tex`（重复合作段）、`results_evolution.tex`（增长与老化段） |
| **C null model 与时间结构** | 实现两种 null model（P1、P2）并验证其保持性质；突发性、记忆、持续性、turnover | M2a、M2b（接触、通信）、null model 库 | 接触×2、通信×1（用 A 的数据） | 活动是否真的突发且有记忆（B、M 相对 null 差多少）？关系是否持久（边重复、Jaccard）？打乱时间戳后哪些量改变、哪些不变？ | `nullmodels.py`（第 1 周优先交付）、`stats.py`、`c_summary.csv`；`results_activity.tex`（突发性、持续性段）、Methods 随机化小节 |
| **D 路径、中心性与传播、Case 3** | 时间可达性、时序中心性、事件驱动 SIR；Hospital 案例 | M3a、M3b、M3c；Case 3 | 接触×2、通信×1 | 忽略时间顺序会高估可达范围多少（R 值）？静态与时序中心性排名有多一致（Kendall τ）？真实传播比 null 慢多少？Hospital 中不同角色的差别？ | `paths.py`、`spreading.py`、`d_summary.csv`；`results_function.tex`、`cases.tex`（Case 3）、Methods Part IV 小节 |
| **E 动态社区、Case 2** | 每快照社区检测、跨快照匹配、与静态划分和真值比较；小学案例 | M4；Case 2 | 接触×2、通信×1、合作（年度快照） | 动态社区与静态聚合划分差多少？社区稳定性（相邻 NMI）如何？与班级/角色真值吻合度多少？打乱时间戳后稳定性掉多少？结果对分辨率参数是否敏感？ | `community.py`、`e_summary.csv`；`results_evolution.tex`（动态社区段）、`cases.tex`（Case 2）、Methods 动态社区段 |

**每人的共同要求**
- 每块代码附小规模单元测试（手造例子）；随机种子固定；图由 `scripts/` 一键生成。
- 结果以统一格式输出 `results/<owner>_summary.csv`，列 `dataset, metric, value, null_mean, null_std`。
- 每人写自己那块的 Methods 小节与 Results 小节（含图表说明和分析），其余章节由全组之后统一整理。
- 跨数据集总表由 A 写一个 `scripts/make_summary_table.py` 读取各人的 summary 拼接，其他人只需保证格式正确。

**依赖与独立性安排**
- A 先交 `data/processed/`（目标：第 1 周前 3 天）。C、D、E 在此之前用 SocioPatterns 小学单个样本自行开发，函数写成"输入 `events.csv`，输出指标"，数据一到即可批量跑。
- C 先交 `nullmodels.py`（第 1 周内）。D、E 在此之前用"打乱时间戳"一行实现占位。
- B 完全独立：数据来源、网络类型、方法都与其他人不交叉，只需保持 summary 格式一致。
- E 的合作网络输入来自 B 的产出（年度快照），在 B 交付前先用接触、通信数据开发。

## 7. 实现清单

- [ ] 环境与库验证（第 0 天）
- [ ] `io.py` + 转换脚本，跑通所有数据集
- [ ] M0/M1：快照与窗口；Δt 网格（接触 5 min–1 day；通信 1 h–1 month；引用 1 年；合作 1 年）
- [ ] M2：事件间隔、B、M；边持续性与 Jaccard
- [ ] M2c：PA kernel（Jeong 2003：按 Δt 内新边累积分布）、老化、densification 拟合
- [ ] M3a/b/c：时间可达性、时序 closeness、事件驱动 SIR（种子随机，重复 ≥100 次；SI 在确定传播时等价于 M3a，不单独做）
- [ ] M4：每快照社区检测 → 跨快照匹配 → 与静态划分、真值比较
- [ ] Null models（Gauvin 2022）：
  - [ ] P1 打乱时间戳（保留静态图与事件数，破坏时间相关）
  - [ ] P2 打乱边/配置模型（破坏拓扑，保留时间序列）
- [ ] 每个 null 生成 ≥20 样本，报告均值 ± 标准差
- [ ] 固定随机种子；所有图由 `scripts/` 一键生成

## 8. 结果与分析

- [ ] 每个 ✓ 格子产出一张图或一行表
- [ ] 汇总表：数据集 × 时间效应指标（核心表）
- [ ] 稳健性：Δt 的选择、观测区间（前半/后半）、小学与医院两个接触网络互相对照
- [ ] 每个假设给结论：支持 / 不支持 / 依赖数据类型或窗口
- [ ] Discussion 四问：
  1. 哪些结论静态网络就能得到？
  2. 哪些必须用时间窗口或完整事件顺序？
  3. 为什么不同网络对时间的敏感度不同（生成机制、时间尺度、边语义）？
  4. 结论是否依赖窗口、观测区间、随机化规则？
- [ ] 局限性：时间精度、观测边界、采样偏差、引用网络的退化性（DAG、无删除）、社区检测对分辨率参数的敏感

## 9. 报告写作

**全文统一骨架**：四个部分 + 七个假设，在 Related Work、Methods、Results、Discussion 中按同一顺序出现。

| 部分 | 问题 | 假设 | 方法 | Results 文件（负责人） |
|---|---|---|---|---|
| I 表示与聚合 | 聚合和窗口会丢失什么？ | H1 | M0、M1 | `results_aggregation.tex`（A、B） |
| II 活动模式 | 互动是否突发、重复、持久？ | H2 突发/记忆；H3 持续/更替 | M2a、M2b | `results_activity.tex`（C、B） |
| III 结构演化 | 网络如何增长、老化、重组？ | H4 PA+老化+densification；H5 社区重组 | M2c、M4 | `results_evolution.tex`（B、E） |
| IV 功能 | 时间顺序是否改变可达性、中心性、传播？ | H6 可达性/中心性；H7 传播减速 | M3a–c | `results_function.tex`（D） |

- 每个 Results 小节结尾写一句"Verdict on Hx"；`results_cross.tex` 的表汇总 H1–H7 × 网络类型。
- Methods 的表 `tab:hypotheses` 合并了原来的"文献→假设→方法"表和"方法×数据"矩阵，Related Work 不再单独放表。
- 案例研究是独立一章（`cases.tex`），在 Results 之后、Discussion 之前，每个案例标明对应的假设。
- 每个 `.tex` 文件里用 `% Owner: X` 标出各段负责人；多人共用一个文件时只改自己的段落。

- [ ] Abstract（最后写）
- [ ] Introduction：动机、RQ、四个部分、贡献
- [ ] Related Work：四个部分 + 随机化对照，每小节标出对应的假设
- [ ] Data（表 `tab:data` 数据卡）
- [ ] Methods：表 `tab:hypotheses` + 四个部分 + null models + 时间效应指标（每个假设一个）
- [ ] Results：四个部分，每节末尾给出 verdict；最后是跨网络汇总表
- [ ] Case Studies：两个案例
- [ ] Discussion & Limitations
- [ ] Conclusion
- [ ] 图：统一配色字号，单栏为主，汇总图跨双栏
- [ ] 检查：引用格式、图表编号、页数（⚠️ 待确认老师的页数/格式要求）

## 10. 时间安排（截止日期待确认，按周倒推）

| 阶段 | A | B | C | D | E |
|---|---|---|---|---|---|
| 第 0 天 | 环境、库验证、数据链接确认、接口约定（全员） | | | | |
| 第 1 周 | 3 个数据集下载清洗、M0、交付 `data/processed/` | AMiner 解析与子领域截取、构建引用与合作网络、M0 | `nullmodels.py` 两种实现与测试并交付 | 在小学样本上实现可达性与 SIR，单元测试 | 在小学样本上实现快照社区检测与匹配 |
| 第 2 周 | M1 全数据集、Δt 网格 | M1、M2b、M2c（PA kernel、老化、densification） | M2a、M2b 全数据集、与 null 对比 | M3a、M3b 全数据集 | M4 全数据集、与静态划分和真值对比 |
| 第 3 周 | 汇总表脚本、稳健性（前后半段、两个接触网络互相对照） | 补充与完善 M2c 图表 | 稳健性（null 样本数、Δt） | M3c 传播与 null 对比、Case 3 | Case 2、分辨率参数敏感性 |
| 第 4 周 | 各自完成本块 Results 小节与图表，交 `*_summary.csv`；之后全组统一整理其余章节与全文 | | | | |

## 11. 风险与对策

- 合作网络数据难获取 → 第 0 天验证来源，不行则降级为可选，加强接触网络分析
- 传播模拟太慢 → 先接触网络；通信网络截取子时间段；必要时用库自带的快速实现
- `raphtory`/`tnetwork` 接口不稳或功能不足 → 用 `teneto` 或自实现，单元测试兜底（`pip index` 已确认两者均可在 Python 3.13 下解析，但尚未实际 import 测试）
- 社区检测结果对分辨率参数敏感 → 报告中固定参数并做一次敏感性检查
- 待确认：页数限制、是否需要 presentation、是否要求提交代码、截止日期
