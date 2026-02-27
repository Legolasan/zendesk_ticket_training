"""
Database storage service for ticket data and analysis
"""
from datetime import datetime
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from models.schema import (
    Ticket, Comment, TicketMetric, TicketAudit,
    AIAnalysis, CustomFieldMapping
)


class StorageService:
    """Handle all database operations"""

    def __init__(self, db_session: Session):
        self.session = db_session

    def store_complete_ticket(self, ticket_data: Dict, analysis_data: Dict) -> int:
        """
        Store complete ticket data including analysis

        Args:
            ticket_data: Raw ticket data from Zendesk
            analysis_data: AI analysis results

        Returns:
            ticket_id of stored ticket
        """
        ticket_info = ticket_data.get('ticket', {})
        ticket_id = ticket_info.get('id')

        print(f"💾 Storing ticket {ticket_id} to database...")

        try:
            # 1. Store/update ticket
            self._store_ticket(ticket_info)

            # 2. Store comments
            self._store_comments(ticket_id, ticket_data.get('comments', []))

            # 3. Store metrics
            self._store_metrics(ticket_id, ticket_data.get('metrics', {}))

            # 4. Store audits
            self._store_audits(ticket_id, ticket_data.get('audits', []))

            # 5. Store AI analysis
            self._store_analysis(ticket_id, analysis_data)

            # 6. Store/update custom field mappings
            self._store_custom_field_mappings(ticket_data.get('custom_fields_mapping', []))

            # Commit all changes
            self.session.commit()
            print(f"✅ Ticket {ticket_id} stored successfully")

            return ticket_id

        except Exception as e:
            self.session.rollback()
            print(f"❌ Error storing ticket {ticket_id}: {e}")
            raise

    def _store_ticket(self, ticket_info: Dict):
        """Store or update ticket record"""
        ticket_id = ticket_info.get('id')

        # Check if ticket exists
        ticket = self.session.query(Ticket).filter_by(ticket_id=ticket_id).first()

        if ticket:
            # Update existing
            print(f"   Updating existing ticket {ticket_id}")
        else:
            # Create new
            ticket = Ticket(ticket_id=ticket_id)
            print(f"   Creating new ticket {ticket_id}")

        # Update fields
        ticket.subject = ticket_info.get('subject')
        ticket.description = ticket_info.get('description')
        ticket.status = ticket_info.get('status')
        ticket.priority = ticket_info.get('priority')
        ticket.ticket_type = ticket_info.get('type')

        ticket.requester_id = ticket_info.get('requester_id')
        ticket.assignee_id = ticket_info.get('assignee_id')
        ticket.submitter_id = ticket_info.get('submitter_id')
        ticket.group_id = ticket_info.get('group_id')
        ticket.organization_id = ticket_info.get('organization_id')

        # Parse timestamps
        ticket.created_at = self._parse_datetime(ticket_info.get('created_at'))
        ticket.updated_at = self._parse_datetime(ticket_info.get('updated_at'))
        ticket.solved_at = self._parse_datetime(ticket_info.get('updated_at'))  # Use updated_at as solved time

        ticket.tags = ticket_info.get('tags', [])
        ticket.custom_fields = ticket_info.get('custom_fields', [])
        ticket.satisfaction_rating = ticket_info.get('satisfaction_rating')
        ticket.via_channel = ticket_info.get('via', {}).get('channel')
        ticket.custom_status_id = ticket_info.get('custom_status_id')

        ticket.fetched_at = datetime.utcnow()

        if not self.session.object_session(ticket):
            self.session.add(ticket)

    def _store_comments(self, ticket_id: int, comments: List[Dict]):
        """Store ticket comments"""
        print(f"   Storing {len(comments)} comments")

        for comment_data in comments:
            zendesk_comment_id = comment_data.get('id')

            # Check if comment exists
            comment = self.session.query(Comment).filter_by(
                zendesk_comment_id=zendesk_comment_id
            ).first()

            if comment:
                continue  # Skip existing comments

            # Determine author type (simple heuristic)
            author_type = 'agent'  # Default
            if comment_data.get('public', True):
                # Could enhance this with user role lookup
                author_type = 'customer' if not comment_data.get('public') else 'agent'

            comment = Comment(
                ticket_id=ticket_id,
                zendesk_comment_id=zendesk_comment_id,
                author_id=comment_data.get('author_id'),
                author_type=author_type,
                body=comment_data.get('body'),
                html_body=comment_data.get('html_body'),
                plain_body=comment_data.get('plain_body'),
                is_public=comment_data.get('public', True),
                comment_type=comment_data.get('type', 'Comment'),
                created_at=self._parse_datetime(comment_data.get('created_at')),
                attachments=comment_data.get('attachments', []),
                metadata=comment_data.get('metadata', {})
            )

            self.session.add(comment)

    def _store_metrics(self, ticket_id: int, metrics_data: Dict):
        """Store ticket metrics"""
        if not metrics_data:
            return

        print(f"   Storing metrics")

        # Check if metrics exist
        metric = self.session.query(TicketMetric).filter_by(ticket_id=ticket_id).first()

        if not metric:
            metric = TicketMetric(ticket_id=ticket_id)

        # Extract timing data (handle both nested and flat structures)
        reply_time = metrics_data.get('reply_time_in_minutes', {})
        if isinstance(reply_time, dict):
            metric.first_reply_time_minutes = reply_time.get('calendar')
            metric.first_reply_time_business_minutes = reply_time.get('business')
        else:
            metric.first_reply_time_minutes = reply_time

        resolution_time = metrics_data.get('full_resolution_time_in_minutes', {})
        if isinstance(resolution_time, dict):
            metric.full_resolution_time_minutes = resolution_time.get('calendar')
            metric.full_resolution_time_business_minutes = resolution_time.get('business')
        else:
            metric.full_resolution_time_minutes = resolution_time

        agent_wait = metrics_data.get('agent_wait_time_in_minutes', {})
        if isinstance(agent_wait, dict):
            metric.agent_wait_time_minutes = agent_wait.get('calendar')

        requester_wait = metrics_data.get('requester_wait_time_in_minutes', {})
        if isinstance(requester_wait, dict):
            metric.requester_wait_time_minutes = requester_wait.get('calendar')

        on_hold = metrics_data.get('on_hold_time_in_minutes', {})
        if isinstance(on_hold, dict):
            metric.on_hold_time_minutes = on_hold.get('calendar')

        # Activity counts
        metric.reply_count = metrics_data.get('replies')
        metric.reopens = metrics_data.get('reopens')
        metric.assignee_stations = metrics_data.get('assignee_stations')
        metric.group_stations = metrics_data.get('group_stations')

        # Timestamps
        metric.assigned_at = self._parse_datetime(metrics_data.get('assigned_at'))
        metric.solved_at = self._parse_datetime(metrics_data.get('solved_at'))
        metric.initially_assigned_at = self._parse_datetime(metrics_data.get('initially_assigned_at'))
        metric.latest_comment_added_at = self._parse_datetime(metrics_data.get('latest_comment_added_at'))

        # Store raw metrics for reference
        metric.raw_metrics = metrics_data

        if not self.session.object_session(metric):
            self.session.add(metric)

    def _store_audits(self, ticket_id: int, audits: List[Dict]):
        """Store ticket audits"""
        print(f"   Storing {len(audits)} audits")

        for audit_data in audits:
            zendesk_audit_id = audit_data.get('id')

            # Check if audit exists
            audit = self.session.query(TicketAudit).filter_by(
                zendesk_audit_id=zendesk_audit_id
            ).first()

            if audit:
                continue  # Skip existing audits

            audit = TicketAudit(
                ticket_id=ticket_id,
                zendesk_audit_id=zendesk_audit_id,
                author_id=audit_data.get('author_id'),
                created_at=self._parse_datetime(audit_data.get('created_at')),
                events=audit_data.get('events', []),
                via=audit_data.get('via', {}),
                metadata=audit_data.get('metadata', {})
            )

            self.session.add(audit)

    def _store_analysis(self, ticket_id: int, analysis_data: Dict):
        """Store AI analysis"""
        if not analysis_data:
            return

        print(f"   Storing AI analysis")

        # Check if analysis exists
        analysis = self.session.query(AIAnalysis).filter_by(ticket_id=ticket_id).first()

        if not analysis:
            analysis = AIAnalysis(ticket_id=ticket_id)

        # Extract metadata
        metadata = analysis_data.get('_metadata', {})
        analysis.analyzed_at = self._parse_datetime(metadata.get('analyzed_at'))
        analysis.ai_provider = metadata.get('ai_provider')
        analysis.ai_model = metadata.get('ai_model')

        # Satisfaction scores
        satisfaction = analysis_data.get('satisfaction_scores', {})
        analysis.tonality_score = satisfaction.get('tonality_score')
        analysis.tonality_summary = satisfaction.get('tonality_summary')
        analysis.professionalism_score = satisfaction.get('professionalism_score')
        analysis.professionalism_summary = satisfaction.get('professionalism_summary')
        analysis.empathy_score = satisfaction.get('empathy_score')
        analysis.empathy_summary = satisfaction.get('empathy_summary')
        analysis.responsiveness_score = satisfaction.get('responsiveness_score')
        analysis.overall_satisfaction_score = satisfaction.get('overall_satisfaction_score')

        # Delay handling
        delay = analysis_data.get('delay_handling', {})
        analysis.avg_response_delay_minutes = delay.get('avg_response_delay_minutes')
        analysis.max_response_delay_minutes = delay.get('max_response_delay_minutes')
        analysis.delay_handling_score = delay.get('delay_handling_score')
        analysis.delay_handling_summary = delay.get('delay_handling_summary')

        # Blocker analysis
        blocker = analysis_data.get('blocker_analysis', {})
        analysis.blocker_detected = blocker.get('blocker_detected', False)
        analysis.blocker_description = blocker.get('blocker_description')
        analysis.blocker_handling_score = blocker.get('blocker_handling_score')

        # Resolution analysis
        resolution = analysis_data.get('resolution_analysis', {})
        analysis.resolution_type = resolution.get('resolution_type')
        analysis.resolution_description = resolution.get('resolution_description')
        analysis.resolution_effectiveness_score = resolution.get('resolution_effectiveness_score')

        # Theme classification
        theme = analysis_data.get('theme_classification', {})
        analysis.issue_theme = theme.get('issue_theme')
        analysis.issue_theme_confidence = theme.get('issue_theme_confidence')
        analysis.resolution_theme = theme.get('resolution_theme')

        # Sentiment analysis
        sentiment = analysis_data.get('sentiment_analysis', {})
        analysis.customer_sentiment_start = sentiment.get('customer_sentiment_start')
        analysis.customer_sentiment_end = sentiment.get('customer_sentiment_end')
        analysis.sentiment_change = sentiment.get('sentiment_change')

        # Conversation metrics
        conv_metrics = analysis_data.get('conversation_metrics', {})
        analysis.total_exchanges = conv_metrics.get('total_exchanges')
        analysis.customer_messages = conv_metrics.get('customer_messages')
        analysis.agent_messages = conv_metrics.get('agent_messages')

        # Summary
        summary = analysis_data.get('summary', {})
        analysis.ai_summary = summary.get('ai_summary')
        analysis.improvement_recommendations = summary.get('improvement_recommendations', [])

        # Store raw response
        analysis.raw_ai_response = metadata.get('raw_response')

        if not self.session.object_session(analysis):
            self.session.add(analysis)

    def _store_custom_field_mappings(self, custom_fields: List[Dict]):
        """Store or update custom field mappings"""
        if not custom_fields:
            return

        print(f"   Updating custom field mappings ({len(custom_fields)} fields)")

        for field_data in custom_fields:
            field_id = field_data.get('id')

            # Check if mapping exists
            mapping = self.session.query(CustomFieldMapping).filter_by(field_id=field_id).first()

            if not mapping:
                mapping = CustomFieldMapping(field_id=field_id)

            mapping.field_key = field_data.get('key')
            mapping.field_title = field_data.get('title')
            mapping.field_type = field_data.get('type')
            mapping.field_description = field_data.get('description')
            mapping.is_active = field_data.get('active', True)
            mapping.field_options = field_data.get('custom_field_options', [])
            mapping.updated_at = datetime.utcnow()

            if not self.session.object_session(mapping):
                mapping.created_at = datetime.utcnow()
                self.session.add(mapping)

    def _parse_datetime(self, dt_string: Optional[str]) -> Optional[datetime]:
        """Parse datetime string to datetime object"""
        if not dt_string:
            return None

        try:
            # Handle ISO format with timezone
            from dateutil import parser
            return parser.isoparse(dt_string)
        except Exception:
            return None

    def get_ticket_with_analysis(self, ticket_id: int) -> Optional[Dict]:
        """Retrieve ticket with all related data and analysis"""
        ticket = self.session.query(Ticket).filter_by(ticket_id=ticket_id).first()

        if not ticket:
            return None

        return {
            'ticket': ticket,
            'comments': ticket.comments,
            'metrics': ticket.metrics,
            'audits': ticket.audits,
            'analysis': ticket.analysis
        }

    def get_all_analyzed_tickets(self, limit: int = 100) -> List[Ticket]:
        """Get all tickets with analysis"""
        return self.session.query(Ticket).join(AIAnalysis).limit(limit).all()
