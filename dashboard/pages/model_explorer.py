import dash
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import sys, os

# Ensure we can import from parent directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data_utils import load_data, get_model_stats, COLORS, PLOTLY_TEMPLATE

dash.register_page(__name__, path='/model-explorer', name='Model Explorer')

# Get initial list of models
df_init = load_data()
ALL_MODELS = sorted(list(set(df_init['model_a']) | set(df_init['model_b'])))

layout = html.Div([
    html.Div([
        html.H2("🔍 Model Explorer", className="mb-1 fw-bold"),
        html.P("Deep dive into specific model performance and response characteristics.",
               className="text-muted mb-4"),
    ]),

    # Selection Card
    dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.Label("Select Model to Analyze", className="text-muted small mb-2"),
                    dcc.Dropdown(
                        id='me-model-select',
                        options=[{'label': m, 'value': m} for m in ALL_MODELS],
                        value='gpt-4-1106-preview',
                        clearable=False,
                        style={"backgroundColor": "#2d2d4e", "color": "#fff"},
                        className="dark-dropdown",
                    ),
                ], md=6),
                dbc.Col([
                    html.Label("Filter by Minimum Battle Count", className="text-muted small mb-2"),
                    dcc.Slider(
                        id='me-min-battles',
                        min=0, max=200, step=10, value=20,
                        marks={0:'0', 100:'100', 200:'200'},
                        tooltip={"placement": "bottom", "always_visible": True},
                    ),
                ], md=6),
            ]),
        ])
    ], className="mb-4", style={"backgroundColor": "#1a1a2e", "border": "1px solid #2d2d4e"}),

    # KPI Row
    html.Div(id='me-kpis', className="mb-4"),

    # Charts Row 1
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Outcome Distribution", className="fw-semibold"),
                dbc.CardBody([dcc.Graph(id='me-outcome-pie', config={'displayModeBar': False})]),
            ], style={"backgroundColor": "#1a1a2e", "border": "1px solid #2d2d4e"}),
        ], md=4),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Response Length vs. Arena Average", className="fw-semibold"),
                dbc.CardBody([dcc.Graph(id='me-length-dist', config={'displayModeBar': False})]),
            ], style={"backgroundColor": "#1a1a2e", "border": "1px solid #2d2d4e"}),
        ], md=8),
    ], className="mb-4 g-3"),

    # Charts Row 2
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Win Rate Against Top Opponents", className="fw-semibold"),
                dbc.CardBody([dcc.Graph(id='me-opponents-bar', config={'displayModeBar': False})]),
            ], style={"backgroundColor": "#1a1a2e", "border": "1px solid #2d2d4e"}),
        ], md=12),
    ], className="g-3"),
])

# ── Callbacks ─────────────────────────────────────────────────────────────────

@callback(
    Output('me-kpis', 'children'),
    Output('me-outcome-pie', 'figure'),
    Output('me-length-dist', 'figure'),
    Output('me-opponents-bar', 'figure'),
    Input('me-model-select', 'value'),
    Input('me-min-battles', 'value'),
)
def update_model_explorer(selected_model, min_battles):
    df = load_data()
    stats = get_model_stats(0) # Get all to find our model
    
    # Filter stats for specific model
    m_stats = stats[stats['model'] == selected_model].iloc[0]
    
    # 1. KPIs
    kpis = dbc.Row([
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H4(f"{int(m_stats['total']):,}", className="fw-bold mb-0", style={"color": COLORS['accent']}),
            html.Small("Total Battles", className="text-muted"),
        ]), style={"backgroundColor": "#12122a"}), md=3),
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H4(f"{m_stats['win_rate']:.1%}", className="fw-bold mb-0", style={"color": COLORS['model_a']}),
            html.Small("Win Rate", className="text-muted"),
        ]), style={"backgroundColor": "#12122a"}), md=3),
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H4(f"{int(m_stats['avg_length']):,}", className="fw-bold mb-0", style={"color": COLORS['tie']}),
            html.Small("Avg Response (chars)", className="text-muted"),
        ]), style={"backgroundColor": "#12122a"}), md=3),
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H4(f"{m_stats['tie_rate']:.1%}", className="fw-bold mb-0", style={"color": "#fff"}),
            html.Small("Tie Rate", className="text-muted"),
        ]), style={"backgroundColor": "#12122a"}), md=3),
    ], className="g-2")

    # 2. Outcome Pie
    fig_pie = go.Figure(go.Pie(
        labels=['Wins', 'Ties', 'Losses'],
        values=[m_stats['wins'], m_stats['ties'], m_stats['total'] - m_stats['wins'] - m_stats['ties']],
        hole=0.6,
        marker_colors=[COLORS['model_a'], COLORS['tie'], COLORS['model_b']],
        textinfo='percent',
    ))
    fig_pie.update_layout(template=PLOTLY_TEMPLATE, height=300, margin=dict(t=20, b=20, l=20, r=20),
                          legend=dict(orientation='h', y=-0.1))

    # 3. Length Distribution (Box plot)
    # Get lengths for this model vs all others
    m_lengths = pd.concat([
        df[df['model_a'] == selected_model]['response_a_length'],
        df[df['model_b'] == selected_model]['response_b_length']
    ])
    others_lengths = pd.concat([
        df[df['model_a'] != selected_model]['response_a_length'],
        df[df['model_b'] != selected_model]['response_b_length']
    ])
    
    fig_len = go.Figure()
    fig_len.add_trace(go.Box(y=others_lengths, name="Arena Average", marker_color="#666", opacity=0.5))
    fig_len.add_trace(go.Box(y=m_lengths, name=selected_model, marker_color=COLORS['accent']))
    fig_len.update_layout(template=PLOTLY_TEMPLATE, height=300, title="Response Length Comparison",
                          yaxis=dict(gridcolor='#2d2d4e', title="Characters"))

    # 4. Opponents Bar Chart
    # Find battles where this model participated
    opp_df = df[(df['model_a'] == selected_model) | (df['model_b'] == selected_model)].copy()
    opp_df['opponent'] = opp_df.apply(lambda r: r['model_b'] if r['model_a'] == selected_model else r['model_a'], axis=1)
    opp_df['is_win'] = opp_df.apply(lambda r: 1 if (r['model_a'] == selected_model and r['winner_model_a'] == 1) or 
                                               (r['model_b'] == selected_model and r['winner_model_b'] == 1) else 0, axis=1)
    
    opp_stats = opp_df.groupby('opponent').agg(
        battles=('is_win', 'count'),
        win_rate=('is_win', 'mean')
    ).reset_index()
    
    opp_stats = opp_stats[opp_stats['battles'] >= (min_battles or 5)].sort_values('win_rate', ascending=False).head(10)
    
    fig_opp = go.Figure(go.Bar(
        x=opp_stats['win_rate'],
        y=opp_stats['opponent'],
        orientation='h',
        marker=dict(
            color=opp_stats['win_rate'],
            colorscale='RdYlGn',
            showscale=False  # Set to True if you want a color bar on the side
        ),
        hovertemplate='Opponent: %{y}<br>Win Rate: %{x:.1%}<extra></extra>'
    ))
    fig_opp.update_layout(template=PLOTLY_TEMPLATE, height=400, 
                          title=f"Top 10 Matchups for {selected_model}",
                          xaxis=dict(title="Win Rate", tickformat=".0%", range=[0,1]),
                          yaxis=dict(autorange="reversed"))

    return kpis, fig_pie, fig_len, fig_opp