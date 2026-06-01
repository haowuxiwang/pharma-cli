---
name: stats-cli
description: Use when user needs statistical analysis, SPC control charts, process capability, hypothesis testing, regression, DOE, outlier detection, or trend analysis. Triggers: 统计分析, 控制图, 过程能力, t检验, ANOVA, 回归, DOE, 正态性检验, 异常值, 趋势分析, SPC, Cp, Cpk, capability, normality, regression, correlation, outlier, quality, manufacturing.
---

# stats-cli

AI-friendly statistical analysis CLI for manufacturing.

## Prerequisites

1. **R** installed (set `RSCRIPT_PATH` env var or add R to PATH)
2. **R packages**: `jsonlite`, `qcc`, `nortest`, `car`, `MASS`, `base64enc`

Install R packages:
```r
install.packages(c("jsonlite", "qcc", "nortest", "car", "MASS", "base64enc"), repos="https://cloud.r-project.org")
```

## Installation

```bash
pip install stats-cli
# or
cd stats-cli && pip install -e .
```

## Commands

### Descriptive Statistics
```bash
stats-cli descriptive -v 10.2 -v 10.5 -v 10.1 -v 10.3 -v 10.4
stats-cli descriptive -f data.csv -c "Column1"
```
Output: mean, median, SD, RSD%, range, quartiles, 95% CI, skewness, kurtosis

### Normality Tests
```bash
stats-cli normality -v 10.2 -v 10.5 -v 10.1 -v 10.3 -v 10.4
stats-cli normality -f data.txt
```
Output: Shapiro-Wilk, Anderson-Darling, Lilliefors tests + histogram data + Q-Q plot data

### Process Capability
```bash
stats-cli capability -v 10.2 -v 10.5 -v 10.1 --usl 11.0 --lsl 9.0
stats-cli capability -f data.csv -c "Concentration" --usl 11.0 --lsl 9.0 --target 10.0
```
Output: Cp, Cpk, Pp, Ppk, capability rating

### Control Charts
```bash
stats-cli control-chart imr -v 10.2 -v 10.5 -v 10.1 -v 10.3 -v 10.4
stats-cli control-chart xbar -f data.csv -c "measurement" --subgroup-size 5
```
Chart types: `xbar`, `r`, `imr`, `p`, `np`, `c`, `u`
Output: center, UCL, LCL, out-of-control points, Western Electric rule violations

### t-Tests
```bash
stats-cli ttest one_sample -v 10.2 -v 10.5 -v 10.1 --mu 10.0
stats-cli ttest two_sample -v 10.2 -v 10.5 -v2 11.3 -v2 11.5
stats-cli ttest paired -v 10.2 -v 10.5 -v2 10.8 -v2 10.9
```
Output: t-statistic, p-value, significance

### ANOVA
```bash
stats-cli anova one_way -g '[10.2,10.5,10.1]' -g '[11.3,11.5,11.1]' -g '[10.8,10.9,10.7]'
```
Output: F-statistic, p-value, significance, Tukey post-hoc (for one-way)

### Regression
```bash
stats-cli regression --x 1 --x 2 --x 3 --x 4 --x 5 --y 2.1 --y 3.9 --y 6.2 --y 7.8 --y 10.1 --type linear
```
Types: `linear`, `quadratic`, `polynomial`
Output: R-squared, coefficients, p-values

### Correlation
```bash
stats-cli correlation --x 1 --x 2 --x 3 --x 4 --x 5 --y 2.1 --y 3.9 --y 6.2 --y 7.8 --y 10.1 --method pearson
```
Methods: `pearson`, `spearman`, `kendall`
Output: correlation coefficient, p-value, R-squared

### Outlier Detection
```bash
stats-cli outlier -v 10.2 -v 10.5 -v 10.1 -v 10.3 -v 15.0 --method grubbs
```
Methods: `grubbs`, `dixon`, `iqr`, `zscore`
Output: outliers detected, clean data

### Trend Analysis
```bash
stats-cli trend -v 10.2 -v 10.5 -v 10.1 -v 10.3 -v 10.4 --test-type cusum --target 10.3
```
Test types: `cusum`, `ewma`, `runs`
Output: CUSUM values, alarm points, stability assessment

### Design of Experiments
```bash
stats-cli doe full_factorial -f '{"name":"Temp","levels":3}' -f '{"name":"Time","levels":2}' -r '[10,12,11,13,12,14]'
```
DOE types: `full_factorial`, `fractional_factorial`, `response_surface`
Output: design matrix, main effects, ANOVA table

## Chart Generation

Add `--plot` flag to generate base64-encoded PNG charts:

```bash
stats-cli --plot control-chart imr -v 10.2 -v 10.5 -v 10.1 -v 10.3 -v 10.4
stats-cli --plot normality -v 10.2 -v 10.5 -v 10.1 -v 10.3 -v 10.4
stats-cli --plot capability -v 10.2 -v 10.5 -v 10.1 --usl 11.0 --lsl 9.0
```

The `plot` field in JSON output contains the base64-encoded PNG image.

## JSON Output Format

All commands output JSON to stdout:

```json
{
  "n": 5,
  "mean": 10.3,
  "median": 10.3,
  "std": 0.1581,
  "interpretation": "..."
}
```

## AI Agent Usage Notes

1. **Always parse JSON output** - The CLI returns structured JSON
2. **Use `--plot` for visualization** - Returns base64 PNG in `plot` field
3. **File input** - Use `-f` for file input (supports .txt, .csv, .json)
4. **Column selection** - Use `-c` to specify CSV column name
5. **Multiple values** - Use `-v` flag repeatedly for multiple values
6. **Groups for ANOVA** - Use `-g` with JSON arrays: `-g '[1,2,3]' -g '[4,5,6]'`

## Common Workflows

### 1. Data Quality Check
```bash
# Check for outliers
stats-cli outlier -f data.csv -c "measurement" --method grubbs

# Check normality
stats-cli normality -f data.csv -c "measurement"
```

### 2. Process Capability Study
```bash
# Descriptive stats
stats-cli descriptive -f data.csv -c "measurement"

# Normality check
stats-cli normality -f data.csv -c "measurement"

# Capability analysis
stats-cli capability -f data.csv -c "measurement" --usl 11.0 --lsl 9.0
```

### 3. SPC Monitoring
```bash
# I-MR chart for individual measurements
stats-cli control-chart imr -f data.csv -c "measurement"

# X-bar chart for subgroups
stats-cli control-chart xbar -f data.csv -c "measurement" --subgroup-size 5
```

## Error Handling

- If R is not found, set `RSCRIPT_PATH` environment variable
- If R packages are missing, install them with `install.packages()`
- Minimum sample sizes: normality (3), capability (2), control charts (2)
