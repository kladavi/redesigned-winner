"""
Tests for Incident Log Analyzer
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_loader import DataLoader
from src.trend_analyzer import TrendAnalyzer
from src.quality_analyzer import QualityAnalyzer
from src.suggestion_engine import SuggestionEngine, SuggestionPriority


class TestDataLoader:
    """Tests for DataLoader class."""
    
    def test_detect_servicenow_source(self):
        """Test ServiceNow source detection."""
        df = pd.DataFrame({
            'number': ['INC001', 'INC002'],
            'sys_id': ['abc', 'def'],
            'short_description': ['Test 1', 'Test 2'],
            'priority': ['1 - High', '2 - Medium'],
            'state': ['New', 'Closed']
        })
        
        loader = DataLoader()
        source = loader._detect_source(df)
        assert source == 'servicenow'
    
    def test_detect_newrelic_source(self):
        """Test NewRelic source detection."""
        df = pd.DataFrame({
            'incident_id': [1, 2],
            'condition_name': ['Alert 1', 'Alert 2'],
            'policy_name': ['Policy 1', 'Policy 1'],
            'entity_name': ['app1', 'app2']
        })
        
        loader = DataLoader()
        source = loader._detect_source(df)
        assert source == 'newrelic'
    
    def test_detect_moogsoft_source(self):
        """Test Moogsoft source detection."""
        df = pd.DataFrame({
            'alert_id': ['ALT-001', 'ALT-002'],
            'sig_id': ['SIG-001', 'SIG-002'],
            'source': ['nagios', 'prometheus'],
            'class': ['Server', 'Network'],
            'severity': [3, 4]
        })
        
        loader = DataLoader()
        source = loader._detect_source(df)
        assert source == 'moogsoft'
    
    def test_normalize_servicenow_columns(self):
        """Test ServiceNow column normalization."""
        df = pd.DataFrame({
            'number': ['INC001'],
            'short_description': ['Test issue'],
            'sys_created_on': ['2025-01-15 10:00:00']
        })
        
        loader = DataLoader()
        normalized = loader.normalize_dataframe(df, 'servicenow')
        
        assert 'id' in normalized.columns
        assert 'title' in normalized.columns
        assert 'created_time' in normalized.columns


class TestTrendAnalyzer:
    """Tests for TrendAnalyzer class."""
    
    @pytest.fixture
    def sample_df(self):
        """Create sample DataFrame with time data."""
        dates = pd.date_range('2025-01-01', periods=100, freq='H')
        return pd.DataFrame({
            'created_time': dates,
            'severity': np.random.choice(['critical', 'high', 'medium', 'low'], 100),
            'category': np.random.choice(['Network', 'Hardware', 'Software'], 100),
            'source': np.random.choice(['server1', 'server2', 'server3'], 100)
        })
    
    def test_analyze_all_returns_expected_keys(self, sample_df):
        """Test that analyze_all returns all expected sections."""
        analyzer = TrendAnalyzer(sample_df)
        results = analyzer.analyze_all()
        
        assert 'summary' in results
        assert 'temporal_patterns' in results
        assert 'category_analysis' in results
        assert 'severity_distribution' in results
    
    def test_temporal_patterns_with_time_data(self, sample_df):
        """Test temporal pattern analysis."""
        analyzer = TrendAnalyzer(sample_df)
        results = analyzer.analyze_all()
        
        assert 'hourly_distribution' in results['temporal_patterns']
        assert 'daily_distribution' in results['temporal_patterns']
    
    def test_summary_stats(self, sample_df):
        """Test summary statistics."""
        analyzer = TrendAnalyzer(sample_df)
        results = analyzer.analyze_all()
        
        assert results['summary']['total_incidents'] == 100
        assert 'date_range' in results['summary']


class TestQualityAnalyzer:
    """Tests for QualityAnalyzer class."""
    
    @pytest.fixture
    def df_with_issues(self):
        """Create DataFrame with quality issues."""
        return pd.DataFrame({
            'id': [1, 2, 3, 3, 4],  # Duplicate id
            'title': ['Test', None, 'OK', 'Test', 'N/A'],  # Missing and placeholder
            'severity': ['high', 'HIGH', 'medium', 'high', 'low'],  # Case inconsistency
            'created_time': ['2025-01-01', 'invalid', '2025-01-03', '2025-01-04', '2025-01-05']
        })
    
    def test_detect_duplicates(self, df_with_issues):
        """Test duplicate detection."""
        analyzer = QualityAnalyzer(df_with_issues)
        results = analyzer.analyze_all()
        
        assert results['duplicates']['full_row_duplicates'] >= 0
    
    def test_detect_missing_data(self, df_with_issues):
        """Test missing data detection."""
        analyzer = QualityAnalyzer(df_with_issues)
        results = analyzer.analyze_all()
        
        assert 'title' in results['missing_data']['by_column']
    
    def test_completeness_score(self, df_with_issues):
        """Test completeness score calculation."""
        analyzer = QualityAnalyzer(df_with_issues)
        results = analyzer.analyze_all()
        
        assert 'completeness_score' in results['completeness_score']
        assert 'grade' in results['completeness_score']
        assert results['completeness_score']['completeness_score'] <= 100


class TestSuggestionEngine:
    """Tests for SuggestionEngine class."""
    
    @pytest.fixture
    def mock_trend_results(self):
        return {
            'summary': {'total_incidents': 1000},
            'temporal_patterns': {
                'weekly_trend': {'direction': 'increasing', 'change_percent': 25}
            },
            'severity_distribution': {
                'column': 'severity',
                'distribution': {'critical': 400, 'medium': 600},
                'high_severity_count': 400
            },
            'category_analysis': {},
            'top_sources': {},
            'anomalies': {'volume_spikes': [{'date': '2025-01-15', 'count': 50}]}
        }
    
    @pytest.fixture
    def mock_quality_results(self):
        return {
            'completeness_score': {'completeness_score': 65, 'grade': 'D'},
            'issues_list': [
                {'severity': 'high', 'message': 'Critical issue'},
                {'severity': 'medium', 'message': 'Medium issue'}
            ],
            'missing_data': {'critical_columns_affected': [{'column': 'id', 'null_count': 10}]},
            'duplicates': {'full_row_duplicates': 5, 'duplicate_percentage': 0.5}
        }
    
    def test_generates_suggestions(self, mock_trend_results, mock_quality_results):
        """Test that suggestions are generated."""
        df = pd.DataFrame({'id': [1, 2, 3], 'severity': ['high', 'medium', 'low']})
        
        engine = SuggestionEngine(df, mock_trend_results, mock_quality_results)
        suggestions = engine.generate_all_suggestions()
        
        assert len(suggestions) > 0
    
    def test_suggestions_have_required_fields(self, mock_trend_results, mock_quality_results):
        """Test suggestion structure."""
        df = pd.DataFrame({'id': [1, 2, 3], 'severity': ['high', 'medium', 'low']})
        
        engine = SuggestionEngine(df, mock_trend_results, mock_quality_results)
        suggestions = engine.generate_all_suggestions()
        
        for s in suggestions:
            assert s.title
            assert s.description
            assert s.priority in SuggestionPriority
            assert len(s.actions) > 0
    
    def test_critical_quality_generates_critical_suggestion(self, mock_trend_results, mock_quality_results):
        """Test that low quality score generates critical suggestion."""
        df = pd.DataFrame({'id': [1, 2, 3]})
        
        engine = SuggestionEngine(df, mock_trend_results, mock_quality_results)
        suggestions = engine.generate_all_suggestions()
        
        critical_suggestions = [s for s in suggestions if s.priority == SuggestionPriority.CRITICAL]
        assert len(critical_suggestions) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
