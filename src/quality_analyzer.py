"""
Quality Analyzer Module
Identifies data quality issues in incident logs.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple
from collections import defaultdict
import logging
import re

logger = logging.getLogger(__name__)


class QualityAnalyzer:
    """Identifies data quality issues in incident log data."""
    
    # Expected columns for each source system
    EXPECTED_COLUMNS = {
        'newrelic': ['incident_id', 'condition_name', 'policy_name', 'severity', 'opened_at'],
        'moogsoft': ['alert_id', 'description', 'severity', 'source', 'first_event_time'],
        'servicenow': ['number', 'short_description', 'priority', 'state', 'sys_created_on']
    }
    
    # Critical columns that should never be null
    CRITICAL_COLUMNS = ['id', 'title', 'severity', 'created_time', 'incident_id', 
                       'number', 'alert_id', 'description', 'short_description']
    
    def __init__(self, df: pd.DataFrame, source: str = None):
        """
        Initialize the quality analyzer.
        
        Args:
            df: DataFrame to analyze
            source: Detected source system (newrelic, moogsoft, servicenow)
        """
        self.df = df
        self.source = source
        self.issues = []
    
    def analyze_all(self) -> Dict[str, Any]:
        """Run all quality checks and return comprehensive results."""
        return {
            'summary': self._get_quality_summary(),
            'missing_data': self._check_missing_data(),
            'duplicates': self._check_duplicates(),
            'data_types': self._check_data_types(),
            'value_issues': self._check_value_issues(),
            'consistency': self._check_consistency(),
            'completeness_score': self._calculate_completeness_score(),
            'issues_list': self.issues
        }
    
    def _get_quality_summary(self) -> Dict[str, Any]:
        """Get overall quality summary."""
        total_cells = self.df.shape[0] * self.df.shape[1]
        null_cells = self.df.isna().sum().sum()
        
        return {
            'total_rows': len(self.df),
            'total_columns': len(self.df.columns),
            'total_cells': total_cells,
            'null_cells': int(null_cells),
            'overall_fill_rate': round((1 - null_cells / total_cells) * 100, 2) if total_cells > 0 else 0,
            'memory_usage_mb': round(self.df.memory_usage(deep=True).sum() / (1024 * 1024), 2)
        }
    
    def _check_missing_data(self) -> Dict[str, Any]:
        """Check for missing/null values in each column."""
        missing_analysis = {}
        critical_missing = []
        
        for col in self.df.columns:
            null_count = int(self.df[col].isna().sum())
            null_pct = round(self.df[col].isna().mean() * 100, 2)
            
            if null_count > 0:
                missing_analysis[col] = {
                    'null_count': null_count,
                    'null_percent': null_pct,
                    'severity': 'high' if null_pct > 50 else ('medium' if null_pct > 10 else 'low')
                }
                
                # Check if critical column
                if any(crit in col.lower() for crit in self.CRITICAL_COLUMNS):
                    critical_missing.append({
                        'column': col,
                        'null_count': null_count,
                        'null_percent': null_pct
                    })
                    self.issues.append({
                        'type': 'critical_missing_data',
                        'severity': 'high',
                        'column': col,
                        'message': f"Critical column '{col}' has {null_count} ({null_pct}%) missing values"
                    })
        
        return {
            'columns_with_nulls': len(missing_analysis),
            'by_column': missing_analysis,
            'critical_columns_affected': critical_missing
        }
    
    def _check_duplicates(self) -> Dict[str, Any]:
        """Check for duplicate records."""
        # Full row duplicates
        full_dups = self.df.duplicated().sum()
        
        # Check key column duplicates
        key_columns = ['id', 'incident_id', 'number', 'alert_id', 'sys_id']
        key_dups = {}
        
        for col in key_columns:
            if col in self.df.columns:
                dup_count = self.df[col].dropna().duplicated().sum()
                if dup_count > 0:
                    key_dups[col] = {
                        'duplicate_count': int(dup_count),
                        'duplicate_values': self.df[col][self.df[col].duplicated(keep=False)].value_counts().head(5).to_dict()
                    }
                    self.issues.append({
                        'type': 'duplicate_keys',
                        'severity': 'high',
                        'column': col,
                        'message': f"Found {dup_count} duplicate values in key column '{col}'"
                    })
        
        if full_dups > 0:
            self.issues.append({
                'type': 'duplicate_rows',
                'severity': 'medium',
                'message': f"Found {full_dups} fully duplicate rows"
            })
        
        return {
            'full_row_duplicates': int(full_dups),
            'key_column_duplicates': key_dups,
            'duplicate_percentage': round(full_dups / len(self.df) * 100, 2) if len(self.df) > 0 else 0
        }
    
    def _check_data_types(self) -> Dict[str, Any]:
        """Check for data type issues."""
        type_issues = {}
        
        # Check timestamp columns that should be datetime
        time_patterns = ['time', 'date', 'created', 'opened', 'closed', 'resolved']
        for col in self.df.columns:
            col_lower = col.lower()
            if any(p in col_lower for p in time_patterns):
                if self.df[col].dtype == 'object':
                    # Try to parse and see what fails
                    try:
                        parsed = pd.to_datetime(self.df[col], errors='coerce')
                        failed = parsed.isna() & self.df[col].notna()
                        if failed.sum() > 0:
                            type_issues[col] = {
                                'expected_type': 'datetime',
                                'actual_type': str(self.df[col].dtype),
                                'unparseable_count': int(failed.sum()),
                                'sample_bad_values': self.df[col][failed].head(5).tolist()
                            }
                            self.issues.append({
                                'type': 'datetime_parse_error',
                                'severity': 'medium',
                                'column': col,
                                'message': f"Column '{col}' has {failed.sum()} values that cannot be parsed as datetime"
                            })
                    except Exception:
                        pass
        
        # Check numeric columns
        numeric_patterns = ['count', 'duration', 'time_to', 'ttm', 'mttr']
        for col in self.df.columns:
            col_lower = col.lower()
            if any(p in col_lower for p in numeric_patterns):
                if self.df[col].dtype == 'object':
                    type_issues[col] = {
                        'expected_type': 'numeric',
                        'actual_type': str(self.df[col].dtype),
                        'sample_values': self.df[col].head(5).tolist()
                    }
        
        return {
            'issues_found': len(type_issues),
            'details': type_issues,
            'column_types': {col: str(dtype) for col, dtype in self.df.dtypes.items()}
        }
    
    def _check_value_issues(self) -> Dict[str, Any]:
        """Check for problematic values."""
        issues = {}
        
        # Check for obviously wrong values
        for col in self.df.columns:
            col_issues = []
            
            if self.df[col].dtype == 'object':
                # Check for placeholder/test values
                test_patterns = [r'\btest\b', r'\bxxx\b', r'\bTBD\b', r'\bN/?A\b', 
                               r'\bnull\b', r'\bnone\b', r'\b-\b$', r'^\s*$']
                
                for pattern in test_patterns:
                    matches = self.df[col].astype(str).str.contains(pattern, case=False, regex=True, na=False)
                    if matches.sum() > 0:
                        col_issues.append({
                            'pattern': pattern,
                            'count': int(matches.sum()),
                            'samples': self.df[col][matches].head(3).tolist()
                        })
                
                # Check for very short values in description fields
                if 'description' in col.lower() or 'title' in col.lower():
                    short_vals = self.df[col].dropna().astype(str).str.len() < 5
                    if short_vals.sum() > 0:
                        col_issues.append({
                            'issue': 'very_short_values',
                            'count': int(short_vals.sum()),
                            'samples': self.df[col][short_vals].head(5).tolist()
                        })
            
            if col_issues:
                issues[col] = col_issues
                self.issues.append({
                    'type': 'value_quality',
                    'severity': 'low',
                    'column': col,
                    'message': f"Column '{col}' has {len(col_issues)} types of value quality issues"
                })
        
        return issues
    
    def _check_consistency(self) -> Dict[str, Any]:
        """Check for data consistency issues."""
        consistency_issues = {}
        
        # Check severity/priority consistency
        severity_cols = ['severity', 'priority', 'urgency', 'impact']
        for col in severity_cols:
            if col in self.df.columns:
                unique_vals = self.df[col].dropna().unique()
                if len(unique_vals) > 0:
                    # Check for mixed case inconsistencies
                    lower_vals = set(str(v).lower() for v in unique_vals)
                    if len(lower_vals) < len(unique_vals):
                        consistency_issues[f'{col}_case_inconsistency'] = {
                            'unique_values': [str(v) for v in unique_vals],
                            'normalized_unique': list(lower_vals)
                        }
                        self.issues.append({
                            'type': 'case_inconsistency',
                            'severity': 'low',
                            'column': col,
                            'message': f"Column '{col}' has case inconsistencies (e.g., 'High' vs 'high')"
                        })
        
        # Check for time order issues
        if 'created_time' in self.df.columns and 'resolved_time' in self.df.columns:
            created = pd.to_datetime(self.df['created_time'], errors='coerce')
            resolved = pd.to_datetime(self.df['resolved_time'], errors='coerce')
            invalid_order = (resolved < created) & created.notna() & resolved.notna()
            
            if invalid_order.sum() > 0:
                consistency_issues['time_order'] = {
                    'invalid_count': int(invalid_order.sum()),
                    'message': 'Resolved time is before created time'
                }
                self.issues.append({
                    'type': 'time_order_error',
                    'severity': 'high',
                    'message': f"{invalid_order.sum()} records have resolved_time before created_time"
                })
        
        return consistency_issues
    
    def _calculate_completeness_score(self) -> Dict[str, Any]:
        """Calculate an overall data completeness score."""
        # Weight critical columns higher
        critical_weight = 2.0
        normal_weight = 1.0
        
        total_weight = 0
        weighted_fill = 0
        
        for col in self.df.columns:
            fill_rate = 1 - self.df[col].isna().mean()
            is_critical = any(crit in col.lower() for crit in self.CRITICAL_COLUMNS)
            
            weight = critical_weight if is_critical else normal_weight
            total_weight += weight
            weighted_fill += fill_rate * weight
        
        score = (weighted_fill / total_weight) * 100 if total_weight > 0 else 0
        
        # Penalize for duplicates
        dup_penalty = (self.df.duplicated().sum() / len(self.df)) * 10 if len(self.df) > 0 else 0
        final_score = max(0, score - dup_penalty)
        
        return {
            'completeness_score': round(final_score, 1),
            'grade': self._score_to_grade(final_score),
            'issues_count': len(self.issues)
        }
    
    def _score_to_grade(self, score: float) -> str:
        """Convert numeric score to letter grade."""
        if score >= 90:
            return 'A'
        elif score >= 80:
            return 'B'
        elif score >= 70:
            return 'C'
        elif score >= 60:
            return 'D'
        else:
            return 'F'
    
    def get_quality_report(self) -> str:
        """Generate a human-readable quality report."""
        results = self.analyze_all()
        
        lines = [
            "=== Data Quality Analysis Report ===",
            f"\nDataset: {results['summary']['total_rows']:,} rows × {results['summary']['total_columns']} columns",
            f"Memory Usage: {results['summary']['memory_usage_mb']:.1f} MB",
            f"Overall Fill Rate: {results['summary']['overall_fill_rate']}%",
            f"\n📊 Completeness Score: {results['completeness_score']['completeness_score']}/100 (Grade: {results['completeness_score']['grade']})",
            f"\n⚠️  Issues Found: {len(results['issues_list'])}"
        ]
        
        # Group issues by severity
        high_issues = [i for i in results['issues_list'] if i.get('severity') == 'high']
        medium_issues = [i for i in results['issues_list'] if i.get('severity') == 'medium']
        low_issues = [i for i in results['issues_list'] if i.get('severity') == 'low']
        
        if high_issues:
            lines.append(f"\n🔴 High Severity Issues ({len(high_issues)}):")
            for issue in high_issues[:5]:
                lines.append(f"   • {issue['message']}")
        
        if medium_issues:
            lines.append(f"\n🟡 Medium Severity Issues ({len(medium_issues)}):")
            for issue in medium_issues[:5]:
                lines.append(f"   • {issue['message']}")
        
        if results['duplicates']['full_row_duplicates'] > 0:
            lines.append(f"\n📋 Duplicate Rows: {results['duplicates']['full_row_duplicates']:,}")
        
        return '\n'.join(lines)
