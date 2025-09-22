from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import UserProfile


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = UserProfile
        fields = (
            'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'github_username'
        )
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = UserProfile.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserLoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            user = authenticate(username=email, password=password)
            if not user:
                raise serializers.ValidationError('Invalid credentials')
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled')
            attrs['user'] = user
        else:
            raise serializers.ValidationError('Must include email and password')
        
        return attrs


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile"""
    
    full_name = serializers.ReadOnlyField()
    has_github_token = serializers.ReadOnlyField()
    has_ai_keys = serializers.ReadOnlyField()
    
    # Write-only fields for sensitive data
    github_token = serializers.CharField(write_only=True, required=False, allow_blank=True)
    openai_api_key = serializers.CharField(write_only=True, required=False, allow_blank=True)
    anthropic_api_key = serializers.CharField(write_only=True, required=False, allow_blank=True)
    
    class Meta:
        model = UserProfile
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name',
            'github_username', 'full_name', 'has_github_token', 'has_ai_keys',
            'github_token', 'openai_api_key', 'anthropic_api_key',
            'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'username', 'created_at', 'updated_at')
    
    def update(self, instance, validated_data):
        # Handle encrypted fields
        if 'github_token' in validated_data:
            instance.github_token = validated_data.pop('github_token')
        if 'openai_api_key' in validated_data:
            instance.openai_api_key = validated_data.pop('openai_api_key')
        if 'anthropic_api_key' in validated_data:
            instance.anthropic_api_key = validated_data.pop('anthropic_api_key')
        
        # Update other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for changing password"""
    
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("New passwords don't match")
        return attrs
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect")
        return value