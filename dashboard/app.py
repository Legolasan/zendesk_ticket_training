"""
Dash/Plotly dashboard for ticket analysis visualization
"""
import dash
from dash import dcc, html, Input, Output, dash_table
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import func

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from models.schema import Database, Ticket, AIAnalysis, TicketMetric

# Initialize database
database = Database(Config.DATABASE_URL)

# Initialize Dash app
app = dash.Dash(
    __name__,
    title='Zendesk Analysis Dashboard',
    update_title='Loading...'
)

# Define colors
COLORS = {
    'primary': '#1f77b4',
    'success': '#2ca02c',
    'warning': '#ff7f0e',
    'danger': '#d62728',
    'background': '#f8f9fa',
    'card': '#ffffff',
    'text': '#212529'
}

# Dashboard layout
app.layout = html.Div([
    # Header
    html.Div([
        html.H1('🎯 Zendesk Ticket Analysis Dashboard', style={'color': COLORS['primary']}),
        html.P('AI-Powered Customer Satisfaction Analysis', style={'color': '#6c757d'}),
    ], style={
        'textAlign': 'center',
        'padding': '20px',
        'backgroundColor': COLORS['background']
    }),

    # Date range selector
    html.Div([
        html.Label('Select Date Range:', style={'fontWeight': 'bold'}),
        dcc.DatePickerRange(
            id='date-range',
            start_date=(datetime.now() - timedelta(days=30)).date(),
            end_date=datetime.now().date(),
            display_format='YYYY-MM-DD'
        ),
        html.Button('Refresh Data', id='refresh-button', n_clicks=0,
                   style={'marginLeft': '20px', 'padding': '10px 20px'})
    ], style={'textAlign': 'center', 'padding': '20px'}),

    # Key Metrics Row
    html.Div(id='key-metrics', style={'padding': '20px'}),

    # Charts Row 1: Satisfaction Trends
    html.Div([
        html.Div([
            dcc.Graph(id='satisfaction-trend')
        ], style={'width': '50%', 'display': 'inline-block', 'padding': '10px'}),

        html.Div([
            dcc.Graph(id='score-distribution')
        ], style={'width': '50%', 'display': 'inline-block', 'padding': '10px'}),
    ]),

    # Charts Row 2: Issue Analysis
    html.Div([
        html.Div([
            dcc.Graph(id='issue-themes')
        ], style={'width': '50%', 'display': 'inline-block', 'padding': '10px'}),

        html.Div([
            dcc.Graph(id='resolution-types')
        ], style={'width': '50%', 'display': 'inline-block', 'padding': '10px'}),
    ]),

    # Charts Row 3: Performance Analysis
    html.Div([
        html.Div([
            dcc.Graph(id='response-time-analysis')
        ], style={'width': '50%', 'display': 'inline-block', 'padding': '10px'}),

        html.Div([
            dcc.Graph(id='sentiment-changes')
        ], style={'width': '50%', 'display': 'inline-block', 'padding': '10px'}),
    ]),

    # Recent Tickets Table
    html.Div([
        html.H3('📋 Recent Analyzed Tickets', style={'padding': '20px'}),
        html.Div(id='tickets-table', style={'padding': '20px'})
    ]),

    # Auto-refresh interval (every 5 minutes)
    dcc.Interval(
        id='interval-component',
        interval=5*60*1000,  # 5 minutes in milliseconds
        n_intervals=0
    )

], style={'fontFamily': 'Arial, sans-serif'})


def fetch_ticket_data(start_date, end_date):
    """Fetch ticket data from database"""
    session = database.get_session()

    try:
        # Query tickets with analysis in date range
        tickets = session.query(Ticket, AIAnalysis, TicketMetric)\
            .join(AIAnalysis, Ticket.ticket_id == AIAnalysis.ticket_id)\
            .outerjoin(TicketMetric, Ticket.ticket_id == TicketMetric.ticket_id)\
            .filter(Ticket.created_at.between(start_date, end_date))\
            .all()

        # Convert to dataframe
        data = []
        for ticket, analysis, metric in tickets:
            data.append({
                'ticket_id': ticket.ticket_id,
                'subject': ticket.subject,
                'created_at': ticket.created_at,
                'solved_at': ticket.solved_at,
                'priority': ticket.priority,
                'status': ticket.status,
                'overall_score': analysis.overall_satisfaction_score,
                'tonality_score': analysis.tonality_score,
                'professionalism_score': analysis.professionalism_score,
                'empathy_score': analysis.empathy_score,
                'responsiveness_score': analysis.responsiveness_score,
                'issue_theme': analysis.issue_theme,
                'resolution_type': analysis.resolution_type,
                'resolution_effectiveness': analysis.resolution_effectiveness_score,
                'sentiment_start': analysis.customer_sentiment_start,
                'sentiment_end': analysis.customer_sentiment_end,
                'sentiment_change': analysis.sentiment_change,
                'first_reply_time': metric.first_reply_time_minutes if metric else None,
                'resolution_time': metric.full_resolution_time_minutes if metric else None,
                'blocker_detected': analysis.blocker_detected,
                'ai_summary': analysis.ai_summary
            })

        df = pd.DataFrame(data)
        return df

    finally:
        session.close()


@app.callback(
    [Output('key-metrics', 'children'),
     Output('satisfaction-trend', 'figure'),
     Output('score-distribution', 'figure'),
     Output('issue-themes', 'figure'),
     Output('resolution-types', 'figure'),
     Output('response-time-analysis', 'figure'),
     Output('sentiment-changes', 'figure'),
     Output('tickets-table', 'children')],
    [Input('refresh-button', 'n_clicks'),
     Input('interval-component', 'n_intervals'),
     Input('date-range', 'start_date'),
     Input('date-range', 'end_date')]
)
def update_dashboard(n_clicks, n_intervals, start_date, end_date):
    """Update all dashboard components"""

    # Fetch data
    df = fetch_ticket_data(start_date, end_date)

    if df.empty:
        empty_fig = go.Figure()
        empty_fig.add_annotation(text="No data available", showarrow=False)
        return (
            html.Div("No tickets found in date range"),
            empty_fig, empty_fig, empty_fig, empty_fig, empty_fig, empty_fig,
            html.Div("No tickets to display")
        )

    # Key Metrics Cards
    key_metrics = create_key_metrics(df)

    # Satisfaction Trend Over Time
    satisfaction_trend = create_satisfaction_trend(df)

    # Score Distribution (Box plot)
    score_distribution = create_score_distribution(df)

    # Issue Themes (Pie chart)
    issue_themes = create_issue_themes_chart(df)

    # Resolution Types (Bar chart)
    resolution_types = create_resolution_types_chart(df)

    # Response Time Analysis
    response_time_analysis = create_response_time_analysis(df)

    # Sentiment Changes (Sankey diagram)
    sentiment_changes = create_sentiment_changes(df)

    # Tickets Table
    tickets_table = create_tickets_table(df)

    return (
        key_metrics,
        satisfaction_trend,
        score_distribution,
        issue_themes,
        resolution_types,
        response_time_analysis,
        sentiment_changes,
        tickets_table
    )


def create_key_metrics(df):
    """Create key metrics cards"""
    total_tickets = len(df)
    avg_satisfaction = df['overall_score'].mean()
    avg_response_time = df['first_reply_time'].mean()
    blocker_rate = (df['blocker_detected'].sum() / total_tickets * 100) if total_tickets > 0 else 0

    cards = html.Div([
        # Total Tickets
        html.Div([
            html.H4(f"{total_tickets}"),
            html.P("Total Tickets")
        ], style=card_style(COLORS['primary'])),

        # Avg Satisfaction
        html.Div([
            html.H4(f"{avg_satisfaction:.1f}/10"),
            html.P("Avg Satisfaction")
        ], style=card_style(COLORS['success'])),

        # Avg Response Time
        html.Div([
            html.H4(f"{avg_response_time:.0f}m"),
            html.P("Avg Response Time")
        ], style=card_style(COLORS['warning'])),

        # Blocker Rate
        html.Div([
            html.H4(f"{blocker_rate:.1f}%"),
            html.P("Blocker Rate")
        ], style=card_style(COLORS['danger'])),

    ], style={'display': 'flex', 'justifyContent': 'space-around', 'flexWrap': 'wrap'})

    return cards


def card_style(color):
    """Generate card style"""
    return {
        'backgroundColor': COLORS['card'],
        'padding': '20px',
        'margin': '10px',
        'borderRadius': '10px',
        'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
        'textAlign': 'center',
        'minWidth': '200px',
        'borderLeft': f'5px solid {color}'
    }


def create_satisfaction_trend(df):
    """Create satisfaction score trend over time"""
    df_sorted = df.sort_values('created_at')

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df_sorted['created_at'],
        y=df_sorted['overall_score'],
        mode='lines+markers',
        name='Overall Score',
        line=dict(color=COLORS['primary'], width=2)
    ))

    fig.update_layout(
        title='Customer Satisfaction Score Over Time',
        xaxis_title='Date',
        yaxis_title='Score (1-10)',
        yaxis=dict(range=[0, 10]),
        hovermode='x unified'
    )

    return fig


def create_score_distribution(df):
    """Create box plot of score distributions"""
    scores_df = pd.DataFrame({
        'Category': ['Overall', 'Tonality', 'Professional', 'Empathy', 'Responsive'] * len(df),
        'Score': pd.concat([
            df['overall_score'],
            df['tonality_score'],
            df['professionalism_score'],
            df['empathy_score'],
            df['responsiveness_score']
        ])
    })

    fig = px.box(scores_df, x='Category', y='Score', color='Category',
                 title='Score Distribution by Category')

    fig.update_layout(yaxis=dict(range=[0, 10]), showlegend=False)

    return fig


def create_issue_themes_chart(df):
    """Create pie chart of issue themes"""
    theme_counts = df['issue_theme'].value_counts()

    fig = px.pie(
        values=theme_counts.values,
        names=theme_counts.index,
        title='Issue Theme Distribution'
    )

    return fig


def create_resolution_types_chart(df):
    """Create bar chart of resolution types"""
    resolution_counts = df['resolution_type'].value_counts()

    fig = px.bar(
        x=resolution_counts.index,
        y=resolution_counts.values,
        title='Resolution Type Breakdown',
        labels={'x': 'Resolution Type', 'y': 'Count'},
        color=resolution_counts.values,
        color_continuous_scale='blues'
    )

    return fig


def create_response_time_analysis(df):
    """Create response time vs satisfaction scatter plot"""
    fig = px.scatter(
        df,
        x='first_reply_time',
        y='overall_score',
        color='priority',
        size='resolution_time',
        hover_data=['ticket_id', 'subject'],
        title='Response Time vs Satisfaction Score',
        labels={
            'first_reply_time': 'First Reply Time (minutes)',
            'overall_score': 'Satisfaction Score'
        }
    )

    return fig


def create_sentiment_changes(df):
    """Create sentiment change visualization"""
    sentiment_flow = df.groupby(['sentiment_start', 'sentiment_end']).size().reset_index(name='count')

    # Create labels
    labels = list(set(df['sentiment_start'].unique().tolist() + df['sentiment_end'].unique().tolist()))
    label_dict = {label: idx for idx, label in enumerate(labels)}

    # Create source, target, value lists
    source = [label_dict[row['sentiment_start']] for _, row in sentiment_flow.iterrows()]
    target = [len(labels)//2 + label_dict[row['sentiment_end']] for _, row in sentiment_flow.iterrows()]
    value = sentiment_flow['count'].tolist()

    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=labels + labels,
        ),
        link=dict(
            source=source,
            target=target,
            value=value
        )
    )])

    fig.update_layout(title='Customer Sentiment Journey (Start → End)')

    return fig


def create_tickets_table(df):
    """Create table of recent tickets"""
    table_df = df[['ticket_id', 'subject', 'created_at', 'overall_score',
                   'issue_theme', 'resolution_type']].head(20).copy()

    table_df['created_at'] = pd.to_datetime(table_df['created_at']).dt.strftime('%Y-%m-%d %H:%M')

    return dash_table.DataTable(
        data=table_df.to_dict('records'),
        columns=[
            {'name': 'Ticket ID', 'id': 'ticket_id'},
            {'name': 'Subject', 'id': 'subject'},
            {'name': 'Created', 'id': 'created_at'},
            {'name': 'Score', 'id': 'overall_score'},
            {'name': 'Theme', 'id': 'issue_theme'},
            {'name': 'Resolution', 'id': 'resolution_type'},
        ],
        style_cell={
            'textAlign': 'left',
            'padding': '10px'
        },
        style_header={
            'backgroundColor': COLORS['primary'],
            'color': 'white',
            'fontWeight': 'bold'
        },
        style_data_conditional=[
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': COLORS['background']
            }
        ],
        page_size=10
    )


if __name__ == '__main__':
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║         Zendesk Ticket Analysis Dashboard                   ║
    ║         Dash/Plotly Visualization                            ║
    ╚══════════════════════════════════════════════════════════════╝
    """)

    print(f"\n🚀 Starting dashboard on port {Config.DASH_PORT}...")
    print(f"🔗 Dashboard URL: http://localhost:{Config.DASH_PORT}\n")

    app.run_server(
        host='0.0.0.0',
        port=Config.DASH_PORT,
        debug=True
    )
