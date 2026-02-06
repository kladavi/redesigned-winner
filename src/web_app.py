"""
Web Application for Incident Log Analyzer
Provides drag-and-drop file upload and interactive analysis.
"""

import os
import json
import tempfile
import logging
from pathlib import Path
from flask import Flask, request, jsonify, render_template_string
from werkzeug.utils import secure_filename

from src.data_loader import DataLoader
from src.trend_analyzer import TrendAnalyzer
from src.quality_analyzer import QualityAnalyzer
from src.suggestion_engine import SuggestionEngine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()

ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}


def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# HTML template embedded for single-file deployment
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Incident Log Analyzer</title>
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: #e4e4e7;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        header {
            text-align: center;
            padding: 30px 0;
        }
        
        h1 {
            font-size: 2.5rem;
            background: linear-gradient(90deg, #60a5fa, #a78bfa);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }
        
        .subtitle {
            color: #9ca3af;
            font-size: 1.1rem;
        }
        
        .drop-zone {
            border: 3px dashed #4b5563;
            border-radius: 16px;
            padding: 60px 40px;
            text-align: center;
            transition: all 0.3s ease;
            background: rgba(255, 255, 255, 0.02);
            cursor: pointer;
            margin-bottom: 30px;
        }
        
        .drop-zone:hover, .drop-zone.dragover {
            border-color: #60a5fa;
            background: rgba(96, 165, 250, 0.1);
        }
        
        .drop-zone-icon {
            font-size: 4rem;
            margin-bottom: 20px;
        }
        
        .drop-zone-text {
            font-size: 1.3rem;
            margin-bottom: 10px;
        }
        
        .drop-zone-hint {
            color: #6b7280;
            font-size: 0.9rem;
        }
        
        .file-input {
            display: none;
        }
        
        .file-info {
            background: rgba(96, 165, 250, 0.1);
            border: 1px solid #3b82f6;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
            display: none;
        }
        
        .file-info.show {
            display: block;
        }
        
        .file-name {
            font-weight: 600;
            color: #60a5fa;
            font-size: 1.1rem;
        }
        
        .file-size {
            color: #9ca3af;
            font-size: 0.9rem;
        }
        
        .btn {
            padding: 14px 32px;
            border: none;
            border-radius: 10px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        
        .btn-primary {
            background: linear-gradient(90deg, #3b82f6, #8b5cf6);
            color: white;
        }
        
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(59, 130, 246, 0.3);
        }
        
        .btn-primary:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }
        
        .loading {
            display: none;
            text-align: center;
            padding: 40px;
        }
        
        .loading.show {
            display: block;
        }
        
        .spinner {
            width: 50px;
            height: 50px;
            border: 4px solid rgba(96, 165, 250, 0.2);
            border-top-color: #60a5fa;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        .results {
            display: none;
        }
        
        .results.show {
            display: block;
        }
        
        .card {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 20px;
        }
        
        .card-header {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .card-icon {
            font-size: 1.5rem;
        }
        
        .card-title {
            font-size: 1.3rem;
            font-weight: 600;
        }
        
        .metric-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 20px;
        }
        
        .metric {
            text-align: center;
            padding: 15px;
            background: rgba(0, 0, 0, 0.2);
            border-radius: 10px;
        }
        
        .metric-value {
            font-size: 2rem;
            font-weight: 700;
            color: #60a5fa;
        }
        
        .metric-label {
            font-size: 0.85rem;
            color: #9ca3af;
            margin-top: 5px;
        }
        
        .grade {
            display: inline-block;
            padding: 8px 20px;
            border-radius: 8px;
            font-size: 1.5rem;
            font-weight: 700;
        }
        
        .grade-a { background: #22c55e; color: white; }
        .grade-b { background: #84cc16; color: white; }
        .grade-c { background: #eab308; color: black; }
        .grade-d { background: #f97316; color: white; }
        .grade-f { background: #ef4444; color: white; }
        
        .suggestion-list {
            list-style: none;
        }
        
        .suggestion-item {
            background: rgba(0, 0, 0, 0.2);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 15px;
            border-left: 4px solid;
        }
        
        .suggestion-critical { border-left-color: #ef4444; }
        .suggestion-high { border-left-color: #f97316; }
        .suggestion-medium { border-left-color: #eab308; }
        .suggestion-low { border-left-color: #22c55e; }
        
        .suggestion-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 10px;
        }
        
        .suggestion-title {
            font-weight: 600;
            font-size: 1.1rem;
        }
        
        .suggestion-badge {
            padding: 4px 10px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
        }
        
        .badge-critical { background: #ef4444; }
        .badge-high { background: #f97316; }
        .badge-medium { background: #eab308; color: black; }
        .badge-low { background: #22c55e; }
        
        .suggestion-desc {
            color: #d1d5db;
            margin-bottom: 15px;
            line-height: 1.5;
        }
        
        .suggestion-actions {
            background: rgba(0, 0, 0, 0.2);
            border-radius: 8px;
            padding: 15px;
        }
        
        .suggestion-actions h4 {
            font-size: 0.85rem;
            color: #9ca3af;
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .suggestion-actions ul {
            list-style: none;
            padding-left: 0;
        }
        
        .suggestion-actions li {
            padding: 5px 0;
            padding-left: 20px;
            position: relative;
        }
        
        .suggestion-actions li::before {
            content: "→";
            position: absolute;
            left: 0;
            color: #60a5fa;
        }
        
        .issues-list {
            list-style: none;
        }
        
        .issue-item {
            padding: 12px 15px;
            background: rgba(0, 0, 0, 0.2);
            border-radius: 8px;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .issue-severity {
            width: 10px;
            height: 10px;
            border-radius: 50%;
        }
        
        .severity-high { background: #ef4444; }
        .severity-medium { background: #eab308; }
        .severity-low { background: #22c55e; }
        
        .tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        
        .tab {
            padding: 10px 20px;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .tab:hover {
            background: rgba(255, 255, 255, 0.1);
        }
        
        .tab.active {
            background: #3b82f6;
            border-color: #3b82f6;
        }
        
        .tab-content {
            display: none;
        }
        
        .tab-content.active {
            display: block;
        }
        
        .chart-container {
            background: rgba(0, 0, 0, 0.2);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
        }
        
        .bar-chart {
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        
        .bar-row {
            display: flex;
            align-items: center;
            gap: 15px;
        }
        
        .bar-label {
            width: 120px;
            font-size: 0.9rem;
            color: #9ca3af;
            text-align: right;
            flex-shrink: 0;
        }
        
        .bar-track {
            flex: 1;
            height: 24px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 4px;
            overflow: hidden;
        }
        
        .bar-fill {
            height: 100%;
            background: linear-gradient(90deg, #3b82f6, #8b5cf6);
            border-radius: 4px;
            display: flex;
            align-items: center;
            justify-content: flex-end;
            padding-right: 10px;
            font-size: 0.8rem;
            font-weight: 600;
            min-width: 40px;
        }
        
        .reset-btn {
            position: fixed;
            bottom: 30px;
            right: 30px;
            padding: 15px 25px;
            background: #374151;
            color: white;
            border: none;
            border-radius: 50px;
            cursor: pointer;
            font-weight: 600;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
            display: none;
        }
        
        .reset-btn.show {
            display: block;
        }
        
        .reset-btn:hover {
            background: #4b5563;
        }
        
        @media (max-width: 768px) {
            h1 { font-size: 1.8rem; }
            .drop-zone { padding: 40px 20px; }
            .bar-label { width: 80px; font-size: 0.8rem; }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🔍 Incident Log Analyzer</h1>
            <p class="subtitle">Drag and drop your CSV or Excel files to analyze trends and quality</p>
        </header>
        
        <div id="uploadSection">
            <div class="drop-zone" id="dropZone">
                <div class="drop-zone-icon">📁</div>
                <div class="drop-zone-text">Drop your incident log file here</div>
                <div class="drop-zone-hint">Supports CSV, XLSX files up to 100MB</div>
                <div class="drop-zone-hint" style="margin-top: 10px;">NewRelic • Moogsoft • ServiceNow</div>
                <input type="file" class="file-input" id="fileInput" accept=".csv,.xlsx,.xls">
            </div>
            
            <div class="file-info" id="fileInfo">
                <span class="file-name" id="fileName"></span>
                <span class="file-size" id="fileSize"></span>
            </div>
            
            <div style="text-align: center;">
                <button class="btn btn-primary" id="analyzeBtn" disabled>
                    🚀 Analyze File
                </button>
            </div>
        </div>
        
        <div class="loading" id="loading">
            <div class="spinner"></div>
            <p>Analyzing your data...</p>
            <p style="color: #6b7280; font-size: 0.9rem; margin-top: 10px;">This may take a moment for large files</p>
        </div>
        
        <div class="results" id="results">
            <div class="tabs">
                <div class="tab active" data-tab="overview">📊 Overview</div>
                <div class="tab" data-tab="quality">🎯 Quality</div>
                <div class="tab" data-tab="trends">📈 Trends</div>
                <div class="tab" data-tab="suggestions">💡 Suggestions</div>
            </div>
            
            <!-- Overview Tab -->
            <div class="tab-content active" id="tab-overview">
                <div class="card">
                    <div class="card-header">
                        <span class="card-icon">📋</span>
                        <span class="card-title">File Summary</span>
                    </div>
                    <div class="metric-grid" id="summaryMetrics"></div>
                </div>
                
                <div class="card">
                    <div class="card-header">
                        <span class="card-icon">⚡</span>
                        <span class="card-title">Key Insights</span>
                    </div>
                    <div id="keyInsights"></div>
                </div>
            </div>
            
            <!-- Quality Tab -->
            <div class="tab-content" id="tab-quality">
                <div class="card">
                    <div class="card-header">
                        <span class="card-icon">🎯</span>
                        <span class="card-title">Data Quality Score</span>
                    </div>
                    <div style="text-align: center; margin-bottom: 20px;">
                        <span class="grade" id="qualityGrade">-</span>
                        <p style="margin-top: 10px; color: #9ca3af;" id="qualityScore"></p>
                    </div>
                    <div class="metric-grid" id="qualityMetrics"></div>
                </div>
                
                <div class="card">
                    <div class="card-header">
                        <span class="card-icon">⚠️</span>
                        <span class="card-title">Issues Found</span>
                    </div>
                    <ul class="issues-list" id="issuesList"></ul>
                </div>
            </div>
            
            <!-- Trends Tab -->
            <div class="tab-content" id="tab-trends">
                <div class="card">
                    <div class="card-header">
                        <span class="card-icon">📈</span>
                        <span class="card-title">Volume Trends</span>
                    </div>
                    <div id="volumeTrend"></div>
                </div>
                
                <div class="card">
                    <div class="card-header">
                        <span class="card-icon">🕐</span>
                        <span class="card-title">Peak Hours</span>
                    </div>
                    <div class="chart-container">
                        <div class="bar-chart" id="hourlyChart"></div>
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-header">
                        <span class="card-icon">📊</span>
                        <span class="card-title">Severity Distribution</span>
                    </div>
                    <div class="chart-container">
                        <div class="bar-chart" id="severityChart"></div>
                    </div>
                </div>
            </div>
            
            <!-- Suggestions Tab -->
            <div class="tab-content" id="tab-suggestions">
                <div class="card">
                    <div class="card-header">
                        <span class="card-icon">💡</span>
                        <span class="card-title">Recommendations</span>
                    </div>
                    <ul class="suggestion-list" id="suggestionsList"></ul>
                </div>
            </div>
        </div>
    </div>
    
    <button class="reset-btn" id="resetBtn">↻ Analyze Another File</button>

    <script>
        const dropZone = document.getElementById('dropZone');
        const fileInput = document.getElementById('fileInput');
        const fileInfo = document.getElementById('fileInfo');
        const fileName = document.getElementById('fileName');
        const fileSize = document.getElementById('fileSize');
        const analyzeBtn = document.getElementById('analyzeBtn');
        const uploadSection = document.getElementById('uploadSection');
        const loading = document.getElementById('loading');
        const results = document.getElementById('results');
        const resetBtn = document.getElementById('resetBtn');
        
        let selectedFile = null;
        
        // Drag and drop handlers
        dropZone.addEventListener('click', () => fileInput.click());
        
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        });
        
        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('dragover');
        });
        
        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
            const file = e.dataTransfer.files[0];
            if (file) handleFile(file);
        });
        
        fileInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) handleFile(file);
        });
        
        function handleFile(file) {
            const ext = file.name.split('.').pop().toLowerCase();
            if (!['csv', 'xlsx', 'xls'].includes(ext)) {
                alert('Please upload a CSV or Excel file');
                return;
            }
            
            selectedFile = file;
            fileName.textContent = file.name;
            fileSize.textContent = ` (${formatBytes(file.size)})`;
            fileInfo.classList.add('show');
            analyzeBtn.disabled = false;
        }
        
        function formatBytes(bytes) {
            if (bytes === 0) return '0 Bytes';
            const k = 1024;
            const sizes = ['Bytes', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        }
        
        analyzeBtn.addEventListener('click', async () => {
            if (!selectedFile) return;
            
            uploadSection.style.display = 'none';
            loading.classList.add('show');
            
            const formData = new FormData();
            formData.append('file', selectedFile);
            
            try {
                const response = await fetch('/api/analyze', {
                    method: 'POST',
                    body: formData
                });
                
                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.error || 'Analysis failed');
                }
                
                const data = await response.json();
                displayResults(data);
            } catch (error) {
                alert('Error: ' + error.message);
                resetUI();
            }
        });
        
        function displayResults(data) {
            loading.classList.remove('show');
            results.classList.add('show');
            resetBtn.classList.add('show');
            
            // Summary metrics
            const meta = data.metadata;
            const summary = data.trend_analysis.summary;
            document.getElementById('summaryMetrics').innerHTML = `
                <div class="metric">
                    <div class="metric-value">${(meta.row_count || meta.total_rows || 0).toLocaleString()}</div>
                    <div class="metric-label">Total Incidents</div>
                </div>
                <div class="metric">
                    <div class="metric-value">${meta.column_count || meta.files?.[0]?.column_count || '-'}</div>
                    <div class="metric-label">Columns</div>
                </div>
                <div class="metric">
                    <div class="metric-value">${meta.detected_source || meta.files?.[0]?.detected_source || 'Unknown'}</div>
                    <div class="metric-label">Source System</div>
                </div>
                <div class="metric">
                    <div class="metric-value">${meta.file_size_mb || meta.files?.[0]?.file_size_mb || '-'} MB</div>
                    <div class="metric-label">File Size</div>
                </div>
            `;
            
            // Key insights
            const insights = [];
            if (summary.date_range) {
                insights.push(`📅 Data spans ${summary.date_range.span_days} days (${summary.date_range.start?.substring(0,10)} to ${summary.date_range.end?.substring(0,10)})`);
            }
            const trend = data.trend_analysis.temporal_patterns?.weekly_trend;
            if (trend?.direction) {
                const icon = trend.direction === 'increasing' ? '📈' : (trend.direction === 'decreasing' ? '📉' : '➡️');
                insights.push(`${icon} Volume is ${trend.direction} (${trend.change_percent > 0 ? '+' : ''}${trend.change_percent}% week-over-week)`);
            }
            const qualityScore = data.quality_analysis.completeness_score;
            insights.push(`🎯 Data quality grade: ${qualityScore.grade} (${qualityScore.completeness_score}/100)`);
            insights.push(`💡 ${data.suggestions.total_suggestions} recommendations generated`);
            
            document.getElementById('keyInsights').innerHTML = insights.map(i => 
                `<p style="padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,0.1);">${i}</p>`
            ).join('');
            
            // Quality tab
            const grade = qualityScore.grade;
            const gradeEl = document.getElementById('qualityGrade');
            gradeEl.textContent = grade;
            gradeEl.className = 'grade grade-' + grade.toLowerCase();
            document.getElementById('qualityScore').textContent = `Score: ${qualityScore.completeness_score}/100`;
            
            const qualitySummary = data.quality_analysis.summary;
            document.getElementById('qualityMetrics').innerHTML = `
                <div class="metric">
                    <div class="metric-value">${qualitySummary.overall_fill_rate}%</div>
                    <div class="metric-label">Fill Rate</div>
                </div>
                <div class="metric">
                    <div class="metric-value">${qualitySummary.null_cells.toLocaleString()}</div>
                    <div class="metric-label">Null Cells</div>
                </div>
                <div class="metric">
                    <div class="metric-value">${data.quality_analysis.duplicates?.full_row_duplicates || 0}</div>
                    <div class="metric-label">Duplicates</div>
                </div>
                <div class="metric">
                    <div class="metric-value">${qualitySummary.memory_usage_mb} MB</div>
                    <div class="metric-label">Memory Usage</div>
                </div>
            `;
            
            // Issues list
            const issues = data.quality_analysis.issues_list || [];
            document.getElementById('issuesList').innerHTML = issues.length > 0 
                ? issues.slice(0, 10).map(issue => `
                    <li class="issue-item">
                        <span class="issue-severity severity-${issue.severity || 'low'}"></span>
                        <span>${issue.message}</span>
                    </li>
                `).join('')
                : '<li class="issue-item">✅ No significant issues found</li>';
            
            // Trends tab
            const temporal = data.trend_analysis.temporal_patterns || {};
            if (trend) {
                document.getElementById('volumeTrend').innerHTML = `
                    <div style="text-align: center; padding: 20px;">
                        <div style="font-size: 3rem;">${trend.direction === 'increasing' ? '📈' : (trend.direction === 'decreasing' ? '📉' : '➡️')}</div>
                        <div style="font-size: 1.5rem; font-weight: 600; margin: 10px 0;">${trend.direction.toUpperCase()}</div>
                        <div style="color: #9ca3af;">
                            Recent avg: ${trend.recent_avg} incidents/day<br>
                            Previous avg: ${trend.previous_avg} incidents/day<br>
                            Change: ${trend.change_percent > 0 ? '+' : ''}${trend.change_percent}%
                        </div>
                    </div>
                `;
            } else {
                document.getElementById('volumeTrend').innerHTML = '<p style="text-align:center;color:#6b7280;">Insufficient time data for trend analysis</p>';
            }
            
            // Hourly chart
            const hourly = temporal.hourly_distribution || {};
            const maxHourly = Math.max(...Object.values(hourly), 1);
            document.getElementById('hourlyChart').innerHTML = Object.entries(hourly)
                .sort((a, b) => parseInt(a[0]) - parseInt(b[0]))
                .slice(0, 12)
                .map(([hour, count]) => `
                    <div class="bar-row">
                        <span class="bar-label">${hour}:00</span>
                        <div class="bar-track">
                            <div class="bar-fill" style="width: ${(count/maxHourly*100)}%">${count}</div>
                        </div>
                    </div>
                `).join('') || '<p style="color:#6b7280;">No hourly data available</p>';
            
            // Severity chart
            const severity = data.trend_analysis.severity_distribution?.distribution || {};
            const maxSev = Math.max(...Object.values(severity), 1);
            document.getElementById('severityChart').innerHTML = Object.entries(severity)
                .sort((a, b) => b[1] - a[1])
                .map(([sev, count]) => `
                    <div class="bar-row">
                        <span class="bar-label">${sev}</span>
                        <div class="bar-track">
                            <div class="bar-fill" style="width: ${(count/maxSev*100)}%">${count}</div>
                        </div>
                    </div>
                `).join('') || '<p style="color:#6b7280;">No severity data available</p>';
            
            // Suggestions
            const suggestions = data.suggestions.suggestions || [];
            document.getElementById('suggestionsList').innerHTML = suggestions.length > 0
                ? suggestions.map(s => `
                    <li class="suggestion-item suggestion-${s.priority}">
                        <div class="suggestion-header">
                            <span class="suggestion-title">${s.title}</span>
                            <span class="suggestion-badge badge-${s.priority}">${s.priority}</span>
                        </div>
                        <p class="suggestion-desc">${s.description}</p>
                        <div class="suggestion-actions">
                            <h4>Recommended Actions</h4>
                            <ul>
                                ${s.actions.map(a => `<li>${a}</li>`).join('')}
                            </ul>
                        </div>
                    </li>
                `).join('')
                : '<li class="issue-item">✅ No recommendations at this time</li>';
        }
        
        // Tab switching
        document.querySelectorAll('.tab').forEach(tab => {
            tab.addEventListener('click', () => {
                document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
                document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
                tab.classList.add('active');
                document.getElementById('tab-' + tab.dataset.tab).classList.add('active');
            });
        });
        
        // Reset
        resetBtn.addEventListener('click', resetUI);
        
        function resetUI() {
            selectedFile = null;
            fileInput.value = '';
            fileInfo.classList.remove('show');
            analyzeBtn.disabled = true;
            loading.classList.remove('show');
            results.classList.remove('show');
            resetBtn.classList.remove('show');
            uploadSection.style.display = 'block';
            
            // Reset tabs
            document.querySelectorAll('.tab').forEach((t, i) => {
                t.classList.toggle('active', i === 0);
            });
            document.querySelectorAll('.tab-content').forEach((c, i) => {
                c.classList.toggle('active', i === 0);
            });
        }
    </script>
</body>
</html>
'''


@app.route('/')
def index():
    """Serve the main application page."""
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/analyze', methods=['POST'])
def analyze():
    """Analyze uploaded incident log file."""
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Supported: CSV, XLSX'}), 400
    
    try:
        # Save to temp file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        logger.info(f"Processing file: {filename}")
        
        # Load and analyze
        loader = DataLoader()
        df, source, metadata = loader.load_file(filepath)
        
        # Normalize if source detected
        if source:
            df = loader.normalize_dataframe(df, source)
        
        # Run analyses
        trend_analyzer = TrendAnalyzer(df)
        trend_results = trend_analyzer.analyze_all()
        
        quality_analyzer = QualityAnalyzer(df, source)
        quality_results = quality_analyzer.analyze_all()
        
        suggestion_engine = SuggestionEngine(df, trend_results, quality_results, source)
        suggestion_results = suggestion_engine.to_dict()
        
        # Clean up temp file
        try:
            os.remove(filepath)
        except Exception:
            pass
        
        # Return results
        return jsonify({
            'metadata': metadata,
            'trend_analysis': trend_results,
            'quality_analysis': quality_results,
            'suggestions': suggestion_results
        })
        
    except Exception as e:
        logger.error(f"Analysis error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/health')
def health():
    """Health check endpoint."""
    return jsonify({'status': 'ok'})


def run_server(host='127.0.0.1', port=5000, debug=False):
    """Run the web server."""
    print(f"\n🚀 Incident Log Analyzer Web Interface")
    print(f"   Open http://{host}:{port} in your browser\n")
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    run_server(debug=True)
