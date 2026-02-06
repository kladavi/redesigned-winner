# Architecture - Incident Log Analyzer

## Overview
This document describes the system architecture, component interactions, and data flows for the Incident Log Analyzer.

---

## System Context

```
┌─────────────────────────────────────────────────────────────────────┐
│                         External Systems                             │
├─────────────────┬─────────────────┬─────────────────────────────────┤
│   ServiceNow    │    NewRelic     │           Moogsoft              │
│   (Incidents)   │    (Alerts)     │           (Alerts)              │
└────────┬────────┴────────┬────────┴────────────┬────────────────────┘
         │                 │                      │
         │    Export CSV/XLSX files manually      │
         │                 │                      │
         ▼                 ▼                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Incident Log Analyzer                             │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                      File System                             │    │
│  │   *.csv, *.xlsx files (up to 100MB)                         │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                              │                                       │
│         ┌────────────────────┼────────────────────┐                 │
│         ▼                    ▼                    ▼                 │
│  ┌─────────────┐    ┌─────────────────┐    ┌──────────────┐        │
│  │ Web Browser │    │ Analysis Engine │    │     CLI      │        │
│  │ (drag/drop) │    │                 │    │   (commands) │        │
│  └──────┬──────┘    └────────┬────────┘    └──────┬───────┘        │
│         │                    │                    │                 │
│         └────────────────────┼────────────────────┘                 │
│                              ▼                                       │
│               ┌──────────────┼──────────────┐                       │
│               ▼              ▼              ▼                       │
│        ┌──────────┐   ┌──────────┐   ┌──────────┐                  │
│        │   Web    │   │   JSON   │   │ Console  │                  │
│        │  (HTML)  │   │  stdout  │   │  (Rich)  │                  │
│        └──────────┘   └──────────┘   └──────────┘                  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Component Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                      Presentation Layer                             │
├──────────────────────────────┬─────────────────────────────────────┤
│         CLI (src/cli.py)     │       Web (src/web_app.py)          │
│   • Command parsing (Click)  │   • Flask REST API                  │
│   • Console output (Rich)    │   • Drag-drop file upload           │
│   • Error handling           │   • Interactive HTML/JS UI          │
└──────────────────────────────┴────────────────┬────────────────────┘
                                                │
                                                │ orchestrates
                                                ▼
┌────────────────────────────────────────────────────────────────────┐
│                        Core Analysis Layer                          │
├────────────────────┬───────────────────┬───────────────────────────┤
│                    │                   │                           │
│   ┌────────────────▼───┐  ┌───────────▼────────┐  ┌──────────────▼─────┐
│   │    DataLoader      │  │   TrendAnalyzer    │  │   QualityAnalyzer  │
│   │ (data_loader.py)   │  │ (trend_analyzer.py)│  │(quality_analyzer.py│
│   ├────────────────────┤  ├────────────────────┤  ├────────────────────┤
│   │ • Load CSV/XLSX    │  │ • Temporal patterns│  │ • Missing data     │
│   │ • Detect source    │  │ • Volume trends    │  │ • Duplicates       │
│   │ • Normalize cols   │  │ • Anomaly detection│  │ • Type issues      │
│   │ • Parse datetimes  │  │ • Category analysis│  │ • Completeness     │
│   └────────────────────┘  └────────────────────┘  └────────────────────┘
│              │                     │                       │
│              │                     └───────────┬───────────┘
│              │                                 │
│              ▼                                 ▼
│   ┌──────────────────┐              ┌─────────────────────┐
│   │  pd.DataFrame    │──────────────│  Analysis Results   │
│   │  (normalized)    │              │  (Dict[str, Any])   │
│   └──────────────────┘              └──────────┬──────────┘
│                                                │
│                                                ▼
│                                   ┌────────────────────────┐
│                                   │   SuggestionEngine     │
│                                   │ (suggestion_engine.py) │
│                                   ├────────────────────────┤
│                                   │ • Analyze quality      │
│                                   │ • Analyze trends       │
│                                   │ • Generate suggestions │
│                                   │ • Prioritize actions   │
│                                   └────────────┬───────────┘
│                                                │
└────────────────────────────────────────────────┼────────────────────┘
                                                 │
                                                 ▼
                                   ┌────────────────────────┐
                                   │  List[Suggestion]      │
                                   │  (Prioritized output)  │
                                   └────────────────────────┘
```

---

## Data Flow

### 1. File Loading Flow

```
Input File (.csv/.xlsx)
         │
         ▼
┌─────────────────────────┐
│   Check file exists     │
│   Check file size       │
└────────────┬────────────┘
             │
             ▼
    ┌────────────────┐
    │  Size > 50MB?  │
    └───────┬────────┘
            │
     ┌──────┴──────┐
     │ Yes         │ No
     ▼             ▼
┌──────────┐  ┌──────────┐
│ Chunked  │  │ Direct   │
│ Loading  │  │ Loading  │
└────┬─────┘  └────┬─────┘
     │             │
     └──────┬──────┘
            │
            ▼
┌─────────────────────────┐
│   Detect Source System  │
│   (Match column names)  │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│   Normalize Columns     │
│   (Apply mappings)      │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│   Parse Datetime Cols   │
└────────────┬────────────┘
             │
             ▼
    pd.DataFrame (normalized)
```

### 2. Analysis Flow

```
pd.DataFrame (normalized)
         │
         ├─────────────────────────┐
         │                         │
         ▼                         ▼
┌─────────────────┐      ┌─────────────────┐
│ TrendAnalyzer   │      │ QualityAnalyzer │
│                 │      │                 │
│ • Find time col │      │ • Null counts   │
│ • Extract hour  │      │ • Dup detection │
│ • Extract day   │      │ • Type check    │
│ • Calc volumes  │      │ • Value check   │
│ • Detect spikes │      │ • Calc score    │
└────────┬────────┘      └────────┬────────┘
         │                        │
         ▼                        ▼
    trend_results           quality_results
    (Dict)                  (Dict)
         │                        │
         └───────────┬────────────┘
                     │
                     ▼
           ┌─────────────────┐
           │SuggestionEngine │
           │                 │
           │ Combines both   │
           │ results to      │
           │ generate        │
           │ suggestions     │
           └────────┬────────┘
                    │
                    ▼
           List[Suggestion]
```

### 3. Output Flow

```
Analysis Results
       │
       ▼
┌──────────────────┐
│   Output Format? │
└────────┬─────────┘
         │
   ┌─────┴─────┐
   │           │
   ▼           ▼
 text        json
   │           │
   ▼           ▼
┌──────────┐  ┌──────────┐
│Rich Panel│  │json.dumps│
│formatting│  │          │
└────┬─────┘  └────┬─────┘
     │             │
     ▼             ▼
  Console       stdout
  (colored)     or file
```

---

## Component Interfaces

### DataLoader

```python
class DataLoader:
    def __init__(self, chunk_size: int = 50000): ...
    
    def load_file(self, file_path: str) -> Tuple[pd.DataFrame, str, Dict[str, Any]]:
        """Returns (dataframe, detected_source, metadata)"""
    
    def normalize_dataframe(self, df: pd.DataFrame, source: str) -> pd.DataFrame:
        """Applies column mappings for detected source"""
    
    def _detect_source(self, df: pd.DataFrame) -> Optional[str]:
        """Matches columns against SOURCE_SIGNATURES"""
```

### TrendAnalyzer

```python
class TrendAnalyzer:
    def __init__(self, df: pd.DataFrame): ...
    
    def analyze_all(self) -> Dict[str, Any]:
        """Returns complete trend analysis results"""
    
    def get_trend_summary(self) -> str:
        """Returns human-readable summary"""
```

### QualityAnalyzer

```python
class QualityAnalyzer:
    def __init__(self, df: pd.DataFrame, source: str = None): ...
    
    def analyze_all(self) -> Dict[str, Any]:
        """Returns complete quality analysis results"""
    
    def get_quality_report(self) -> str:
        """Returns human-readable report"""
```

### SuggestionEngine

```python
class SuggestionEngine:
    def __init__(self, df, trend_results, quality_results, source): ...
    
    def generate_all_suggestions(self) -> List[Suggestion]:
        """Generates prioritized suggestion list"""
    
    def get_suggestions_report(self) -> str:
        """Returns human-readable suggestions"""
    
    def to_dict(self) -> Dict[str, Any]:
        """Export as dictionary for JSON"""
```

---

## Standard Schema

After normalization, DataFrames use this standard column schema:

| Standard Column | Type | Description |
|----------------|------|-------------|
| `id` | string | Unique incident identifier |
| `title` | string | Short description/summary |
| `category` | string | Incident category |
| `source` | string | Affected system/component |
| `severity` | string | Priority/severity level |
| `status` | string | Current state |
| `created_time` | datetime | When incident was opened |
| `resolved_time` | datetime | When incident was resolved |
| `_source_file` | string | Original file name (multi-file) |
| `_source_system` | string | Detected source system |

---

## Deployment Architecture

```
┌────────────────────────────────────────────────┐
│              User's Machine                     │
│                                                 │
│  ┌──────────────────────────────────────────┐  │
│  │            Python Environment             │  │
│  │              (3.9+)                       │  │
│  │  ┌────────────────────────────────────┐  │  │
│  │  │     Incident Log Analyzer          │  │  │
│  │  │     (pip install -e .)             │  │  │
│  │  └────────────────────────────────────┘  │  │
│  │                    │                      │  │
│  │  Dependencies:     │                      │  │
│  │  • pandas          │                      │  │
│  │  • openpyxl        │                      │  │
│  │  • rich            │                      │  │
│  │  • click           │                      │  │
│  │  • numpy           │                      │  │
│  │  • scipy           │                      │  │
│  └──────────────────────────────────────────┘  │
│                                                 │
│  ┌──────────────────────────────────────────┐  │
│  │              File System                  │  │
│  │  • Input: *.csv, *.xlsx                  │  │
│  │  • Output: *.json (optional)             │  │
│  └──────────────────────────────────────────┘  │
└────────────────────────────────────────────────┘
```

---

## Security Considerations

| Concern | Mitigation |
|---------|------------|
| Malicious file content | Pandas handles parsing; no code execution |
| Path traversal | Uses `pathlib.Path` for safe path handling |
| Memory exhaustion | Chunked loading, file size warnings |
| Sensitive data in logs | Only log file names, not content |

---

## Future Architecture Considerations

1. **Plugin System**: Allow external source system adapters
2. **Database Backend**: Store analysis history for trend comparison
3. **API Server**: REST API for integration with other tools
4. **Distributed Processing**: Dask/Spark for very large datasets
5. **Real-time Streaming**: Process incident streams vs. batch files

---

## Change Log

| Date | Version | Change | Author |
|------|---------|--------|--------|
| 2026-02-06 | 1.0 | Initial architecture documentation | System |
