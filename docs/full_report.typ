#set document(title: [水热法制备纳米 $"TiO"_2$ 及光催化降解罗丹明 B 实验报告], author: "madSUNitist")

#set text(
  font: "Source Han Sans SC",
  weight: 300,
  size: 12pt,
  // lang: "zh",
)
#set par(first-line-indent: 2em)

#show heading: it => {
  set text(font: "Source Han Serif", weight: "bold")
  v(1em, weak: true)
  it
  v(1em, weak: true)
}
#set heading(numbering: "1.")

#align(center)[
  #text(font: "Source Han Serif", size: 18pt, weight: "bold")[水热法制备纳米 $"TiO"_2$ 及光催化降解罗丹明 B]
  #v(1em)
  #text(font: "Source Han Serif", size: 16pt, weight: "bold")[实验报告]
]

#v(2em)

= 实验原理 <sec:principle>

== $"TiO"_2$ 纳米材料概述 <sec:overview>

二氧化钛 ( $"TiO"_2$ ) 是光催化领域最广泛研究的半导体材料之一, 以其化学及生物惰性、低成本、环境友好和优异的光催化活性著称 @jawale2025enhanced @tee2024structurally。作为基准光催化剂, $"TiO"_2$ 在环境修复和能源转换方面提供了出色的解决方案 @tee2024structurally。

$"TiO"_2$ 在自然界中主要以三种晶型存在：金红石型 (Rutile, 四方晶系) 、锐钛矿型 (Anatase, 四方晶系) 和板钛矿型 (Brookite, 斜方晶系) , 对应的带隙能量分别约为 3.0 eV、3.2 eV 和 3.4 eV @jawale2025enhanced。这三种结构均由 $"TiO"_6$ 八面体通过不同方式共享顶点和棱边构成。金红石相是热力学最稳定的 $"TiO"_2$ 相, 但锐钛矿相因其更高的比表面积和更强的光生电荷分离能力, 通常表现出更优异的光催化活性 @alam2025xray @jawale2025enhanced。研究表明, 锐钛矿/金红石混合相体系可提供比纯相更高的光催化活性, 这归因于两相之间的协同效应和能带排列促进了电荷分离 @jawale2025enhanced。

高性能光催化剂应具备三个关键特性：合适的带隙能量、合适的能级位置以及高效的电荷分离能力。$"TiO"_2$ 在前两方面表现良好, 但第三方面 --- 抑制光生电子和空穴的复合 --- 仍需要通过合成策略和改性手段进行调控 @jawale2025enhanced @tee2024structurally。

== $"TiO"_2$ 光催化原理 <sec:photocatalysis>

光催化的理论基础是半导体能带理论。半导体的能带由充满电子的价带 (Valence Band, VB) 和空的导带 (Conduction Band, CB) 构成, 价带和导带之间的能量间隙称为禁带。当能量大于或等于 $"TiO"_2$ 带隙能 ($E_g$) 的紫外光照射半导体时, 价带上的电子跃迁至导带, 同时在价带上产生带正电的空穴 ($h^+$) , 形成电子-空穴对 ($e^- \/ h^+$) ：

$ "TiO"_2 + h nu -> "TiO"_2 (e^- + h^+) $

在极短的时间 (ps 量级) 内, 光生电子和空穴迁移至 $"TiO"_2$ 表面参与氧化还原反应。表面吸附的氧分子是有效的电子捕获剂, 与光生电子反应生成超氧阴离子自由基 ($"O"_2^(-) dot.c$) ; 同时, 表面吸附的水分子和氢氧根离子被价带空穴氧化, 生成羟基自由基 ($dot.c "OH"$) ：

$ "O"_2 + e^- &-> "O"_2^- dot.c \ 
"H"_2"O" + h^+ &->  dot.c "OH" + "H"^+ $

$dot.c "OH"$ 和 $"O"_2^- dot.c$ 是降解有机污染物的主要活性氧物种。此外, 光生空穴本身也可直接氧化有机物分子 @tee2024structurally。然而, $"TiO"_2$ 光催化剂的主要缺陷在于光生载流子的高复合率、较低的电子导电性以及仅在紫外光区的吸收限制 (仅可吸收不足 5% 的太阳光谱) @tee2024structurally。因此, 增强可见光吸收、改善电荷分离和传输效率以及确保催化稳定性是当前 $"TiO"_2$ 光催化研究的前沿方向 @tee2024structurally。

诸多因素可显著影响 $"TiO"_2$ 的光催化性能, 包括结晶度、晶相组成、比表面积、暴露晶面和表面形貌 @jawale2025enhanced。锐钛矿型 $"TiO"_2$ 因其较强光活性和催化性能, 广泛应用于染料敏化太阳能电池、光降解、环境修复、水分解和自清洁表面等领域 @alam2025xray。

== 水热法制备原理 <sec:hydrothermal>

水热法 (Hydrothermal Method) 是制备 $"TiO"_2$ 纳米材料的重要合成方法之一 @jawale2025enhanced。该方法在密闭容器中以水为反应介质, 在一定温度和自生压强下进行化学反应。与化学气相沉积 (CVD) 、溶胶-凝胶法等合成路线相比, 水热法制备 $"TiO"_2$ 在高温高压下一次完成, 无需后期晶化处理, 所得粉体粒度分布窄、团聚程度低、成分纯净, 且制备过程污染小 @jawale2025enhanced。

合成方法、实验参数和晶体结构构型对 $"TiO"_2$ 纳米材料的最终特性具有显著影响 @alam2025xray。通过调节反应时间、温度和前驱体浓度等参数, 可以实现对 $"TiO"_2$ 纳米结构的形貌、尺寸和晶相组成的精确调控 @jawale2025enhanced。

本实验以钛酸正丁酯 ($"Ti"("OC"_4"H"_9)_4$) 为钛源, 以氯化铵 ($"NH"_4"Cl"$) 为形貌控制剂, 在 160 $degree"C"$ 水热条件下反应 8 小时制备纳米 $"TiO"_2$ 。

== 纳米材料表征方法 <sec:characterization>

=== X 射线粉末衍射 (XRD) <sec:xrd>

X 射线粉末衍射 (XRD) 是表征纳米材料晶相结构和晶粒尺寸的基础技术 @nasiri2023modified @alam2025xray。当一束单色 X 射线照射晶体时, 由于晶体具有周期性结构, 当晶面间距 $d_("hkl")$ 与 X 射线入射角 $theta$ 之间满足布拉格 (Bragg) 方程时产生衍射：

$ 2d_("hkl") sin theta = lambda $

其中 $lambda$ 为 X 射线波长, $2theta$ 为衍射角, $d_("hkl")$ 为 Miller 指数为 $("hkl")$ 的晶面间距。不同物相的粉末衍射峰在数目、位置和强度上具有特征性, 通过比对 ICDD/JCPDS 标准卡片可进行物相定性鉴定。定量分析方面, 可采用全粉末图拟合 (WPPF) 方法进行 Rietveld 精修, 精确确定多相体系中各组分的含量比和晶体结构参数 @alam2025xray。

晶粒尺寸 ($D$) 可通过 Scherrer 公式估算 @bokuniaeva2019estimation：

$ D = (k lambda) / (beta cos theta) $

其中 $k$ 为 Scherrer 常数 (通常取 0.89) , $lambda$ 为 X 射线波长, $beta$ 为衍射峰半高宽 (弧度) , $theta$ 为布拉格衍射角。Scherrer 公式自 1918 年提出以来被广泛使用 @nasiri2023modified。然而, 传统 Scherrer 公式仅使用单一衍射峰进行计算, 误差较大。改进的 Scherrer 方法 (Modified Scherrer method) 通过综合考虑全部衍射峰的信息, 可获得更高精度的晶粒尺寸值, 其结果与透射电子显微镜 (TEM) 和 BET 法的测量值具有良好的一致性 @nasiri2023modified。此外, Debye 方程和 Williamson-Hall 图作为补充方法, 可用于区分晶粒尺寸效应和晶格应变对衍射峰宽化的贡献 @bokuniaeva2019estimation @alam2025xray。

应当注意的是, 由 XRD 计算的晶粒尺寸指的是相干衍射域的大小, 由于纳米颗粒常以多晶聚集体的形式存在, 晶粒尺寸通常不等于一次颗粒的粒径 @nasiri2023modified。

=== 扫描电子显微镜 (SEM) <sec:sem>

扫描电子显微镜 (SEM) 是最直接的纳米粒子形貌和粒径观察方法。通过测量图像中单个颗粒的尺寸乘以相应的放大倍数, 可直接得到实际粒径。SEM 微观形貌观察结果与 XRD 法计算结果可相互验证。此外, 颗粒的团聚程度、分散状态和表面拓扑结构均可通过 SEM 进行直观评价。

= 实验目的 <sec:purpose>

+ 了解水热法制备 $"TiO"_2$ 的一般原理及光催化降解典型污染物的原理
+ 掌握制备纳米 $"TiO"_2$ 过程中反应条件的选择和控制
+ 掌握光催化降解典型污染物的操作过程和催化性能评价方法
+ 了解并掌握材料的常规表征手段 (XRD、SEM)
+ 综合训练化学实验的基本操作技能

= 仪器和试剂 <sec:equipment>

== 仪器 <sec:instruments>

- 量筒、烧杯、磁力搅拌器
- 超声波清洗机
- 离心机、抽滤装置
- 恒温水浴锅、烘箱
- 不锈钢晶化釜 (聚四氟乙烯内衬)
- LED 光催化反应器 (10 W, 280 nm UV LED, 25 $degree"C"$, 200 RPM 磁力搅拌)
- X 射线衍射仪 (德国布鲁克公司 D8 FOCUS, $"Cu" "K"alpha$, $lambda = 1.5406 angstrom$, $40.0 "kV" times 40.0 "mA"$)
- 扫描电子显微镜 (SEM)
- 紫外可见光分光光度计 (检测波长 554 nm)

== 试剂 <sec:reagents>

- 钛酸正丁酯 ($"Ti"("OC"_4"H"_9)_4$)
- 氯化铵 ($"NH"_4"Cl"$)
- 无水乙醇 ($"C"_2"H"_5"OH"$)
- 罗丹明 B (Rhodamine B, $"C"_28"H"_31"ClN"_2"O"_3$)

= 实验步骤 <sec:procedure>

== $"TiO"_2$ 纳米粒子的制备 <sec:synthesis>

+ 配制 40 mL 氯化铵水溶液：称取 $0.396 "g"$ $"NH"_4"Cl"$ (理论 $0.391 "g"$) 溶于 40 mL 去离子水。计算过程：
$ n("Ti"("OC"_4"H"_9)_4) &= (10 "mL" times 0.996 "g/mL") / (340.32 "g/mol") \ 
&approx 0.0293 "mol" \ 
n("NH"_4"Cl") &= 0.25 times n("Ti"("OC"_4"H"_9)_4) \ 
&approx 0.00732 "mol" \
m("NH"_4"Cl") &= 0.00732 "mol" times 53.49 "g/mol" \ 
&approx 0.391 "g" $

+ 将 20 mL 无水乙醇与 10 mL 钛酸正丁酯 (密度 $0.996 "g/mL"$, 实际称取 $9.662 "g"$) 混合
+ 以约 2 滴/秒的速度将上述混合液缓慢滴入氯化铵溶液中, 滴入后溶液立刻浑浊。搅拌 15 min 后体系呈白色浊液
+ 将乳白色前驱体转移至聚四氟乙烯内衬的水热反应釜中, 160 $degree"C"$ 反应 8 小时
+ 反应结束后冷却至室温, 用乙醇洗涤除去有机物, 再用去离子水洗涤 3 遍
+ 3k RPM 离心, 得到乳白色糊状物
+ 将产物于 80 $degree"C"$ 烘干 12 小时, 得到纳米 $"TiO"_2$ 粉末
+ 称量并计算产率

== 测试与表征 <sec:testing>

/ XRD 测试: 采用德国布鲁克公司 D8 FOCUS 型 X 射线衍射仪 ($"Cu" "K"alpha$, $40.0 "kV" times 40.0 "mA"$), $2theta$ 扫描范围 $10 degree - 80 degree$, 扫描速率 $10 degree"/min"$, 步宽 $0.01 degree$, 共 7001 个数据点。

/ SEM 测试: 采用扫描电子显微镜对产物形貌进行观察。将少量样品分散于导电胶上, 喷金处理后在不同放大倍率下拍摄图像。

== 光催化降解实验 <sec:degradation_exp>

+ 罗丹明 B 溶液配制：
  + 设计方案：罗丹明 B 摩尔质量 $479.01 "g/mol"$; 称取 $0.239 "g"$ RhB, 定容于 500 mL 容量瓶; 取 2 mL 该溶液定容至 100 mL, 得到 $0.02 "mM"$ 的 RhB 溶液。、
  + 实际采用：取 3 mL $0.2 "mM"$ RhB 溶液与 27 mL 去离子水混合, 得到 30 mL $0.02 "mM"$ 的 RhB 溶液。
+ 设计方案为称取 $0.04 "g"$ $"TiO"_2$ 光催化剂分散于 40 mL RhB 溶液中 (催化剂用量 $1.0 "g" dot.c "L"^(-1)$) ; 实际称取 0.0302 g 光催化剂, 分散于 30 mL RhB 溶液中 (催化剂用量 $1.0067 "g" dot.c "L"^(-1)$)
+ 暗处搅拌 30 分钟以达到吸附-脱附平衡
+ 开启 10 W 280 nm UV LED 灯光照 (反应器温度 25 $degree"C"$, 搅拌速率 200 RPM) , 保持搅拌使催化剂处于悬浮状态
+ 分别于光照 0、5、15、30、45、60、90 分钟取样
+ 用 0.45 $mu"m"$ 滤膜过滤除去悬浮催化剂, 取滤液用分光光度计测定 554 nm 处的吸光度
+ 以 $c \/ c_0$ 对 $t$ 作图得降解曲线, 按一级反应动力学拟合求速率常数 $k$ 和半衰期 $t_(1\/2)$

= 数据处理及实验结果 <sec:results>

#set par(first-line-indent: 2em)

== 产率计算 <sec:yield>

理论产量计算：以钛酸正丁酯中 Ti 含量为基准, $"Ti"("OC"_4"H"_9)_4$ 与 $"TiO"_2$ 的化学计量比为 $1:1$。

$ n(("Ti"("OC"_4"H"_9)_4)) &= (9.662 "g") / (340.32 "g/mol") \ 
 &approx 0.0284 "mol" \
 n("TiO"_2) &= n("Ti"("OC"_4"H"_9)_4) \
 &approx 0.0284 "mol" \
 m_("theory")("TiO"_2) &= 0.0284 "mol" times 79.9 "g/mol" \
 &approx 2.27 "g" $

- 理论产量：2.27 g\
- 实际产量：1.1779 g\
- 产率：$1.1779 \/ 2.27 times 100% = 51.9%$

产率约 52%, 水热合成过程中存在一定产物损失, 可能原因包括离心转移过程中的产物损失、洗涤过程造成的粉体流失以及部分前驱体未完全转化为 $"TiO"_2$ 等。

== SEM 形貌分析 <sec:sem_analysis>

对 9 张 SEM 图像 (编号 01-03, 06-09, 11-12, 放大倍率不同) 进行颗粒分割与 Feret 直径测量, 标注结果见 @fig:sem_annotated。图像经透视矫正、SEM 区域裁剪、二值化阈值分割、大团块排除及分水岭分割后, 提取单颗粒并计算 Feret 直径 (最大卡钳距离) 。比例尺分别为 3 $mu"m"$ (01-03) 和 5 $mu"m"$ (06-12) 。

=== 逐图统计 <sec:per_image>

对 9 张图像逐图统计 Feret 直径分布, 结果如 @fig:per_image_stats 所示。各图像因放大倍率不同, 比例尺分别为 3 $mu"m"$ (01-03) 和 5 $mu"m"$ (06-12) , 统计指标包括颗粒数、均值、中位值和标准差。

#figure(
  placement: auto,
  table(
    columns: 6,
    stroke: none,

    table.hline(),
    table.header(
      [idx], [颗粒数 $n$], [mean (nm)], [med (nm)], [std (nm)], [scale (nm/px)],
    ),

    table.hline(stroke: 0.5pt),

    [01], [302], [452], [397], [237], [18.18],
    [02], [309], [426], [379], [221], [18.07],
    [03], [309], [438], [400], [225], [18.07],
    [06], [523], [908], [822], [476], [33.65],
    [07], [379], [819], [696], [475], [31.06],
    [08], [418], [781], [674], [447], [30.86],
    [09], [408], [945], [876], [469], [37.31],
    [11], [590], [748], [663], [395], [34.48],
    [12], [497], [857], [753], [462], [34.72],

    table.hline(),
  ),
  caption: [逐图 Feret 直径统计 (单颗粒) ],
) <fig:per_image_stats>

颗粒分割与 Feret 直径标注的可视化结果如 @fig:sem_annotated 所示。绿色轮廓为识别出的单颗粒, 蓝色线段标示 Feret 直径 (最大卡钳距离) , 红色数字为实测直径值 (nm) 。

#figure(
  placement: auto,
  grid(
    columns: 4,
    rows: 4,
    gutter: 0.3em,
    grid.cell(colspan: 4, align: center)[#image("../sem_pipeline/output/annotated/01_annotated.jpg", width: 100%) #v(-1em) (a) 01],
    align(center)[#image("../sem_pipeline/output/annotated/02_annotated.jpg", width: 100%) #v(-1em) (b) 02],
    align(center)[#image("../sem_pipeline/output/annotated/03_annotated.jpg", width: 100%) #v(-1em) (c) 03],
    align(center)[#image("../sem_pipeline/output/annotated/06_annotated.jpg", width: 100%) #v(-1em) (d) 06],
    align(center)[#image("../sem_pipeline/output/annotated/07_annotated.jpg", width: 100%) #v(-1em) (e) 07],
    align(center)[#image("../sem_pipeline/output/annotated/08_annotated.jpg", width: 100%) #v(-1em) (f) 08],
    align(center)[#image("../sem_pipeline/output/annotated/09_annotated.jpg", width: 100%) #v(-1em) (g) 09],
    align(center)[#image("../sem_pipeline/output/annotated/11_annotated.jpg", width: 100%) #v(-1em) (h) 11],
    align(center)[#image("../sem_pipeline/output/annotated/12_annotated.jpg", width: 100%) #v(-1em) (i) 12],
  ),
  caption: [SEM 颗粒分割及 Feret 直径标注图 (绿色轮廓为单颗粒, 蓝色线段为 Feret 直径, 红字标注数值) ],
) <fig:sem_annotated>

=== 合并统计 <sec:combined>

全部 3735 个颗粒的合并统计如 @fig:combined_stats：

#figure(
  // placement: auto,
  table(
    columns: 7,
    stroke: none,

    table.hline(),
    table.header([$n$], [均值 (nm)], [中位值 (nm)], [标准差 (nm)], [$D_10$ (nm)], [$D_50$ (nm)], [$D_90$ (nm)]),

    table.hline(stroke: 0.5pt),

    [3735], [741], [630], [448], [277], [630], [1416],
    table.hline(),
  ),
  caption: [全部颗粒 Feret 直径合并统计],
) <fig:combined_stats>

全部 3735 个颗粒的整体分布特征由对数正态拟合直方图 (@fig:combined_histogram) 呈现如下。黑色虚线为对数正态分布拟合曲线, 反映颗粒体系典型的右偏态分布特征。

#figure(
  placement: auto,
  image("../sem_pipeline/output/histograms/combined_histogram.svg", width: 100%),
  caption: [$"TiO"_2$ 纳米颗粒 Feret 直径分布 (直方图, 黑色虚线为对数正态拟合曲线) ],
) <fig:combined_histogram>

为进一步展示各图像的粒度分布细节, 逐图直方图及对数正态拟合如 @fig:per_image_histograms 所示。蓝色柱状图为实测粒径分布, 红色曲线为对数正态概率密度拟合, 可直观观察各图像间粒度分布的一致性和离散程度。

#figure(
  placement: auto,
  grid(
    columns: 3,
    rows: 3,
    gutter: 0.3em,
    align(center)[#image("../sem_pipeline/output/histograms/01_histogram.svg", width: 100%) (a) 01],
    align(center)[#image("../sem_pipeline/output/histograms/02_histogram.svg", width: 100%) (b) 02],
    align(center)[#image("../sem_pipeline/output/histograms/03_histogram.svg", width: 100%) (c) 03],
    align(center)[#image("../sem_pipeline/output/histograms/06_histogram.svg", width: 100%) (d) 06],
    align(center)[#image("../sem_pipeline/output/histograms/07_histogram.svg", width: 100%) (e) 07],
    align(center)[#image("../sem_pipeline/output/histograms/08_histogram.svg", width: 100%) (f) 08],
    align(center)[#image("../sem_pipeline/output/histograms/09_histogram.svg", width: 100%) (g) 09],
    align(center)[#image("../sem_pipeline/output/histograms/11_histogram.svg", width: 100%) (h) 11],
    align(center)[#image("../sem_pipeline/output/histograms/12_histogram.svg", width: 100%) (i) 12],
  ),
  caption: [逐图 Feret 直径分布直方图 (蓝色柱状图为实测分布, 红色曲线为对数正态拟合) ],
) <fig:per_image_histograms>

== XRD 物相分析 <sec:xrd_analysis>

=== 数据处理方法 <sec:data_processing>

对原始衍射数据进行三步预处理：
+ *ALS 基线扣除*：非对称最小二乘法 ($lambda = 10^6$, $p = 0.001$, 迭代 10 次) , 拟合信号下包络线并扣除荧光背底
+ *Savitzky-Golay 平滑*：15 点三次多项式滤波, 去除电子噪声同时保留峰形
+ *参考引导局部峰验证*：参考峰位置由 CIF 晶体结构文件 (AFLOW.org 数据库, 详见 @sec:simulated) 通过 pymatgen XRD 模拟器 ($"Cu" "K"alpha$, $10 degree - 80 degree$, symprec = 0.1) 精确计算得到。对每个参考位置, 在 $plus.minus 0.50 degree$ 窄窗内搜索局部最大值, 在 $plus.minus 2.0 degree$ 宽窗内计算突出度 (prominence) , 要求突出度超过宽窗内信号极差的 10% (局部相对阈值)。

为排除噪声和误匹配造成的假阳性, 额外施加三层过滤条件：
+ *绝对噪声阈值*：取基线扣除后信号最低 30% 区间的 RMS 值, 要求峰高 $>= 3 sigma$ 方可纳入考量, 避免将基线噪声波动误判为衍射峰
+ *峰位偏移容差*：要求实测峰位与 CIF 模拟参考位的偏移不超过 $plus.minus 0.25 degree$, 滤除因搜索窗过宽导致的误配 (如将锐钛矿真峰匹配到偏移 0.3 degree 以外的金红石参考位)
+ *独立主峰共识*：两相各取 5 个最强且与另一相不重叠 (参考峰间距 $> 0.15 degree$) 的主峰作为判据峰。任一物相须有至少 3 个独立主峰同时通过上述所有验证, 方可认定为该相确实存在于样品中

由于 X 射线衍射实验采用 $10 degree"/min"$ 的高速扫描 (常规慢扫为 $2 degree"/min"$ 或更低) , 步宽 $0.01 degree$ 下每个数据点的停留时间极短, 导致衍射图谱噪声显著增大、弱峰难以分辨。高本底噪声限制了 FWHM 半高宽测量的精度, 尤其对于强度较低或峰位重叠的衍射峰, 可靠测量几乎无法实现。后文晶粒尺寸分析 (Scherrer 公式) 仅对疏离度较高的孤立峰进行, 且结果应视为高噪声条件下的近似值。若需获得更高质量的数据, 建议在后续实验中采用慢扫 ($<= 2 degree"/min"$) 条件重新采集。

=== 物相鉴定 <sec:phase_id>

经三层过滤验证 (3 $sigma$ 噪声阈值 + $plus.minus 0.25 degree$ 偏移容差 + $>= 3$ 独立主峰共识) , 样品鉴定为*纯锐钛矿相* (Anatase, 四方晶系, I4$""_1$/amd) 。参考峰位置由 CIF 晶体结构文件通过粉末衍射模拟精确计算得到 (详见 @sec:simulated) , 共 24 个独立参考峰 (锐钛矿 13 + 金红石 11) 。经噪声阈值和偏移容差过滤后, 共 7 个峰通过验证 (锐钛矿 5, 金红石 2) 。锐钛矿的 5 个已确认主峰中, 有 4 个属于独立判据峰, 满足 $>= 3$ 的共识要求; 金红石仅有 2 个独立判据峰通过验证, 未达到确认门槛, 判定为暂定/不存在 (tentative/absent) 。模拟参考图谱见 @fig:simulated_xrd, 晶体结构数据来源于 AFLOW.org 数据库 @mehl2017aflow @hicks2019aflow。

sample_01 经验证, 未达到金红石独立主峰共识要求, 判定为纯锐钛矿相。

=== 模拟参考衍射图谱 <sec:simulated>

粉末 XRD 参考衍射图谱由晶体结构 CIF 文件通过第一性原理模拟得到, 而非查找 JCPDS/ICDD 数据库。具体方法如下：

/ 晶体结构来源: 锐钛矿和金红石 $"TiO"_2$ 的 CIF 文件取自 AFLOW.org 晶体学原型数据库 (AFLOW Library of Crystallographic Prototypes) @mehl2017aflow @hicks2019aflow, 具体参数见 @fig:cif_sources：

/ 模拟参数: 采用 pymatgen ``XRDCalculator`` ($"Cu" "K"alpha$, 波长 $1.5406 angstrom$, symprec = 0.1) , $2theta$ 扫描范围 $10 degree - 80 degree$, 与实验条件一致。模拟过程自动处理对称性等价反射 (multiplicity) 、原子散射因子和 Lorentz-极化因子。最终峰表不经任何事后修改 (如 JCPDS 数据库查询) 。模拟结果见 @fig:simulated_xrd。

#figure(
  // placement: auto,
  table(
    columns: 4,
    stroke: none,

    table.hline(),
    table.header([物相], [AFLOW 原型], [空间群], [晶胞参数]),

    table.hline(stroke: 0.5pt),

    [Anatase], [A2B_tI12_141_e_a-001], [I4$""_1$/amd (141)], [$a = b = 3.785 angstrom$, $c = 9.514 angstrom$],
    [Rutile], [A2B_tP6_136_f_a-001], [P4$""_2$/mnm (136)], [$a = b = 4.592 angstrom$, $c = 2.957 angstrom$],
    table.hline(),
  ),
  caption: [$"TiO"_2$ 晶体结构 CIF 文件来源 (AFLOW.org 数据库) ],
) <fig:cif_sources>

#figure(
  // placement: auto,
  image("../xrd_pipeline/output/simulated_comparison.svg", width: 100%),
  caption: [$"TiO"_2$ 模拟粉末 XRD 参考图谱 ($"Cu" "K"alpha$, $40.0 "kV" \/ 40.0 "mA"$, $10 degree - 80 degree$) 。蓝色：锐钛矿 Anatase, 红色：金红石 Rutile。竖线高度对应归一化相对强度 (最强峰 = 100) 。],
) <fig:simulated_xrd>

模拟图谱与实验谱图 (@fig:sample01_xrd) 的叠加对比可同时观察物相匹配度：实验峰位若与模拟竖线重合, 确认该物相存在; 若偏移或缺失, 提示晶格应变或含量低于检测限。

=== 物相定量分析 <sec:quantitative>

本分析采用两套互补方法对物相组成进行估算：

/ Spurr-Myers 双峰法: 由锐钛矿 (101) ($2theta = 25.32 degree$) 和金红石 (110) ($2theta = 27.47 degree$) 两个最强且互不重叠的特征峰强度比估算锐钛矿含量：

$ w_("Anatase") (%) = 100 / (1 + 1.26 dot (I_("Rutile(110)")) / (I_("Anatase(101)"))) $

经噪声过滤后, 金红石 (110) 参考位 ($27.47 degree plus.minus 0.15 degree$) 内信号强度低于 3 $sigma$ 噪声阈值 ($8.90$ counts) , $I_("Rutile(110)")$ 被视为 0, 公式退化为 $w_("Anatase") = 100%$。这意味着在传统的 Spurr-Myers 框架下, 样品为*纯锐钛矿相*。

/ NNLS 全谱分解: 将实验谱与 CIF 模拟展宽谱做非负最小二乘拟合 ($2theta = 20 degree - 65 degree$, $"FWHM" = 1.0 degree$) , 得到 Anatase/Rutile $= 83.3"/"16.7$ ($R^2 = 0.33$) 。NNLS 方法虽倾向于为金红石分配约 17% 的权重, 但其 $R^2$ 值偏低, 且该分解受限于归一化后对弱特征峰的过拟合倾向——当实验谱中存在少量偏离纯锐钛矿的噪声/本底波动时, NNLS 会将其"解释"为金红石贡献。考虑到金红石在独立峰共识检验中未达到确认门槛 (2/3) , NNLS 给出的金红石比例不宜作为物相存在的独立证据。

综合 Spurr-Myers (100% Anatase) 、NNLS (以 Anatase 为主, 但信度有限) 以及独立峰共识 (Anatase CONFIRMED, Rutile TENTATIVE) 三方面判断, 样品为*纯锐钛矿相* (@fig:sample01_xrd) 。后续讨论中仅以锐钛矿的晶体学参数进行分析。

#figure(
  placement: auto,
  image("../xrd_pipeline/output/sample_01.svg", width: 100%),
  caption: [sample_01 XRD 衍射图谱。上图：基线扣除 + 平滑后实验谱图 (黑色实线) , 虚线为 ALS 基线, 蓝色/红色标注为通过三层验证的实测衍射峰位置及 $2theta$ 值, $D=7 "nm"$ 为 Scherrer 晶粒尺寸; 下图：模拟参考棒状图 (蓝色 Anatase, 红色 Rutile, 归一化相对强度, 向下绘制) 。左上角标注物相组成及独立峰共识检验结果],
) <fig:sample01_xrd>

=== 晶粒尺寸分析 <sec:scherrer>

晶粒尺寸 ($D$) 通过 Scherrer 公式计算 (原理详见 @sec:xrd) ：

$ D = (K lambda) / (beta cos theta) $

其中 $K = 0.89$, $lambda = 0.15406$ nm ($"Cu" "K"alpha$), $beta$ 为经仪器展宽校正后的衍射峰半高宽 (弧度) 。仪器展宽 $"fwhm"_"inst" = 0.01 degree$ 通过 $beta = sqrt("fwhm"_"meas"^2 - "fwhm"_"inst"^2)$ 校正。FWHM 测量采用线性插值法在半峰高处搜索交点, 数据预处理为 Savitzky-Golay 15 点三次多项式平滑。

由于金红石相未通过独立峰共识检验, 仅对锐钛矿特征峰进行 Scherrer 分析。锐钛矿 (101) 面 ($2theta = 25.29 degree$) 的 FWHM 为 $1.1339 degree$, 经仪器展宽校正后计算得晶粒尺寸 $D = 7.1$ nm (@fig:sample01_xrd) 。其余锐钛矿衍射峰因与相邻峰间距过小 ($< 1.5 degree$) , 无法可靠分离半高宽, 未纳入定量分析。

XRD 晶粒尺寸 (锐钛矿 $approx 7$ nm) 远小于 SEM 观测的 Feret 粒径 (合并中位值 630 nm, @fig:combined_stats) , 说明 SEM 观测到的颗粒为多晶聚集体, 每个颗粒由多个 XRD 相干衍射域 (晶粒) 组成。这一现象在纳米 $"TiO"_2$ 的 XRD-SEM 联合表征中常见。较小的锐钛矿晶粒尺寸 (约 7 nm) 意味着较大的比表面积, 有利于光催化反应中活性位点的暴露。

== 光催化降解动力学 <sec:kinetics>

=== 实验数据 <sec:kinetics_data>

以 $"TiO"_2$ 为光催化剂 ($1.0 "g" dot.c "L"^(-1)$) , 在紫外光照射下催化降解罗丹明 B (初始浓度 $0.02 "mmol" dot.c "L"^(-1)$) 。于不同时间取样, 测定 554 nm 处吸光度 $A$, 以 $c \/ c_0 = A \/ A_0$ 计算残余浓度比。

=== 一级动力学拟合 <sec:kinetics_fit>

光催化降解反应通常遵循 Langmuir-Hinshelwood 一级动力学模型：

$ ln(c/c_0) = -k t $

以 $ln(c \/ c_0)$ 对时间 $t$ 做线性回归, 求得动力学参数如 @fig:kinetic_params 所示。

#figure(
  // placement: auto,
  grid(
    columns: (1fr, 1fr),
    gutter: 1.5em,
    align(center + horizon)[
      #figure(
        table(
          columns: 4,
          stroke: none,

          table.hline(),
          table.header(
            [$t$ (min)], [$A$ (554 nm)],       [$c \/ c_0$], [$ln(c \/ c_0)$],
          ),

          table.hline(stroke: 0.5pt),

          [0], [1.351], [1.000], [0],
          [5], [1.125], [0.833], [$-$0.183],
          [15], [1.043], [0.772], [$-$0.259],
          [30], [0.745], [0.551], [$-$0.595],
          [45], [0.475], [0.352], [$-$1.045],
          [60], [0.229], [0.170], [$-$1.775],
          [90], [0.058], [0.043], [$-$3.148],
          table.hline(),
        ),
        caption: [光催化降解 RhB 实验数据],
      ) <fig:degradation_data>
    ],
    align(center + horizon)[
      #figure(
        table(
          columns: 2,
          stroke: none,

          table.hline(),
          table.header([参数], [数值]),

          table.hline(stroke: 0.5pt),

          [$k$], [$0.0340 plus.minus 0.0031 "min"^(-1)$],
          [$b$], [0.1900],
          [$R^2$], [0.9597],
          [$t_(1\/2)$], [$ln 2 \/k = 20.4$ min],
          table.hline(),
        ),
        caption: [一级动力学拟合参数],
      ) <fig:kinetic_params>
    ],
  ),
)

$R^2 = 0.96$ 表明实验数据与一级动力学模型吻合良好 (@fig:degradation_kinetics) 。截距偏离理想值 0 (为 0.19) , 可能与暗吸附未能完全达到平衡或初始阶段反应机制存在短暂诱导期有关。半衰期 $t_(1\/2) = 20.4$ min, 表明催化剂具有较好的光催化降解活性。

#figure(
  // placement: auto,
  grid(
    columns: (1fr, 1fr),
    gutter: 1em,
    align(center + horizon)[
      #image("../degradation_pipeline/output/degradation_curve.svg", width: 100%) #v(-1em)
      (a) $"TiO"_2$ 光催化降解 RhB 曲线 ($c \/ c_0$ vs $t$)
    ],
    align(center + horizon)[
      #image("../degradation_pipeline/output/kinetic_fit.svg", width: 100%) #v(-1em)
      (b) 一级动力学拟合 ($ln(c \/ c_0)$ vs $t$)
    ],
  ),
  caption: [$"TiO"_2$ 光催化降解 RhB 降解曲线及一级动力学拟合],
) <fig:degradation_kinetics>

#set par(first-line-indent: 2em)

== 分析与讨论 <sec:discussion>

=== 水热合成 <sec:disc_synthesis>

产率为 51.9%, 合成过程中存在一定的产物损失。可能原因包括：(1) 离心和洗涤转移过程中粉体流失; (2) 部分钛酸正丁酯在滴加过程中水解不够完全, 未充分参与水热反应; (3) 烘干过程中可能存在的粉体粘结和转移损失。实验过程中观察到滴入 $"NH"_4"Cl"$ 后溶液立刻浑浊, 表明水解反应迅速发生; 搅拌 15 min 后体系呈白色浊液, 说明前驱体已初步形成。

=== SEM 形貌分析 <sec:disc_sem>

SEM 图像分析表明 (@fig:sem_annotated, @fig:per_image_histograms) , 颗粒呈不规则块状形貌, Feret 中位粒径约 630 nm (@fig:combined_stats) , 粒径分布呈对数正态分布特征 --- 中位值低于均值, 分布向右偏斜, 这是纳米颗粒体系的常见特征。

图中观察到一定程度的颗粒团聚现象, 这主要来源于 SEM 制样过程中样品用量过多导致的颗粒堆叠, 而非合成本身的团聚问题。在后续实验中应当优化制样分散工艺, 以获得更具代表性的单颗粒形貌。

Feret 直径 (最大卡钳距离) 相较于等效圆直径 (ECD) 更适合表征不规则块状 $"TiO"_2$ 颗粒的真实尺寸, 因为 $"TiO"_2$ 颗粒多为多边形/块状形貌, ECD 会系统性低估。

=== XRD 物相鉴定 <sec:disc_xrd>

经三层过滤的严谨验证, 样品最终鉴定为*纯锐钛矿相* (Anatase, @fig:sample01_xrd), 金红石相未能通过独立主峰共识检验 (2/3, 低于 3 峰门槛) 。Spurr-Myers 公式在噪声过滤后直接退化为 100% Anatase。锐钛矿 (101) 面衍射峰 ($2theta approx 25.3 degree$) 为最强峰, 与锐钛矿纳米材料的典型衍射特征一致。

需特别指出, 本分析管线在开发过程中经历了多次迭代完善。早期版本采用宽松的参考引导匹配策略 (仅依赖 $plus.minus 0.50 degree$ 搜索窗和 10% 局部突出度阈值, 不设噪声过滤和偏移容差) , 曾将样品判定为锐钛矿/金红石混合相 (Spurr-Myers $approx 76.6%"/"23.4%$)。该早期结论后被证明不可靠, 原因在于：

/ 搜索窗过宽导致误配: 锐钛矿真峰与金红石参考位之间存在 $0.3 - 0.5 degree$ 的系统偏移, 在 $plus.minus 0.50 degree$ 搜索窗下被误匹配, 产生大量虚假的金红石"验证峰"
/ 缺乏噪声阈值: 锐钛矿主峰 (101) 的尾部强度在 $27.5 degree$ 附近仍高于本底, 被 Spurr-Myers 的窄窗口 ($plus.minus 0.15 degree$) 直接拾取, 计算出虚假的金红石含量
/ 缺乏相共识机制: 单个弱峰的偶然通过被等同于物相存在, 未要求系统的峰形证据

引入三层过滤机制 (3 $sigma$ 噪声阈值、$plus.minus 0.25 degree$ 偏移容差、$>= 3$ 独立主峰共识) 后, 金红石的判定由"确认"降级为"暂定"。这一修改并非人为调参偏向某一相, 而是对两相*完全对称地*施加同等严格的验证标准：锐钛矿同样需要 $>= 3$ 个独立主峰通过全部过滤方可确认。Anatase 轻松通过 (4/3) , 而 Rutile 在 sample_01 中未达标 (2/3) , 表明金红石信号不具有系统性和一致性。

Scherrer 公式估算的锐钛矿晶粒尺寸约 7 nm (@fig:sample01_xrd), 远小于 SEM 观测的颗粒粒径 (中位 630 nm, @fig:combined_stats) 。这一差异符合纳米材料 XRD-SEM 联合表征的典型特征：SEM 图像中的颗粒为多晶聚集体, 单个颗粒包含多个晶粒 (相干衍射域) 。较小的锐钛矿晶粒 (约 7 nm) 意味着较大的比表面积, 有利于光催化反应中活性位点的暴露。

然而, 本实验采用的高速扫描条件 ($10 degree"/min"$) 严重限制了 XRD 分析的深度。高速扫描导致各数据点计数时间不足, 衍射图谱噪声水平偏高, 使得：(1) 多数衍射峰的半高宽无法可靠测量 (峰间重叠与噪声导致峰形失真) ; (2) 弱峰可能被噪声掩盖; (3) 无法进行更高阶的分析。若需获得更准确的晶粒尺寸及晶格应变信息, 建议在后续实验中采用慢扫条件 ($<= 2 degree"/min"$) 重新采集数据。

=== 光催化性能 <sec:disc_photocat>

一级动力学拟合的 $R^2 = 0.9597$ (@fig:degradation_data, @fig:kinetic_params) , 表明降解过程基本符合一级动力学。速率常数 $k = 0.0340 "min"^(-1)$, 半衰期 $t_(1\/2) = 20.4$ min, 90 分钟时降解率达 95.7% (@fig:degradation_kinetics) , 显示出良好的光催化活性。

截距为正值 (0.19) 而非 0, 可能的原因包括：
+ 暗吸附 30 分钟未能完全达到吸附平衡, 导致光照初期存在快速吸附贡献
+ 反应最初几分钟可能存在非一级动力学的诱导期
+ 后期 (60-90 分钟) RhB 浓度极低时, 分光光度计灵敏度有限导致测量误差增大


= 结论 <sec:conclusion>

+ 通过水热法成功制备了纳米 $"TiO"_2$ 光催化剂, 产率 51.9%
+ XRD 分析表明样品为*纯锐钛矿相* (Anatase), 金红石相未通过独立峰共识检验 (2/3, @fig:sample01_xrd) , Spurr-Myers 公式经噪声过滤后指示 100% Anatase; Scherrer 公式估算晶粒尺寸约 7 nm, 与 SEM 粒径差异表明颗粒为多晶聚集体。高速扫描 ($10 degree"/min"$) 限制了 XRD 精细分析的能力
+ SEM 分析显示颗粒呈不规则块状形貌, Feret 中位粒径约 630 nm (@fig:combined_stats, @fig:sem_annotated)
+ 光催化降解 RhB 实验表明催化剂具有良好活性 (@fig:degradation_kinetics) ：$k = 0.0340 "min"^(-1)$, $t_(1\/2) = 20.4$ min, 90 min 降解率 95.7%, 一级动力学 $R^2 = 0.96$
+ 实验整体较为成功, 后续可在合成工艺 (提高产率) 和制样分散工艺方面进一步优化

= 原始数据记录 <sec:raw_data>

原始数据文件：

- SEM 原始图像：#link("https://github.com/madSUNitist/TiO2-experiments/tree/main/sem_pipeline/data")[`sem_pipeline/data/`]
- SEM 颗粒测量数据：`sem_pipeline/output/data/*_particles.csv`
- XRD 原始数据：#link("https://github.com/madSUNitist/TiO2-experiments/tree/main/xrd_pipeline/data")[`xrd_pipeline/data/`]

光催化吸光度原始数据：

#figure(
  // placement: auto,
  table(
    columns: 8,
    stroke: none,

    table.hline(),
    table.header([$t$ (min)], [0], [5], [15], [30], [45], [60], [90]),

    table.hline(stroke: 0.5pt),

    [$A$ (554 nm)], [1.351], [1.125], [1.043], [0.745], [0.475], [0.229], [0.058],
    table.hline(),
  ),
  caption: [光催化降解 RhB 吸光度原始数据],
) <fig:raw_absorbance>

所有数据处理脚本和参数配置详见各 Pipeline 源代码, 全部算法为确定性算法, 可完全复现。

完整代码仓库: #link("https://github.com/madSUNitist/TiO2-experiments")[github.com/madSUNitist/TiO2-experiments]

#pagebreak()

#set text(size: 10pt)
#set par(first-line-indent: 0em)
#set bibliography(style: "ieee", title: "参考文献")
#bibliography("refs/refs.bib")

#pagebreak()

#image("./scripts/01.jpg")
#image("./scripts/02.jpg")
#image("./scripts/03.jpg")
#image("./scripts/04.jpg")