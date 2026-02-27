# 🤖 CLAUDE.md - AI Assistant Context

This file provides comprehensive context for AI assistants (like Claude) to effectively help developers work with this codebase.

---

## 📖 Project Overview

**Name**: Zendesk Ticket Analysis System
**Purpose**: AI-powered analysis of Zendesk support tickets for customer satisfaction insights
**Status**: Production-ready, actively maintained
**Tech Stack**: Python 3.8+, Flask, PostgreSQL, Claude/GPT, Dash/Plotly

### What This System Does

This is a **webhook-driven, AI-powered ticket analysis system** that:

1. **Listens** for Zendesk ticket solved events via webhook
2. **Fetches** complete ticket data from Zendesk API (tickets, comments, audits, metrics, custom fields)
3. **Analyzes** using AI (Claude or GPT) across 10+ satisfaction dimensions
4. **Stores** insights in PostgreSQL for trending and reporting
5. **Visualizes** results in an interactive Dash/Plotly dashboard

**Processing Time**: 30-60 seconds per ticket
**Volume**: Designed for 15-20 tickets/day, scalable to 100+

---

## 🎯 Core Functionality

### 1. Webhook Processing (`app.py`)
- **Endpoint**: `POST /webhook/ticket-solved`
- Receives Zendesk webhook when ticket status changes to "solved"
- Extracts `ticket_id` from payload
- Triggers processing pipeline: fetch → analyze → store

### 2. Data Fetching (`services/zendesk_client.py`)
Makes **4 parallel API calls** to Zendesk:
- `GET /api/v2/tickets/{id}` - Core ticket data
- `GET /api/v2/tickets/{id}/comments` - Full conversation
- `GET /api/v2/tickets/{id}/audits` - Complete timeline/history
- `GET /api/v2/tickets/{id}/metrics` - SLA & performance metrics
- `GET /api/v2/ticket_fields` - Custom field definitions (cached)

**Key Features**:
- Rate limit handling (respects 429 responses)
- Automatic pagination
- Retry logic with exponential backoff
- Authentication via API token

### 3. AI Analysis (`services/ai_analyzer.py`)
**Configurable**: Claude (Anthropic) or GPT (OpenAI)

**Analysis Dimensions** (all 1-10 scores):
- **Tonality**: Agent warmth, friendliness, positivity
- **Professionalism**: Expertise, clarity, proper conduct
- **Empathy**: Understanding and care for customer
- **Responsiveness**: Speed and proactive communication
- **Overall Satisfaction**: Composite score

**Additional Analysis**:
- Delay handling (avg/max delays, communication quality)
- Blocker detection (identification and handling)
- Resolution type (workaround, engineering_fix, escalated, cold_close)
- Issue theme (billing, technical, bug, feature_request, etc.)
- Sentiment journey (customer mood start → end)
- Conversation metrics (total exchanges, back-and-forth count)

**Prompt Engineering**:
- Structured prompt in `prompts/analysis_prompt.py`
- Includes full conversation transcript
- Timeline of events
- SLA/metric context
- Returns structured JSON with scores and summaries

### 4. Storage (`services/storage.py`)
**Database**: PostgreSQL with SQLAlchemy ORM

**6 Tables**:
1. `tickets` - Core data + custom fields (JSONB)
2. `comments` - Full conversation with author tracking
3. `ticket_metrics` - SLA, timing, performance data
4. `ticket_audits` - Complete event timeline
5. `ai_analysis` - All AI scores and insights
6. `custom_field_mappings` - Dynamic field definitions

**Key Features**:
- Upsert logic (updates existing tickets)
- Proper foreign key relationships
- JSON storage for flexible custom fields
- Datetime parsing from ISO format

### 5. Dashboard (`dashboard/app.py`)
**Framework**: Dash/Plotly

**7 Visualizations**:
1. Key metrics cards (total tickets, avg scores, response times)
2. Satisfaction trend over time (line chart)
3. Score distribution by category (box plot)
4. Issue theme breakdown (pie chart)
5. Resolution type distribution (bar chart)
6. Response time vs satisfaction (scatter plot)
7. Sentiment journey (Sankey diagram)
8. Recent tickets table (paginated)

**Features**:
- Auto-refresh every 5 minutes
- Date range filtering
- Interactive charts
- Responsive design

---

## 🗂️ Project Structure

```
zendesk_analysis/
├── app.py                      # Flask webhook receiver & REST API
├── config.py                   # Environment configuration
├── migrate.py                  # Database migration script
├── test_ticket.py              # Testing utility
├── setup.sh                    # Installation script
│
├── models/
│   └── schema.py               # SQLAlchemy models (6 tables)
│
├── services/
│   ├── zendesk_client.py      # Zendesk API client
│   ├── ai_analyzer.py         # AI analysis engine
│   └── storage.py             # Database operations
│
├── prompts/
│   └── analysis_prompt.py     # AI prompt templates
│
└── dashboard/
    └── app.py                 # Dash/Plotly dashboard
```

---

## 🔑 Key Design Decisions

### Why These Technologies?

1. **Flask**: Lightweight, perfect for webhooks, easy to deploy
2. **PostgreSQL**: ACID compliance, JSON support, mature ecosystem
3. **SQLAlchemy**: Type-safe ORM, migration support, relationship handling
4. **Claude/GPT**: Strong reasoning, JSON output, consistent scoring
5. **Dash/Plotly**: Python-native, interactive charts, easy to customize

### Why Synchronous Processing?

For **15-20 tickets/day**, synchronous processing is:
- ✅ Simple to understand and debug
- ✅ Easier to deploy (no queue infrastructure)
- ✅ Sufficient performance
- ✅ Lower operational complexity

**When to add async?** If volume exceeds 100+ tickets/day, consider:
- Celery for task queue
- Redis for caching
- Separate worker processes

### Why Separate Tables?

Instead of storing everything in one `tickets` table:
- ✅ Normalized design (reduce duplication)
- ✅ Efficient queries (index on specific tables)
- ✅ Easy to extend (add more analysis types)
- ✅ Clear data relationships

---

## 🔧 Configuration

### Environment Variables (`.env`)

**Required**:
```env
ZENDESK_SUBDOMAIN=your-company          # Just subdomain, not full URL
ZENDESK_EMAIL=you@company.com
ZENDESK_API_TOKEN=your_token_here       # From Zendesk Admin → API

DATABASE_URL=postgresql://user:pass@host:5432/db_name

AI_PROVIDER=claude                       # or "openai"
ANTHROPIC_API_KEY=sk-ant-xxx            # If using Claude
OPENAI_API_KEY=sk-xxx                   # If using OpenAI
```

**Optional**:
```env
WEBHOOK_SECRET=optional_webhook_secret  # For webhook signature validation
FLASK_PORT=5000
DASH_PORT=8050
FLASK_ENV=production
```

### How Config Works

1. `config.py` loads from `.env` using `python-dotenv`
2. `Config.validate()` checks all required variables exist
3. Components import from `config.py` and use `Config.VARIABLE_NAME`

---

## 💾 Database Schema Deep Dive

### tickets Table
```python
ticket_id: int (PK)
subject: str
description: text
status: str (pending, open, solved, closed)
priority: str (low, normal, high, urgent)
ticket_type: str (question, incident, problem, task)

# People
requester_id: int
assignee_id: int
submitter_id: int
group_id: int
organization_id: int

# Timestamps
created_at: datetime
updated_at: datetime
solved_at: datetime

# Flexible data
tags: JSON (array)
custom_fields: JSON (array of objects)
satisfaction_rating: JSON (object)
via_channel: str (web, email, api, chat, etc.)
```

### comments Table
```python
comment_id: int (PK, autoincrement)
ticket_id: int (FK → tickets.ticket_id)
zendesk_comment_id: int (unique, actual Zendesk ID)

author_id: int
author_type: str (customer, agent, system)

body: text (plain text)
html_body: text (HTML formatted)
plain_body: text (alternative plain text)

is_public: bool
comment_type: str (Comment, VoiceComment)
created_at: datetime

attachments: JSON (array)
metadata: JSON (object)
```

### ticket_metrics Table
```python
metric_id: int (PK, autoincrement)
ticket_id: int (FK → tickets.ticket_id, unique)

# Response times (minutes)
first_reply_time_minutes: int
first_reply_time_business_minutes: int

# Resolution times
full_resolution_time_minutes: int
full_resolution_time_business_minutes: int

# Wait times
agent_wait_time_minutes: int
requester_wait_time_minutes: int
on_hold_time_minutes: int

# Activity counts
reply_count: int
reopens: int
assignee_stations: int (number of reassignments)
group_stations: int (number of group changes)

# Timestamps
assigned_at: datetime
solved_at: datetime
initially_assigned_at: datetime
latest_comment_added_at: datetime

raw_metrics: JSON (full API response for reference)
```

### ticket_audits Table
```python
audit_id: int (PK, autoincrement)
ticket_id: int (FK → tickets.ticket_id)
zendesk_audit_id: int (unique, actual Zendesk ID)

author_id: int
created_at: datetime

events: JSON (array of event objects)
# Events track: field changes, comments, notifications, etc.

via: JSON (how update was made: web, api, rule, etc.)
metadata: JSON (system metadata)
```

### ai_analysis Table
```python
analysis_id: int (PK, autoincrement)
ticket_id: int (FK → tickets.ticket_id, unique)

# Metadata
analyzed_at: datetime
ai_provider: str (claude, openai)
ai_model: str (claude-3-5-sonnet-20241022, gpt-4-turbo, etc.)

# Satisfaction Scores (1-10)
tonality_score: float
tonality_summary: text
professionalism_score: float
professionalism_summary: text
empathy_score: float
empathy_summary: text
responsiveness_score: float
overall_satisfaction_score: float

# Delay Handling
avg_response_delay_minutes: float
max_response_delay_minutes: float
delay_handling_score: float
delay_handling_summary: text

# Blocker Analysis
blocker_detected: bool
blocker_description: text
blocker_handling_score: float

# Resolution
resolution_type: str (workaround, engineering_fix, escalated, cold_close)
resolution_description: text
resolution_effectiveness_score: float

# Themes
issue_theme: str (billing, technical, feature_request, etc.)
issue_theme_confidence: float (0-1)
resolution_theme: str (quick_fix, investigation_required, etc.)

# Sentiment
customer_sentiment_start: str (positive, neutral, negative, frustrated)
customer_sentiment_end: str
sentiment_change: str (improved, declined, stable)

# Conversation Metrics
total_exchanges: int
customer_messages: int
agent_messages: int

# Summary
ai_summary: text (2-3 sentences)
improvement_recommendations: JSON (array of strings)

raw_ai_response: JSON (full AI response for debugging)
```

### custom_field_mappings Table
```python
field_id: int (PK, Zendesk field ID)
field_key: str (unique, e.g., "priority_reason")
field_title: str (e.g., "Priority Reason")
field_type: str (text, dropdown, checkbox, date, etc.)
field_description: text
is_active: bool

field_options: JSON (for dropdown/multiselect: array of option objects)

created_at: datetime
updated_at: datetime
```

---

## 🔄 Data Flow Example

Let's trace a ticket through the system:

### 1. Ticket Solved in Zendesk
- Ticket #12345 status changed to "Solved"
- Zendesk trigger fires
- Webhook POST sent to `https://your-app.com/webhook/ticket-solved`

```json
{
  "type": "zen:event-type:ticket.status_changed",
  "detail": {
    "id": "12345",
    "status": "SOLVED",
    "subject": "Cannot login to account",
    "priority": "HIGH"
  }
}
```

### 2. Webhook Received (`app.py`)
```python
@app.route('/webhook/ticket-solved', methods=['POST'])
def ticket_solved_webhook():
    payload = request.get_json()
    ticket_id = payload['detail']['id']  # 12345

    # Trigger processing
    result = process_ticket(ticket_id)
    return jsonify({'success': True})
```

### 3. Data Fetching (`services/zendesk_client.py`)
```python
zendesk_client.fetch_complete_ticket_data(12345)
```

Makes 4 API calls:
```
GET /api/v2/tickets/12345
→ Returns: subject, description, status, custom_fields, etc.

GET /api/v2/tickets/12345/comments
→ Returns: 8 comments (4 from customer, 4 from agent)

GET /api/v2/tickets/12345/audits
→ Returns: 15 audit records (status changes, assignments, etc.)

GET /api/v2/tickets/12345/metrics
→ Returns: first_reply_time=15min, resolution_time=2hr
```

### 4. AI Analysis (`services/ai_analyzer.py`)
```python
ai_analyzer.analyze_ticket(ticket_data)
```

**Prompt sent to Claude**:
- Ticket info (subject, priority, status)
- Metrics (15min first reply, 2hr resolution)
- Timeline (15 events)
- Full conversation (8 messages formatted)

**Claude returns JSON**:
```json
{
  "satisfaction_scores": {
    "overall_satisfaction_score": 8.5,
    "tonality_score": 9.0,
    "professionalism_score": 8.5,
    "empathy_score": 9.0,
    "responsiveness_score": 7.5,
    "tonality_summary": "Agent maintained warm, friendly tone..."
  },
  "resolution_analysis": {
    "resolution_type": "workaround",
    "resolution_description": "Provided password reset workaround...",
    "resolution_effectiveness_score": 8.0
  },
  "theme_classification": {
    "issue_theme": "account_access",
    "issue_theme_confidence": 0.95
  },
  "sentiment_analysis": {
    "customer_sentiment_start": "frustrated",
    "customer_sentiment_end": "positive",
    "sentiment_change": "improved"
  },
  "ai_summary": "Agent provided quick, empathetic support..."
}
```

### 5. Storage (`services/storage.py`)
```python
storage.store_complete_ticket(ticket_data, analysis)
```

Inserts/updates across 6 tables:
```sql
-- tickets
INSERT INTO tickets (ticket_id, subject, status, ...)
VALUES (12345, 'Cannot login to account', 'solved', ...)
ON CONFLICT (ticket_id) DO UPDATE ...

-- comments (8 rows)
INSERT INTO comments (ticket_id, zendesk_comment_id, body, ...)
VALUES (12345, 98765, 'I cannot login...', ...)

-- ticket_metrics (1 row)
INSERT INTO ticket_metrics (ticket_id, first_reply_time_minutes, ...)
VALUES (12345, 15, ...)

-- ticket_audits (15 rows)
INSERT INTO ticket_audits (ticket_id, events, ...)
VALUES (12345, '[...]', ...)

-- ai_analysis (1 row)
INSERT INTO ai_analysis (ticket_id, overall_satisfaction_score, ...)
VALUES (12345, 8.5, ...)

-- Commit all
COMMIT;
```

### 6. Dashboard Update (`dashboard/app.py`)
Dashboard auto-refreshes every 5 minutes:
```python
@app.callback(...)
def update_dashboard(n_intervals):
    df = fetch_ticket_data(start_date, end_date)
    # Query joins tickets + ai_analysis + ticket_metrics

    # Update all charts with new data
    return (
        key_metrics,
        satisfaction_trend,
        score_distribution,
        ...
    )
```

User sees:
- Overall score: 8.5/10
- Issue: Account Access
- Resolution: Workaround
- Sentiment: Improved ✅

---

## 🧪 Testing Guide

### Manual Testing Workflow

```bash
# 1. Test connections
python test_ticket.py test
# ✅ Tests Zendesk API, AI API, Database

# 2. View custom fields (understand your Zendesk setup)
python test_ticket.py fields
# Shows all custom fields with types and options

# 3. Process a real ticket
python test_ticket.py process --ticket-id 12345
# Runs full pipeline: fetch → analyze → store
# Shows detailed output at each step

# 4. Check database
psql -d zendesk_analysis
SELECT ticket_id, subject, overall_satisfaction_score
FROM tickets t
JOIN ai_analysis a ON t.ticket_id = a.ticket_id;

# 5. Test webhook manually
curl -X POST http://localhost:5000/webhook/ticket-solved \
  -H "Content-Type: application/json" \
  -d '{"detail": {"id": "12345", "status": "SOLVED"}}'

# 6. View in dashboard
# Open http://localhost:8050
```

### Common Test Scenarios

**Scenario 1: First time setup**
```bash
./setup.sh                    # Install
python migrate.py             # Create tables
python test_ticket.py test    # Verify connections
```

**Scenario 2: Test with real ticket**
```bash
# Find a solved ticket in Zendesk (get ID from URL)
python test_ticket.py process --ticket-id 12345
# Check output for any errors
```

**Scenario 3: Verify custom fields captured**
```bash
python test_ticket.py fields
# Check if your custom fields are listed

# Then process a ticket and check database
psql -d zendesk_analysis -c "SELECT custom_fields FROM tickets WHERE ticket_id=12345;"
# Should show JSON with your custom field values
```

---

## 🚨 Common Issues & Solutions

### Issue 1: "Configuration error: Missing ZENDESK_SUBDOMAIN"
**Cause**: `.env` file not created or not loaded
**Solution**:
```bash
cp .env.example .env
nano .env  # Add your credentials
```

### Issue 2: "Zendesk API connection failed: 401 Unauthorized"
**Cause**: Invalid API token or email
**Solution**:
- Go to Zendesk Admin → API → Add token
- Format email correctly: `your-email@company.com`
- Token format: long alphanumeric string

### Issue 3: "psycopg2.OperationalError: could not connect to server"
**Cause**: PostgreSQL not running or wrong DATABASE_URL
**Solution**:
```bash
# Check PostgreSQL is running
pg_isready

# Test connection manually
psql postgresql://user:pass@host:5432/dbname

# Check DATABASE_URL format:
# postgresql://username:password@hostname:port/database_name
```

### Issue 4: "Claude API error: Invalid API key"
**Cause**: Missing or incorrect Anthropic API key
**Solution**:
- Get key from: https://console.anthropic.com/settings/keys
- Format: `sk-ant-api03-...`
- Set in `.env`: `ANTHROPIC_API_KEY=sk-ant-...`

### Issue 5: Webhook receives no data
**Cause**: Zendesk trigger not configured
**Solution**:
1. Zendesk Admin → Triggers
2. Create trigger: Status changes to Solved → Notify webhook
3. Test with a real ticket

### Issue 6: "Too many custom fields to fetch"
**Not actually an issue!** The system handles this automatically:
- Calls `GET /api/v2/ticket_fields` once
- Stores mappings in `custom_field_mappings` table
- Subsequent tickets use cached mappings

---

## 🔍 Code Navigation Tips

### Where to find things:

**Want to change AI analysis criteria?**
→ `prompts/analysis_prompt.py` (modify scoring guidelines)

**Want to add a new satisfaction metric?**
→ 1. Update `prompts/analysis_prompt.py` (add to JSON schema)
→ 2. Update `models/schema.py` (add column to `AIAnalysis`)
→ 3. Update `services/storage.py` (add field mapping)
→ 4. Update `dashboard/app.py` (add visualization)

**Want to change Zendesk API calls?**
→ `services/zendesk_client.py` (add new methods)

**Want to add a new dashboard chart?**
→ `dashboard/app.py` (add figure function + callback)

**Want to add a REST API endpoint?**
→ `app.py` (add Flask route)

**Want to change database schema?**
→ `models/schema.py` (modify SQLAlchemy models)
→ Run: `python migrate.py` to apply changes

---

## 🎓 Key Concepts for AI Assistants

When helping developers with this codebase:

### 1. The Processing Pipeline is Linear
```
Webhook → Fetch → Analyze → Store → Visualize
```
Each step depends on the previous. Don't skip steps.

### 2. Everything Revolves Around ticket_id
- Webhook extracts it
- API calls use it
- Database relations reference it
- Dashboard queries by it

### 3. Custom Fields are Dynamic
- System doesn't know your custom fields in advance
- Fetches field definitions from Zendesk
- Stores as JSON in `tickets.custom_fields`
- Maps definitions in `custom_field_mappings` table

### 4. AI Analysis is Structured
- Prompt includes full context (conversation, metrics, timeline)
- Expects JSON response with specific schema
- Validates structure before storing
- Stores both parsed results and raw response

### 5. Database Design is Normalized
- One ticket → Many comments
- One ticket → One metrics record
- One ticket → Many audits
- One ticket → One analysis
- Use JOINs for full picture

### 6. Dashboard is Reactive
- Auto-refreshes every 5 minutes
- Queries database directly (no caching)
- Date range filtering
- All charts update together

---

## 💡 Extension Ideas

When asked "How can I extend this system?", suggest:

### Easy Extensions (2-4 hours)
- Add email alerts for low satisfaction scores
- Export data to CSV/Excel
- Add agent performance leaderboard
- Add more dashboard filters (by agent, priority, etc.)
- Add webhook signature validation

### Medium Extensions (1-2 days)
- Real-time notifications (WebSocket)
- Slack integration for alerts
- Custom report generation
- Batch analysis of historical tickets
- A/B testing of agent responses

### Advanced Extensions (1+ weeks)
- Predictive analytics (predict satisfaction before resolution)
- Agent coaching suggestions
- Automated response templates
- Multi-language support
- Voice sentiment analysis (if call recordings exist)

---

## 📝 Documentation Standards

When writing code in this project:

### 1. Module Docstrings
```python
"""
Brief one-line description

More detailed explanation if needed.
"""
```

### 2. Function Docstrings
```python
def analyze_ticket(ticket_data: Dict) -> Dict:
    """
    Analyze ticket and return structured results

    Args:
        ticket_data: Complete ticket data from Zendesk

    Returns:
        Dictionary with analysis results

    Raises:
        ValueError: If ticket_data is invalid
    """
```

### 3. Inline Comments
- Explain "why", not "what"
- Use for complex logic
- Keep concise

### 4. Type Hints
- Use for function parameters and returns
- Use `Dict`, `List`, `Optional` from typing module

---

## 🎯 Quick Reference

### Most Important Files
1. `app.py` - Start here for webhook logic
2. `services/zendesk_client.py` - Zendesk API interactions
3. `services/ai_analyzer.py` - AI analysis logic
4. `prompts/analysis_prompt.py` - AI prompts and scoring
5. `models/schema.py` - Database structure

### Most Common Tasks
```bash
# Start services
python app.py                          # Webhook receiver
python dashboard/app.py                # Dashboard

# Testing
python test_ticket.py test             # Test connections
python test_ticket.py process --ticket-id ID

# Database
python migrate.py                      # Create/update tables
psql -d zendesk_analysis              # Query database

# Deployment
git push                               # Render auto-deploys
```

### Key Configuration
- API credentials: `.env`
- AI prompts: `prompts/analysis_prompt.py`
- Database schema: `models/schema.py`
- Flask port: 5000 (configurable)
- Dashboard port: 8050 (configurable)

---

## 🤖 AI Assistant Guidelines

When helping with this codebase:

### DO:
- ✅ Read relevant files before suggesting changes
- ✅ Consider the full pipeline (webhook → analyze → store)
- ✅ Test suggestions against existing code structure
- ✅ Provide complete code examples
- ✅ Explain trade-offs of different approaches
- ✅ Point to relevant documentation files

### DON'T:
- ❌ Suggest breaking changes without migration plan
- ❌ Ignore error handling
- ❌ Forget about rate limits (Zendesk, AI APIs)
- ❌ Recommend synchronous → async without good reason
- ❌ Suggest features without considering database schema

### When Asked to Debug:
1. Check recent changes (git log)
2. Review error message carefully
3. Check relevant log output
4. Test isolated components
5. Verify configuration/environment
6. Check API rate limits

### When Asked to Add Features:
1. Understand requirement fully
2. Check if similar functionality exists
3. Consider database schema changes
4. Plan API modifications
5. Update documentation
6. Suggest testing approach

---

## 📚 External Resources

### Zendesk API
- [API Reference](https://developer.zendesk.com/api-reference/)
- [Tickets API](https://developer.zendesk.com/api-reference/ticketing/tickets/tickets/)
- [Webhooks](https://developer.zendesk.com/documentation/webhooks/)

### AI APIs
- [Anthropic Claude Docs](https://docs.anthropic.com/)
- [OpenAI API Docs](https://platform.openai.com/docs/)

### Frameworks
- [Flask Documentation](https://flask.palletsprojects.com/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/)
- [Dash/Plotly](https://dash.plotly.com/)

---

## 🎉 Summary

This is a **production-ready, webhook-driven ticket analysis system** that:
- Automatically processes tickets when solved
- Fetches ALL data from Zendesk (including custom fields)
- Analyzes with AI across 10+ satisfaction metrics
- Stores in PostgreSQL for trending
- Visualizes in interactive dashboard

**Key Strengths**:
- Well-structured codebase (2,475 lines)
- Comprehensive error handling
- Production-tested deployment
- Extensive documentation
- Easy to extend

**Perfect for**: Support teams wanting to systematically improve customer satisfaction with data-driven insights.

---

**Last Updated**: 2026-02-27
**Version**: 1.0.0
**Maintained**: Yes, actively maintained
