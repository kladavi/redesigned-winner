# Copilot Instructions for Incident Log Analyzer

## ⚠️ Documentation Requirements
**Before implementing any feature, update the relevant documentation:**
- `/docs/requirements.md` - Add/modify requirements being addressed
- `/docs/design.md` - Document design decisions
- `/docs/architecture.md` - Update if affecting component interactions
- See `AGENT.md` for complete conventions and naming standards

## Project Overview
This is a Python CLI tool that analyzes alert/incident log files from NewRelic, Moogsoft, and ServiceNow. It identifies trends, data quality issues, and generates actionable suggestions.

## Architecture
- `src/data_loader.py` - Loads CSV/XLSX files, auto-detects source system, normalizes columns
- `src/trend_analyzer.py` - Identifies temporal patterns, volume trends, anomalies
- `src/quality_analyzer.py` - Checks for duplicates, missing data, type issues
- `src/suggestion_engine.py` - Generates prioritized recommendations
- `src/cli.py` - Click-based CLI with rich console output

## Key Patterns

### Source Detection
The `DataLoader._detect_source()` matches column names against signatures:
- ServiceNow: `number`, `sys_id`, `short_description`, `priority`, `state`
- NewRelic: `incident_id`, `condition_name`, `policy_name`, `entity_name`  
- Moogsoft: `alert_id`, `sig_id`, `source`, `class`, `severity`

### Column Normalization
Use `COLUMN_MAPPINGS` in `data_loader.py` to map source-specific columns to standard names (`id`, `title`, `severity`, `created_time`, etc.)

### Adding New Suggestions
Add methods to `SuggestionEngine` that append `Suggestion` objects:
```python
self.suggestions.append(Suggestion(
    title="...",
    description="...",
    priority=SuggestionPriority.HIGH,
    category=SuggestionCategory.OPERATIONAL,
    actions=["Action 1", "Action 2"],
    evidence={'key': 'value'}
))
```

## Naming Standards
- **Files**: `snake_case.py` (e.g., `data_loader.py`)
- **Classes**: `PascalCase` (e.g., `TrendAnalyzer`)
- **Functions**: `snake_case` (e.g., `load_file()`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `SOURCE_SIGNATURES`)
- **Tests**: `test_<module>.py` (e.g., `test_data_loader.py`)

## Commands
```bash
pip install -r requirements.txt      # Install dependencies
python analyze.py analyze file.csv   # Run full analysis
pytest tests/                        # Run tests
python scripts/generate_sample_data.py  # Generate test data
```

## Testing
- Tests are in `tests/test_analyzer.py` using pytest
- Use fixtures for sample DataFrames
- Test source detection, normalization, and suggestion generation
