---
name: stats-cli
description: Use when user needs statistical analysis, SPC control charts, process capability, hypothesis testing, regression, DOE, outlier detection, trend analysis, MSA/Gage R&R, data cleaning, data transformation, reliability analysis, multivariate analysis, time series, power analysis, or chi-square tests. Triggers: 统计分析, 控制图, 过程能力, t检验, ANOVA, 回归, DOE, 正态性检验, 异常值, 趋势分析, SPC, Cp, Cpk, capability, normality, regression, correlation, outlier, quality, manufacturing, 质量分析, 过程控制, 假设检验, 方差分析, 实验设计, MSA, Gage R&R, 测量系统分析, 数据清洗, 数据变换, Box-Cox, 可靠性, Weibull, 生存分析, PCA, 聚类, 判别分析, 时间序列, ARIMA, 功效分析, 样本量, 卡方检验, chi-square.
---

# stats-cli

AI-friendly statistical analysis CLI for manufacturing, powered by R.

## Quick Start: Don't Know What Analysis to Use?

**Follow this decision tree:**

1. **用户描述模糊时** → 先用 `explore` 命令查看数据结构
2. **比较数据** → 看下面的"比较分析决策树"
3. **关系分析** → 看下面的"关系分析决策树"
4. **预测/趋势** → 看下面的"预测分析决策树"
5. **质量控制** → 看下面的"质量控制决策树"

---

## Decision Tree 1: 比较分析（两组或多组数据比较）

```
用户想比较数据
    │
    ├── 只有2组？
    │   ├── 数据是正态的？ → ttest (先用 normality 检查)
    │   │   ├── 等方差？ → two_sample t-test
    │   │   └── 不等方差？ → two_sample t-test (自动检测)
    │   └── 数据非正态？ → nonparametric mann_whitney
    │
    ├── 有3+组？
    │   ├── 数据是正态的？ → anova one_way
    │   │   └── 显著？ → multiple-comparison tukey
    │   └── 数据非正态？ → nonparametric kruskal_wallis
    │
    └── 配对数据？（同一样本前后对比）
        ├── 正态？ → ttest paired
        └── 非正态？ → nonparametric wilcoxon
```

**前置检查流程：**
```bash
# 1. 先检查正态性
stats-cli normality -f data.csv -c "column"

# 2. 根据结果选择检验方法
# 如果 p > 0.05 (正态) → 用参数检验
# 如果 p <= 0.05 (非正态) → 用非参数检验
```

---

## Decision Tree 2: 关系分析（变量之间是否有关系）

```
用户想分析变量关系
    │
    ├── 两个连续变量？
    │   ├── 看相关性 → correlation
    │   └── 看因果关系 → regression linear
    │
    ├── 多个自变量影响一个因变量？
    │   ├── 线性关系 → regression multiple
    │   └── 自动选择重要变量 → regression stepwise
    │
    ├── 因变量是分类变量（0/1）？
    │   └── regression logistic
    │
    └── 多个变量同时分析？
        ├── 降维 → multivariate pca
        ├── 分组 → multivariate cluster
        └── 分类 → multivariate discriminant
```

---

## Decision Tree 3: 预测/趋势分析

```
用户想预测或分析趋势
    │
    ├── 数据有季节性？
    │   ├── 有 → timeseries decomposition (frequency=周期长度)
    │   └── 无 → 继续
    │
    ├── 想预测未来值？
    │   ├── 短期预测 → timeseries exp_smoothing
    │   └── 长期预测 → timeseries arima
    │
    └── 想检测趋势是否存在？
        └── trend (CUSUM/EWMA/Runs test)
```

---

## Decision Tree 4: 质量控制

```
用户想做质量控制/SPC
    │
    ├── 监控过程稳定性？
    │   ├── 个体值 → control-chart imr
    │   ├── 子组均值 → control-chart xbar
    │   └── 计数数据 → control-chart p/np/c/u
    │
    ├── 评估过程能力？
    │   ├── 先检查正态性
    │   ├── 正态 → capability (Cp/Cpk)
    │   └── 非正态 → capability --type boxcox
    │
    ├── 验证测量系统？
    │   └── gage-rr crossed/nested/attribute
    │
    └── 分析失效/寿命？
        └── reliability weibull/stability
```

---

## Prerequisites

1. **R** installed (set `RSCRIPT_PATH` env var or add R to PATH)
2. **R packages**: `jsonlite`, `qcc`, `nortest`, `car`, `MASS`, `base64enc`, `survival`

Install R packages:
```r
install.packages(c("jsonlite", "qcc", "nortest", "car", "MASS", "base64enc", "survival"), repos="https://cloud.r-project.org")
```

---

## Installation

```bash
pip install stats-cli
# or
cd stats-cli && pip install -e .
```

---

## All Commands (26 commands)

### Data Exploration
```bash
stats-cli explore -f data.xlsx                    # 查看数据结构
stats-cli discover                                 # 列出所有命令
stats-cli discover capability                      # 查看命令详情
```

### Basic Statistics
```bash
stats-cli descriptive -f data.csv -c "weight"      # 描述性统计
stats-cli normality -f data.csv -c "weight"        # 正态性检验
stats-cli outlier -f data.csv -c "weight"           # 异常值检测
```

### Hypothesis Testing
```bash
stats-cli ttest one_sample -v 10.2 -v 10.5 --mu 10.0    # 单样本 t 检验
stats-cli ttest two_sample -v 10.2 -v 10.5 -v2 11.3 -v2 11.5  # 双样本 t 检验
stats-cli anova one_way -g '[10.2,10.5]' -g '[11.3,11.5]'     # 单因素 ANOVA
stats-cli nonparametric mann_whitney --x 10.2 --x 10.5 --y 11.3 --y 11.5  # Mann-Whitney
stats-cli nonparametric chi_square --observed 50 --observed 30 --observed 20  # 卡方检验
stats-cli equivalence tost -v 10.2 -v 10.5 -v2 10.3 -v2 10.6 --delta 0.5  # 等效性检验
stats-cli power t_test --effect-size 0.5 --power 0.80  # 功效分析/样本量
```

### Regression
```bash
stats-cli regression --x 1 --x 2 --x 3 --y 2 --y 4 --y 6  # 线性回归
stats-cli regression -f data.csv --y-column "y" --x-columns "x1" --x-columns "x2" --type multiple  # 多元回归
stats-cli regression -f data.csv --y-column "y" --x-columns "x1" --x-columns "x2" --type stepwise  # 逐步回归
stats-cli correlation -f data.xlsx --x-column "temp" --y-column "yield"  # 相关分析
```

### SPC / Quality Control
```bash
stats-cli control-chart imr -f data.csv -c "weight"     # I-MR 控制图
stats-cli control-chart xbar -f data.csv -c "weight" --subgroup-size 5  # X-bar 图
stats-cli capability -f data.csv -c "weight" --usl 11.0 --lsl 9.0  # 过程能力
stats-cli capability -f data.csv -c "weight" --usl 11.0 --type boxcox  # 非正态能力
stats-cli trend -f data.csv -c "weight" --test-type cusum  # 趋势分析
```

### MSA / Measurement System Analysis
```bash
stats-cli gage-rr crossed -f msa_data.json --tolerance 10.0  # 交叉 Gage R&R
stats-cli gage-rr bias -m 10.1 -m 10.2 -m 10.3 --reference-value 10.0  # 偏倚研究
stats-cli gage-rr stability -m 10.1 -m 10.2 -m 10.3 -m 10.4 -m 10.5  # 稳定性研究
```

### Reliability / Survival Analysis
```bash
stats-cli reliability weibull -t 100 -t 200 -t 300 -s 1 -s 1 -s 1  # Weibull 分析
stats-cli reliability stability -t 0 -t 3 -t 6 -t 9 -t 12 -v 100 -v 99 -v 98 -v 97 -v 96 --lsl 90  # 货架期
stats-cli reliability distribution -t 100 -t 200 -t 300 -s 1 -s 1 -s 1  # 分布拟合
```

### Multivariate Analysis
```bash
stats-cli multivariate pca -f data.csv -c "x1" -c "x2" -c "x3"  # 主成分分析
stats-cli multivariate cluster -f data.xlsx --method kmeans --n-clusters 3  # 聚类分析
stats-cli multivariate discriminant -f data.csv -c "x1" -c "x2" -g "group"  # 判别分析
stats-cli multivariate correlation_matrix -f data.csv  # 相关矩阵
```

### Time Series
```bash
stats-cli timeseries exp_smoothing -v 10 -v 12 -v 11 -v 13 -v 14 --frequency 4  # 指数平滑
stats-cli timeseries acf -f data.csv -c "residuals" --max-lag 20  # ACF/PACF 分析
stats-cli timeseries decomposition -f data.csv -c "monthly_sales" --frequency 12  # 季节分解
```

### DOE (Design of Experiments)
```bash
stats-cli doe full_factorial -f '{"name":"Temp","levels":3}' -f '{"name":"Time","levels":2}'  # 全因子设计
```

### Data Processing
```bash
stats-cli clean -f data.csv -c "weight" --method impute_mean  # 缺失值处理
stats-cli transform -f data.csv -c "weight" --method boxcox   # 数据变换
```

### Reporting
```bash
stats-cli report -f data.csv -c "weight" --usl 11.0 --lsl 9.0  # 综合报告
```

---

## Scenario-Based Workflows

### 场景1: "帮我分析这组数据"
```bash
# Step 1: 先看数据结构
stats-cli explore -f data.xlsx

# Step 2: 描述性统计
stats-cli descriptive -f data.xlsx -c "column_name"

# Step 3: 检查正态性
stats-cli normality -f data.xlsx -c "column_name"

# Step 4: 根据结果选择下一步
# - 正态？→ 可以做 t-test, ANOVA, capability
# - 非正态？→ 用 nonparametric 或 transform boxcox
```

### 场景2: "比较两批物料是否一致"
```bash
# 先检查正态性
stats-cli normality -f batch1.xlsx -c "weight"
stats-cli normality -f batch2.xlsx -c "weight"

# 正态 → t-test
stats-cli ttest two_sample -f batch1.xlsx -c "weight" -f2 batch2.xlsx -c2 "weight"

# 非正态 → Mann-Whitney
stats-cli nonparametric mann_whitney --x 10.2 --x 10.5 --y 11.3 --y 11.5
```

### 场景3: "评估工艺稳定性"
```bash
# 控制图
stats-cli control-chart imr -f data.csv -c "weight"

# 过程能力
stats-cli capability -f data.csv -c "weight" --usl 11.0 --lsl 9.0

# 趋势分析
stats-cli trend -f data.csv -c "weight" --test-type cusum
```

### 场景4: "验证测量系统"
```bash
# Gage R&R
stats-cli gage-rr crossed -f msa_data.json --tolerance 10.0

# 偏倚研究
stats-cli gage-rr bias -m 10.1 -m 10.2 -m 10.3 --reference-value 10.0
```

### 场景5: "预测未来趋势"
```bash
# 先看数据模式
stats-cli timeseries acf -f data.csv -c "value"

# 指数平滑预测
stats-cli timeseries exp_smoothing -f data.csv -c "value" --n-forecast 12
```

---

## Output Format

All commands output JSON:
```json
{
  "status": "success",
  "version": "0.3.0",
  "timestamp": "2026-06-02T10:00:00Z",
  "data": { ... }
}
```

---

## Error Handling

Error responses:
```json
{
  "status": "error",
  "error_type": "R_SCRIPT_ERROR",
  "message": "...",
  "suggestion": "..."
}
```

---

## File Support

| Format | Extension | Notes |
|--------|-----------|-------|
| Excel | .xlsx, .xls | Multi-sheet supported |
| CSV | .csv | Auto-detect encoding and delimiter |
| JSON | .json | Structured data |
| Text | .txt | One value per line |
