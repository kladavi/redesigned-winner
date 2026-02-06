"""
Suggestion Engine
Generates actionable insights and recommendations based on analysis results.
"""

import pandas as pd
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class SuggestionPriority(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class SuggestionCategory(Enum):
    DATA_QUALITY = "data_quality"
    TREND_INSIGHT = "trend_insight"
    OPERATIONAL = "operational"
    INVESTIGATION = "investigation"
    OPTIMIZATION = "optimization"


@dataclass
class Suggestion:
    """Represents an actionable suggestion."""
    title: str
    description: str
    priority: SuggestionPriority
    category: SuggestionCategory
    actions: List[str]
    evidence: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'title': self.title,
            'description': self.description,
            'priority': self.priority.value,
            'category': self.category.value,
            'actions': self.actions,
            'evidence': self.evidence
        }


class SuggestionEngine:
    """Generates actionable suggestions based on trend and quality analysis."""
    
    def __init__(self, 
                 df: pd.DataFrame,
                 trend_results: Dict[str, Any],
                 quality_results: Dict[str, Any],
                 source: str = None):
        """
        Initialize the suggestion engine.
        
        Args:
            df: The analyzed DataFrame
            trend_results: Results from TrendAnalyzer
            quality_results: Results from QualityAnalyzer
            source: Detected source system
        """
        self.df = df
        self.trend_results = trend_results
        self.quality_results = quality_results
        self.source = source
        self.suggestions: List[Suggestion] = []
    
    def generate_all_suggestions(self) -> List[Suggestion]:
        """Generate all suggestions based on analysis results."""
        self.suggestions = []
        
        self._analyze_data_quality_issues()
        self._analyze_volume_patterns()
        self._analyze_severity_distribution()
        self._analyze_repeat_incidents()
        self._analyze_resolution_patterns()
        self._analyze_source_concentration()
        self._suggest_further_analysis()
        
        # Sort by priority
        priority_order = {
            SuggestionPriority.CRITICAL: 0,
            SuggestionPriority.HIGH: 1,
            SuggestionPriority.MEDIUM: 2,
            SuggestionPriority.LOW: 3
        }
        self.suggestions.sort(key=lambda s: priority_order[s.priority])
        
        return self.suggestions
    
    def _analyze_data_quality_issues(self):
        """Generate suggestions for data quality issues."""
        quality_score = self.quality_results.get('completeness_score', {})
        score = quality_score.get('completeness_score', 100)
        
        if score < 70:
            high_issues = [i for i in self.quality_results.get('issues_list', []) 
                         if i.get('severity') == 'high']
            
            self.suggestions.append(Suggestion(
                title="Critical Data Quality Issues Detected",
                description=f"Data quality score is {score}/100. High-severity issues found that may impact analysis accuracy.",
                priority=SuggestionPriority.CRITICAL,
                category=SuggestionCategory.DATA_QUALITY,
                actions=[
                    "Review and fix missing values in critical columns",
                    "Investigate duplicate records and determine root cause",
                    "Validate data export process from source system",
                    "Consider implementing data validation at ingestion time"
                ],
                evidence={
                    'score': score,
                    'high_issues_count': len(high_issues),
                    'issues': [i['message'] for i in high_issues[:5]]
                }
            ))
        
        # Missing critical data
        missing = self.quality_results.get('missing_data', {})
        critical_missing = missing.get('critical_columns_affected', [])
        
        if critical_missing:
            self.suggestions.append(Suggestion(
                title="Critical Fields Have Missing Values",
                description="Essential incident fields contain null values, which may indicate data collection issues.",
                priority=SuggestionPriority.HIGH,
                category=SuggestionCategory.DATA_QUALITY,
                actions=[
                    "Audit the data pipeline for these fields",
                    "Set up alerts for null values in critical fields",
                    "Review integration configuration with source systems"
                ],
                evidence={
                    'affected_columns': critical_missing
                }
            ))
        
        # Duplicates
        dups = self.quality_results.get('duplicates', {})
        if dups.get('full_row_duplicates', 0) > 0:
            dup_pct = dups.get('duplicate_percentage', 0)
            self.suggestions.append(Suggestion(
                title="Duplicate Records Detected",
                description=f"{dups['full_row_duplicates']:,} duplicate rows found ({dup_pct}% of data).",
                priority=SuggestionPriority.MEDIUM if dup_pct < 5 else SuggestionPriority.HIGH,
                category=SuggestionCategory.DATA_QUALITY,
                actions=[
                    "De-duplicate data before analysis",
                    "Check for duplicate webhook/API calls at source",
                    "Review deduplication rules in monitoring tool"
                ],
                evidence=dups
            ))
    
    def _analyze_volume_patterns(self):
        """Analyze volume patterns and generate insights."""
        temporal = self.trend_results.get('temporal_patterns', {})
        
        # Weekly trend analysis
        weekly_trend = temporal.get('weekly_trend', {})
        if weekly_trend.get('direction') == 'increasing':
            change = weekly_trend.get('change_percent', 0)
            if change > 20:
                self.suggestions.append(Suggestion(
                    title="Significant Increase in Incident Volume",
                    description=f"Incident volume increased by {change:.1f}% compared to the previous week.",
                    priority=SuggestionPriority.HIGH,
                    category=SuggestionCategory.TREND_INSIGHT,
                    actions=[
                        "Investigate root causes for the volume increase",
                        "Check for new deployments or infrastructure changes",
                        "Review alert thresholds - they may be too sensitive",
                        "Analyze if increase is from a specific source/category"
                    ],
                    evidence=weekly_trend
                ))
        
        # Volume spikes
        anomalies = self.trend_results.get('anomalies', {})
        spikes = anomalies.get('volume_spikes', [])
        
        if spikes:
            self.suggestions.append(Suggestion(
                title="Volume Spike Days Identified",
                description=f"Found {len(spikes)} days with abnormally high incident volumes.",
                priority=SuggestionPriority.MEDIUM,
                category=SuggestionCategory.INVESTIGATION,
                actions=[
                    "Correlate spike dates with deployment calendars",
                    "Check for infrastructure events on these dates",
                    "Review if spikes align with known outages",
                    "Consider implementing automatic scaling during peak periods"
                ],
                evidence={'spikes': spikes[:5]}
            ))
        
        # Peak hours insight
        peak_hours = temporal.get('peak_hours', {})
        if peak_hours:
            peak_list = list(peak_hours.keys())[:3]
            self.suggestions.append(Suggestion(
                title="Peak Incident Hours Identified",
                description=f"Highest incident volume occurs at hours: {', '.join(map(str, peak_list))}:00",
                priority=SuggestionPriority.LOW,
                category=SuggestionCategory.OPERATIONAL,
                actions=[
                    "Ensure adequate on-call coverage during peak hours",
                    "Schedule maintenance windows outside peak hours",
                    "Consider automated remediation for common issues during peaks"
                ],
                evidence={'peak_hours': peak_hours}
            ))
    
    def _analyze_severity_distribution(self):
        """Analyze severity/priority distribution."""
        severity = self.trend_results.get('severity_distribution', {})
        
        if severity and 'distribution' in severity:
            dist = severity['distribution']
            high_count = severity.get('high_severity_count', 0)
            total = sum(dist.values()) if dist else 1
            high_pct = (high_count / total) * 100 if total > 0 else 0
            
            if high_pct > 30:
                self.suggestions.append(Suggestion(
                    title="High Proportion of Critical/High Severity Incidents",
                    description=f"{high_pct:.1f}% of incidents are high severity. This may indicate systemic issues or overly aggressive alerting.",
                    priority=SuggestionPriority.HIGH,
                    category=SuggestionCategory.OPERATIONAL,
                    actions=[
                        "Review severity classification criteria",
                        "Audit high-severity alerts for false positives",
                        "Investigate common patterns in high-severity incidents",
                        "Consider severity auto-escalation rules"
                    ],
                    evidence={
                        'high_severity_count': high_count,
                        'high_severity_percent': round(high_pct, 1),
                        'distribution': dist
                    }
                ))
    
    def _analyze_repeat_incidents(self):
        """Analyze repeat/recurring incidents."""
        categories = self.trend_results.get('category_analysis', {})
        
        for col_name, analysis in categories.items():
            top_values = analysis.get('top_10', {})
            if top_values:
                top_item = list(top_values.items())[0] if top_values else None
                if top_item:
                    name, count = top_item
                    total = len(self.df)
                    pct = (count / total) * 100 if total > 0 else 0
                    
                    if pct > 20:
                        self.suggestions.append(Suggestion(
                            title=f"High Concentration in '{col_name}'",
                            description=f"'{name}' accounts for {pct:.1f}% of all incidents. Consider targeted improvement.",
                            priority=SuggestionPriority.MEDIUM,
                            category=SuggestionCategory.OPTIMIZATION,
                            actions=[
                                f"Deep dive into '{name}' incidents for root cause",
                                "Create automated remediation runbooks",
                                "Consider infrastructure improvements",
                                "Review if alert is adding value or just noise"
                            ],
                            evidence={
                                'category': col_name,
                                'top_value': name,
                                'count': count,
                                'percentage': round(pct, 1)
                            }
                        ))
    
    def _analyze_resolution_patterns(self):
        """Analyze incident resolution patterns."""
        # Check for resolution time data
        if 'created_time' in self.df.columns and 'resolved_time' in self.df.columns:
            df_resolved = self.df.dropna(subset=['created_time', 'resolved_time']).copy()
            
            if len(df_resolved) > 0:
                created = pd.to_datetime(df_resolved['created_time'], errors='coerce')
                resolved = pd.to_datetime(df_resolved['resolved_time'], errors='coerce')
                
                resolution_time = (resolved - created).dt.total_seconds() / 3600  # hours
                resolution_time = resolution_time[resolution_time > 0]
                
                if len(resolution_time) > 0:
                    avg_hours = resolution_time.mean()
                    median_hours = resolution_time.median()
                    
                    if avg_hours > 24:
                        self.suggestions.append(Suggestion(
                            title="Long Average Resolution Time",
                            description=f"Average resolution time is {avg_hours:.1f} hours (median: {median_hours:.1f} hours).",
                            priority=SuggestionPriority.MEDIUM,
                            category=SuggestionCategory.OPERATIONAL,
                            actions=[
                                "Identify bottlenecks in resolution workflow",
                                "Review escalation procedures",
                                "Implement SLA monitoring and alerting",
                                "Create troubleshooting guides for common issues"
                            ],
                            evidence={
                                'avg_resolution_hours': round(avg_hours, 2),
                                'median_resolution_hours': round(median_hours, 2),
                                'sample_size': len(resolution_time)
                            }
                        ))
    
    def _analyze_source_concentration(self):
        """Analyze if incidents are concentrated on specific sources."""
        sources = self.trend_results.get('top_sources', {})
        
        for source_col, data in sources.items():
            if source_col.startswith('_'):
                continue
                
            top_sources = data.get('top_10', {})
            unique_count = data.get('unique_count', 0)
            
            if top_sources and unique_count > 0:
                top_source = list(top_sources.items())[0] if top_sources else None
                if top_source:
                    name, count = top_source
                    pct = (count / len(self.df)) * 100 if len(self.df) > 0 else 0
                    
                    if pct > 30:
                        self.suggestions.append(Suggestion(
                            title=f"Single Source Generating Most Incidents",
                            description=f"'{name}' generates {pct:.1f}% of all incidents from {source_col}.",
                            priority=SuggestionPriority.HIGH,
                            category=SuggestionCategory.INVESTIGATION,
                            actions=[
                                f"Investigate health and stability of '{name}'",
                                "Review monitoring configuration for this source",
                                "Consider dedicated runbooks for this source",
                                "Evaluate if infrastructure upgrade needed"
                            ],
                            evidence={
                                'source_column': source_col,
                                'top_source': name,
                                'incident_count': count,
                                'percentage': round(pct, 1)
                            }
                        ))
    
    def _suggest_further_analysis(self):
        """Suggest additional analyses that could be valuable."""
        suggestions_to_add = []
        
        # Correlation analysis suggestion
        if len(self.df.columns) > 5:
            suggestions_to_add.append(Suggestion(
                title="Recommended: Correlation Analysis",
                description="With multiple attributes, correlation analysis could reveal hidden patterns.",
                priority=SuggestionPriority.LOW,
                category=SuggestionCategory.OPTIMIZATION,
                actions=[
                    "Analyze correlation between incident categories and times",
                    "Look for patterns in source-severity relationships",
                    "Identify co-occurring incident types"
                ],
                evidence={'column_count': len(self.df.columns)}
            ))
        
        # Time series forecasting suggestion
        temporal = self.trend_results.get('temporal_patterns', {})
        if temporal.get('daily_volume', {}).get('count', 0) > 30:
            suggestions_to_add.append(Suggestion(
                title="Recommended: Volume Forecasting",
                description="Sufficient historical data for incident volume forecasting.",
                priority=SuggestionPriority.LOW,
                category=SuggestionCategory.OPTIMIZATION,
                actions=[
                    "Build time series forecast for capacity planning",
                    "Set up anomaly detection on predicted vs actual",
                    "Plan staffing based on predicted volumes"
                ],
                evidence={'days_of_data': temporal.get('daily_volume', {}).get('count', 0)}
            ))
        
        self.suggestions.extend(suggestions_to_add)
    
    def get_suggestions_report(self) -> str:
        """Generate a human-readable suggestions report."""
        if not self.suggestions:
            self.generate_all_suggestions()
        
        lines = [
            "=== Actionable Insights & Recommendations ===",
            f"\nTotal Suggestions: {len(self.suggestions)}"
        ]
        
        # Group by priority
        for priority in [SuggestionPriority.CRITICAL, SuggestionPriority.HIGH, 
                        SuggestionPriority.MEDIUM, SuggestionPriority.LOW]:
            priority_suggestions = [s for s in self.suggestions if s.priority == priority]
            
            if priority_suggestions:
                emoji = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🟢'}
                lines.append(f"\n{emoji[priority.value]} {priority.value.upper()} Priority ({len(priority_suggestions)})")
                
                for i, s in enumerate(priority_suggestions, 1):
                    lines.append(f"\n  {i}. {s.title}")
                    lines.append(f"     {s.description}")
                    lines.append(f"     Category: {s.category.value}")
                    lines.append(f"     Recommended Actions:")
                    for action in s.actions[:3]:
                        lines.append(f"       • {action}")
        
        return '\n'.join(lines)
    
    def to_dict(self) -> Dict[str, Any]:
        """Export all suggestions as dictionary."""
        if not self.suggestions:
            self.generate_all_suggestions()
        
        return {
            'total_suggestions': len(self.suggestions),
            'by_priority': {
                p.value: len([s for s in self.suggestions if s.priority == p])
                for p in SuggestionPriority
            },
            'suggestions': [s.to_dict() for s in self.suggestions]
        }
