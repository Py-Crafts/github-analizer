from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import AIAgent, AgentTemplate
from .serializers import (
    AIAgentSerializer,
    AgentTemplateSerializer,
    CreateAgentFromTemplateSerializer,
    AgentValidationSerializer,
    AgentTestSerializer
)


class AIAgentListCreateView(generics.ListCreateAPIView):
    """List and create AI agents"""
    
    serializer_class = AIAgentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return AIAgent.objects.filter(user=self.request.user)


class AIAgentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """AI agent detail view"""
    
    serializer_class = AIAgentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return AIAgent.objects.filter(user=self.request.user)


class AgentTemplateListView(generics.ListAPIView):
    """List public agent templates"""
    
    serializer_class = AgentTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = AgentTemplate.objects.filter(is_public=True)
        
        # Filter by category
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)
        
        return queryset


class CreateAgentFromTemplateView(generics.CreateAPIView):
    """Create an agent from a template"""
    
    serializer_class = CreateAgentFromTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        agent = serializer.save()
        
        return Response(
            AIAgentSerializer(agent).data,
            status=status.HTTP_201_CREATED
        )


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def validate_agent_config(request):
    """Validate agent configuration"""
    serializer = AgentValidationSerializer(data=request.data)
    
    if serializer.is_valid():
        return Response({
            'valid': True,
            'message': 'Agent configuration is valid'
        })
    else:
        return Response({
            'valid': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def test_agent(request):
    """Test an agent with sample data"""
    serializer = AgentTestSerializer(data=request.data, context={'request': request})
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    agent_id = serializer.validated_data['agent_id']
    sample_data = serializer.validated_data['sample_data']
    
    try:
        agent = AIAgent.objects.get(id=agent_id, user=request.user)
        
        # Format the prompt with sample data
        formatted_prompt = agent.format_prompt(sample_data)
        
        return Response({
            'agent_name': agent.name,
            'formatted_prompt': formatted_prompt,
            'sample_data': sample_data,
            'ai_provider': agent.ai_provider,
            'model_name': agent.model_name,
            'message': 'Prompt formatted successfully. This is how your agent will receive the data.'
        })
        
    except AIAgent.DoesNotExist:
        return Response(
            {'error': 'Agent not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except ValueError as e:
        return Response(
            {'error': f'Prompt formatting error: {str(e)}'},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def agent_models_list(request):
    """Get available AI models for each provider"""
    models = {
        'openai': [
            {'value': 'gpt-3.5-turbo', 'label': 'GPT-3.5 Turbo', 'description': 'Fast and efficient for most tasks'},
            {'value': 'gpt-4', 'label': 'GPT-4', 'description': 'More capable, better reasoning'},
            {'value': 'gpt-4-turbo', 'label': 'GPT-4 Turbo', 'description': 'Latest GPT-4 with improved performance'},
        ],
        'anthropic': [
            {'value': 'claude-3-haiku', 'label': 'Claude 3 Haiku', 'description': 'Fast and lightweight'},
            {'value': 'claude-3-sonnet', 'label': 'Claude 3 Sonnet', 'description': 'Balanced performance and speed'},
            {'value': 'claude-3-opus', 'label': 'Claude 3 Opus', 'description': 'Most capable Claude model'},
        ]
    }
    
    return Response(models)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def prompt_placeholders(request):
    """Get available prompt placeholders and their descriptions"""
    placeholders = {
        'developer_name': 'Name of the developer being analyzed',
        'repository_name': 'Name of the repository',
        'commit_data': 'Formatted commit data and statistics',
        'date_range': 'Date range of the analysis',
        'total_commits': 'Total number of commits',
        'total_additions': 'Total lines added',
        'total_deletions': 'Total lines deleted',
        'file_changes': 'Total number of files changed'
    }
    
    return Response({
        'placeholders': placeholders,
        'example_usage': 'Analyze the performance of {developer_name} in {repository_name} over {date_range}. Total commits: {total_commits}'
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def agent_categories(request):
    """Get available agent template categories"""
    categories = [
        {'value': 'performance', 'label': 'Performance Analysis'},
        {'value': 'quality', 'label': 'Code Quality'},
        {'value': 'productivity', 'label': 'Developer Productivity'},
        {'value': 'collaboration', 'label': 'Team Collaboration'},
        {'value': 'security', 'label': 'Security Analysis'},
        {'value': 'general', 'label': 'General Analysis'},
    ]
    
    return Response(categories)