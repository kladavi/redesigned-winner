"""
Incident Log Analyzer - Main Entry Point
Command-line interface for analyzing alert/incident log files.
"""

import click
import json
import sys
import logging
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import print as rprint

from src.data_loader import DataLoader, load_multiple_files
from src.trend_analyzer import TrendAnalyzer
from src.quality_analyzer import QualityAnalyzer
from src.suggestion_engine import SuggestionEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

console = Console()


@click.group()
@click.version_option(version='1.0.0')
def cli():
    """
    Incident Log Analyzer
    
    Analyze alert and incident logs from NewRelic, Moogsoft, and ServiceNow.
    Identifies trends, quality issues, and generates actionable insights.
    """
    pass


@cli.command()
@click.argument('files', nargs=-1, type=click.Path(exists=True))
@click.option('--output', '-o', type=click.Path(), help='Output file for JSON results')
@click.option('--format', '-f', 'output_format', type=click.Choice(['text', 'json']), 
              default='text', help='Output format')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def analyze(files, output, output_format, verbose):
    """
    Analyze one or more incident log files.
    
    Supports CSV and XLSX files up to 100MB from NewRelic, Moogsoft, and ServiceNow.
    
    Examples:
    
        incident-analyzer analyze incidents.csv
        
        incident-analyzer analyze file1.csv file2.xlsx -o results.json
        
        incident-analyzer analyze data/*.csv --format json
    """
    if not files:
        console.print("[red]Error: No files specified[/red]")
        console.print("Usage: incident-analyzer analyze <file1> [file2] ...")
        sys.exit(1)
    
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            # Load data
            task = progress.add_task("Loading data files...", total=None)
            loader = DataLoader()
            
            if len(files) == 1:
                df, source, metadata = loader.load_file(files[0])
                if source:
                    df = loader.normalize_dataframe(df, source)
            else:
                df, metadata = load_multiple_files(list(files))
                source = metadata['files'][0].get('detected_source') if metadata['files'] else None
            
            progress.update(task, description="Running trend analysis...")
            trend_analyzer = TrendAnalyzer(df)
            trend_results = trend_analyzer.analyze_all()
            
            progress.update(task, description="Checking data quality...")
            quality_analyzer = QualityAnalyzer(df, source)
            quality_results = quality_analyzer.analyze_all()
            
            progress.update(task, description="Generating suggestions...")
            suggestion_engine = SuggestionEngine(df, trend_results, quality_results, source)
            suggestions = suggestion_engine.generate_all_suggestions()
            suggestion_results = suggestion_engine.to_dict()
        
        # Prepare combined results
        results = {
            'metadata': metadata,
            'trend_analysis': trend_results,
            'quality_analysis': quality_results,
            'suggestions': suggestion_results
        }
        
        # Output results
        if output_format == 'json' or output:
            json_output = json.dumps(results, indent=2, default=str)
            
            if output:
                Path(output).write_text(json_output)
                console.print(f"[green]Results saved to {output}[/green]")
            
            if output_format == 'json' and not output:
                print(json_output)
        else:
            _print_text_report(metadata, trend_analyzer, quality_analyzer, suggestion_engine)
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.argument('file', type=click.Path(exists=True))
def info(file):
    """
    Show basic information about an incident log file.
    
    Example:
    
        incident-analyzer info incidents.csv
    """
    try:
        loader = DataLoader()
        df, source, metadata = loader.load_file(file)
        
        console.print(Panel.fit(
            f"[bold]{metadata['file_name']}[/bold]\n"
            f"Size: {metadata['file_size_mb']} MB\n"
            f"Rows: {metadata['row_count']:,}\n"
            f"Columns: {metadata['column_count']}\n"
            f"Detected Source: {source or 'Unknown'}",
            title="File Information"
        ))
        
        # Column list
        table = Table(title="Columns")
        table.add_column("Column Name", style="cyan")
        table.add_column("Type", style="green")
        table.add_column("Non-Null", style="yellow")
        
        for col in df.columns[:20]:
            non_null = df[col].notna().sum()
            table.add_row(
                col,
                str(df[col].dtype),
                f"{non_null:,} ({non_null/len(df)*100:.1f}%)"
            )
        
        if len(df.columns) > 20:
            table.add_row("...", f"({len(df.columns) - 20} more)", "")
        
        console.print(table)
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument('file', type=click.Path(exists=True))
def quality(file):
    """
    Run only quality analysis on a file.
    
    Example:
    
        incident-analyzer quality incidents.csv
    """
    try:
        loader = DataLoader()
        df, source, _ = loader.load_file(file)
        
        analyzer = QualityAnalyzer(df, source)
        console.print(analyzer.get_quality_report())
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument('file', type=click.Path(exists=True))
def trends(file):
    """
    Run only trend analysis on a file.
    
    Example:
    
        incident-analyzer trends incidents.csv
    """
    try:
        loader = DataLoader()
        df, source, _ = loader.load_file(file)
        
        if source:
            df = loader.normalize_dataframe(df, source)
        
        analyzer = TrendAnalyzer(df)
        console.print(analyzer.get_trend_summary())
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option('--host', '-h', default='127.0.0.1', help='Host to bind to')
@click.option('--port', '-p', default=5000, help='Port to bind to')
@click.option('--debug', '-d', is_flag=True, help='Enable debug mode')
def web(host, port, debug):
    """
    Launch interactive web interface with drag-and-drop file upload.
    
    Example:
    
        incident-analyzer web
        
        incident-analyzer web --port 8080
        
        incident-analyzer web --host 0.0.0.0 --port 5000
    """
    try:
        from src.web_app import run_server
        run_server(host=host, port=port, debug=debug)
    except ImportError as e:
        console.print("[red]Error: Flask is required for web interface[/red]")
        console.print("Install with: pip install flask")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


def _print_text_report(metadata, trend_analyzer, quality_analyzer, suggestion_engine):
    """Print formatted text report to console."""
    
    # Header
    console.print()
    console.print(Panel.fit(
        "[bold blue]Incident Log Analysis Report[/bold blue]",
        subtitle=f"Analyzed {metadata.get('row_count', metadata.get('total_rows', 0)):,} incidents"
    ))
    
    # Metadata
    if 'files' in metadata:
        console.print(f"\n[bold]Files Analyzed:[/bold] {len(metadata['files'])}")
        for f in metadata['files']:
            console.print(f"  • {f['file_name']} ({f['detected_source'] or 'unknown'}) - {f['row_count']:,} rows")
    else:
        console.print(f"\n[bold]File:[/bold] {metadata.get('file_name', 'N/A')}")
        console.print(f"[bold]Source System:[/bold] {metadata.get('detected_source', 'Unknown')}")
    
    # Quality Summary
    console.print()
    console.print(Panel(quality_analyzer.get_quality_report(), title="Data Quality", border_style="yellow"))
    
    # Trend Summary
    console.print()
    console.print(Panel(trend_analyzer.get_trend_summary(), title="Trend Analysis", border_style="blue"))
    
    # Suggestions
    console.print()
    console.print(Panel(suggestion_engine.get_suggestions_report(), title="Recommendations", border_style="green"))


def main():
    """Main entry point."""
    cli()


if __name__ == '__main__':
    main()
