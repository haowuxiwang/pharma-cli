# stats-cli

AI-friendly statistical analysis CLI for manufacturing, powered by R.

**Version**: 0.4.0  
**Commands**: 26  
**Tests**: 385 (88% coverage)  
**JMP/Minitab Coverage**: ~75%

---

## Features

### Data Exploration
- **explore**: Inspect Excel/CSV structure (columns, types, missing values)
- **discover**: List all available commands and schemas

### Basic Statistics
- **descriptive**: Mean, median, SD, RSD%, range, quartiles, 95% CI, skewness, kurtosis
- **normality**: Shapiro-Wilk, Anderson-Darling, Lilliefors tests
- **outlier**: Grubbs, Dixon, IQR, Z-score outlier detection

### Hypothesis Testing
- **ttest**: One-sample, two-sample, paired t-tests
- **anova**: One-way, two-way ANOVA with Tukey post-hoc
- **nonparametric**: Mann-Whitney, Kruskal-Wallis, Wilcoxon, Chi-square, Friedman
- **homogeneity**: Levene, Bartlett variance tests
- **multiple-comparison**: Tukey, Bonferroni, Scheffe
- **equivalence**: TOST (Two One-Sided Tests)
- **power**: Sample size and power analysis (t-test, ANOVA, proportion)

### Regression & Correlation
- **regression**: Linear, quadratic, polynomial, multiple, logistic, stepwise
- **correlation**: Pearson, Spearman, Kendall

### SPC / Quality Control
- **control-chart**: X-bar, R, I-MR, p, np, c, u, EWMA, CUSUM
- **capability**: Cp, Cpk, Pp, Ppk, Cpm, Box-Cox non-normal capability
- **trend**: CUSUM, EWMA, runs test

### MSA (Measurement System Analysis)
- **gage-rr**: Crossed, nested, attribute, bias, linearity, stability

### Reliability
- **reliability**: Weibull, Kaplan-Meier, distribution fitting, stability/shelf life

### Multivariate
- **multivariate**: PCA, cluster (hierarchical/k-means), discriminant, correlation matrix

### Time Series
- **timeseries**: Exponential smoothing, ARIMA, decomposition, ACF/PACF

### DOE
- **doe**: Full factorial, fractional factorial, response surface, Taguchi

### Data Processing
- **clean**: Drop, impute mean/median, winsorize, clip
- **transform**: Log, sqrt, Box-Cox, Johnson, rank, standardize, reciprocal

### Reporting
- **report**: Comprehensive HTML report
- **run**: Execute custom R scripts

---

## Prerequisites

1. **R** installed (set `RSCRIPT_PATH` env var or add R to PATH)
2. **R packages**:

```r
install.packages(c("jsonlite", "qcc", "nortest", "car", "MASS", "base64enc", "survival"), repos="https://cloud.r-project.org")
```

---

## Installation

```bash
# From source
git clone https://github.com/haowuxiwang/pharma-cli.git
cd pharma-cli
pip install -e .
```

---

## Quick Start

```bash
# Explore data structure
stats-cli explore -f data.xlsx

# Descriptive statistics
stats-cli descriptive -f data.csv -c "weight"

# Normality test
stats-cli normality -f data.csv -c "weight"

# Process capability
stats-cli capability -f data.csv -c "weight" --usl 11.0 --lsl 9.0

# Control chart
stats-cli control-chart imr -f data.csv -c "weight"

# t-test
stats-cli ttest two_sample -v 10.2 -v 10.5 -v2 11.3 -v2 11.5
```

---

## All Commands

| Category | Commands |
|----------|----------|
| Data Exploration | `explore`, `discover` |
| Basic Statistics | `descriptive`, `normality`, `outlier` |
| Hypothesis Testing | `ttest`, `anova`, `nonparametric`, `homogeneity`, `multiple-comparison`, `equivalence`, `power` |
| Regression | `regression`, `correlation` |
| SPC | `control-chart`, `capability`, `trend` |
| MSA | `gage-rr` |
| Reliability | `reliability` |
| Multivariate | `multivariate` |
| Time Series | `timeseries` |
| DOE | `doe` |
| Data Processing | `clean`, `transform` |
| Reporting | `report`, `run` |

---

## Decision Trees for AI Agents

### Comparing Groups
```
2 groups → normality check → t-test or Mann-Whitney
3+ groups → normality check → ANOVA or Kruskal-Wallis
Paired → normality check → paired t-test or Wilcoxon
```

### Relationship Analysis
```
2 continuous → correlation or linear regression
Multiple predictors → multiple or stepwise regression
Binary outcome → logistic regression
Many variables → PCA or cluster
```

### Quality Control
```
Monitor stability → control-chart imr/xbar
Assess capability → capability with USL/LSL
Verify measurement → gage-rr
Analyze failures → reliability weibull
```

---

## Output Format

All commands output JSON:

```json
{
  "status": "success",
  "version": "0.4.0",
  "timestamp": "2026-06-02T10:00:00Z",
  "data": {
    "n": 5,
    "mean": 10.3,
    "std": 0.1581,
    "interpretation": "..."
  }
}
```

---

## File Support

| Format | Extension | Notes |
|--------|-----------|-------|
| Excel | .xlsx, .xls | Multi-sheet with `--sheet` |
| CSV | .csv | Auto-detect encoding and delimiter |
| JSON | .json | Structured data |
| Text | .txt | One value per line |

---

## Testing

```bash
python -m pytest tests/ -v
```

- **Test Cases**: 385
- **Pass Rate**: 100%
- **Code Coverage**: 88%

---

## Project Structure

```
pharma-cli/
├── cli/                  # Python CLI
│   ├── main.py           # Entry point (60 lines)
│   ├── r_engine.py       # R script executor
│   ├── data_cleaner.py   # Dirty data handler
│   ├── charts.py         # Plotly charts
│   ├── reports.py        # Jinja2 reports
│   ├── validators.py     # Input validation
│   └── commands/         # 26 command modules
├── r_scripts/            # 23 R scripts
├── tests/                # 385 tests
├── .claude/skills/       # Claude Code Skill
├── SKILL.md              # Skill definition
└── excel/                # Test data
```

---

## License

MIT

---

## Support

- **Issues**: https://github.com/haowuxiwang/pharma-cli/issues
