# Incident Log Analyzer

A powerful Python tool for analyzing alert and incident logs from **NewRelic**, **Moogsoft**, and **ServiceNow**. Automatically identifies trends, data quality issues, and generates actionable insights.

## Features

- **Multi-Source Support**: Automatically detects and parses logs from NewRelic, Moogsoft, and ServiceNow
- **Large File Handling**: Optimized for files up to 100MB with chunked loading
- **Trend Analysis**: Identifies temporal patterns, volume spikes, and anomalies
- **Quality Analysis**: Detects duplicates, missing data, and inconsistencies
- **Smart Suggestions**: Generates prioritized, actionable recommendations
- **Multiple Output Formats**: Rich console output or JSON export

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd incident-log-analyzer

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Or install as package
pip install -e .
```

## Quick Start

### Web Interface (Recommended)

Launch the interactive web interface with drag-and-drop file upload:

```bash
# Start the web server
python analyze.py web

# Or use the installed command
incident-analyzer web

# Custom port
incident-analyzer web --port 8080
```

Then open http://localhost:5000 in your browser and drag your file onto the page.

![Web Interface Features]
- 📁 Drag-and-drop file upload
- 📊 Interactive results with tabs (Overview, Quality, Trends, Suggestions)
- 📈 Visual charts for hourly distribution and severity
- 💡 Prioritized recommendations with action items

### Command Line Analysis

```bash
# Full analysis with rich console output
python analyze.py analyze incidents.csv

# Or use the installed command
incident-analyzer analyze incidents.csv
```

### Analyze Multiple Files

```bash
incident-analyzer analyze newrelic_alerts.csv servicenow_incidents.xlsx moogsoft_events.csv
```

### Export Results as JSON

```bash
incident-analyzer analyze incidents.csv -o results.json

# Or just print JSON to stdout
incident-analyzer analyze incidents.csv --format json
```

### Quick Commands

```bash
# Show file information and column details
incident-analyzer info incidents.csv

# Run only quality analysis
incident-analyzer quality incidents.csv

# Run only trend analysis
incident-analyzer trends incidents.csv

# Launch web interface
incident-analyzer web
```

## Supported File Formats

| Format | Extensions | Notes |
|--------|-----------|-------|
| CSV | `.csv` | Chunked loading for large files |
| Excel | `.xlsx`, `.xls` | Requires openpyxl |

## Source System Detection

The analyzer automatically detects the source system based on column names:

### NewRelic
Detected columns: `incident_id`, `condition_name`, `policy_name`, `entity_name`, `violation_url`

### Moogsoft
Detected columns: `alert_id`, `situation_id`, `sig_id`, `source`, `class`, `manager`, `moog_id`

### ServiceNow
Detected columns: `number`, `sys_id`, `caller_id`, `assignment_group`, `short_description`, `priority`, `state`

## Analysis Output

### Trend Analysis
- **Temporal Patterns**: Hourly, daily, and monthly distributions
- **Volume Trends**: Week-over-week changes with direction
- **Peak Detection**: Identifies busiest hours and days
- **Anomaly Detection**: Flags unusual volume spikes

### Quality Analysis
- **Missing Data**: Identifies columns with null values
- **Duplicates**: Detects duplicate records and keys
- **Data Type Issues**: Finds unparseable dates and type mismatches
- **Value Problems**: Flags test values, placeholders, and inconsistencies
- **Completeness Score**: Overall data quality grade (A-F)

### Suggestions
Prioritized recommendations in categories:
- 🔴 **Critical**: Immediate attention required
- 🟠 **High**: Important issues to address
- 🟡 **Medium**: Improvements to consider
- 🟢 **Low**: Optimization opportunities

## Example Output

```
╭──────────────────────────────────────────────────────────╮
│              Incident Log Analysis Report                │
│              Analyzed 15,234 incidents                   │
╰──────────────────────────────────────────────────────────╯

File: servicenow_incidents.csv
Source System: ServiceNow

╭─ Data Quality ───────────────────────────────────────────╮
│ Dataset: 15,234 rows × 42 columns                        │
│ Memory Usage: 48.3 MB                                    │
│ Overall Fill Rate: 87.3%                                 │
│                                                          │
│ 📊 Completeness Score: 82/100 (Grade: B)                 │
│                                                          │
│ ⚠️  Issues Found: 12                                     │
│                                                          │
│ 🔴 High Severity Issues (3):                             │
│    • Critical column 'resolved_at' has 2,341 missing     │
│    • Found 156 duplicate values in key column 'number'   │
╰──────────────────────────────────────────────────────────╯

╭─ Recommendations ────────────────────────────────────────╮
│ 🔴 CRITICAL Priority (1)                                 │
│                                                          │
│   1. Critical Data Quality Issues Detected               │
│      Data quality score is 82/100. Issues may impact     │
│      analysis accuracy.                                  │
│      Recommended Actions:                                │
│        • Review and fix missing values                   │
│        • Investigate duplicate records                   │
╰──────────────────────────────────────────────────────────╯
```

## Programmatic Usage

```python
from src.data_loader import DataLoader
from src.trend_analyzer import TrendAnalyzer
from src.quality_analyzer import QualityAnalyzer
from src.suggestion_engine import SuggestionEngine

# Load data
loader = DataLoader()
df, source, metadata = loader.load_file('incidents.csv')

# Normalize column names
df = loader.normalize_dataframe(df, source)

# Run analyses
trend_results = TrendAnalyzer(df).analyze_all()
quality_results = QualityAnalyzer(df, source).analyze_all()

# Generate suggestions
engine = SuggestionEngine(df, trend_results, quality_results, source)
suggestions = engine.generate_all_suggestions()

# Get reports
print(engine.get_suggestions_report())
```

## Project Structure

```
incident-log-analyzer/
├── analyze.py              # Main entry point
├── requirements.txt        # Python dependencies
├── pyproject.toml         # Package configuration
├── README.md              # This file
├── src/
│   ├── __init__.py
│   ├── data_loader.py     # File loading and normalization
│   ├── trend_analyzer.py  # Trend and pattern analysis
│   ├── quality_analyzer.py # Data quality checks
│   ├── suggestion_engine.py # Recommendation generation
│   └── cli.py             # Command-line interface
├── tests/
│   └── test_analyzer.py   # Unit tests
└── sample_data/           # Sample incident files
```

## Configuration

### Adjusting Chunk Size for Large Files

```python
loader = DataLoader(chunk_size=100000)  # Process 100K rows at a time
```

### Custom Column Mappings

Extend `COLUMN_MAPPINGS` in `data_loader.py` to support additional source systems.

## Requirements

- Python 3.9+
- pandas >= 2.0.0
- openpyxl >= 3.1.0
- rich >= 13.0.0
- click >= 8.1.0
- numpy >= 1.24.0

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src/
ruff check src/
```

## License

MIT License - see LICENSE file for details.