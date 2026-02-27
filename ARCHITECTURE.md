# 🏗️ System Architecture

## Overview

This system provides real-time AI-powered analysis of Zendesk support tickets with a focus on customer satisfaction metrics.

---

## 📊 High-Level Architecture

```
┌─────────────────┐
│   Zendesk       │
│   (Ticket       │
│    Solved)      │
└────────┬────────┘
         │ Webhook
         ▼
┌─────────────────────────────────────────────┐
│           Flask Webhook Receiver            │
│  - Receives ticket solved events            │
│  - Extracts ticket_id                       │
│  - Triggers processing pipeline             │
└────────┬────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│        Zendesk API Client                   │
│  - Fetches ticket details                   │
│  - Gets all comments (conversation)         │
│  - Retrieves audit trail (timeline)         │
│  - Pulls metrics (SLA, timing)              │
│  - Queries custom fields                    │
└────────┬────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│           AI Analyzer                       │
│  - Claude or GPT (configurable)             │
│  - Analyzes tonality, professionalism       │
│  - Evaluates empathy & responsiveness       │
│  - Classifies resolution type               │
│  - Detects blockers & delays                │
│  - Generates themes & summaries             │
└────────┬────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│         PostgreSQL Database                 │
│  - Stores raw ticket data                   │
│  - Saves AI analysis results                │
│  - Maintains audit trail                    │
│  - Tracks custom field mappings             │
└────────┬────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│        Dash/Plotly Dashboard                │
│  - Real-time visualization                  │
│  - Satisfaction trends                      │
│  - Performance metrics                      │
│  - Theme breakdown                          │
│  - Agent insights                           │
└─────────────────────────────────────────────┘
```

---

## 🔄 Processing Pipeline

### 1. Webhook Event Receipt
```
Zendesk Trigger → POST /webhook/ticket-solved
```
- Webhook payload contains ticket_id and status
- Validates webhook signature (optional)
- Extracts ticket_id from payload

### 2. Data Fetching (Parallel API Calls)
```python
zendesk_client.fetch_complete_ticket_data(ticket_id)
```
Fetches in parallel:
- ✅ Ticket details (subject, description, fields, etc.)
- ✅ All comments (full conversation history)
- ✅ Audit trail (every change/event)
- ✅ Metrics (SLA, response times)
- ✅ Custom field definitions

### 3. AI Analysis
```python
ai_analyzer.analyze_ticket(ticket_data)
```
Analyzes:
- **Satisfaction Scores** (1-10):
  - Tonality (warmth, friendliness)
  - Professionalism (expertise, clarity)
  - Empathy (understanding, care)
  - Responsiveness (speed, updates)
  - Overall satisfaction

- **Delay Handling**:
  - Average response delay
  - Maximum delay
  - How delays were communicated

- **Blocker Detection**:
  - Whether blockers occurred
  - How they were handled
  - Impact on resolution

- **Resolution Classification**:
  - Type (workaround, engineering_fix, escalated, cold_close)
  - Effectiveness
  - Description

- **Theme Analysis**:
  - Issue category (billing, technical, etc.)
  - Resolution approach
  - Confidence score

- **Sentiment Tracking**:
  - Customer sentiment at start
  - Customer sentiment at end
  - Sentiment change trajectory

### 4. Database Storage
```python
storage.store_complete_ticket(ticket_data, analysis)
```
Stores to 6 tables:
- `tickets` - Core ticket info
- `comments` - Full conversation
- `ticket_metrics` - SLA & timing data
- `ticket_audits` - Complete timeline
- `ai_analysis` - All AI scores & insights
- `custom_field_mappings` - Field definitions

### 5. Dashboard Updates
Dashboard auto-refreshes every 5 minutes to show latest data.

---

## 🗄️ Database Schema

### tickets
```sql
ticket_id (PK)
subject, description, status, priority, ticket_type
requester_id, assignee_id, group_id, organization_id
created_at, updated_at, solved_at
tags (JSON), custom_fields (JSON), satisfaction_rating (JSON)
via_channel, custom_status_id
```

### comments
```sql
comment_id (PK)
ticket_id (FK)
zendesk_comment_id, author_id, author_type
body, html_body, plain_body
is_public, comment_type, created_at
attachments (JSON), metadata (JSON)
```

### ticket_metrics
```sql
metric_id (PK)
ticket_id (FK)
first_reply_time_minutes, first_reply_time_business_minutes
full_resolution_time_minutes, full_resolution_time_business_minutes
agent_wait_time_minutes, requester_wait_time_minutes
reply_count, reopens, assignee_stations, group_stations
assigned_at, solved_at, initially_assigned_at
raw_metrics (JSON)
```

### ticket_audits
```sql
audit_id (PK)
ticket_id (FK)
zendesk_audit_id, author_id, created_at
events (JSON), via (JSON), metadata (JSON)
```

### ai_analysis
```sql
analysis_id (PK)
ticket_id (FK)
analyzed_at, ai_provider, ai_model

-- Satisfaction Scores
tonality_score, tonality_summary
professionalism_score, professionalism_summary
empathy_score, empathy_summary
responsiveness_score
overall_satisfaction_score

-- Delay Handling
avg_response_delay_minutes, max_response_delay_minutes
delay_handling_score, delay_handling_summary

-- Blocker Analysis
blocker_detected, blocker_description, blocker_handling_score

-- Resolution
resolution_type, resolution_description, resolution_effectiveness_score

-- Themes
issue_theme, issue_theme_confidence, resolution_theme

-- Sentiment
customer_sentiment_start, customer_sentiment_end, sentiment_change

-- Conversation Metrics
total_exchanges, customer_messages, agent_messages

-- Summary
ai_summary, improvement_recommendations (JSON)
raw_ai_response (JSON)
```

### custom_field_mappings
```sql
field_id (PK)
field_key, field_title, field_type, field_description
is_active, field_options (JSON)
created_at, updated_at
```

---

## 🧩 Component Details

### 1. Flask Webhook Receiver (`app.py`)
**Purpose**: Receive and process webhook events from Zendesk

**Endpoints**:
- `POST /webhook/ticket-solved` - Main webhook endpoint
- `GET /health` - Health check
- `POST /api/test-ticket/<id>` - Manual trigger for testing
- `GET /api/tickets` - List analyzed tickets
- `GET /api/tickets/<id>` - Get ticket details

**Flow**:
1. Receive webhook
2. Extract ticket_id
3. Call `process_ticket(ticket_id)`
4. Return success/error

### 2. Zendesk Client (`services/zendesk_client.py`)
**Purpose**: Interface with Zendesk API

**Key Methods**:
- `get_ticket(ticket_id)` - Fetch ticket details
- `get_ticket_comments(ticket_id)` - Get conversation
- `get_ticket_audits(ticket_id)` - Get timeline
- `get_ticket_metrics(ticket_id)` - Get SLA data
- `get_custom_fields()` - List custom fields
- `fetch_complete_ticket_data(ticket_id)` - All-in-one fetch

**Features**:
- Rate limit handling (429 responses)
- Automatic retry logic
- Pagination support
- Authentication via API token

### 3. AI Analyzer (`services/ai_analyzer.py`)
**Purpose**: Analyze tickets using Claude or GPT

**Supported Providers**:
- Claude (Anthropic) - Recommended
- GPT (OpenAI)

**Process**:
1. Build analysis prompt with ticket data
2. Send to AI API
3. Parse JSON response
4. Validate structure
5. Return structured analysis

**Configuration**:
- Temperature: 0.3 (consistent results)
- Max tokens: 4096
- Model: Claude 3.5 Sonnet or GPT-4 Turbo

### 4. Storage Service (`services/storage.py`)
**Purpose**: Handle all database operations

**Key Methods**:
- `store_complete_ticket()` - Save everything
- `_store_ticket()` - Upsert ticket
- `_store_comments()` - Save comments
- `_store_metrics()` - Save metrics
- `_store_audits()` - Save audits
- `_store_analysis()` - Save AI analysis
- `get_ticket_with_analysis()` - Retrieve ticket
- `get_all_analyzed_tickets()` - List tickets

### 5. Analysis Prompt (`prompts/analysis_prompt.py`)
**Purpose**: Generate AI prompts for ticket analysis

**Components**:
- `SYSTEM_PROMPT` - Instructions for AI
- `build_analysis_prompt()` - Format ticket data
- `_format_conversation()` - Format comments
- `_format_timeline()` - Format audit events
- `_format_metrics()` - Format SLA data

**Prompt Structure**:
```
1. Ticket metadata
2. Performance metrics
3. Timeline of events
4. Full conversation
5. Analysis requirements
6. JSON output schema
7. Scoring guidelines
```

### 6. Dashboard (`dashboard/app.py`)
**Purpose**: Visualize analysis results

**Visualizations**:
1. **Key Metrics Cards**
   - Total tickets
   - Avg satisfaction
   - Avg response time
   - Blocker rate

2. **Satisfaction Trend**
   - Line chart over time
   - Shows score evolution

3. **Score Distribution**
   - Box plot by category
   - Shows quartiles & outliers

4. **Issue Themes**
   - Pie chart of categories
   - Distribution breakdown

5. **Resolution Types**
   - Bar chart of resolution methods
   - Color-coded by frequency

6. **Response Time vs Satisfaction**
   - Scatter plot
   - Bubble size = resolution time
   - Color = priority

7. **Sentiment Journey**
   - Sankey diagram
   - Start → End sentiment flow

8. **Recent Tickets Table**
   - Paginated list
   - Key metrics visible

---

## 🔐 Security Considerations

### 1. API Keys
- Store in environment variables
- Never commit to git
- Use separate keys for dev/prod

### 2. Webhook Validation
- Optional webhook secret
- Signature verification
- IP whitelisting (if needed)

### 3. Database
- Use connection pooling
- Parameterized queries (SQLAlchemy)
- Regular backups

### 4. Rate Limiting
- Handles Zendesk rate limits
- Respects Retry-After headers
- Exponential backoff

---

## 📈 Scalability

### Current Design (15-20 tickets/day)
- ✅ Synchronous processing
- ✅ Single Flask instance
- ✅ Direct database writes

### Future Scale (100+ tickets/day)
Consider:
- 🔄 Celery task queue
- 🔄 Redis for caching
- 🔄 Multiple workers
- 🔄 Load balancer

---

## 🧪 Testing Strategy

### Unit Tests
- Test individual components
- Mock external APIs
- Validate data transformations

### Integration Tests
- Test full pipeline
- Use test Zendesk account
- Verify database writes

### Manual Testing
```bash
# Test connections
python test_ticket.py test

# Process test ticket
python test_ticket.py process --ticket-id 123

# List custom fields
python test_ticket.py fields
```

---

## 📊 Monitoring

### Application Logs
- Flask request logs
- Processing time metrics
- Error tracking

### Database Monitoring
- Query performance
- Connection pool usage
- Table sizes

### API Usage
- Zendesk API calls
- AI API usage & costs
- Rate limit tracking

---

## 🔄 Data Flow Example

```
1. Ticket #12345 solved in Zendesk
   ↓
2. Zendesk trigger fires
   ↓
3. POST /webhook/ticket-solved
   payload: {"detail": {"id": "12345", "status": "SOLVED"}}
   ↓
4. Extract ticket_id = 12345
   ↓
5. Fetch from Zendesk API (4 parallel calls):
   - Ticket: "Unable to login"
   - Comments: 8 messages
   - Audits: 12 events
   - Metrics: First reply 15min, Resolution 2hr
   ↓
6. Send to Claude/GPT for analysis
   Prompt: 15,000 tokens
   Response: 1,500 tokens
   ↓
7. Parse JSON response:
   {
     "overall_satisfaction_score": 8.5,
     "tonality_score": 9,
     "issue_theme": "account_access",
     "resolution_type": "workaround",
     ...
   }
   ↓
8. Store in PostgreSQL (6 tables)
   ↓
9. Dashboard auto-refreshes
   ↓
10. User views insights! 🎉
```

---

## 🎯 Key Design Decisions

### Why Flask?
- Lightweight
- Easy to deploy
- Good for webhooks

### Why PostgreSQL?
- ACID compliance
- JSON support
- Mature ecosystem

### Why Claude/GPT?
- Strong reasoning
- JSON output
- Consistent results

### Why Dash/Plotly?
- Python-native
- Interactive charts
- Easy to customize

### Why synchronous processing?
- Simple for low volume
- Easier debugging
- No queue complexity

---

## 📚 Dependencies

### Core
- Flask 3.0.0 - Web framework
- SQLAlchemy 2.0.23 - ORM
- psycopg2-binary 2.9.9 - PostgreSQL adapter

### APIs
- requests 2.31.0 - HTTP client
- anthropic 0.18.1 - Claude API
- openai 1.12.0 - GPT API

### Dashboard
- dash 2.14.2 - Dashboard framework
- plotly 5.18.0 - Plotting library
- pandas 2.1.4 - Data manipulation

### Utilities
- python-dotenv 1.0.0 - Environment variables
- python-dateutil 2.8.2 - Date parsing

---

## 🚀 Deployment Options

### Option 1: Render (Recommended)
- Easy setup
- Auto-deploy from git
- Free tier available
- Managed PostgreSQL

### Option 2: AWS
- EC2 + RDS
- More control
- Higher complexity

### Option 3: Heroku
- Simple deployment
- Good for prototypes
- Limited free tier

### Option 4: Self-hosted
- Own server
- Full control
- Requires DevOps

---

## 💡 Future Enhancements

### Phase 2
- [ ] Agent performance dashboards
- [ ] Email alerts for low scores
- [ ] Export to CSV/Excel
- [ ] Custom date range filters

### Phase 3
- [ ] Real-time notifications
- [ ] Slack integration
- [ ] Predictive analytics
- [ ] A/B testing of responses

### Phase 4
- [ ] Multi-language support
- [ ] Voice sentiment analysis
- [ ] Agent coaching suggestions
- [ ] Automated response templates

---

## 📖 References

- [Zendesk API Docs](https://developer.zendesk.com/api-reference/)
- [Claude API Docs](https://docs.anthropic.com/)
- [Dash Documentation](https://dash.plotly.com/)
- [SQLAlchemy Docs](https://docs.sqlalchemy.org/)
