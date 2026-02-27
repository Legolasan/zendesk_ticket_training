"""
Test script to manually process a ticket
Useful for testing without setting up webhooks
"""
import sys
import argparse
from datetime import datetime

from config import Config
from models.schema import Database
from services.zendesk_client import ZendeskClient
from services.ai_analyzer import AIAnalyzer
from services.storage import StorageService


def process_ticket(ticket_id: int):
    """Process a single ticket manually"""

    print(f"""
    ╔══════════════════════════════════════════════════════════════╗
    ║         Manual Ticket Processing                            ║
    ║         Ticket ID: {ticket_id:<44} ║
    ╚══════════════════════════════════════════════════════════════╝
    """)

    try:
        # Validate configuration
        Config.validate()

        # Initialize services
        print("\n🔧 Initializing services...")
        database = Database(Config.DATABASE_URL)
        zendesk_client = ZendeskClient(
            subdomain=Config.ZENDESK_SUBDOMAIN,
            email=Config.ZENDESK_EMAIL,
            api_token=Config.ZENDESK_API_TOKEN
        )
        ai_analyzer = AIAnalyzer(
            provider=Config.AI_PROVIDER,
            api_key=Config.ANTHROPIC_API_KEY if Config.AI_PROVIDER == 'claude' else Config.OPENAI_API_KEY
        )

        start_time = datetime.utcnow()

        # Step 1: Fetch ticket data
        print(f"\n📥 Step 1: Fetching ticket {ticket_id} from Zendesk...")
        ticket_data = zendesk_client.fetch_complete_ticket_data(ticket_id)

        # Display ticket info
        ticket = ticket_data.get('ticket', {})
        print(f"\n📋 Ticket Information:")
        print(f"   Subject: {ticket.get('subject')}")
        print(f"   Status: {ticket.get('status')}")
        print(f"   Priority: {ticket.get('priority')}")
        print(f"   Created: {ticket.get('created_at')}")
        print(f"   Comments: {len(ticket_data.get('comments', []))}")
        print(f"   Audits: {len(ticket_data.get('audits', []))}")

        # Step 2: Analyze with AI
        print(f"\n🤖 Step 2: Analyzing with {Config.AI_PROVIDER.upper()}...")
        analysis = ai_analyzer.analyze_ticket(ticket_data)

        # Validate
        ai_analyzer.validate_analysis(analysis)

        # Display analysis highlights
        print(f"\n📊 Analysis Highlights:")
        scores = analysis.get('satisfaction_scores', {})
        print(f"   Overall Score: {scores.get('overall_satisfaction_score', 'N/A')}/10")
        print(f"   Tonality: {scores.get('tonality_score', 'N/A')}/10")
        print(f"   Professionalism: {scores.get('professionalism_score', 'N/A')}/10")
        print(f"   Empathy: {scores.get('empathy_score', 'N/A')}/10")

        theme = analysis.get('theme_classification', {})
        print(f"\n   Issue Theme: {theme.get('issue_theme')}")

        resolution = analysis.get('resolution_analysis', {})
        print(f"   Resolution Type: {resolution.get('resolution_type')}")

        summary = analysis.get('summary', {})
        print(f"\n   Summary: {summary.get('ai_summary')}")

        # Step 3: Store in database
        print(f"\n💾 Step 3: Storing in database...")
        session = database.get_session()
        storage = StorageService(session)

        stored_id = storage.store_complete_ticket(ticket_data, analysis)
        session.close()

        # Calculate time
        end_time = datetime.utcnow()
        processing_time = (end_time - start_time).total_seconds()

        print(f"\n✅ Processing completed successfully!")
        print(f"   Total time: {processing_time:.2f}s")
        print(f"   Ticket ID: {stored_id}")

        print(f"\n💡 View in dashboard: http://localhost:{Config.DASH_PORT}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def test_connections():
    """Test API connections"""
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║         Connection Test                                      ║
    ╚══════════════════════════════════════════════════════════════╝
    """)

    try:
        Config.validate()

        # Test Zendesk
        print("\n🔍 Testing Zendesk connection...")
        zendesk_client = ZendeskClient(
            subdomain=Config.ZENDESK_SUBDOMAIN,
            email=Config.ZENDESK_EMAIL,
            api_token=Config.ZENDESK_API_TOKEN
        )
        zendesk_client.test_connection()

        # Test AI
        print(f"\n🔍 Testing {Config.AI_PROVIDER.upper()} connection...")
        ai_analyzer = AIAnalyzer(
            provider=Config.AI_PROVIDER,
            api_key=Config.ANTHROPIC_API_KEY if Config.AI_PROVIDER == 'claude' else Config.OPENAI_API_KEY
        )
        ai_analyzer.test_connection()

        # Test Database
        print(f"\n🔍 Testing database connection...")
        database = Database(Config.DATABASE_URL)
        session = database.get_session()
        session.close()
        print("✅ Database connection successful!")

        print(f"\n✅ All connections working!")

    except Exception as e:
        print(f"\n❌ Connection test failed: {e}")
        sys.exit(1)


def list_custom_fields():
    """List all custom fields from Zendesk"""
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║         Custom Fields List                                   ║
    ╚══════════════════════════════════════════════════════════════╝
    """)

    try:
        Config.validate()

        zendesk_client = ZendeskClient(
            subdomain=Config.ZENDESK_SUBDOMAIN,
            email=Config.ZENDESK_EMAIL,
            api_token=Config.ZENDESK_API_TOKEN
        )

        custom_fields = zendesk_client.get_custom_fields()

        print(f"\n📋 Found {len(custom_fields)} custom fields:\n")

        for field in custom_fields:
            print(f"ID: {field.get('id')}")
            print(f"   Title: {field.get('title')}")
            print(f"   Key: {field.get('key')}")
            print(f"   Type: {field.get('type')}")
            print(f"   Active: {field.get('active')}")

            # Show options if dropdown/multiselect
            if field.get('custom_field_options'):
                options = [opt.get('value') for opt in field.get('custom_field_options', [])]
                print(f"   Options: {', '.join(options[:5])}{'...' if len(options) > 5 else ''}")

            print()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Zendesk Ticket Analysis Test Tool')
    parser.add_argument('command', choices=['process', 'test', 'fields'],
                       help='Command to run: process (analyze ticket), test (test connections), fields (list custom fields)')
    parser.add_argument('--ticket-id', type=int, help='Ticket ID to process (required for process command)')

    args = parser.parse_args()

    if args.command == 'process':
        if not args.ticket_id:
            print("❌ Error: --ticket-id is required for process command")
            sys.exit(1)
        process_ticket(args.ticket_id)

    elif args.command == 'test':
        test_connections()

    elif args.command == 'fields':
        list_custom_fields()
