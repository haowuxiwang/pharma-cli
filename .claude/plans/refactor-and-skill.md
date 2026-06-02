# Python Fallback 实现计划

## 问题

飞书 Aily 环境没有 R，导致 22/24 个命令失败。只有 `explore` 和 `discover` 可用。

## 解决方案

添加 Python fallback，让基础统计功能在没有 R 的情况下也能工作。

## 实现计划

### Step 1: 添加 scipy 依赖

修改 `setup.py`，添加 `scipy` 到 `install_requires`。

### Step 2: 创建 Python 统计引擎

新建 `cli/py_engine.py`，实现以下功能：

```python
# Tier 1 - 纯 numpy（已有）
def descriptive(values)      # 均值、中位数、标准差、四分位、CI
def clean_data(values, method)  # drop/impute/winsorize/clip
def transform_data(values, method)  # log/sqrt/boxcox/standardize
def outlier_detection(values, method)  # iqr/zscore

# Tier 2 - 需要 scipy
def normality_test(values)   # Shapiro-Wilk, Anderson-Darling
def ttest(data, type)        # 单样本/双样本/配对
def correlation(x, y, method)  # Pearson/Spearman/Kendall
def nonparametric_test(data, type)  # Mann-Whitney, Kruskal-Wallis
```

### Step 3: 修改 r_engine.py

在 `run_r_file()` 中添加 R 检测：
- 如果 R 未安装，返回 `{"error": True, "error_type": "R_NOT_FOUND", "suggestion": "Install R or use Python fallback"}`
- 不再抛出 RuntimeError

### Step 4: 修改命令添加 fallback

对每个支持 Python fallback 的命令：
```python
@click.command()
def descriptive(...):
    data = load_data(...)
    try:
        result = run_r_file("descriptive.R", data)
    except RNotFoundError:
        result = py_descriptive(data)  # Python fallback
    output(result)
```

### Step 5: 更新 SKILL.md

添加说明：
```
## Python Fallback

如果 R 未安装，以下命令仍可使用 Python 实现：
- descriptive, clean, transform, outlier (IQR/Z-score)
- normality, ttest, correlation, nonparametric (需要 scipy)
```

## 预期结果

| 场景 | 之前 | 之后 |
|------|------|------|
| 有 R 环境 | 24/24 命令可用 | 24/24 命令可用 |
| 无 R 环境 | 2/24 命令可用 | 10/24 命令可用 |
