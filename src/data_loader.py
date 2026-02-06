"""
Data Loader Module
Handles loading CSV and XLSX files with support for large files (<100MB).
Automatically detects source system (NewRelic, Moogsoft, ServiceNow).
"""

import pandas as pd
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
import logging

logger = logging.getLogger(__name__)


class DataLoader:
    """Loads and preprocesses incident/alert log files."""
    
    # Column name patterns for source detection
    SOURCE_SIGNATURES = {
        'newrelic': [
            'incident_id', 'condition_name', 'policy_name', 'entity_name',
            'violation_url', 'runbook_url', 'nrql_query', 'account_id'
        ],
        'moogsoft': [
            'alert_id', 'situation_id', 'sig_id', 'source', 'class', 
            'manager', 'severity', 'first_event_time', 'last_event_time',
            'moog_id', 'dedup_key'
        ],
        'servicenow': [
            'number', 'sys_id', 'caller_id', 'assignment_group', 'assigned_to',
            'short_description', 'priority', 'state', 'category', 'subcategory',
            'cmdb_ci', 'impact', 'urgency', 'incident_state'
        ]
    }
    
    # Common column mappings for normalization
    COLUMN_MAPPINGS = {
        'newrelic': {
            'incident_id': 'id',
            'condition_name': 'title',
            'policy_name': 'category',
            'entity_name': 'source',
            'opened_at': 'created_time',
            'closed_at': 'resolved_time',
            'duration': 'duration_seconds',
            'severity': 'severity'
        },
        'moogsoft': {
            'alert_id': 'id',
            'description': 'title',
            'class': 'category',
            'source': 'source',
            'first_event_time': 'created_time',
            'last_event_time': 'resolved_time',
            'severity': 'severity'
        },
        'servicenow': {
            'number': 'id',
            'short_description': 'title',
            'category': 'category',
            'cmdb_ci': 'source',
            'sys_created_on': 'created_time',
            'resolved_at': 'resolved_time',
            'priority': 'severity',
            'state': 'status'
        }
    }
    
    def __init__(self, chunk_size: int = 50000):
        """
        Initialize the data loader.
        
        Args:
            chunk_size: Number of rows to process at a time for large files
        """
        self.chunk_size = chunk_size
    
    def load_file(self, file_path: str) -> Tuple[pd.DataFrame, str, Dict[str, Any]]:
        """
        Load a CSV or XLSX file and detect its source.
        
        Args:
            file_path: Path to the file to load
            
        Returns:
            Tuple of (DataFrame, detected_source, metadata)
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_size_mb = path.stat().st_size / (1024 * 1024)
        logger.info(f"Loading file: {path.name} ({file_size_mb:.2f} MB)")
        
        if file_size_mb > 100:
            logger.warning(f"File size ({file_size_mb:.2f} MB) exceeds recommended 100MB limit")
        
        # Load based on file extension
        suffix = path.suffix.lower()
        if suffix == '.csv':
            df = self._load_csv(path, file_size_mb)
        elif suffix in ['.xlsx', '.xls']:
            df = self._load_excel(path)
        else:
            raise ValueError(f"Unsupported file format: {suffix}")
        
        # Detect source system
        detected_source = self._detect_source(df)
        
        # Build metadata
        metadata = {
            'file_name': path.name,
            'file_size_mb': round(file_size_mb, 2),
            'row_count': len(df),
            'column_count': len(df.columns),
            'columns': list(df.columns),
            'detected_source': detected_source
        }
        
        logger.info(f"Loaded {len(df):,} rows from {detected_source or 'unknown'} source")
        
        return df, detected_source, metadata
    
    def _load_csv(self, path: Path, file_size_mb: float) -> pd.DataFrame:
        """Load CSV file, using chunked reading for large files."""
        if file_size_mb > 50:
            # Chunked loading for large files
            chunks = []
            for chunk in pd.read_csv(path, chunksize=self.chunk_size, low_memory=False):
                chunks.append(chunk)
            return pd.concat(chunks, ignore_index=True)
        else:
            return pd.read_csv(path, low_memory=False)
    
    def _load_excel(self, path: Path) -> pd.DataFrame:
        """Load Excel file."""
        return pd.read_excel(path, engine='openpyxl')
    
    def _detect_source(self, df: pd.DataFrame) -> Optional[str]:
        """Detect the source system based on column names."""
        columns_lower = {col.lower().replace(' ', '_') for col in df.columns}
        
        best_match = None
        best_score = 0
        
        for source, signatures in self.SOURCE_SIGNATURES.items():
            matches = sum(1 for sig in signatures if sig in columns_lower)
            score = matches / len(signatures)
            
            if score > best_score and matches >= 2:
                best_score = score
                best_match = source
        
        return best_match
    
    def normalize_dataframe(self, df: pd.DataFrame, source: str) -> pd.DataFrame:
        """
        Normalize column names to a common schema.
        
        Args:
            df: Input DataFrame
            source: Detected source system
            
        Returns:
            DataFrame with normalized column names
        """
        if source not in self.COLUMN_MAPPINGS:
            return df.copy()
        
        mapping = self.COLUMN_MAPPINGS[source]
        df_normalized = df.copy()
        
        # Create lowercase column mapping
        col_lower_map = {col.lower().replace(' ', '_'): col for col in df.columns}
        
        # Rename columns that match
        rename_map = {}
        for old_name, new_name in mapping.items():
            if old_name in col_lower_map:
                rename_map[col_lower_map[old_name]] = new_name
        
        df_normalized = df_normalized.rename(columns=rename_map)
        
        # Parse datetime columns
        for col in ['created_time', 'resolved_time']:
            if col in df_normalized.columns:
                df_normalized[col] = pd.to_datetime(
                    df_normalized[col], 
                    errors='coerce',
                    infer_datetime_format=True
                )
        
        return df_normalized


def load_multiple_files(file_paths: list) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Load and combine multiple incident log files.
    
    Args:
        file_paths: List of file paths to load
        
    Returns:
        Tuple of (combined DataFrame, combined metadata)
    """
    loader = DataLoader()
    all_dfs = []
    all_metadata = {'files': []}
    
    for path in file_paths:
        df, source, meta = loader.load_file(path)
        
        # Normalize if source detected
        if source:
            df = loader.normalize_dataframe(df, source)
        
        # Add source tracking column
        df['_source_file'] = meta['file_name']
        df['_source_system'] = source or 'unknown'
        
        all_dfs.append(df)
        all_metadata['files'].append(meta)
    
    combined = pd.concat(all_dfs, ignore_index=True, sort=False)
    all_metadata['total_rows'] = len(combined)
    all_metadata['total_files'] = len(file_paths)
    
    return combined, all_metadata
