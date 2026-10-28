# -*- coding: utf-8 -*-
"""
【大数据招聘岗位数据分析】可视化方案 —— 4 张图
=================================================
输入：notebook/数据分析岗_清洗后.csv（3984 行 × 25 列清洗后宽表）
输出：portfolio/assets/chart1_direction.png
      portfolio/assets/chart2_city.png
      portfolio/assets/chart3_edu_exp.png
      portfolio/assets/chart4_exp_salary.png
      portfolio/assets/图表数据核对.txt

设计原则
--------
1. 每张图只回答应届生的一个具体决策问题：投什么岗 / 去哪投 / 我够不够格 / 起薪多少
2. 所有薪资统计只用「薪资分析可用 == True」的 3334 条，剔除「面议」与业务异常值，
   保证四张图口径一致（否则图表之间无法互相印证）
3. 样本量 < 阈值的分组不画进主图，避免小样本均值把人带偏
"""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")            # 无界面后端，服务器/脚本环境下也能出图
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

# ----------------------------------------------------------------------------
# 0. 全局设置：中文字体 + 负号 + 配色
# ----------------------------------------------------------------------------
# Windows 下优先用微软雅黑，回退黑体；缺字体时中文会显示成方框，所以做了列表回退
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "SimSun"]
plt.rcParams["axes.unicode_minus"] = False   # 解决负号显示为方块的问题
plt.rcParams["figure.facecolor"] = "white"
plt.rcParams["axes.facecolor"] = "white"
plt.rcParams["axes.edgecolor"] = "#D5DAE2"
plt.rcParams["axes.linewidth"] = 0.9
plt.rcParams["axes.grid"] = True
plt.rcParams["grid.color"] = "#E8ECF2"
plt.rcParams["grid.linewidth"] = 0.8
plt.rcParams["axes.axisbelow"] = True        # 网格线画在图形下方
plt.rcParams["font.size"] = 11
plt.rcParams["axes.titlesize"] = 14
plt.rcParams["axes.titleweight"] = "bold"
plt.rcParams["axes.labelcolor"] = "#3C4759"
plt.rcParams["xtick.color"] = "#5A6577"
plt.rcParams["ytick.color"] = "#5A6577"

BLUE = "#2C6E9B"      # 主色：机会量
ORANGE = "#E8833A"    # 强调色：薪资
GRAY = "#8C97A8"      # 辅助：说明文字
LIGHT = "#DCE6F0"

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "data" / "数据分析岗_清洗后.csv"
OUT = BASE / "assets"
OUT.mkdir(parents=True, exist_ok=True)

# 千元格式化：把 18500 显示成 18.5k，比原始数字好读，也避免纵轴标签过长
kfmt = FuncFormatter(lambda v, _: f"{v/1000:g}k")
wanfmt = FuncFormatter(lambda v, _: f"¥{v/1000:g}k")


def add_footnote(fig, text):
    """统一的脚注：把数据口径和样本量写在图底，防止脱离上下文被误读。"""
    fig.text(0.012, 0.015, text, fontsize=8.5, color=GRAY, ha="left", va="bottom")


def save(fig, name):
    path = OUT / name
    fig.savefig(path, dpi=170, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("已保存：", path.name)


# ----------------------------------------------------------------------------
# 1. 读数据
# ----------------------------------------------------------------------------
df = pd.read_csv(DATA, encoding="utf-8-sig")
sal = df[df["薪资分析可用"]].copy()      # 薪资口径：3334 条
print(f"全量 {len(df)} 条，进入薪资统计 {len(sal)} 条（{len(sal)/len(df):.1%}）\n")

report = []
report.append("=" * 72)
report.append("可视化方案 —— 图表底层数据核对表")
report.append("=" * 72)
report.append(f"数据源：猎聘「数据分析」关键词公开招聘页抓取快照，2019-12-03 ~ 2019-12-20")
report.append(f"清洗后样本：{len(df)} 条（其中薪资可分析 {len(sal)} 条，{len(sal)/len(df):.1%}）")
report.append("")

# ============================================================================
# 图 1｜岗位方向：机会量与薪资梯度（横向双面板条形图）
# ============================================================================
g = sal.groupby("岗位方向")["月薪中位"].agg(
    n="size",
    p25=lambda s: s.quantile(0.25),
    med="median",
    p75=lambda s: s.quantile(0.75),
)
g_all = g.copy()
g = g[g["n"] >= 50].sort_values("n", ascending=True)   # 升序 → 条形图从上到下由大到小

# 全量口径的岗位占比（用于标注"主入口"）
share = df["岗位方向"].value_counts(normalize=True)

fig, axes = plt.subplots(1, 2, figsize=(13, 5.6), gridspec_kw={"width_ratios": [1, 1.15]})

# --- 左：岗位数量（机会有多少）---
ax = axes[0]
bars = ax.barh(g.index, g["n"], color=BLUE, height=0.62)
for b, (name, v) in zip(bars, g["n"].items()):
    # 标注：条数 + 该方向占全量的比例（占比用全量算，与图 3 的分母保持一致）
    ax.text(v + 60, b.get_y() + b.get_height() / 2,
            f"{v:,} 条 · {share.get(name, 0):.1%}",
            va="center", fontsize=9.5, color="#3C4759")
ax.set_xlabel("岗位数量（条）")
ax.set_title("机会量：谁在招人", loc="left")
ax.set_xlim(0, g["n"].max() * 1.42)     # 预留右侧空间，防止标注串到右边子图
ax.set_ylim(-1.0, len(g) - 0.4)         # 底部留白给图例，两个子图必须一致才能对齐条形
ax.grid(axis="y", visible=False)

# --- 右：月薪中位 + P25~P75 区间 ---
ax = axes[1]
y = np.arange(len(g))
ax.barh(y, g["med"], color=LIGHT, height=0.62, label="月薪中位数")
ax.errorbar(g["med"], y,
            xerr=[g["med"] - g["p25"], g["p75"] - g["med"]],
            fmt="o", color=ORANGE, ecolor=ORANGE, elinewidth=1.6,
            capsize=4, markersize=7, label="P25 ~ P75 区间")
for yi, (_, row) in zip(y, g.iterrows()):
    ax.text(row["p75"] + 900, yi, f"{row['med']/1000:g}k", va="center",
            fontsize=10, color=ORANGE, fontweight="bold")
ax.set_yticks(y)
ax.set_yticklabels(g.index)
ax.set_xlabel("月薪（元/月）")
ax.xaxis.set_major_formatter(kfmt)
ax.set_title("薪资梯度：哪个方向更贵", loc="left")
ax.set_xlim(0, g["p75"].max() * 1.3)
ax.set_ylim(-1.0, len(g) - 0.4)
ax.grid(axis="y", visible=False)
ax.legend(loc="lower right", frameon=False, fontsize=9.5)

fig.suptitle("图 1｜岗位方向：机会量与薪资梯度（样本量 ≥ 50 的方向）",
             fontsize=15, fontweight="bold", x=0.012, ha="left", y=1.02)
fig.subplots_adjust(top=0.84, bottom=0.16, wspace=0.28)
add_footnote(fig, "注：抓取关键词为「数据分析」，故「数据开发/数仓」仅 6 条（样本不足未入图），"
                  "不代表市场上该方向岗位少；薪资口径仅含公开薪资，不含「面议」。")
save(fig, "chart1_direction.png")

report.append("【图 1】岗位方向")
report.append(g_all.sort_values("n", ascending=False).round(0).to_string())
report.append(f"  数据分析方向占全量 {share.get('数据分析', 0):.1%}；"
              f"数据分析薪资中位 {g.loc['数据分析','med']:.0f}，"
              f"算法/挖掘 {g.loc['算法/挖掘','med']:.0f}（+{(g.loc['算法/挖掘','med']/g.loc['数据分析','med']-1):.1%}）")
report.append("")

# ============================================================================
# 图 2｜城市：机会密度 vs 薪资水平（双轴：柱 + 点线）
# ============================================================================
# 排除「未知」：这 487 条城市缺失的岗位薪资中位显著高于任何真实城市（MNAR），
# 混进城市排名会让"某个城市"凭空出现，必须单独说明而不是画进来
city = (sal[sal["城市"] != "未知"]
        .groupby("城市")["月薪中位"]
        .agg(n="size", med="median"))
city_dropped_n = len(sal) - city["n"].sum()
city = city[city["n"] >= 30].sort_values("n", ascending=False)

fig, ax1 = plt.subplots(figsize=(12, 5.8))
x = np.arange(len(city))
bars = ax1.bar(x, city["n"], color=BLUE, width=0.58, label="岗位数量")
for xi, v in zip(x, city["n"]):
    ax1.text(xi, v + 12, f"{v}", ha="center", fontsize=9.5, color="#3C4759")

ax1.set_xticks(x)
ax1.set_xticklabels(city.index)
ax1.set_ylabel("岗位数量（条）", color=BLUE)
ax1.set_xlabel("城市（按岗位数量排序，仅保留样本 ≥ 30）")
ax1.set_ylim(0, city["n"].max() * 1.18)
ax1.grid(axis="x", visible=False)

# 右轴：薪资中位。双轴容易误读，所以左轴用柱、右轴用点线并明确标出数值
ax2 = ax1.twinx()
ax2.plot(x, city["med"], color=ORANGE, marker="o", markersize=8, linewidth=2,
         label="月薪中位数", zorder=5)
for xi, v in zip(x, city["med"]):
    # 加白色底框 + 高 zorder：否则靠近柱顶时数字会被蓝色柱体盖住（广州就是这种情况）
    ax2.annotate(f"{v/1000:g}k", (xi, v), textcoords="offset points", xytext=(0, 13),
                 ha="center", fontsize=10, color=ORANGE, fontweight="bold", zorder=10,
                 bbox=dict(boxstyle="round,pad=0.18", facecolor="white",
                           edgecolor="none", alpha=0.92))
ax2.set_ylabel("月薪中位数（元/月）", color=ORANGE)
ax2.set_ylim(city["med"].min() * 0.72, city["med"].max() * 1.16)
ax2.yaxis.set_major_formatter(kfmt)
ax2.grid(False)

top5 = city.head(5)["n"].sum()
fig.suptitle("图 2｜城市：机会密度与薪资水平（一线集中度极高）",
             fontsize=15, fontweight="bold", x=0.012, ha="left", y=1.0)
fig.subplots_adjust(top=0.86, bottom=0.17, left=0.07, right=0.9)
add_footnote(fig, f"注：已剔除「城市未知」{city_dropped_n} 条——该组薪资中位显著高于所有真实城市，"
                  "属缺失非随机（高薪岗位常不写城市），混入排名会造成误读。")
save(fig, "chart2_city.png")

report.append("【图 2】城市（样本 ≥ 30）")
report.append(city.round(0).to_string())
report.append(f"  TOP5 城市合计 {top5} 条，占薪资样本 {top5/len(sal):.1%}；"
              f"北京中位最高 {city.loc['北京','med']:.0f}，广州最低 {city.loc['广州','med']:.0f}")
report.append("")

# ============================================================================
# 图 3｜学历 × 经验：可投岗位矩阵（带数值标注的热力图）
# ============================================================================
edu_order = ["中专/中技", "大专", "不限", "本科", "硕士"]      # 由低到高
exp_order = ["不限", "1年以内", "1-3年", "3-5年", "5年以上"]   # 由宽到严
mat = (pd.crosstab(df["学历_规范"], df["经验档位"])
       .reindex(index=edu_order, columns=exp_order)
       .fillna(0).astype(int))
mat_pct = mat / len(df)          # 转成占全量比例，读者一眼知道"这个格子有多稀有"

fig, ax = plt.subplots(figsize=(11, 5.4))
im = ax.imshow(mat.values, cmap="Blues", aspect="auto")
ax.set_xticks(range(len(exp_order)))
ax.set_xticklabels(exp_order)
ax.set_yticks(range(len(edu_order)))
ax.set_yticklabels(edu_order)
ax.set_xlabel("经验要求 →  越靠右门槛越高")
ax.set_ylabel("学历要求 →  越靠下越稀缺")
ax.grid(False)

vmax = mat.values.max()
for i in range(len(edu_order)):
    for j in range(len(exp_order)):
        v = mat.values[i, j]
        # 深色格子用白字，浅色格子用深字，保证对比度
        color = "white" if v > vmax * 0.55 else "#22303F"
        ax.text(j, i, f"{v:,}\n{v/len(df):.1%}", ha="center", va="center",
                fontsize=10.5, color=color, linespacing=1.4)

# 给"大专 + 应届可投"这个最关键的两格加橙框（不加箭头文字，避免压住格内数值）
for j in [0, 1]:
    ax.add_patch(plt.Rectangle((j - 0.5, 0.5), 1, 1, fill=False,
                               edgecolor=ORANGE, linewidth=2.6, zorder=5))

cb = fig.colorbar(im, ax=ax, pad=0.015)
cb.set_label("岗位数量（条）")
cb.outline.set_visible(False)

fig.suptitle("图 3｜学历 × 经验：岗位机会矩阵（格内为该组合的岗位数与占比）",
             fontsize=15, fontweight="bold", x=0.012, ha="left", y=1.02)
fig.text(0.012, 0.935, "橙框：大专学历、且经验不限或要求 1 年以内 —— 共 169 条，仅占全量的 4.2%",
         fontsize=11, color=ORANGE, fontweight="bold", ha="left")
fig.subplots_adjust(top=0.83, bottom=0.16, left=0.1, right=0.98)
add_footnote(fig, f"注：全量 {len(df)} 条为分母；「博士」仅 {len(df[df['学历_规范']=='博士'])} 条，样本过小未单列。"
                  "「不限」表示招聘方未设该维度的门槛。")
save(fig, "chart3_edu_exp.png")

report.append("【图 3】学历 × 经验 岗位数矩阵（行=学历，列=经验）")
report.append(mat.to_string())
report.append("  占比（占全量）：")
report.append((mat_pct * 100).round(1).to_string())
report.append(f"  本科+1-3年 = {mat.loc['本科','1-3年']} 条，占全量 {mat.loc['本科','1-3年']/len(df):.1%}（最大格子）")
report.append(f"  大专应届可投（不限+1年以内）= {mat.loc['大专','不限'] + mat.loc['大专','1年以内']} 条，"
              f"占全量 {(mat.loc['大专','不限'] + mat.loc['大专','1年以内'])/len(df):.1%}")
report.append("")

# ============================================================================
# 图 4｜经验阶梯：薪资分布与涨幅（箱线图）
# ============================================================================
exp_all = ["1年以内", "1-3年", "3-5年", "5年以上", "不限"]
data, labels, stats = [], [], []
for e in exp_all:
    s = sal.loc[sal["经验档位"] == e, "月薪中位"].dropna()
    if len(s) >= 30:
        data.append(s.values)
        labels.append(e)
        stats.append((len(s), s.median(), s.quantile(0.25), s.quantile(0.75)))

fig, ax = plt.subplots(figsize=(11.5, 5.8))
bp = ax.boxplot(
    data, patch_artist=True, widths=0.5, medianprops=dict(color=ORANGE, linewidth=2.4),
    boxprops=dict(facecolor=LIGHT, edgecolor=BLUE, linewidth=1.2),
    whiskerprops=dict(color=BLUE, linewidth=1.1),
    capprops=dict(color=BLUE, linewidth=1.1),
    flierprops=dict(marker="o", markersize=3.2, markerfacecolor=GRAY,
                    markeredgecolor="none", alpha=0.45),
)
# 「不限」不是一个更高的经验档位，而是招聘方没设门槛，用灰箱区分，防止被读成"最高档"
for i, lab in enumerate(labels):
    if lab == "不限":
        bp["boxes"][i].set_facecolor("#EDEFF3")
        bp["boxes"][i].set_edgecolor(GRAY)
        bp["medians"][i].set_color(GRAY)
        for key in ("whiskers", "caps"):
            for art in bp[key][2 * i:2 * i + 2]:
                art.set_color(GRAY)

ax.set_xticks(range(1, len(labels) + 1))
ax.set_xticklabels([f"{l}\n{'（未设门槛）' if l == '不限' else ''}n={n}"
                    for l, (n, *_ ) in zip(labels, stats)])
ax.set_ylabel("月薪（元/月）")
ax.set_xlabel("经验要求（横轴按门槛由低到高排列）")
ax.yaxis.set_major_formatter(kfmt)
ax.set_ylim(0, 62000)
ax.grid(axis="x", visible=False)

# 在箱体上方标出中位数（涨幅改用标题下方一行文字表达，比画箭头更不容易和文字打架）
for i, (n, med, p25, p75) in enumerate(stats, start=1):
    ax.text(i, p75 + 1700, f"中位 {med/1000:g}k", ha="center", fontsize=10.5,
            color=ORANGE if labels[i - 1] != "不限" else GRAY, fontweight="bold")

gains = [(labels[k], stats[k][1] / stats[k - 1][1] - 1) for k in range(1, 4)]
gain_txt = "经验递进的中位涨幅：" + "  ·  ".join(
    f"{labels[k]}→{labels[k + 1]}  +{g * 100:.0f}%" for k, (_, g) in enumerate(gains)
)

fig.suptitle("图 4｜经验阶梯：起薪分布与档位间涨幅",
             fontsize=15, fontweight="bold", x=0.012, ha="left", y=1.02)
fig.text(0.012, 0.935, gain_txt, fontsize=11, color="#3C4759", ha="left")
fig.subplots_adjust(top=0.83, bottom=0.17, left=0.09, right=0.98)
add_footnote(fig, "注：箱体为 P25~P75，横线为中位数，须为 P10~P90 内非离群点；"
                  "薪资口径为公开薪资（不含「面议」），原始区间取上下限均值。")
save(fig, "chart4_exp_salary.png")

report.append("【图 4】经验档位薪资分布")
report.append(f"{'档位':<8}{'n':>6}{'P25':>9}{'中位':>9}{'P75':>9}")
for l, (n, med, p25, p75) in zip(labels, stats):
    report.append(f"{l:<8}{n:>6}{p25:>9,.0f}{med:>9,.0f}{p75:>9,.0f}")
report.append("")

# ----------------------------------------------------------------------------
# 3. 落地建议用的交叉统计：大专应届可投岗位在哪里
# ----------------------------------------------------------------------------
fresh = df[df["经验档位"].isin(["不限", "1年以内"])]
dazhuan_fresh = fresh[fresh["学历_规范"] == "大专"]
report.append("【交叉】大专 + 应届可投（经验不限/1年以内）的分布")
report.append(f"  合计 {len(dazhuan_fresh)} 条，占全量 {len(dazhuan_fresh)/len(df):.1%}")
report.append("  城市 TOP6：" + "，".join(
    f"{k}({v})" for k, v in dazhuan_fresh["城市"].value_counts().head(6).items()))
report.append("  方向：" + "，".join(
    f"{k}({v})" for k, v in dazhuan_fresh["岗位方向"].value_counts().head(4).items()))
report.append(f"  该群体薪资中位：{dazhuan_fresh.loc[dazhuan_fresh['薪资分析可用'],'月薪中位'].median():,.0f} 元/月")
report.append("")
report.append("【交叉】各学历中「应届可投」岗位的比例")
for edu in ["大专", "本科", "硕士"]:
    tot = (df["学历_规范"] == edu).sum()
    fr = ((df["学历_规范"] == edu) & df["经验档位"].isin(["不限", "1年以内"])).sum()
    report.append(f"  {edu}：{fr}/{tot} = {fr/tot:.1%} 的岗位对无经验者开放")
report.append("")

(OUT / "图表数据核对.txt").write_text("\n".join(report), encoding="utf-8")
print("\n".join(report))
