import xlsxwriter
from io import BytesIO
from datetime import datetime
from django.http import HttpResponse
from django.utils.text import slugify
from collections import Counter


class ExcelExporter:
    """Utility class for creating Excel exports of analysis data."""
    
    def __init__(self):
        self.workbook = None
        self.worksheet = None
        self.buffer = BytesIO()
    
    def create_analysis_export(self, analysis_results, export_format='detailed'):
        """
        Create Excel export for analysis results.
        
        Args:
            analysis_results: QuerySet of AnalysisResult objects
            export_format: 'summary' or 'detailed'
        
        Returns:
            BytesIO buffer containing Excel file
        """
        # Create workbook
        self.workbook = xlsxwriter.Workbook(self.buffer, {'in_memory': True})
        
        # Define formats
        header_format = self.workbook.add_format({
            'bold': True,
            'bg_color': '#4472C4',
            'font_color': 'white',
            'border': 1
        })
        
        cell_format = self.workbook.add_format({
            'border': 1,
            'text_wrap': True,
            'valign': 'top'
        })
        
        date_format = self.workbook.add_format({
            'border': 1,
            'num_format': 'yyyy-mm-dd hh:mm:ss'
        })
        
        if export_format == 'summary':
            self._create_summary_sheet(analysis_results, header_format, cell_format, date_format)
        else:
            self._create_detailed_sheets(analysis_results, header_format, cell_format, date_format)
        
        self.workbook.close()
        self.buffer.seek(0)
        return self.buffer
    
    def _create_summary_sheet(self, analysis_results, header_format, cell_format, date_format):
        """Create summary sheet with key metrics."""
        worksheet = self.workbook.add_worksheet('Analysis Summary')
        
        # Headers
        headers = [
            'Repository', 'Developer', 'Analysis Type', 'Date Range',
            'Total Commits', 'Lines Added', 'Lines Deleted', 'Files Changed',
            'AI Provider', 'Model', 'Cost', 'Created Date', 'Status'
        ]
        
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)
        
        # Data rows
        for row, result in enumerate(analysis_results, 1):
            task = result.task
            worksheet.write(row, 0, task.repository_name, cell_format)
            worksheet.write(row, 1, task.developer_name or 'All Developers', cell_format)
            worksheet.write(row, 2, task.analysis_type, cell_format)
            worksheet.write(row, 3, f"{task.date_from} to {task.date_to}", cell_format)
            worksheet.write(row, 4, task.total_commits or 0, cell_format)
            worksheet.write(row, 5, task.total_additions or 0, cell_format)
            worksheet.write(row, 6, task.total_deletions or 0, cell_format)
            worksheet.write(row, 7, task.file_changes or 0, cell_format)
            worksheet.write(row, 8, result.ai_provider, cell_format)
            worksheet.write(row, 9, result.model_used, cell_format)
            worksheet.write(row, 10, float(result.cost_usd or 0), cell_format)
            worksheet.write(row, 11, result.created_at, date_format)
            worksheet.write(row, 12, task.status, cell_format)
        
        # Auto-adjust column widths
        worksheet.autofit()
    
    def _create_detailed_sheets(self, analysis_results, header_format, cell_format, date_format):
        """Create detailed sheets with full analysis content."""
        # Summary sheet
        self._create_summary_sheet(analysis_results, header_format, cell_format, date_format)
        
        # Detailed analysis sheet
        worksheet = self.workbook.add_worksheet('Detailed Analysis')
        
        headers = [
            'Repository', 'Developer', 'Analysis Type', 'AI Analysis',
            'Key Insights', 'Recommendations', 'Metadata', 'Created Date'
        ]
        
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)
        
        for row, result in enumerate(analysis_results, 1):
            task = result.task
            analysis_data = result.analysis_result or {}
            
            worksheet.write(row, 0, task.repository_name, cell_format)
            worksheet.write(row, 1, task.developer_name or 'All Developers', cell_format)
            worksheet.write(row, 2, task.analysis_type, cell_format)
            worksheet.write(row, 3, analysis_data.get('analysis', ''), cell_format)
            worksheet.write(row, 4, '\n'.join(analysis_data.get('key_insights', [])), cell_format)
            worksheet.write(row, 5, '\n'.join(analysis_data.get('recommendations', [])), cell_format)
            worksheet.write(row, 6, str(analysis_data.get('metadata', {})), cell_format)
            worksheet.write(row, 7, result.created_at, date_format)
        
        # Set column widths
        worksheet.set_column('A:B', 15)
        worksheet.set_column('C:C', 20)
        worksheet.set_column('D:F', 40)
        worksheet.set_column('G:G', 25)
        worksheet.set_column('H:H', 20)
        
        # Raw data sheet if needed
        if len(analysis_results) <= 100:  # Only for smaller datasets
            self._create_raw_data_sheet(analysis_results, header_format, cell_format, date_format)
    
    def _create_raw_data_sheet(self, analysis_results, header_format, cell_format, date_format):
        """Create sheet with raw commit data."""
        worksheet = self.workbook.add_worksheet('Raw Commit Data')
        
        headers = [
            'Repository', 'Developer', 'Commit Hash', 'Message',
            'Date', 'Additions', 'Deletions', 'Files Changed'
        ]
        
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)
        
        row = 1
        for result in analysis_results:
            task = result.task
            commit_data = task.commit_data or []
            
            for commit in commit_data:
                worksheet.write(row, 0, task.repository_name, cell_format)
                worksheet.write(row, 1, task.developer_name or 'All', cell_format)
                worksheet.write(row, 2, commit.get('sha', ''), cell_format)
                worksheet.write(row, 3, commit.get('message', ''), cell_format)
                worksheet.write(row, 4, commit.get('date', ''), cell_format)
                worksheet.write(row, 5, commit.get('additions', 0), cell_format)
                worksheet.write(row, 6, commit.get('deletions', 0), cell_format)
                worksheet.write(row, 7, len(commit.get('files', [])), cell_format)
                row += 1
        
        worksheet.autofit()


def create_export_response(buffer, filename_base, file_format='xlsx'):
    """
    Create HTTP response for file download.
    
    Args:
        buffer: BytesIO buffer containing file data
        filename_base: Base filename without extension
        file_format: File format ('xlsx', 'csv', etc.)
    
    Returns:
        HttpResponse for file download
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{slugify(filename_base)}_{timestamp}.{file_format}"
    
    if file_format == 'xlsx':
        content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    elif file_format == 'csv':
        content_type = 'text/csv'
    else:
        content_type = 'application/octet-stream'
    
    response = HttpResponse(
        buffer.getvalue(),
        content_type=content_type
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def analyze_commit_patterns(commit_data):
    """
    Analyze commit patterns from commit data
    
    Args:
        commit_data: List of commit dictionaries
    
    Returns:
        Dictionary with pattern analysis
    """
    if not commit_data:
        return {}
    
    # Convert date strings to datetime and extract patterns
    hours = []
    days_of_week = []
    additions = []
    deletions = []
    
    for commit in commit_data:
        if 'date' in commit:
            try:
                # Parse datetime string
                if isinstance(commit['date'], str):
                    dt = datetime.fromisoformat(commit['date'].replace('Z', '+00:00'))
                else:
                    dt = commit['date']
                
                hours.append(dt.hour)
                days_of_week.append(dt.strftime('%A'))  # Full day name
            except (ValueError, AttributeError):
                pass
        
        if 'additions' in commit and commit['additions'] is not None:
            additions.append(commit['additions'])
        if 'deletions' in commit and commit['deletions'] is not None:
            deletions.append(commit['deletions'])
    
    # Calculate statistics
    patterns = {
        'total_commits': len(commit_data),
        'avg_additions': sum(additions) / len(additions) if additions else 0,
        'avg_deletions': sum(deletions) / len(deletions) if deletions else 0,
        'most_active_hour': Counter(hours).most_common(1)[0][0] if hours else None,
        'most_active_day': Counter(days_of_week).most_common(1)[0][0] if days_of_week else None,
        'hourly_distribution': dict(Counter(hours)) if hours else {},
        'daily_distribution': dict(Counter(days_of_week)) if days_of_week else {}
    }
    
    return patterns


def validate_export_parameters(request):
    """
    Validate export request parameters.
    
    Args:
        request: Django request object
    
    Returns:
        Tuple of (is_valid, errors, cleaned_data)
    """
    errors = []
    cleaned_data = {}
    
    # Export format
    export_format = request.GET.get('format', 'detailed')
    if export_format not in ['summary', 'detailed']:
        errors.append('Invalid export format. Must be "summary" or "detailed".')
    cleaned_data['format'] = export_format
    
    # File type
    file_type = request.GET.get('type', 'xlsx')
    if file_type not in ['xlsx', 'csv']:
        errors.append('Invalid file type. Must be "xlsx" or "csv".')
    cleaned_data['type'] = file_type
    
    # Date range
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    if date_from:
        try:
            cleaned_data['date_from'] = datetime.strptime(date_from, '%Y-%m-%d').date()
        except ValueError:
            errors.append('Invalid date_from format. Use YYYY-MM-DD.')
    
    if date_to:
        try:
            cleaned_data['date_to'] = datetime.strptime(date_to, '%Y-%m-%d').date()
        except ValueError:
            errors.append('Invalid date_to format. Use YYYY-MM-DD.')
    
    # Repository filter
    repository = request.GET.get('repository')
    if repository:
        cleaned_data['repository'] = repository
    
    # Developer filter
    developer = request.GET.get('developer')
    if developer:
        cleaned_data['developer'] = developer
    
    return len(errors) == 0, errors, cleaned_data