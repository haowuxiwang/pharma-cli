# pharma-cli

AI-agent-friendly statistical analysis CLI powered by R.

Designed for local AI agents (Claude Code, Cursor, etc.) to perform statistical analysis programmatically.

## Features

### Core Statistics
- **descriptive**: Mean, median, SD, RSD%, range, quartiles, 95% CI, skewness, kurtosis
- **normality**: Shapiro-Wilk, Anderson-Darling, Lilliefors tests
- **capability**: Cp, Cpk, Pp, Ppk (pharma-compliant)

### Hypothesis Testing
- **ttest**: One-sample, two-sample, paired t-tests
- **anova**: One-way, two-way ANOVA with Tukey post-hoc

### Statistical Process Control
- **control-chart**: X-bar, R, I-MR, p, np, c, u charts with Western Electric rules

### Regression & Correlation
- **regression**: Linear, quadratic, polynomial regression
- **correlation**: Pearson, Spearman, Kendall correlation

### Quality Tools
- **outlier**: Grubbs, Dixon, IQR, Z-score outlier detection
- **trend**: CUSUM, EWMA, runs test for trend detection
- **doe**: Full factorial, fractional factorial, response surface designs

### Chart Generation
- **--plot**: Generate base64-encoded PNG charts for visualization

### Advanced
- **run**: Execute custom R scripts with JSON I/O

## Prerequisites

1. **R** installed at `D:\R-4.6.0\bin` (or set `RSCRIPT_PATH` env var)
2. **R packages**: `jsonlite`, `qcc`, `nortest`, `car`, `MASS`

Install R packages:
```r
install.packages(c("jsonlite", "qcc", "nortest", "car", "MASS"), repos="https://cloud.r-project.org")
```

## Installation

```bash
# From PyPI (when published)
pip install pharma-cli

# From source
git clone https://github.com/your-username/pharma-cli.git
cd pharma-cli
pip install -e .
```

## Usage Examples

### Descriptive Statistics
```bash
pharma-cli descriptive -v 10.2 -v 10.5 -v 10.1 -v 10.3 -v 10.4
pharma-cli descriptive -f data.csv -c "Concentration"
```

### Normality Test
```bash
pharma-cli normality -f data.txt
```

### Process Capability
```bash
pharma-cli capability -f data.txt --usl 11.0 --lsl 9.0 --target 10.0
```

### Control Charts
```bash
pharma-cli control-chart imr -f data.txt
pharma-cli control-chart xbar -f data.csv -c "measurement" --subgroup-size 5
```

### t-Tests
```bash
pharma-cli ttest one_sample -v 10.2 -v 10.5 -v 10.1 --mu 10.0
pharma-cli ttest two_sample -v 10.2 -v 10.5 -v 10.1 -v2 11.3 -v2 11.5 -v2 11.1
pharma-cli ttest paired -v 10.2 -v 10.5 -v 10.1 -v2 10.8 -v2 10.9 -v2 10.7
```

### ANOVA
```bash
pharma-cli anova one_way -g '[10.2,10.5,10.1]' -g '[11.3,11.5,11.1]' -g '[10.8,10.9,10.7]'
```

### Regression
```bash
pharma-cli regression --x 1 --x 2 --x 3 --x 4 --x 5 --y 2.1 --y 3.9 --y 6.2 --y 7.8 --y 10.1 --type linear
```

### Correlation
```bash
pharma-cli correlation --x 1 --x 2 --x 3 --x 4 --x 5 --y 2.1 --y 3.9 --y 6.2 --y 7.8 --y 10.1 --method pearson
```

### Outlier Detection
```bash
pharma-cli outlier -v 10.2 -v 10.5 -v 10.1 -v 10.3 -v 15.0 --method grubbs
```

### Trend Analysis
```bash
pharma-cli trend -f data.txt --test-type cusum --target 10.0
pharma-cli trend -f data.txt --test-type ewma --lambda 0.2
```

### Design of Experiments
```bash
pharma-cli doe full_factorial -f '{"name":"Temp","levels":3}' -f '{"name":"Time","levels":2}' -r '[10,12,11,13,12,14]'
```

### Custom R Script
```bash
pharma-cli run my_script.R -d '{"values": [1, 2, 3]}'
```

## Chart Generation

Add `--plot` flag to generate base64-encoded PNG charts:

```bash
# Control chart with visualization
pharma-cli --plot control-chart imr -v 10.2 -v 10.5 -v 10.1 -v 10.3 -v 10.4

# Normality test with histogram and Q-Q plot
pharma-cli --plot normality -v 10.2 -v 10.5 -v 10.1 -v 10.3 -v 10.4

# Capability analysis with specification limits
pharma-cli --plot capability -v 10.2 -v 10.5 -v 10.1 --usl 11.0 --lsl 9.0
```

The `plot` field in JSON output contains the base64-encoded PNG image.

## Output Format

All commands output JSON to stdout:

```json
{
  "n": 5,
  "mean": 10.3,
  "median": 10.3,
  "std": 0.1581,
  "rsd_percent": 1.54,
  "interpretation": "..."
}
```

## For AI Agents

### Claude Code Integration

pharma-cli includes a SKILL.md file for automatic discovery by Claude Code. After installation, Claude Code will automatically use pharma-cli when statistical analysis is needed.

### Manual Usage

```bash
# Descriptive statistics
pharma-cli descriptive -v 1.2 -v 1.3 -v 1.4

# From file
pharma-cli descriptive -f data.csv -c "Column1"

# With chart generation
pharma-cli --plot control-chart imr -f data.csv -c "measurement"
```

### JSON Output

All commands output JSON to stdout, making it easy for AI agents to parse:

```json
{
  "n": 5,
  "mean": 10.3,
  "std": 0.1581,
  "interpretation": "..."
}
```

### Chart Visualization

Use `--plot` flag to get base64-encoded PNG charts for visualization.

## License

MIT
