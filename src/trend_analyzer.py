"""
Trend Analysis Engine
Identifies patterns, frequencies, and correlations in incident data.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class TrendAnalyzer:
    """Analyzes incident data to identify trends and patterns."""
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize the trend analyzer.
        
        Args:
            df: Normalized incident DataFrame
        """
        self.df = df
        self._prepare_data()
    
    def _prepare_data(self):
        """Prepare data for analysis by ensuring proper types."""
        # Identify time columns
        self.time_col = self._find_time_column()
        
        if self.time_col and self.time_col in self.df.columns:
            self.df[self.time_col] = pd.to_datetime(self.df[self.time_col], errors='coerce')
            self.has_time_data = self.df[self.time_col].notna().any()
        else:
            self.has_time_data = False
    
    def _find_time_column(self) -> Optional[str]:
        """Find the primary timestamp column."""
        time_columns = ['created_time', 'opened_at', 'sys_created_on', 
                       'first_event_time', 'timestamp', 'created', 'date']
        
        for col in time_columns:
            if col in self.df.columns:
                return col
        
        # Try to find any datetime-like column
        for col in self.df.columns:
            if 'time' in col.lower() or 'date' in col.lower():
                return col
        
        return None
    
    def analyze_all(self) -> Dict[str, Any]:
        """Run all trend analyses and return comprehensive results."""
        results = {
            'summary': self._get_summary_stats(),
            'temporal_patterns': self._analyze_temporal_patterns() if self.has_time_data else {},
            'category_analysis': self._analyze_categories(),
            'severity_distribution': self._analyze_severity(),
            'top_sources': self._analyze_sources(),
            'correlations': self._find_correlations(),
            'anomalies': self._detect_anomalies() if self.has_time_data else {}
        }
        return results
    
    def _get_summary_stats(self) -> Dict[str, Any]:
        """Get basic summary statistics."""
        stats = {
            'total_incidents': len(self.df),
            'unique_columns': len(self.df.columns),
            'columns': list(self.df.columns)
        }
        
        if self.has_time_data:
            valid_times = self.df[self.time_col].dropna()
            if len(valid_times) > 0:
                stats['date_range'] = {
                    'start': valid_times.min().isoformat(),
                    'end': valid_times.max().isoformat(),
                    'span_days': (valid_times.max() - valid_times.min()).days
                }
        
        return stats
    
    def _analyze_temporal_patterns(self) -> Dict[str, Any]:
        """Analyze time-based patterns in incidents."""
        if not self.has_time_data:
            return {}
        
        df_time = self.df.dropna(subset=[self.time_col]).copy()
        df_time['_hour'] = df_time[self.time_col].dt.hour
        df_time['_day_of_week'] = df_time[self.time_col].dt.day_name()
        df_time['_month'] = df_time[self.time_col].dt.month_name()
        df_time['_date'] = df_time[self.time_col].dt.date
        
        patterns = {
            'hourly_distribution': df_time['_hour'].value_counts().sort_index().to_dict(),
            'daily_distribution': df_time['_day_of_week'].value_counts().to_dict(),
            'monthly_distribution': df_time['_month'].value_counts().to_dict(),
            'daily_volume': df_time.groupby('_date').size().describe().to_dict(),
            'peak_hours': df_time['_hour'].value_counts().nlargest(3).to_dict(),
            'peak_days': df_time['_day_of_week'].value_counts().nlargest(3).to_dict()
        }
        
        # Calculate incident rate trends
        daily_counts = df_time.groupby('_date').size()
        if len(daily_counts) > 7:
            patterns['weekly_trend'] = self._calculate_trend(daily_counts, window=7)
        
        return patterns
    
    def _calculate_trend(self, series: pd.Series, window: int = 7) -> Dict[str, Any]:
        """Calculate trend direction and magnitude."""
        if len(series) < window * 2:
            return {'status': 'insufficient_data'}
        
        recent = series.tail(window).mean()
        previous = series.iloc[-window*2:-window].mean()
        
        if previous > 0:
            change_pct = ((recent - previous) / previous) * 100
        else:
            change_pct = 0
        
        return {
            'recent_avg': round(recent, 2),
            'previous_avg': round(previous, 2),
            'change_percent': round(change_pct, 2),
            'direction': 'increasing' if change_pct > 5 else ('decreasing' if change_pct < -5 else 'stable')
        }
    
    def _analyze_categories(self) -> Dict[str, Any]:
        """Analyze incident categories/types."""
        category_cols = self._find_categorical_columns()
        analysis = {}
        
        for col in category_cols[:5]:  # Limit to top 5 categorical columns
            value_counts = self.df[col].value_counts()
            analysis[col] = {
                'unique_values': len(value_counts),
                'top_10': value_counts.head(10).to_dict(),
                'null_count': int(self.df[col].isna().sum()),
                'null_percent': round(self.df[col].isna().mean() * 100, 2)
            }
        
        return analysis
    
    def _find_categorical_columns(self) -> List[str]:
        """Find columns likely to be categorical."""
        categorical = []
        for col in self.df.columns:
            if col.startswith('_'):
                continue
            if self.df[col].dtype == 'object':
                unique_ratio = self.df[col].nunique() / len(self.df)
                if unique_ratio < 0.5:  # Less than 50% unique values
                    categorical.append(col)
        return categorical
    
    def _analyze_severity(self) -> Dict[str, Any]:
        """Analyze severity/priority distribution."""
        severity_cols = ['severity', 'priority', 'urgency', 'impact']
        
        for col in severity_cols:
            if col in self.df.columns:
                return {
                    'column': col,
                    'distribution': self.df[col].value_counts().to_dict(),
                    'high_severity_count': self._count_high_severity(col),
                    'null_count': int(self.df[col].isna().sum())
                }
        
        return {'status': 'no_severity_column_found'}
    
    def _count_high_severity(self, col: str) -> int:
        """Count high severity incidents."""
        high_values = ['critical', 'high', '1', '2', 'p1', 'p2', 'sev1', 'sev2']
        return int(self.df[col].astype(str).str.lower().isin(high_values).sum())
    
    def _analyze_sources(self) -> Dict[str, Any]:
        """Analyze incident sources/systems."""
        source_cols = ['source', 'entity_name', 'cmdb_ci', 'host', 'service', 
                      'application', 'component', '_source_system']
        
        analysis = {}
        for col in source_cols:
            if col in self.df.columns:
                value_counts = self.df[col].value_counts()
                analysis[col] = {
                    'unique_count': len(value_counts),
                    'top_10': value_counts.head(10).to_dict()
                }
        
        return analysis
    
    def _find_correlations(self) -> Dict[str, Any]:
        """Find correlations between incident attributes."""
        correlations = {}
        
        # Cross-tabulation of key categorical columns
        cat_cols = self._find_categorical_columns()
        
        if len(cat_cols) >= 2:
            # Find most common co-occurrences
            for i, col1 in enumerate(cat_cols[:3]):
                for col2 in cat_cols[i+1:4]:
                    cross_tab = pd.crosstab(
                        self.df[col1].fillna('(null)'), 
                        self.df[col2].fillna('(null)')
                    )
                    
                    # Find top co-occurrences
                    top_pairs = []
                    for row in cross_tab.index[:5]:
                        for col in cross_tab.columns[:5]:
                            count = cross_tab.loc[row, col]
                            if count > 0:
                                top_pairs.append({
                                    'value1': str(row),
                                    'value2': str(col),
                                    'count': int(count)
                                })
                    
                    top_pairs.sort(key=lambda x: x['count'], reverse=True)
                    correlations[f'{col1}_x_{col2}'] = top_pairs[:10]
        
        return correlations
    
    def _detect_anomalies(self) -> Dict[str, Any]:
        """Detect anomalous patterns in the data."""
        if not self.has_time_data:
            return {}
        
        anomalies = {
            'volume_spikes': [],
            'unusual_patterns': []
        }
        
        # Detect volume spikes
        df_time = self.df.dropna(subset=[self.time_col]).copy()
        df_time['_date'] = df_time[self.time_col].dt.date
        daily_counts = df_time.groupby('_date').size()
        
        if len(daily_counts) > 7:
            mean_vol = daily_counts.mean()
            std_vol = daily_counts.std()
            threshold = mean_vol + (2 * std_vol)
            
            spikes = daily_counts[daily_counts > threshold]
            for date, count in spikes.items():
                anomalies['volume_spikes'].append({
                    'date': str(date),
                    'count': int(count),
                    'times_above_average': round(count / mean_vol, 2) if mean_vol > 0 else 0
                })
        
        return anomalies
    
    def get_trend_summary(self) -> str:
        """Generate a human-readable trend summary."""
        results = self.analyze_all()
        
        lines = [
            "=== Incident Trend Analysis Summary ===",
            f"Total Incidents Analyzed: {results['summary']['total_incidents']:,}",
        ]
        
        if 'date_range' in results['summary']:
            dr = results['summary']['date_range']
            lines.append(f"Date Range: {dr['start'][:10]} to {dr['end'][:10]} ({dr['span_days']} days)")
        
        # Temporal insights
        if results['temporal_patterns']:
            patterns = results['temporal_patterns']
            if 'peak_hours' in patterns:
                peak_hours = list(patterns['peak_hours'].keys())[:3]
                lines.append(f"\nPeak Hours: {', '.join(map(str, peak_hours))}:00")
            
            if 'weekly_trend' in patterns:
                trend = patterns['weekly_trend']
                lines.append(f"Weekly Trend: {trend['direction']} ({trend['change_percent']:+.1f}%)")
        
        # Severity insights
        if results['severity_distribution'] and 'distribution' in results['severity_distribution']:
            sev = results['severity_distribution']
            lines.append(f"\nSeverity Column: {sev['column']}")
            lines.append(f"High Severity Count: {sev['high_severity_count']:,}")
        
        # Anomalies
        if results['anomalies'] and results['anomalies'].get('volume_spikes'):
            lines.append(f"\n⚠️  Volume Spikes Detected: {len(results['anomalies']['volume_spikes'])}")
        
        return '\n'.join(lines)
