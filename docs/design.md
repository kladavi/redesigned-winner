# Design Document - Incident Log Analyzer

## Overview
This document captures key design decisions, patterns, and rationale for the Incident Log Analyzer system.

---

## Design Principles

1. **Separation of Concerns** - Each module handles a single responsibility
2. **Extensibility** - Easy to add new source systems and analysis types
3. **Fail-Safe Defaults** - System handles missing/malformed data gracefully
4. **Evidence-Based Suggestions** - All recommendations include supporting data

---

## Module Design

### DataLoader (`data_loader.py`)

**Purpose:** Load, detect, and normalize incident data from multiple sources.

**Key Design Decisions:**

| Decision | Rationale |
|----------|-----------|
| Chunked CSV loading | Memory efficiency for large files (>50MB) |
| Signature-based source detection | Flexible, doesn't require user input |
| Score-based matching (not exact) | Handles partial column sets and variations |
| Normalization to common schema | Enables source-agnostic downstream analysis |

**Extension Points:**
- `SOURCE_SIGNATURES`: Add new source column patterns
- `COLUMN_MAPPINGS`: Define normalization rules for new sources

**Data Structures:**
```python
SOURCE_SIGNATURES = {
    'source_name': ['col1', 'col2', ...]  # Columns that identify this source
}

COLUMN_MAPPINGS = {
    'source_name': {
        'original_col': 'normalized_col',  # Maps source to standard schema
    }
}
```

---

### TrendAnalyzer (`trend_analyzer.py`)

**Purpose:** Identify temporal patterns, volume trends, and anomalies.

**Key Design Decisions:**

| Decision | Rationale |
|----------|-----------|
| Auto-detect time column | Flexibility across different source schemas |
| 2σ threshold for anomalies | Standard statistical approach, catches significant outliers |
| 7-day rolling window for trends | Weekly patterns are common in IT operations |
| Category analysis limit (5 cols) | Performance balance, focus on most relevant |

**Analysis Methods:**

| Method | Output |
|--------|--------|
| `_analyze_temporal_patterns()` | Hourly/daily/monthly distributions, peaks |
| `_calculate_trend()` | Week-over-week direction and % change |
| `_detect_anomalies()` | Days exceeding mean + 2σ volume |
| `_analyze_categories()` | Top values per categorical column |
| `_find_correlations()` | Cross-tabulation of category pairs |

---

### QualityAnalyzer (`quality_analyzer.py`)

**Purpose:** Identify data quality issues affecting analysis reliability.

**Key Design Decisions:**

| Decision | Rationale |
|----------|-----------|
| Critical column weighting | Missing IDs/timestamps more impactful than optional fields |
| Severity levels (high/medium/low) | Prioritize remediation efforts |
| Completeness score formula | `weighted_fill_rate - duplicate_penalty` |
| Pattern-based value checking | Catches common placeholders (test, N/A, TBD) |

**Quality Checks:**

| Check | Severity | Example Issue |
|-------|----------|---------------|
| Critical column nulls | High | `incident_id` has 5% missing |
| Duplicate key values | High | Same `number` appears 3 times |
| Full row duplicates | Medium | Entire rows duplicated |
| Time order violations | High | `resolved_time` before `created_time` |
| Unparseable dates | Medium | Date string cannot be parsed |
| Placeholder values | Low | "TBD", "N/A", "test" in fields |
| Case inconsistencies | Low | "High" vs "high" in severity |

**Completeness Score Calculation:**
```
score = (weighted_fill_sum / total_weights) * 100
score -= (duplicate_percent / total_rows) * 10  # Penalty
grade = A (90+), B (80-89), C (70-79), D (60-69), F (<60)
```

---

### SuggestionEngine (`suggestion_engine.py`)

**Purpose:** Generate actionable, prioritized recommendations.

**Key Design Decisions:**

| Decision | Rationale |
|----------|-----------|
| Dataclass for Suggestion | Type safety, clear structure |
| Enum for Priority/Category | Consistent values, IDE support |
| Evidence field required | Justifies each recommendation |
| Actions list (not single) | Multiple remediation paths |

**Suggestion Structure:**
```python
@dataclass
class Suggestion:
    title: str                    # Short, scannable headline
    description: str              # Context and impact
    priority: SuggestionPriority  # CRITICAL, HIGH, MEDIUM, LOW
    category: SuggestionCategory  # DATA_QUALITY, TREND_INSIGHT, etc.
    actions: List[str]            # Specific steps to take
    evidence: Dict[str, Any]      # Data supporting the suggestion
```

**Priority Triggers:**

| Priority | Condition |
|----------|-----------|
| CRITICAL | Quality score <70, or >20% critical data missing |
| HIGH | Volume increase >20%, or >30% high-severity incidents |
| MEDIUM | Volume spikes detected, duplicate records found |
| LOW | Optimization opportunities, further analysis suggestions |

---

### CLI (`cli.py`)

**Purpose:** User interface via command line with rich output.

**Key Design Decisions:**

| Decision | Rationale |
|----------|-----------|
| Click framework | Declarative, auto-generates help |
| Rich library for output | Beautiful, readable console output |
| Separate commands (analyze, info, quality, trends) | Flexibility, quick checks |
| JSON export option | Integration with other tools |
| Progress spinners | User feedback for long operations |

**Command Structure:**
```
incident-analyzer
├── analyze <files>  # Full analysis
├── info <file>      # Quick file info
├── quality <file>   # Quality-only analysis  
└── trends <file>    # Trends-only analysis
```

---

## Error Handling Strategy

| Scenario | Handling |
|----------|----------|
| File not found | Raise `FileNotFoundError` with path |
| Unsupported format | Raise `ValueError` with supported formats |
| No time column found | Skip temporal analysis, log warning |
| Parse failures | Use `errors='coerce'`, count failures |
| Memory pressure | Chunked loading, limit analysis scope |

---

## Performance Considerations

1. **Large File Loading**: Chunked reading (50K rows default) for CSV >50MB
2. **Analysis Limits**: Category analysis limited to top 5 categorical columns
3. **Lazy Evaluation**: Time parsing only when column is used
4. **Memory**: DataFrame copies minimized, use views where possible

---

## Testing Strategy

| Test Type | Location | Coverage Target |
|-----------|----------|-----------------|
| Unit tests | `tests/test_analyzer.py` | Per-module, 80%+ |
| Fixture data | Test file fixtures | All source types |
| Edge cases | Inline in test classes | Empty data, nulls, invalid types |

---

## Change Log

| Date | Version | Change | Author |
|------|---------|--------|--------|
| 2026-02-06 | 1.0 | Initial design documentation | System |
