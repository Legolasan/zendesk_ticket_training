"""
AI-powered ticket analysis using Claude or GPT
"""
import json
from typing import Dict, Optional
from datetime import datetime

# AI clients
try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

from prompts.analysis_prompt import SYSTEM_PROMPT, build_analysis_prompt


class AIAnalyzer:
    """Analyze tickets using AI (Claude or GPT)"""

    def __init__(self, provider: str = 'claude', api_key: str = None):
        """
        Initialize AI analyzer

        Args:
            provider: 'claude' or 'openai'
            api_key: API key for the chosen provider
        """
        self.provider = provider.lower()
        self.api_key = api_key

        if self.provider == 'claude':
            if Anthropic is None:
                raise ImportError("anthropic package not installed. Run: pip install anthropic")
            self.client = Anthropic(api_key=api_key)
            self.model = "claude-3-5-sonnet-20241022"  # Latest Claude model

        elif self.provider == 'openai':
            if OpenAI is None:
                raise ImportError("openai package not installed. Run: pip install openai")
            self.client = OpenAI(api_key=api_key)
            self.model = "gpt-4-turbo-preview"

        else:
            raise ValueError(f"Invalid provider: {provider}. Must be 'claude' or 'openai'")

        print(f"✅ AI Analyzer initialized with {self.provider} ({self.model})")

    def analyze_ticket(self, ticket_data: Dict) -> Dict:
        """
        Analyze a ticket and return structured results

        Args:
            ticket_data: Complete ticket data from Zendesk

        Returns:
            Dictionary with analysis results
        """
        ticket_id = ticket_data.get('ticket', {}).get('id', 'Unknown')
        print(f"\n🤖 Analyzing ticket {ticket_id} with {self.provider}...")

        try:
            # Build the analysis prompt
            prompt = build_analysis_prompt(ticket_data)

            # Get AI response
            if self.provider == 'claude':
                response = self._analyze_with_claude(prompt)
            else:
                response = self._analyze_with_openai(prompt)

            # Parse and validate response
            analysis = self._parse_analysis(response)

            print(f"✅ Ticket {ticket_id} analyzed successfully")
            return analysis

        except Exception as e:
            print(f"❌ Error analyzing ticket {ticket_id}: {e}")
            raise

    def _analyze_with_claude(self, prompt: str) -> str:
        """Analyze using Claude API"""
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                temperature=0.3,  # Lower temperature for more consistent analysis
                system=SYSTEM_PROMPT,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            # Extract text from response
            response_text = message.content[0].text
            return response_text

        except Exception as e:
            print(f"❌ Claude API error: {e}")
            raise

    def _analyze_with_openai(self, prompt: str) -> str:
        """Analyze using OpenAI API"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=4096
            )

            response_text = response.choices[0].message.content
            return response_text

        except Exception as e:
            print(f"❌ OpenAI API error: {e}")
            raise

    def _parse_analysis(self, response: str) -> Dict:
        """
        Parse AI response and extract JSON

        Args:
            response: Raw AI response text

        Returns:
            Parsed analysis dictionary
        """
        try:
            # Extract JSON from markdown code blocks if present
            if '```json' in response:
                json_start = response.find('```json') + 7
                json_end = response.find('```', json_start)
                json_str = response[json_start:json_end].strip()
            elif '```' in response:
                json_start = response.find('```') + 3
                json_end = response.find('```', json_start)
                json_str = response[json_start:json_end].strip()
            else:
                # Try to parse the whole response
                json_str = response.strip()

            # Parse JSON
            analysis = json.loads(json_str)

            # Add metadata
            analysis['_metadata'] = {
                'analyzed_at': datetime.utcnow().isoformat(),
                'ai_provider': self.provider,
                'ai_model': self.model,
                'raw_response': response  # Store raw response for debugging
            }

            return analysis

        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse AI response as JSON: {e}")
            print(f"Response preview: {response[:500]}...")
            raise ValueError(f"Invalid JSON response from AI: {e}")

    def validate_analysis(self, analysis: Dict) -> bool:
        """
        Validate that the analysis has all required fields

        Args:
            analysis: Parsed analysis dictionary

        Returns:
            True if valid, raises ValueError if not
        """
        required_sections = [
            'satisfaction_scores',
            'delay_handling',
            'blocker_analysis',
            'resolution_analysis',
            'theme_classification',
            'sentiment_analysis',
            'conversation_metrics',
            'summary'
        ]

        for section in required_sections:
            if section not in analysis:
                raise ValueError(f"Missing required section: {section}")

        # Validate scores are in range
        scores_to_check = [
            ('satisfaction_scores', 'tonality_score'),
            ('satisfaction_scores', 'professionalism_score'),
            ('satisfaction_scores', 'empathy_score'),
            ('satisfaction_scores', 'responsiveness_score'),
            ('satisfaction_scores', 'overall_satisfaction_score'),
            ('delay_handling', 'delay_handling_score'),
            ('resolution_analysis', 'resolution_effectiveness_score'),
        ]

        for section, score_key in scores_to_check:
            score = analysis.get(section, {}).get(score_key)
            if score is not None and not (1 <= score <= 10):
                print(f"⚠️  Warning: {section}.{score_key} = {score} is out of range [1-10]")

        print("✅ Analysis validation passed")
        return True

    def test_connection(self) -> bool:
        """Test AI API connection"""
        try:
            print(f"🔍 Testing {self.provider} API connection...")

            test_prompt = "Respond with 'OK' if you can read this."

            if self.provider == 'claude':
                response = self._analyze_with_claude(test_prompt)
            else:
                response = self._analyze_with_openai(test_prompt)

            print(f"✅ {self.provider} API connection successful!")
            return True

        except Exception as e:
            print(f"❌ {self.provider} API connection failed: {e}")
            return False
