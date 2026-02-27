"""
Configuration management for Zendesk Analysis System
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Application configuration"""

    # Zendesk Configuration
    ZENDESK_SUBDOMAIN = os.getenv('ZENDESK_SUBDOMAIN')
    ZENDESK_EMAIL = os.getenv('ZENDESK_EMAIL')
    ZENDESK_API_TOKEN = os.getenv('ZENDESK_API_TOKEN')
    ZENDESK_API_URL = f"https://{ZENDESK_SUBDOMAIN}.zendesk.com/api/v2"

    # Database Configuration
    DATABASE_URL = os.getenv('DATABASE_URL')

    # AI Configuration
    AI_PROVIDER = os.getenv('AI_PROVIDER', 'claude').lower()
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

    # Webhook Configuration
    WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET')

    # Flask Configuration
    FLASK_ENV = os.getenv('FLASK_ENV', 'production')
    FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))

    # Dashboard Configuration
    DASH_PORT = int(os.getenv('DASH_PORT', 8050))

    @classmethod
    def validate(cls):
        """Validate required configuration"""
        required = [
            'ZENDESK_SUBDOMAIN',
            'ZENDESK_EMAIL',
            'ZENDESK_API_TOKEN',
            'DATABASE_URL',
        ]

        missing = []
        for key in required:
            if not getattr(cls, key):
                missing.append(key)

        if missing:
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")

        # Validate AI provider
        if cls.AI_PROVIDER == 'claude' and not cls.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY required when AI_PROVIDER=claude")

        if cls.AI_PROVIDER == 'openai' and not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY required when AI_PROVIDER=openai")

        print("✅ Configuration validated successfully")
        return True
