"""
AI analysis prompt for ticket evaluation
"""

SYSTEM_PROMPT = """You are an expert customer support quality analyst specializing in evaluating support ticket interactions for customer satisfaction.

Your task is to analyze Zendesk support tickets and provide comprehensive assessments of agent performance, customer satisfaction, and resolution effectiveness.

You will evaluate tickets based on:
1. Agent Tonality & Communication Style
2. Professionalism
3. Empathy & Customer Care
4. Response Time & Delay Handling
5. Blocker Detection & Handling
6. Resolution Effectiveness
7. Overall Customer Satisfaction

Provide scores on a 1-10 scale (10 being excellent) with detailed justifications."""


def build_analysis_prompt(ticket_data: dict) -> str:
    """
    Build the analysis prompt with ticket data

    Args:
        ticket_data: Complete ticket data including comments, metrics, and audits

    Returns:
        Formatted prompt string
    """

    ticket = ticket_data.get('ticket', {})
    comments = ticket_data.get('comments', [])
    metrics = ticket_data.get('metrics', {})
    audits = ticket_data.get('audits', [])

    # Build conversation transcript
    conversation = _format_conversation(comments)

    # Build timeline
    timeline = _format_timeline(audits)

    # Build metrics summary
    metrics_summary = _format_metrics(metrics)

    prompt = f"""
# TICKET ANALYSIS REQUEST

## Ticket Information
- **Ticket ID**: {ticket.get('id')}
- **Subject**: {ticket.get('subject')}
- **Priority**: {ticket.get('priority')}
- **Status**: {ticket.get('status')}
- **Created**: {ticket.get('created_at')}
- **Solved**: {ticket.get('updated_at')}
- **Tags**: {', '.join(ticket.get('tags', []))}

## Performance Metrics
{metrics_summary}

## Conversation Timeline
{timeline}

## Full Conversation Transcript
{conversation}

---

# ANALYSIS REQUIREMENTS

Please analyze this ticket and provide a detailed assessment in the following JSON format:

```json
{{
  "satisfaction_scores": {{
    "tonality_score": <1-10>,
    "tonality_summary": "<detailed explanation of agent's tone throughout the conversation>",

    "professionalism_score": <1-10>,
    "professionalism_summary": "<assessment of professional behavior, technical accuracy, and conduct>",

    "empathy_score": <1-10>,
    "empathy_summary": "<evaluation of how well the agent showed understanding and care for customer's situation>",

    "responsiveness_score": <1-10>,
    "overall_satisfaction_score": <1-10>
  }},

  "delay_handling": {{
    "avg_response_delay_minutes": <calculated from conversation>,
    "max_response_delay_minutes": <longest delay>,
    "delay_handling_score": <1-10>,
    "delay_handling_summary": "<how well delays were handled, if customer was kept informed, etc.>"
  }},

  "blocker_analysis": {{
    "blocker_detected": <true/false>,
    "blocker_description": "<what blocker was encountered, if any>",
    "blocker_handling_score": <1-10 or null>,
    "blocker_handling_summary": "<how blocker was communicated and handled>"
  }},

  "resolution_analysis": {{
    "resolution_type": "<one of: workaround, engineering_fix, escalated, cold_close>",
    "resolution_description": "<detailed explanation of how the issue was resolved>",
    "resolution_effectiveness_score": <1-10>
  }},

  "theme_classification": {{
    "issue_theme": "<category: billing, technical, feature_request, account_access, bug_report, integration, performance, data_issue, etc.>",
    "issue_theme_confidence": <0.0-1.0>,
    "resolution_theme": "<how it was resolved: quick_fix, investigation_required, product_limitation, user_error, configuration_change, etc.>"
  }},

  "sentiment_analysis": {{
    "customer_sentiment_start": "<positive/neutral/negative/frustrated>",
    "customer_sentiment_end": "<positive/neutral/negative/frustrated>",
    "sentiment_change": "<improved/declined/stable>"
  }},

  "conversation_metrics": {{
    "total_exchanges": <number>,
    "customer_messages": <count>,
    "agent_messages": <count>
  }},

  "summary": {{
    "ai_summary": "<2-3 sentence overall summary of the ticket handling>",
    "improvement_recommendations": [
      "<specific recommendation 1>",
      "<specific recommendation 2>"
    ]
  }}
}}
```

## Scoring Guidelines

### Tonality (1-10)
- 10: Warm, friendly, professional, positive throughout
- 7-9: Generally positive with minor lapses
- 4-6: Neutral, functional but not engaging
- 1-3: Cold, robotic, or negative tone

### Professionalism (1-10)
- 10: Expert knowledge, clear communication, proper grammar, follows best practices
- 7-9: Good knowledge with minor errors
- 4-6: Adequate but with noticeable issues
- 1-3: Unprofessional, poor communication, or significant errors

### Empathy (1-10)
- 10: Exceptional understanding, acknowledges frustration, personalizes responses
- 7-9: Shows care and understanding consistently
- 4-6: Basic acknowledgment of customer issues
- 1-3: Dismissive or lacks understanding

### Delay Handling (1-10)
- 10: Proactive updates, apologizes for delays, sets clear expectations
- 7-9: Generally responsive with some delays explained
- 4-6: Delays present but minimally addressed
- 1-3: Long delays with no communication

### Resolution Type Classification
- **workaround**: Temporary solution provided, root cause not fixed
- **engineering_fix**: Issue escalated and fixed by product/engineering team
- **escalated**: Transferred to another team/person for resolution
- **cold_close**: Closed without full resolution (customer stopped responding, can't reproduce, etc.)

### Issue Theme Examples
- billing (invoices, payments, refunds)
- technical (bugs, errors, system issues)
- feature_request (new functionality requests)
- account_access (login, permissions)
- bug_report (confirmed product bugs)
- integration (third-party integrations)
- performance (speed, latency issues)
- data_issue (data quality, sync problems)

Provide thorough, honest analysis. Be specific in your summaries with examples from the conversation.
"""

    return prompt


def _format_conversation(comments: list) -> str:
    """Format comments into a readable conversation transcript"""
    if not comments:
        return "No comments available."

    transcript = []
    for idx, comment in enumerate(comments, 1):
        author_id = comment.get('author_id', 'Unknown')
        created_at = comment.get('created_at', '')
        body = comment.get('body', comment.get('plain_body', ''))
        is_public = comment.get('public', True)

        visibility = "Public" if is_public else "Internal Note"

        transcript.append(
            f"\n### Message {idx} [{visibility}]\n"
            f"**From**: User ID {author_id}\n"
            f"**Time**: {created_at}\n"
            f"**Message**:\n{body}\n"
            f"{'-' * 80}"
        )

    return '\n'.join(transcript)


def _format_timeline(audits: list) -> str:
    """Format audits into a timeline of key events"""
    if not audits:
        return "No timeline available."

    timeline_events = []

    for audit in audits:
        created_at = audit.get('created_at', '')
        events = audit.get('events', [])

        for event in events:
            event_type = event.get('type', '')

            # Extract meaningful events
            if event_type == 'Comment':
                timeline_events.append(f"- {created_at}: Comment added")
            elif event_type == 'Change':
                field_name = event.get('field_name', '')
                prev_value = event.get('previous_value', '')
                new_value = event.get('value', '')
                timeline_events.append(
                    f"- {created_at}: {field_name} changed from '{prev_value}' to '{new_value}'"
                )
            elif event_type == 'Notification':
                timeline_events.append(f"- {created_at}: Notification sent")

    return '\n'.join(timeline_events) if timeline_events else "No significant events."


def _format_metrics(metrics: dict) -> str:
    """Format metrics into readable summary"""
    if not metrics:
        return "No metrics available."

    lines = []

    # Reply times
    first_reply = metrics.get('reply_time_in_minutes', {})
    if isinstance(first_reply, dict):
        calendar = first_reply.get('calendar', 'N/A')
        business = first_reply.get('business', 'N/A')
        lines.append(f"- **First Reply Time**: {calendar} min (calendar), {business} min (business hours)")
    else:
        lines.append(f"- **First Reply Time**: {metrics.get('reply_time_in_minutes', 'N/A')} minutes")

    # Resolution time
    full_resolution = metrics.get('full_resolution_time_in_minutes', {})
    if isinstance(full_resolution, dict):
        calendar = full_resolution.get('calendar', 'N/A')
        business = full_resolution.get('business', 'N/A')
        lines.append(f"- **Resolution Time**: {calendar} min (calendar), {business} min (business hours)")
    else:
        lines.append(f"- **Resolution Time**: {metrics.get('full_resolution_time_in_minutes', 'N/A')} minutes")

    # Activity counts
    lines.append(f"- **Reply Count**: {metrics.get('replies', 'N/A')}")
    lines.append(f"- **Reopens**: {metrics.get('reopens', 0)}")
    lines.append(f"- **Assignee Changes**: {metrics.get('assignee_stations', 0)}")

    # Wait times
    agent_wait = metrics.get('agent_wait_time_in_minutes', {})
    if isinstance(agent_wait, dict):
        lines.append(f"- **Agent Wait Time**: {agent_wait.get('calendar', 'N/A')} minutes")

    requester_wait = metrics.get('requester_wait_time_in_minutes', {})
    if isinstance(requester_wait, dict):
        lines.append(f"- **Requester Wait Time**: {requester_wait.get('calendar', 'N/A')} minutes")

    return '\n'.join(lines)
