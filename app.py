"""
Flask webhook receiver for Zendesk ticket solved events
"""
from flask import Flask, request, jsonify
import json
from datetime import datetime

from config import Config
from models.schema import Database
from services.zendesk_client import ZendeskClient
from services.ai_analyzer import AIAnalyzer
from services.storage import StorageService

# Initialize Flask app
app = Flask(__name__)

# Validate configuration
try:
    Config.validate()
except ValueError as e:
    print(f"❌ Configuration error: {e}")
    print("Please set up your .env file with required credentials")
    exit(1)

# Initialize services
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


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat()
    })


@app.route('/webhook/ticket-solved', methods=['POST'])
def ticket_solved_webhook():
    """
    Webhook endpoint for Zendesk ticket solved events

    Expected payload from Zendesk:
    {
        "type": "zen:event-type:ticket.status_changed",
        "detail": {
            "id": "12345",
            "status": "SOLVED",
            ...
        }
    }
    """
    try:
        # Get webhook payload
        payload = request.get_json()

        if not payload:
            return jsonify({'error': 'No payload received'}), 400

        print(f"\n{'='*80}")
        print(f"📨 Webhook received at {datetime.utcnow().isoformat()}")
        print(f"{'='*80}")

        # Validate webhook secret (if configured)
        if Config.WEBHOOK_SECRET:
            webhook_signature = request.headers.get('X-Zendesk-Webhook-Signature')
            # TODO: Implement signature validation
            # For now, just log it
            if webhook_signature:
                print(f"🔐 Webhook signature: {webhook_signature}")

        # Extract ticket ID from payload
        ticket_id = None

        # Handle different webhook formats
        if 'detail' in payload and 'id' in payload['detail']:
            ticket_id = int(payload['detail']['id'])
        elif 'ticket' in payload and 'id' in payload['ticket']:
            ticket_id = int(payload['ticket']['id'])
        elif 'id' in payload:
            ticket_id = int(payload['id'])

        if not ticket_id:
            print(f"❌ Could not extract ticket ID from payload")
            print(f"Payload: {json.dumps(payload, indent=2)}")
            return jsonify({'error': 'Could not extract ticket ID'}), 400

        # Check if ticket is solved
        status = None
        if 'detail' in payload:
            status = payload['detail'].get('status')
        elif 'ticket' in payload:
            status = payload['ticket'].get('status')

        print(f"🎫 Ticket ID: {ticket_id}")
        print(f"📊 Status: {status}")

        # Process the ticket
        result = process_ticket(ticket_id)

        return jsonify({
            'success': True,
            'ticket_id': ticket_id,
            'message': f'Ticket {ticket_id} processed successfully',
            'result': result
        }), 200

    except Exception as e:
        print(f"❌ Error processing webhook: {e}")
        import traceback
        traceback.print_exc()

        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def process_ticket(ticket_id: int) -> dict:
    """
    Complete ticket processing pipeline:
    1. Fetch all ticket data from Zendesk
    2. Analyze with AI
    3. Store in database

    Args:
        ticket_id: Zendesk ticket ID

    Returns:
        Processing result summary
    """
    try:
        print(f"\n🚀 Starting processing pipeline for ticket {ticket_id}")
        start_time = datetime.utcnow()

        # Step 1: Fetch complete ticket data
        print("\n📥 Step 1: Fetching ticket data from Zendesk...")
        ticket_data = zendesk_client.fetch_complete_ticket_data(ticket_id)

        # Step 2: Analyze with AI
        print("\n🤖 Step 2: Analyzing ticket with AI...")
        analysis = ai_analyzer.analyze_ticket(ticket_data)

        # Validate analysis
        ai_analyzer.validate_analysis(analysis)

        # Step 3: Store in database
        print("\n💾 Step 3: Storing data in database...")
        db_session = database.get_session()
        storage = StorageService(db_session)

        stored_ticket_id = storage.store_complete_ticket(ticket_data, analysis)
        db_session.close()

        # Calculate processing time
        end_time = datetime.utcnow()
        processing_time = (end_time - start_time).total_seconds()

        print(f"\n✅ Pipeline completed successfully in {processing_time:.2f}s")
        print(f"{'='*80}\n")

        return {
            'ticket_id': stored_ticket_id,
            'processing_time_seconds': processing_time,
            'overall_satisfaction_score': analysis.get('satisfaction_scores', {}).get('overall_satisfaction_score'),
            'issue_theme': analysis.get('theme_classification', {}).get('issue_theme'),
            'resolution_type': analysis.get('resolution_analysis', {}).get('resolution_type')
        }

    except Exception as e:
        print(f"❌ Error in processing pipeline: {e}")
        raise


@app.route('/api/test-ticket/<int:ticket_id>', methods=['POST'])
def test_ticket_processing(ticket_id: int):
    """
    Manual endpoint to test ticket processing without webhook
    Useful for testing and debugging
    """
    try:
        result = process_ticket(ticket_id)
        return jsonify({
            'success': True,
            'result': result
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/tickets', methods=['GET'])
def get_tickets():
    """Get list of analyzed tickets"""
    try:
        db_session = database.get_session()
        storage = StorageService(db_session)

        tickets = storage.get_all_analyzed_tickets(limit=100)

        result = []
        for ticket in tickets:
            result.append({
                'ticket_id': ticket.ticket_id,
                'subject': ticket.subject,
                'status': ticket.status,
                'created_at': ticket.created_at.isoformat() if ticket.created_at else None,
                'overall_score': ticket.analysis.overall_satisfaction_score if ticket.analysis else None,
                'issue_theme': ticket.analysis.issue_theme if ticket.analysis else None
            })

        db_session.close()

        return jsonify({
            'success': True,
            'count': len(result),
            'tickets': result
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/tickets/<int:ticket_id>', methods=['GET'])
def get_ticket_detail(ticket_id: int):
    """Get detailed ticket information with analysis"""
    try:
        db_session = database.get_session()
        storage = StorageService(db_session)

        ticket_data = storage.get_ticket_with_analysis(ticket_id)

        if not ticket_data:
            return jsonify({
                'success': False,
                'error': 'Ticket not found'
            }), 404

        ticket = ticket_data['ticket']
        analysis = ticket_data['analysis']

        result = {
            'ticket_id': ticket.ticket_id,
            'subject': ticket.subject,
            'description': ticket.description,
            'status': ticket.status,
            'priority': ticket.priority,
            'created_at': ticket.created_at.isoformat() if ticket.created_at else None,
            'solved_at': ticket.solved_at.isoformat() if ticket.solved_at else None,
            'tags': ticket.tags,
        }

        if analysis:
            result['analysis'] = {
                'overall_satisfaction_score': analysis.overall_satisfaction_score,
                'tonality_score': analysis.tonality_score,
                'professionalism_score': analysis.professionalism_score,
                'empathy_score': analysis.empathy_score,
                'issue_theme': analysis.issue_theme,
                'resolution_type': analysis.resolution_type,
                'ai_summary': analysis.ai_summary,
                'improvement_recommendations': analysis.improvement_recommendations
            }

        db_session.close()

        return jsonify({
            'success': True,
            'ticket': result
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║         Zendesk Ticket Analysis System                      ║
    ║         Webhook Receiver & API Server                        ║
    ╚══════════════════════════════════════════════════════════════╝
    """)

    # Test connections on startup
    print("\n🔧 Testing connections...")
    zendesk_client.test_connection()
    ai_analyzer.test_connection()

    print("\n✅ All systems ready!")
    print(f"\n📡 Starting webhook receiver on port {Config.FLASK_PORT}...")
    print(f"🔗 Webhook URL: http://localhost:{Config.FLASK_PORT}/webhook/ticket-solved")
    print(f"💡 Health check: http://localhost:{Config.FLASK_PORT}/health")
    print(f"📊 API docs: http://localhost:{Config.FLASK_PORT}/api/tickets\n")

    app.run(
        host='0.0.0.0',
        port=Config.FLASK_PORT,
        debug=(Config.FLASK_ENV == 'development')
    )
