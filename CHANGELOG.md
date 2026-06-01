# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2026-06-01

### Added

#### Phase 1: Chart Capabilities
- **Interactive Charts**: Added Plotly-based interactive HTML charts
  - Control charts (I-MR, X-bar, R)
  - Histograms with normal curves
  - Q-Q plots
  - Process capability charts
  - Scatter plots
- **CLI Options**: Added `--interactive` flag for interactive charts
- **Charts Module**: Created `cli/charts.py` with chart generation functions

#### Phase 2: Statistical Functions
- **Non-parametric Tests**: Added Mann-Whitney U, Kruskal-Wallis, Wilcoxon signed-rank tests
  - `nonparametric mann_whitney` - Compare two independent groups
  - `nonparametric kruskal_wallis` - Compare multiple groups
  - `nonparametric wilcoxon` - Compare paired samples
- **Equivalence Tests**: Added TOST (Two One-Sided Tests)
  - `equivalence tost` - Two-sample equivalence test
  - `equivalence one_sample_tost` - One-sample equivalence test
- **Regression Diagnostics**: Added diagnostic plots for regression analysis
  - Residuals vs Fitted plot
  - Q-Q plot of residuals
  - Scale-Location plot
  - Cook's distance plot

#### Phase 3: Report Generation
- **HTML Reports**: Added comprehensive HTML report generation
  - Descriptive statistics report
  - Normality test report
  - Process capability report
  - Control chart report
  - Regression report
  - Comprehensive analysis report
- **CLI Options**: Added `--report` flag for HTML reports
- **Report Command**: Added `report` command for comprehensive analysis
- **Templates**: Created Jinja2 HTML templates
  - `base.html` - Base template with styling
  - `descriptive.html` - Descriptive statistics report
  - `comprehensive.html` - Comprehensive analysis report
- **Reports Module**: Created `cli/reports.py` with report generation functions

### Changed

#### Project Renaming
- **Name**: Renamed from `pharma-cli` to `stats-cli`
- **Version**: Updated to 0.3.0
- **Description**: Changed to "AI-friendly statistical analysis CLI for manufacturing"
- **Positioning**: Repositioned as general manufacturing statistical analysis tool

#### Documentation
- **README.md**: Completely rewritten with industry applicability sections
  - Pharmaceutical industry
  - Automotive industry
  - Electronics industry
  - Food & beverage industry
- **QUICK_START.md**: Updated with new commands and examples
- **CLAUDE_CODE_INTEGRATION.md**: Updated with new features
- **CHANGELOG.md**: Created this file

### Fixed

#### R Scripts
- **outlier.R**: Fixed empty vector handling in `round()` function
- **doe.R**: Fixed column name mismatch in `rbind()` for response surface design
- **regression.R**: Fixed `shapiro.test()` error for perfect fit

#### CLI
- **datetime import**: Added missing `datetime` import in main.py
- **Template missing**: Created `comprehensive.html` template

### Testing

#### Test Results
- **Total Tests**: 95
- **Pass Rate**: 100%
- **Code Coverage**: 52% (reduced due to new untested code)

#### New Features Tested
- Interactive charts generation
- Report generation
- Non-parametric tests
- Equivalence tests

## [0.2.0] - 2026-06-01

### Added

#### Core Features
- **11 Statistical Commands**: descriptive, normality, capability, control-chart, ttest, anova, regression, correlation, outlier, trend, doe
- **Input Validation**: Added validators module for input validation
- **Excel Support**: Added direct Excel file reading support
- **Chart Generation**: Added base64 PNG chart generation

#### Documentation
- **README.md**: Project documentation
- **SKILL.md**: Claude Code integration
- **TEST_REPORT.md**: Unit test report
- **REAL_DATA_TEST_REPORT.md**: Real data test report

#### Testing
- **Unit Tests**: 95 test cases
- **Code Coverage**: 78%
- **Real Data Testing**: 6 Excel files tested

### Fixed

#### R Scripts
- **regression.R**: Fixed `shapiro.test()` error for perfect fit
- **doe.R**: Fixed JSON parsing issues
- **trend.R**: Fixed `lambda` parameter issue

#### CLI
- **Excel reading**: Fixed multi-column data handling
- **Column matching**: Fixed numeric column name matching

## [0.1.0] - 2026-06-01

### Added

#### Initial Release
- **Project Structure**: Created CLI and R scripts structure
- **R Engine**: Added R script execution engine
- **Basic Commands**: Implemented core statistical commands
- **Documentation**: Added basic README and documentation

---

## Types of Changes

- **Added** for new features.
- **Changed** for changes in existing functionality.
- **Deprecated** for soon-to-be removed features.
- **Removed** for now removed features.
- **Fixed** for any bug fixes.
- **Security** in case of vulnerabilities.

---

## Version History

| Version | Date | Description |
|---------|------|-------------|
| 0.3.0 | 2026-06-01 | Mixed strategy implementation (charts, statistics, reports) |
| 0.2.0 | 2026-06-01 | Core features, Excel support, testing |
| 0.1.0 | 2026-06-01 | Initial release |

---

## Future Releases

### Planned for 0.4.0
- More control chart types (EWMA, CUSUM charts)
- Improved regression diagnostics
- More DOE methods
- Performance optimization

### Planned for 0.5.0
- GUI interface
- Advanced statistical methods
- Community features
- PyPI publication

---

**Maintained by**: Claude Code
**Repository**: https://github.com/haowuxiwang/pharma-cli
