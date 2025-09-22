from django.core.management.base import BaseCommand
from apps.agents.models import AgentTemplate


class Command(BaseCommand):
    help = 'Create default agent templates'
    
    def handle(self, *args, **options):
        templates = [
            {
                'name': 'Developer Performance Analysis',
                'description': 'Analyzes individual developer performance including commit frequency, code quality, and productivity metrics.',
                'category': 'performance',
                'tags': 'performance,productivity,developer,metrics',
                'default_ai_provider': 'openai',
                'default_model': 'gpt-3.5-turbo',
                'default_temperature': 0.7,
                'default_max_tokens': 2000,
                'system_prompt_template': 'You are an expert software development analyst. Analyze the provided commit data and provide insights about developer performance, productivity, and code quality patterns.',
                'analysis_prompt_template': '''Analyze the performance of {developer_name} in the {repository_name} repository over {date_range}.

Commit Statistics:
- Total commits: {total_commits}
- Total additions: {total_additions}
- Total deletions: {total_deletions}
- Files changed: {file_changes}

Commit Data:
{commit_data}

Please provide a comprehensive analysis covering:
1. Commit frequency and patterns
2. Code contribution volume
3. Work consistency
4. Areas for improvement
5. Overall performance assessment

Focus on actionable insights and specific recommendations.''',
                'default_include_file_changes': True,
                'default_include_commit_messages': True,
                'default_focus_areas': 'productivity,code_quality,consistency',
                'is_public': True
            },
            {
                'name': 'Code Quality Assessment',
                'description': 'Evaluates code quality based on commit patterns, file changes, and development practices.',
                'category': 'quality',
                'tags': 'quality,code,review,best_practices',
                'default_ai_provider': 'anthropic',
                'default_model': 'claude-3-sonnet',
                'default_temperature': 0.5,
                'default_max_tokens': 2500,
                'system_prompt_template': 'You are a senior code reviewer and software architect. Focus on code quality, maintainability, and development best practices when analyzing commit data.',
                'analysis_prompt_template': '''Evaluate the code quality for {developer_name} in {repository_name} over {date_range}.

Statistics:
- Commits: {total_commits}
- Lines added: {total_additions}
- Lines deleted: {total_deletions}
- Files modified: {file_changes}

Recent Commits:
{commit_data}

Assess the following aspects:
1. Code quality indicators from commit patterns
2. Refactoring vs new feature development
3. File organization and structure changes
4. Commit message quality and clarity
5. Potential technical debt indicators

Provide specific recommendations for improving code quality.''',
                'default_include_file_changes': True,
                'default_include_commit_messages': True,
                'default_focus_areas': 'code_quality,maintainability,technical_debt',
                'is_public': True
            },
            {
                'name': 'Team Collaboration Analysis',
                'description': 'Analyzes collaboration patterns, communication, and teamwork effectiveness.',
                'category': 'collaboration',
                'tags': 'collaboration,teamwork,communication',
                'default_ai_provider': 'openai',
                'default_model': 'gpt-4',
                'default_temperature': 0.6,
                'default_max_tokens': 2000,
                'system_prompt_template': 'You are a team dynamics expert analyzing software development collaboration patterns. Focus on teamwork, communication, and collaborative development practices.',
                'analysis_prompt_template': '''Analyze collaboration patterns for {developer_name} in {repository_name} during {date_range}.

Development Activity:
- Total commits: {total_commits}
- Code additions: {total_additions}
- Code deletions: {total_deletions}
- Files affected: {file_changes}

Commit History:
{commit_data}

Evaluate:
1. Collaboration indicators in commit messages
2. Code integration patterns
3. Merge conflict resolution
4. Documentation and communication quality
5. Knowledge sharing evidence

Provide insights on collaboration effectiveness and improvement suggestions.''',
                'default_include_file_changes': True,
                'default_include_commit_messages': True,
                'default_focus_areas': 'collaboration,communication,teamwork',
                'is_public': True
            },
            {
                'name': 'Security-Focused Review',
                'description': 'Focuses on security aspects of code changes and development practices.',
                'category': 'security',
                'tags': 'security,vulnerabilities,best_practices',
                'default_ai_provider': 'anthropic',
                'default_model': 'claude-3-opus',
                'default_temperature': 0.3,
                'default_max_tokens': 2500,
                'system_prompt_template': 'You are a cybersecurity expert specializing in secure coding practices. Analyze commit data for potential security implications and best practices.',
                'analysis_prompt_template': '''Security analysis for {developer_name} in {repository_name} over {date_range}.

Development Metrics:
- Commits analyzed: {total_commits}
- Lines added: {total_additions}
- Lines removed: {total_deletions}
- Files modified: {file_changes}

Commit Details:
{commit_data}

Focus on:
1. Security-related commit patterns
2. Potential vulnerability indicators
3. Security best practices adherence
4. Sensitive data handling patterns
5. Authentication and authorization changes

Highlight security strengths and areas requiring attention.''',
                'default_include_file_changes': True,
                'default_include_commit_messages': True,
                'default_focus_areas': 'security,vulnerabilities,compliance',
                'is_public': True
            },
            {
                'name': 'Productivity Insights',
                'description': 'Comprehensive productivity analysis including efficiency, output quality, and work patterns.',
                'category': 'productivity',
                'tags': 'productivity,efficiency,output,patterns',
                'default_ai_provider': 'openai',
                'default_model': 'gpt-4-turbo',
                'default_temperature': 0.7,
                'default_max_tokens': 2000,
                'system_prompt_template': 'You are a productivity consultant specializing in software development efficiency. Analyze work patterns and provide actionable productivity insights.',
                'analysis_prompt_template': '''Productivity analysis for {developer_name} in {repository_name} during {date_range}.

Work Output:
- Total commits: {total_commits}
- Code added: {total_additions}
- Code removed: {total_deletions}
- Files touched: {file_changes}

Activity Log:
{commit_data}

Analyze:
1. Work velocity and consistency
2. Output quality vs quantity balance
3. Time management indicators
4. Focus area distribution
5. Efficiency patterns and trends

Provide specific recommendations to enhance productivity while maintaining quality.''',
                'default_include_file_changes': True,
                'default_include_commit_messages': True,
                'default_focus_areas': 'productivity,efficiency,time_management',
                'is_public': True
            }
        ]
        
        created_count = 0
        for template_data in templates:
            template, created = AgentTemplate.objects.get_or_create(
                name=template_data['name'],
                defaults=template_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created template: {template.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Template already exists: {template.name}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} new templates')
        )