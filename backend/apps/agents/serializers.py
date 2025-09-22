from rest_framework import serializers
from .models import AIAgent, AgentTemplate


class AIAgentSerializer(serializers.ModelSerializer):
    """Serializer for AIAgent model"""
    
    model_display_name = serializers.ReadOnlyField(source='get_model_display_name')
    
    class Meta:
        model = AIAgent
        fields = [
            'id', 'name', 'description', 'ai_provider', 'model_name',
            'model_display_name', 'prompt_template', 'max_tokens',
            'temperature', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_prompt_template(self, value):
        """Validate prompt template"""
        # Create a temporary agent to validate the template
        temp_agent = AIAgent(prompt_template=value)
        try:
            temp_agent.validate_prompt_template()
        except ValueError as e:
            raise serializers.ValidationError(str(e))
        return value
    
    def validate_max_tokens(self, value):
        """Validate max tokens"""
        if value < 100 or value > 8000:
            raise serializers.ValidationError("Max tokens must be between 100 and 8000")
        return value
    
    def validate_temperature(self, value):
        """Validate temperature"""
        if value < 0 or value > 2:
            raise serializers.ValidationError("Temperature must be between 0 and 2")
        return value
    
    def create(self, validated_data):
        """Create agent with current user"""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class AgentTemplateSerializer(serializers.ModelSerializer):
    """Serializer for AgentTemplate model"""
    
    class Meta:
        model = AgentTemplate
        fields = [
            'id', 'name', 'description', 'category', 'ai_provider',
            'model_name', 'prompt_template', 'max_tokens', 'temperature',
            'is_public', 'usage_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'usage_count', 'created_at', 'updated_at']


class CreateAgentFromTemplateSerializer(serializers.Serializer):
    """Serializer for creating an agent from a template"""
    
    template_id = serializers.IntegerField()
    custom_name = serializers.CharField(max_length=255, required=False)
    
    def validate_template_id(self, value):
        """Validate template exists and is public"""
        try:
            template = AgentTemplate.objects.get(id=value, is_public=True)
        except AgentTemplate.DoesNotExist:
            raise serializers.ValidationError("Template not found or not public")
        return value
    
    def create(self, validated_data):
        """Create agent from template"""
        template = AgentTemplate.objects.get(id=validated_data['template_id'])
        user = self.context['request'].user
        custom_name = validated_data.get('custom_name')
        
        return template.create_agent_for_user(user, custom_name)


class AgentValidationSerializer(serializers.Serializer):
    """Serializer for validating agent configuration"""
    
    ai_provider = serializers.ChoiceField(choices=AIAgent.AI_PROVIDERS)
    model_name = serializers.CharField(max_length=100)
    prompt_template = serializers.CharField()
    
    def validate(self, attrs):
        """Validate the combination of provider and model"""
        provider = attrs['ai_provider']
        model = attrs['model_name']
        
        # Define valid models for each provider
        valid_models = {
            'openai': [
                'gpt-3.5-turbo', 'gpt-4', 'gpt-4-turbo',
                'gpt-4-turbo-preview', 'gpt-3.5-turbo-16k'
            ],
            'anthropic': [
                'claude-3-sonnet-20240229', 'claude-3-opus-20240229',
                'claude-3-haiku-20240307', 'claude-3-sonnet',
                'claude-3-opus', 'claude-3-haiku'
            ]
        }
        
        if model not in valid_models.get(provider, []):
            raise serializers.ValidationError(
                f"Model '{model}' is not valid for provider '{provider}'"
            )
        
        # Validate prompt template
        temp_agent = AIAgent(prompt_template=attrs['prompt_template'])
        try:
            temp_agent.validate_prompt_template()
        except ValueError as e:
            raise serializers.ValidationError({'prompt_template': str(e)})
        
        return attrs


class AgentTestSerializer(serializers.Serializer):
    """Serializer for testing agent with sample data"""
    
    agent_id = serializers.IntegerField()
    sample_data = serializers.DictField(required=False)
    
    def validate_agent_id(self, value):
        """Validate agent exists and belongs to user"""
        user = self.context['request'].user
        try:
            agent = AIAgent.objects.get(id=value, user=user)
        except AIAgent.DoesNotExist:
            raise serializers.ValidationError("Agent not found")
        return value
    
    def validate_sample_data(self, value):
        """Validate sample data has required fields"""
        if not value:
            # Provide default sample data
            return {
                'developer_name': 'John Doe',
                'repository_name': 'sample-repo',
                'commit_data': 'Sample commit data with 10 commits, 150 additions, 50 deletions',
                'date_range': 'Last 30 days',
                'total_commits': 10,
                'total_additions': 150,
                'total_deletions': 50,
                'file_changes': 25
            }
        
        required_fields = ['developer_name', 'repository_name', 'commit_data']
        missing_fields = [field for field in required_fields if field not in value]
        
        if missing_fields:
            raise serializers.ValidationError(
                f"Missing required fields: {', '.join(missing_fields)}"
            )
        
        return value