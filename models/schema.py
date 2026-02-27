"""
Database schema for Zendesk ticket analysis
"""
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, Float, DateTime,
    ForeignKey, JSON, create_engine
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime

Base = declarative_base()


class Ticket(Base):
    """Main ticket information"""
    __tablename__ = 'tickets'

    ticket_id = Column(Integer, primary_key=True)
    subject = Column(String(500))
    description = Column(Text)
    status = Column(String(50))
    priority = Column(String(50))
    ticket_type = Column(String(50))

    # People
    requester_id = Column(Integer)
    assignee_id = Column(Integer)
    submitter_id = Column(Integer)
    group_id = Column(Integer)
    organization_id = Column(Integer)

    # Timestamps
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    solved_at = Column(DateTime)

    # Additional fields
    tags = Column(JSON)  # Array of tags
    custom_fields = Column(JSON)  # All custom fields as JSON
    satisfaction_rating = Column(JSON)  # Satisfaction rating data
    via_channel = Column(String(100))  # How ticket was created (email, web, etc.)

    # Custom status
    custom_status_id = Column(Integer)

    # Relationships
    comments = relationship("Comment", back_populates="ticket", cascade="all, delete-orphan")
    metrics = relationship("TicketMetric", back_populates="ticket", uselist=False, cascade="all, delete-orphan")
    audits = relationship("TicketAudit", back_populates="ticket", cascade="all, delete-orphan")
    analysis = relationship("AIAnalysis", back_populates="ticket", uselist=False, cascade="all, delete-orphan")

    # Metadata
    fetched_at = Column(DateTime, default=datetime.utcnow)


class Comment(Base):
    """Ticket comments/conversation"""
    __tablename__ = 'comments'

    comment_id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_id = Column(Integer, ForeignKey('tickets.ticket_id'), nullable=False)
    zendesk_comment_id = Column(Integer, unique=True)  # Actual Zendesk comment ID

    author_id = Column(Integer)
    author_type = Column(String(50))  # 'customer', 'agent', 'system'

    body = Column(Text)
    html_body = Column(Text)
    plain_body = Column(Text)

    is_public = Column(Boolean)
    comment_type = Column(String(50))  # 'Comment', 'VoiceComment', etc.

    created_at = Column(DateTime)

    # Attachments
    attachments = Column(JSON)  # Array of attachment objects
    metadata = Column(JSON)  # System metadata

    # Relationship
    ticket = relationship("Ticket", back_populates="comments")


class TicketMetric(Base):
    """SLA and performance metrics"""
    __tablename__ = 'ticket_metrics'

    metric_id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_id = Column(Integer, ForeignKey('tickets.ticket_id'), nullable=False, unique=True)

    # Response times (in minutes)
    first_reply_time_minutes = Column(Integer)
    first_reply_time_business_minutes = Column(Integer)

    # Resolution times
    full_resolution_time_minutes = Column(Integer)
    full_resolution_time_business_minutes = Column(Integer)

    # Wait times
    agent_wait_time_minutes = Column(Integer)
    requester_wait_time_minutes = Column(Integer)
    on_hold_time_minutes = Column(Integer)

    # Activity counts
    reply_count = Column(Integer)
    reopens = Column(Integer)
    assignee_stations = Column(Integer)  # Number of times reassigned
    group_stations = Column(Integer)  # Number of group changes

    # Timestamps
    assigned_at = Column(DateTime)
    solved_at = Column(DateTime)
    initially_assigned_at = Column(DateTime)

    # Status tracking
    latest_comment_added_at = Column(DateTime)

    # SLA breach info
    reply_time_in_minutes_calendar = Column(Integer)
    reply_time_in_minutes_business = Column(Integer)

    # Raw metrics JSON (for any additional fields)
    raw_metrics = Column(JSON)

    # Relationship
    ticket = relationship("Ticket", back_populates="metrics")


class TicketAudit(Base):
    """Complete ticket timeline/audit log"""
    __tablename__ = 'ticket_audits'

    audit_id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_id = Column(Integer, ForeignKey('tickets.ticket_id'), nullable=False)
    zendesk_audit_id = Column(Integer, unique=True)  # Actual Zendesk audit ID

    author_id = Column(Integer)
    created_at = Column(DateTime)

    # Events (array of event objects describing changes)
    events = Column(JSON)

    # Via (how the update was made)
    via = Column(JSON)

    # Metadata
    metadata = Column(JSON)

    # Relationship
    ticket = relationship("Ticket", back_populates="audits")


class AIAnalysis(Base):
    """AI-powered ticket analysis"""
    __tablename__ = 'ai_analysis'

    analysis_id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_id = Column(Integer, ForeignKey('tickets.ticket_id'), nullable=False, unique=True)

    # Analysis metadata
    analyzed_at = Column(DateTime, default=datetime.utcnow)
    ai_provider = Column(String(50))  # 'claude' or 'openai'
    ai_model = Column(String(100))  # e.g., 'claude-3-opus-20240229'

    # Customer Satisfaction Scores (1-10)
    tonality_score = Column(Float)
    professionalism_score = Column(Float)
    empathy_score = Column(Float)
    responsiveness_score = Column(Float)
    overall_satisfaction_score = Column(Float)

    # Tonality details
    tonality_summary = Column(Text)  # Description of agent tone

    # Professionalism details
    professionalism_summary = Column(Text)  # Assessment of professional behavior

    # Empathy details
    empathy_summary = Column(Text)  # How well agent showed empathy

    # Response/Delay handling
    avg_response_delay_minutes = Column(Float)
    max_response_delay_minutes = Column(Float)
    delay_handling_score = Column(Float)  # 1-10
    delay_handling_summary = Column(Text)

    # Blocker detection
    blocker_detected = Column(Boolean)
    blocker_description = Column(Text)
    blocker_handling_score = Column(Float)  # How well blockers were handled

    # Resolution classification
    resolution_type = Column(String(50))  # 'workaround', 'engineering_fix', 'escalated', 'cold_close'
    resolution_description = Column(Text)
    resolution_effectiveness_score = Column(Float)  # 1-10

    # Theme classification
    issue_theme = Column(String(100))  # e.g., 'billing', 'technical', 'feature_request'
    issue_theme_confidence = Column(Float)  # 0-1
    resolution_theme = Column(String(100))

    # AI Summary
    ai_summary = Column(Text)  # Overall summary of the ticket handling

    # Recommendations
    improvement_recommendations = Column(JSON)  # Array of suggestions

    # Sentiment analysis
    customer_sentiment_start = Column(String(50))  # 'positive', 'neutral', 'negative'
    customer_sentiment_end = Column(String(50))
    sentiment_change = Column(String(50))  # 'improved', 'declined', 'stable'

    # Back-and-forth analysis
    total_exchanges = Column(Integer)
    customer_messages = Column(Integer)
    agent_messages = Column(Integer)

    # Raw AI response (for debugging)
    raw_ai_response = Column(JSON)

    # Relationship
    ticket = relationship("Ticket", back_populates="analysis")


class CustomFieldMapping(Base):
    """Mapping of Zendesk custom fields for reference"""
    __tablename__ = 'custom_field_mappings'

    field_id = Column(Integer, primary_key=True)
    field_key = Column(String(100), unique=True)
    field_title = Column(String(200))
    field_type = Column(String(50))  # 'text', 'dropdown', 'checkbox', etc.
    field_description = Column(Text)
    is_active = Column(Boolean, default=True)

    # Options for dropdown/multiselect fields
    field_options = Column(JSON)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# Database connection helper
class Database:
    """Database connection and session management"""

    def __init__(self, database_url):
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def create_tables(self):
        """Create all tables"""
        Base.metadata.create_all(self.engine)
        print("✅ Database tables created successfully")

    def drop_tables(self):
        """Drop all tables (use with caution!)"""
        Base.metadata.drop_all(self.engine)
        print("⚠️  All tables dropped")

    def get_session(self):
        """Get a new database session"""
        return self.SessionLocal()
