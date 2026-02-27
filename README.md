# 🎯 Zendesk Ticket Analysis System

<div align="center">

**AI-Powered Customer Satisfaction Analysis for Zendesk Support Tickets**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/flask-3.0.0-green.svg)](https://flask.palletsprojects.com/)
[![PostgreSQL](https://img.shields.io/badge/postgresql-13+-blue.svg)](https://www.postgresql.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[Features](#-features) • [Quick Start](#-quick-start) • [Documentation](#-documentation) • [Architecture](#-architecture) • [Contributing](#-contributing)

</div>

---

## 📖 Overview

This system automatically analyzes Zendesk support tickets when they're solved, providing deep insights into customer satisfaction, agent performance, and support quality. Using AI (Claude or GPT), it evaluates conversations across 10+ dimensions including tonality, professionalism, empathy, and resolution effectiveness.

### What It Does

1. **Receives webhook** when ticket is solved in Zendesk
2. **Fetches complete data**: ticket details, conversation, timeline, metrics, custom fields
3. **AI analyzes** the interaction across multiple satisfaction dimensions
4. **Stores insights** in PostgreSQL for trending and reporting
5. **Visualizes results** in an interactive dashboard

### Perfect For

- Support teams wanting to improve customer satisfaction
- Managers tracking agent performance
- QA teams analyzing ticket quality
- Product teams understanding customer pain points

---

## ✨ Features

### 🤖 AI-Powered Analysis

**Customer Satisfaction Scores (1-10)**
- **Tonality**: Agent warmth, friendliness, positivity
- **Professionalism**: Expertise, clarity, proper conduct
- **Empathy**: Understanding and care for customer situation
- **Responsiveness**: Speed and proactive communication
- **Overall Satisfaction**: Weighted composite score

**Operational Insights**
- **Delay Handling**: Response times and communication during delays
- **Blocker Detection**: Identifies and evaluates blocker handling
- **Resolution Classification**: Workaround, engineering fix, escalated, or cold close
- **Effectiveness Scoring**: How well the issue was resolved

**Conversation Analysis**
- Issue theme categorization (billing, technical, bug, feature request, etc.)
- Resolution approach classification
- Customer sentiment journey (start → end)
- Back-and-forth exchange metrics

**AI Recommendations**
- Actionable improvement suggestions
- Pattern identification
- Best practice highlights

### 📊 Interactive Dashboard

Built with Dash/Plotly featuring:
- Real-time satisfaction trend analysis
- Score distribution across categories
- Issue theme breakdown
- Resolution type analysis
- Response time vs satisfaction correlation
- Customer sentiment flow visualization
- Detailed ticket drill-down

### 🔧 Comprehensive Data Collection

- **All ticket fields** (standard + custom)
- **Complete conversation** history
- **Full audit trail** (every change/event)
- **SLA metrics** (response times, resolution times)
- **Performance data** (reopens, reassignments, delays)
- **Custom field mapping** (automatic discovery and storage)

### 🚀 Production Ready

- Configurable AI provider (Claude or OpenAI)
- Rate limit handling and retry logic
- Error handling and logging
- PostgreSQL with proper indexing
- RESTful API endpoints
- Docker ready (optional)
- One-click Render deployment

---

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- PostgreSQL 13+
- Zendesk account with API access
- Claude (Anthropic) or OpenAI API key

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/Legolasan/zendesk_ticket_training.git
cd zendesk_ticket_training

# 2. Run setup script
chmod +x setup.sh
./setup.sh

# 3. Configure environment variables
cp .env.example .env
nano .env  # Edit with your credentials

# 4. Create database tables
python migrate.py

# 5. Test connections
python test_ticket.py test
```

### Configuration

Edit `.env` with your credentials:

```env
# Zendesk Configuration
ZENDESK_SUBDOMAIN=your-company
ZENDESK_EMAIL=your-email@company.com
ZENDESK_API_TOKEN=your_zendesk_api_token

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/zendesk_analysis

# AI Provider (choose one)
AI_PROVIDER=claude  # or "openai"
ANTHROPIC_API_KEY=sk-ant-your-key-here
OPENAI_API_KEY=sk-your-openai-key-here
```

### Running Locally

```bash
# Start webhook receiver
python app.py

# In another terminal, start dashboard
python dashboard/app.py
```

Access dashboard at `http://localhost:8050`

### Testing

```bash
# Test a specific ticket
python test_ticket.py process --ticket-id 12345

# View custom fields
python test_ticket.py fields

# Test all connections
python test_ticket.py test
```

---

## 📊 How It Works

```
┌─────────────────┐
│   Zendesk       │  Ticket solved
│   Trigger       │
└────────┬────────┘
         │ Webhook
         ▼
┌─────────────────┐
│  Flask Webhook  │  Extract ticket_id
│  Receiver       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Zendesk API    │  Fetch all data:
│  Client         │  • Ticket details
│                 │  • Comments
│                 │  • Audits
└────────┬────────┘  • Metrics
         │           • Custom fields
         ▼
┌─────────────────┐
│  AI Analyzer    │  Analyze:
│  (Claude/GPT)   │  • Satisfaction scores
│                 │  • Resolution quality
│                 │  • Sentiment journey
└────────┬────────┘  • Issue themes
         │
         ▼
┌─────────────────┐
│  PostgreSQL     │  Store everything
│  Database       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Dash Dashboard │  Visualize insights
└─────────────────┘
```

**Processing Time**: ~30-60 seconds per ticket

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [SETUP_GUIDE.md](SETUP_GUIDE.md) | Detailed step-by-step setup instructions |
| [ARCHITECTURE.md](ARCHITECTURE.md) | System architecture and technical details |
| [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) | Complete feature list and capabilities |
| [CLAUDE.md](CLAUDE.md) | AI assistant context and development guide |

---

## 🏗️ Architecture

### Tech Stack

- **Backend**: Flask 3.0.0
- **Database**: PostgreSQL with SQLAlchemy ORM
- **AI**: Anthropic Claude 3.5 Sonnet / OpenAI GPT-4
- **Dashboard**: Dash/Plotly
- **Deployment**: Render (or any Python hosting)

### Database Schema

6 comprehensive tables:
- `tickets` - Core ticket data + custom fields (JSON)
- `comments` - Complete conversation history
- `ticket_metrics` - SLA and performance metrics
- `ticket_audits` - Full timeline of changes
- `ai_analysis` - All AI scores and insights
- `custom_field_mappings` - Dynamic field definitions

### API Endpoints

```bash
# Webhook
POST /webhook/ticket-solved      # Zendesk webhook endpoint

# API
GET  /health                      # Health check
GET  /api/tickets                 # List analyzed tickets
GET  /api/tickets/{id}            # Get ticket details
POST /api/test-ticket/{id}        # Manual processing
```

---

## 🌐 Deployment

### Deploy to Render (Recommended)

1. **Create PostgreSQL Database**
   - Go to [Render](https://render.com) → New PostgreSQL
   - Copy the "External Database URL"

2. **Create Web Service**
   - New Web Service → Connect GitHub repo
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`

3. **Add Environment Variables**
   - Add all variables from `.env.example`
   - Use Render PostgreSQL URL for `DATABASE_URL`

4. **Deploy**
   - Render will auto-deploy on git push

5. **Configure Zendesk Webhook**
   - Go to Zendesk Admin → Webhooks
   - Create webhook pointing to: `https://your-app.onrender.com/webhook/ticket-solved`
   - Create trigger: When ticket status → Solved → Notify webhook

### Deploy Dashboard (Optional)

Create separate web service:
- Start Command: `python dashboard/app.py`
- Same environment variables

---

## 🧪 Testing

### Run Test Suite

```bash
# Test all connections
python test_ticket.py test

# Process a real ticket
python test_ticket.py process --ticket-id 12345

# List custom fields
python test_ticket.py fields
```

### Manual Webhook Test

```bash
curl -X POST http://localhost:5000/webhook/ticket-solved \
  -H "Content-Type: application/json" \
  -d '{
    "detail": {
      "id": "12345",
      "status": "SOLVED"
    }
  }'
```

### API Testing

```bash
# Check health
curl http://localhost:5000/health

# List tickets
curl http://localhost:5000/api/tickets

# Get specific ticket
curl http://localhost:5000/api/tickets/12345
```

---

## 📈 Example Analysis Output

```json
{
  "ticket_id": 12345,
  "satisfaction_scores": {
    "overall_satisfaction_score": 8.5,
    "tonality_score": 9.0,
    "professionalism_score": 8.5,
    "empathy_score": 9.0,
    "responsiveness_score": 7.5
  },
  "resolution_analysis": {
    "resolution_type": "workaround",
    "resolution_effectiveness_score": 8.0
  },
  "theme_classification": {
    "issue_theme": "technical",
    "resolution_theme": "investigation_required"
  },
  "sentiment_analysis": {
    "customer_sentiment_start": "frustrated",
    "customer_sentiment_end": "positive",
    "sentiment_change": "improved"
  },
  "ai_summary": "Agent provided professional support with empathy. Quick workaround provided while engineering investigates root cause.",
  "improvement_recommendations": [
    "Consider proactive updates during investigation",
    "Document workaround in knowledge base"
  ]
}
```

---

## 🔍 Key Metrics Analyzed

### Customer Satisfaction (1-10 scale)
- ✅ Agent tone and communication style
- ✅ Technical expertise and clarity
- ✅ Empathy and customer care
- ✅ Response speed and proactive updates

### Operational Performance
- ✅ First reply time (business & calendar hours)
- ✅ Time to resolution
- ✅ Number of back-and-forth exchanges
- ✅ Blocker identification and handling
- ✅ Delay communication effectiveness

### Resolution Quality
- ✅ Resolution type classification
- ✅ Effectiveness rating
- ✅ Root cause vs workaround identification

### Sentiment Tracking
- ✅ Customer mood at ticket start
- ✅ Customer mood at resolution
- ✅ Sentiment improvement/decline tracking

---

## 🛠️ Customization

### Adjust AI Prompts

Edit `prompts/analysis_prompt.py` to customize:
- Scoring criteria
- Analysis focus areas
- Output format
- Theme categories

### Add Dashboard Visualizations

Edit `dashboard/app.py` to add:
- Custom charts
- New metrics
- Filtering options
- Export functionality

### Extend Database Schema

Edit `models/schema.py` to add:
- New fields
- Additional tables
- Custom relationships

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Built with [Flask](https://flask.palletsprojects.com/)
- AI powered by [Anthropic Claude](https://www.anthropic.com/) & [OpenAI](https://openai.com/)
- Dashboard built with [Dash/Plotly](https://dash.plotly.com/)
- Zendesk integration via [Zendesk API](https://developer.zendesk.com/)

---

## 📞 Support

- 📧 Create an issue in this repository
- 📖 Check [SETUP_GUIDE.md](SETUP_GUIDE.md) for detailed setup help
- 🏗️ See [ARCHITECTURE.md](ARCHITECTURE.md) for technical details
- 🤖 See [CLAUDE.md](CLAUDE.md) for AI development context

---

## 📊 Project Stats

- **2,475+** lines of Python code
- **14** Python modules
- **6** database tables
- **10+** satisfaction metrics
- **7** dashboard visualizations
- **4** comprehensive documentation files

---

<div align="center">

**⭐ Star this repo if you find it useful! ⭐**

Built with ❤️ for better customer support

[Report Bug](https://github.com/Legolasan/zendesk_ticket_training/issues) • [Request Feature](https://github.com/Legolasan/zendesk_ticket_training/issues)

</div>
