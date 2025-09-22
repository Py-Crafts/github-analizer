from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class AIAgent(models.Model):
    """AI Agent model for custom analysis prompts"""
    
    AI_PROVIDERS = [
        ('openai', 'OpenAI'),
        ('anthropic', 'Anthropic (Claude)'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_agents')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    # AI Configuration
    ai_provider = models.CharField(max_length=20, choices=AI_PROVIDERS, default='openai')
    model_name = models.CharField(max_length=100, default='gpt-3.5-turbo')
    
    # Prompt Template
    prompt_template = models.TextField(
        help_text="Use placeholders like {developer_name}, {repository_name}, {commit_data}, {date_range}"
    )
    
    # Analysis Configuration
    max_tokens = models.IntegerField(default=2000)
    temperature = models.FloatField(default=0.7)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'ai_agents'
        verbose_name = 'AI Agent'
        verbose_name_plural = 'AI Agents'
        ordering = ['-created_at']
        unique_together = ['user', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.ai_provider})"
    
    def get_model_display_name(self):
        """Get human-readable model name"""
        model_names = {
            'gpt-3.5-turbo': 'GPT-3.5 Turbo',
            'gpt-4': 'GPT-4',
            'gpt-4-turbo': 'GPT-4 Turbo',
            'claude-3-sonnet': 'Claude 3 Sonnet',
            'claude-3-opus': 'Claude 3 Opus',
            'claude-3-haiku': 'Claude 3 Haiku',
        }
        return model_names.get(self.model_name, self.model_name)
    
    def format_prompt(self, context):
        """Format the prompt template with provided context"""
        try:
            return self.prompt_template.format(**context)
        except KeyError as e:
            raise ValueError(f"Missing context variable: {e}")
    
    def validate_prompt_template(self):
        """Validate that the prompt template has valid placeholders"""
        import re
        placeholders = re.findall(r'\{(\w+)\}', self.prompt_template)
        valid_placeholders = [
            'developer_name', 'repository_name', 'commit_data',
            'date_range', 'total_commits', 'total_additions',
            'total_deletions', 'file_changes'
        ]
        
        invalid_placeholders = [p for p in placeholders if p not in valid_placeholders]
        if invalid_placeholders:
            raise ValueError(f"Invalid placeholders: {', '.join(invalid_placeholders)}")
        
        return True


class AgentTemplate(models.Model):
    """Pre-built agent templates for common analysis tasks"""
    
    CATEGORIES = [
        ('performance', 'Performance Analysis'),
        ('quality', 'Code Quality'),
        ('productivity', 'Developer Productivity'),
        ('collaboration', 'Team Collaboration'),
        ('security', 'Security Analysis'),
        ('general', 'General Analysis'),
    ]
    
    name = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORIES)
    
    # Template Configuration
    ai_provider = models.CharField(max_length=20, choices=AIAgent.AI_PROVIDERS, default='openai')
    model_name = models.CharField(max_length=100, default='gpt-3.5-turbo')
    prompt_template = models.TextField()
    
    # Default Settings
    max_tokens = models.IntegerField(default=2000)
    temperature = models.FloatField(default=0.7)
    
    # Metadata
    is_public = models.BooleanField(default=True)
    usage_count = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'agent_templates'
        verbose_name = 'Agent Template'
        verbose_name_plural = 'Agent Templates'
        ordering = ['category', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.category})"
    
    def create_agent_for_user(self, user, custom_name=None):
        """Create an AI agent for a user based on this template"""
        agent = AIAgent.objects.create(
            user=user,
            name=custom_name or self.name,
            description=self.description,
            ai_provider=self.ai_provider,
            model_name=self.model_name,
            prompt_template=self.prompt_template,
            max_tokens=self.max_tokens,
            temperature=self.temperature
        )
        
        # Increment usage count
        self.usage_count += 1
        self.save(update_fields=['usage_count'])
        
        return agent