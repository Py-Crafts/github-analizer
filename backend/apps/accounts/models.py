from django.contrib.auth.models import AbstractUser
from django.db import models
from utils.encryption import encrypt_data, decrypt_data


class UserProfile(AbstractUser):
    """Extended user model with GitHub and AI integration"""
    
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    email = models.EmailField(unique=True)
    github_username = models.CharField(max_length=100, blank=True, null=True)
    
    # Encrypted fields for sensitive data
    _github_token = models.TextField(blank=True, null=True, help_text="Encrypted GitHub token")
    _openai_api_key = models.TextField(blank=True, null=True, help_text="Encrypted OpenAI API key")
    _anthropic_api_key = models.TextField(blank=True, null=True, help_text="Encrypted Anthropic API key")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    class Meta:
        db_table = 'user_profiles'
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
    
    def __str__(self):
        return f"{self.email} ({self.username})"
    
    @property
    def github_token(self):
        """Decrypt and return GitHub token"""
        if self._github_token:
            return decrypt_data(self._github_token)
        return None
    
    @github_token.setter
    def github_token(self, value):
        """Encrypt and store GitHub token"""
        if value:
            self._github_token = encrypt_data(value)
        else:
            self._github_token = None
    
    @property
    def openai_api_key(self):
        """Decrypt and return OpenAI API key"""
        if self._openai_api_key:
            return decrypt_data(self._openai_api_key)
        return None
    
    @openai_api_key.setter
    def openai_api_key(self, value):
        """Encrypt and store OpenAI API key"""
        if value:
            self._openai_api_key = encrypt_data(value)
        else:
            self._openai_api_key = None
    
    @property
    def anthropic_api_key(self):
        """Decrypt and return Anthropic API key"""
        if self._anthropic_api_key:
            return decrypt_data(self._anthropic_api_key)
        return None
    
    @anthropic_api_key.setter
    def anthropic_api_key(self, value):
        """Encrypt and store Anthropic API key"""
        if value:
            self._anthropic_api_key = encrypt_data(value)
        else:
            self._anthropic_api_key = None
    
    @property
    def full_name(self):
        """Return full name"""
        return f"{self.first_name} {self.last_name}".strip()
    
    def has_github_token(self):
        """Check if user has GitHub token configured"""
        return bool(self._github_token)
    
    def has_ai_keys(self):
        """Check if user has any AI API keys configured"""
        return bool(self._openai_api_key or self._anthropic_api_key)