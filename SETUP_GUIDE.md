# 🚀 Zendesk Ticket Analysis - Setup Guide

Complete step-by-step guide to get your system up and running!

---

## 📋 Prerequisites

Before you begin, make sure you have:

- ✅ Python 3.8+ installed
- ✅ PostgreSQL database (local or cloud)
- ✅ Zendesk account with API access
- ✅ Claude API key (Anthropic) OR OpenAI API key
- ✅ Server for hosting webhook (Render, AWS, etc.)

---

## 🔧 Step 1: Initial Setup

### 1.1 Clone/Download Project
```bash
cd zendesk_analysis
```

### 1.2 Run Setup Script
```bash
chmod +x setup.sh
./setup.sh
```

This will:
- Create a virtual environment
- Install all Python dependencies
- Create a `.env` file from template

---

## 🔑 Step 2: Configure Environment Variables

Edit the `.env` file with your credentials:

```bash
nano .env  # or use your favorite editor
```

### Required Configuration:

#### Zendesk Settings
```env
ZENDESK_SUBDOMAIN=your-company        # e.g., if URL is yourcompany.zendesk.com
ZENDESK_EMAIL=your-email@company.com
ZENDESK_API_TOKEN=your_api_token_here
```

**How to get Zendesk API token:**
1. Go to Zendesk Admin → Apps and integrations → APIs → Zendesk API
2. Click "Add API token"
3. Copy the token

#### Database Settings
```env
DATABASE_URL=postgresql://user:password@localhost:5432/zendesk_analysis
```

**Local PostgreSQL example:**
```bash
# Create database
createdb zendesk_analysis

# If you need to create a user:
psql postgres
CREATE USER zendesk_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE zendesk_analysis TO zendesk_user;
```

**Cloud PostgreSQL (e.g., Render):**
- Go to Render.com → New PostgreSQL
- Copy the "External Database URL"
- Paste as DATABASE_URL

#### AI Configuration
Choose either Claude OR OpenAI:

```env
AI_PROVIDER=claude  # or "openai"

# If using Claude:
ANTHROPIC_API_KEY=sk-ant-your-key-here

# If using OpenAI:
OPENAI_API_KEY=sk-your-key-here
```

**How to get API keys:**
- Claude: https://console.anthropic.com → API Keys
- OpenAI: https://platform.openai.com/api-keys

---

## 🗄️ Step 3: Set Up Database

Run the migration script to create all tables:

```bash
python migrate.py
```

You should see:
```
✅ Migration completed successfully!
Tables created:
   - tickets
   - comments
   - ticket_metrics
   - ticket_audits
   - ai_analysis
   - custom_field_mappings
```

---

## 🧪 Step 4: Test Connections

Before going live, test that everything works:

```bash
python test_ticket.py test
```

This will test:
- ✅ Zendesk API connection
- ✅ Claude/OpenAI API connection
- ✅ Database connection

---

## 📊 Step 5: Test with a Real Ticket

Pick a solved ticket from your Zendesk and test the full pipeline:

```bash
python test_ticket.py process --ticket-id 12345
```

Replace `12345` with an actual ticket ID from your Zendesk.

This will:
1. Fetch all ticket data from Zendesk
2. Analyze with AI
3. Store in database
4. Show you the results

---

## 🌐 Step 6: Set Up Webhook Receiver

### 6.1 Start the Flask App Locally

```bash
python app.py
```

You should see:
```
✅ All systems ready!
📡 Starting webhook receiver on port 5000...
🔗 Webhook URL: http://localhost:5000/webhook/ticket-solved
```

### 6.2 Test the Webhook Endpoint

In another terminal:

```bash
curl -X POST http://localhost:5000/api/test-ticket/12345
```

---

## ☁️ Step 7: Deploy to Render (Production)

### 7.1 Create Render Account
Go to https://render.com and sign up

### 7.2 Create Web Service
1. Click "New +" → "Web Service"
2. Connect your GitHub repo (or upload code)
3. Configure:
   - **Name**: `zendesk-analysis`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`

### 7.3 Add Environment Variables
In Render dashboard, add all your `.env` variables:
- ZENDESK_SUBDOMAIN
- ZENDESK_EMAIL
- ZENDESK_API_TOKEN
- DATABASE_URL (use Render PostgreSQL URL)
- AI_PROVIDER
- ANTHROPIC_API_KEY (or OPENAI_API_KEY)

### 7.4 Deploy
Click "Create Web Service" and wait for deployment.

Your webhook URL will be:
```
https://zendesk-analysis.onrender.com/webhook/ticket-solved
```

---

## 🎣 Step 8: Configure Zendesk Webhook

### 8.1 Create Webhook in Zendesk

1. Go to **Zendesk Admin** → **Apps and integrations** → **Webhooks** → **Webhooks**
2. Click **"Create webhook"**
3. Configure:
   - **Endpoint URL**: `https://your-render-url.onrender.com/webhook/ticket-solved`
   - **Request method**: `POST`
   - **Request format**: `JSON`
   - **Authentication**: None (or add secret if configured)

### 8.2 Create Trigger

1. Go to **Zendesk Admin** → **Objects and rules** → **Business rules** → **Triggers**
2. Click **"Add trigger"**
3. Configure:
   - **Trigger name**: "Send solved tickets to analysis"
   - **Conditions**:
     - Ticket: Status → Changed to → Solved
   - **Actions**:
     - Notifications: Notify by webhook → (Select your webhook)

### 8.3 Test It!

1. Solve a test ticket in Zendesk
2. Check your app logs to see it being processed
3. View results in dashboard

---

## 📈 Step 9: Launch Dashboard

### 9.1 Start Dashboard Locally

```bash
python dashboard/app.py
```

Open your browser to:
```
http://localhost:8050
```

### 9.2 Deploy Dashboard to Render (Optional)

Create another web service:
- **Start Command**: `python dashboard/app.py`
- Add same environment variables

---

## 🎯 Step 10: View Your First Results!

Once a ticket is processed, you'll see:

### In Dashboard:
- 📊 Key metrics (total tickets, avg satisfaction, etc.)
- 📈 Satisfaction trends over time
- 🎨 Issue theme breakdown
- 🔧 Resolution type analysis
- ⏱️ Response time analysis
- 💬 Sentiment journey

### Via API:
```bash
# List all tickets
curl http://localhost:5000/api/tickets

# Get specific ticket
curl http://localhost:5000/api/tickets/12345
```

---

## 🔍 Useful Commands

### List Custom Fields
```bash
python test_ticket.py fields
```

### Process Specific Ticket
```bash
python test_ticket.py process --ticket-id 12345
```

### Check Database
```bash
psql -d zendesk_analysis -c "SELECT count(*) FROM tickets;"
```

### View Logs (Render)
Go to Render dashboard → Your service → Logs

---

## 🐛 Troubleshooting

### Issue: "Configuration error: Missing required configuration"
**Solution**: Make sure `.env` file exists and all required fields are filled

### Issue: "Zendesk API connection failed"
**Solution**:
- Verify API token is correct
- Check subdomain is just the name (not full URL)
- Ensure API access is enabled in Zendesk

### Issue: "Database connection failed"
**Solution**:
- Check DATABASE_URL format
- Ensure PostgreSQL is running
- Verify database exists: `psql -l`

### Issue: "AI API connection failed"
**Solution**:
- Verify API key is correct
- Check you have credits/quota available
- Ensure API_PROVIDER matches your key (claude vs openai)

### Issue: Webhook not receiving data
**Solution**:
- Check webhook URL is publicly accessible
- Verify trigger is active in Zendesk
- Check Zendesk webhook logs (Admin → Webhooks → View activity)
- Test manually: `curl -X POST your-webhook-url/webhook/ticket-solved -H "Content-Type: application/json" -d '{"detail": {"id": "123", "status": "SOLVED"}}'`

---

## 📚 Next Steps

Now that your system is running:

1. ✅ Monitor the first few tickets to ensure analysis quality
2. ✅ Adjust AI prompts if needed (`prompts/analysis_prompt.py`)
3. ✅ Customize dashboard visualizations
4. ✅ Set up alerts for low satisfaction scores
5. ✅ Export data for reporting

---

## 🎉 You're All Set!

Your Zendesk ticket analysis system is now live and analyzing customer satisfaction automatically! 🚀

Need help? Check:
- README.md for architecture details
- Code comments for technical details
- Zendesk docs: https://developer.zendesk.com
- Claude docs: https://docs.anthropic.com

Happy analyzing! 📊
