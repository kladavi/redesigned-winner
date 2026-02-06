# Agent Guidelines for Incident Log Analyzer

This document establishes conventions and standards that AI coding agents must follow when working on this project.

## Documentation Requirements

**All work must be documented.** Before implementing any significant feature or change:

1. **Update `/docs/requirements.md`** - Add or modify requirements being addressed
2. **Update `/docs/design.md`** - Document design decisions and rationale
3. **Update `/docs/architecture.md`** - Update component diagrams or data flows if affected
4. **Add inline comments** - Complex logic must include explanatory comments

## Folder Structure

```
incident-log-analyzer/
├── .github/                    # GitHub-specific files
│   └── copilot-instructions.md # AI assistant context
├── docs/                       # Project documentation
│   ├── requirements.md         # Functional & non-functional requirements
│   ├── design.md              # Design decisions & patterns
│   └── architecture.md        # System architecture & data flows
├── src/                        # Source code (all Python modules)
│   ├── __init__.py
│   ├── cli.py                 # Command-line interface
│   ├── data_loader.py         # Data loading & normalization
│   ├── trend_analyzer.py      # Trend analysis engine
│   ├── quality_analyzer.py    # Quality analysis engine
│   └── suggestion_engine.py   # Recommendation engine
├── tests/                      # Test files (mirror src/ structure)
│   ├── __init__.py
│   └── test_*.py              # Test modules
├── scripts/                    # Utility scripts (not core logic)
│   └── generate_sample_data.py
├── sample_data/                # Generated test data (gitignored if large)
├── analyze.py                  # Main entry point
├── requirements.txt            # Python dependencies
├── pyproject.toml             # Package configuration
├── README.md                   # User-facing documentation
└── AGENT.md                    # This file - agent guidelines
```

## Naming Standards

### Files
| Type | Convention | Example |
|------|------------|---------|
| Python modules | `snake_case.py` | `data_loader.py` |
| Test files | `test_<module>.py` | `test_data_loader.py` |
| Documentation | `lowercase.md` | `architecture.md` |
| Scripts | `snake_case.py` | `generate_sample_data.py` |

### Code
| Type | Convention | Example |
|------|------------|---------|
| Classes | `PascalCase` | `TrendAnalyzer`, `DataLoader` |
| Functions/Methods | `snake_case` | `load_file()`, `analyze_all()` |
| Constants | `UPPER_SNAKE_CASE` | `SOURCE_SIGNATURES`, `COLUMN_MAPPINGS` |
| Private methods | `_leading_underscore` | `_detect_source()`, `_prepare_data()` |
| Variables | `snake_case` | `file_path`, `trend_results` |

### Branches & Commits
- Branch names: `feature/<description>`, `fix/<description>`, `docs/<description>`
- Commit messages: Start with verb (Add, Fix, Update, Remove, Refactor)

## Adding New Features

### New Source System Support
1. Add column signatures to `SOURCE_SIGNATURES` in `data_loader.py`
2. Add column mappings to `COLUMN_MAPPINGS` in `data_loader.py`
3. Add test cases in `tests/test_analyzer.py`
4. Update `/docs/requirements.md` with new source requirements
5. Update `README.md` with detection columns

### New Analysis Type
1. Create new analyzer in `src/<type>_analyzer.py`
2. Follow existing pattern: `__init__(df)`, `analyze_all()`, `get_<type>_report()`
3. Integrate into `cli.py` and suggestion engine
4. Add comprehensive tests
5. Document in `/docs/design.md`

### New Suggestion Category
1. Add to `SuggestionCategory` enum in `suggestion_engine.py`
2. Create analysis method `_analyze_<category>()`
3. Add tests for suggestion generation
4. Document evidence fields in `/docs/design.md`

## Code Quality Standards

### Required for All Changes
- [ ] Type hints on function signatures
- [ ] Docstrings on public classes and methods
- [ ] Unit tests for new functionality
- [ ] No hardcoded values (use constants or config)
- [ ] Error handling with meaningful messages

### Testing Requirements
- Minimum test coverage for new code: 80%
- Test edge cases: empty data, missing columns, invalid types
- Use pytest fixtures for sample data

### Before Committing
```bash
# Run tests
pytest tests/ -v

# Check code style (if installed)
black src/ --check
ruff check src/
```

## Data Flow Overview

```
Input Files (CSV/XLSX)
        │
        ▼
┌─────────────────┐
│   DataLoader    │ ──► Source detection, normalization
└────────┬────────┘
         │
         ▼
    pd.DataFrame (normalized)
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐  ┌────────┐
│ Trend  │  │Quality │
│Analyzer│  │Analyzer│
└───┬────┘  └───┬────┘
    │           │
    └─────┬─────┘
          ▼
   ┌──────────────┐
   │  Suggestion  │
   │    Engine    │
   └──────┬───────┘
          │
          ▼
   Prioritized Suggestions
          │
          ▼
   ┌──────────────┐
   │     CLI      │ ──► Console output or JSON
   └──────────────┘
```

## Questions?

If unclear about conventions, check:
1. This file (`AGENT.md`)
2. Existing code patterns in `src/`
3. Test examples in `tests/`
4. Documentation in `/docs/`
