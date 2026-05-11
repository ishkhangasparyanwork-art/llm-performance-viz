import dash
from dash import html, dcc, callback, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data_utils import load_data, get_model_stats, COLORS, PLOTLY_TEMPLATE

dash.register_page(__name__, path='/', name='Leaderboard', title='Leaderboard – AI Arena')

# ── Layout ────────────────────────────────────────────────────────────────────
layout = html.Div([
    # Header
    html.Div([
        html.H2("🏆 Arena Leaderboard", className="mb-1 fw-bold"),
        html.P("Who dominates the AI Arena? Ranked by win rate across all battles.",
               className="text-muted mb-0"),
    ], className="mb-4"),

    # KPI row
    dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H3("57,477", className="fw-bold mb-0", style={"color": COLORS['model_a']}),
                html.Small("Total Battles", className="text-muted"),
            ])
        ], className="text-center border-0", style={"backgroundColor": "#1a1a2e"})), 
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H3("52", className="fw-bold mb-0", style={"color": COLORS['tie']}),
                html.Small("Unique Models", className="text-muted"),
            ])
        ], className="text-center border-0", style={"backgroundColor": "#1a1a2e"})),
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H3("~35%", className="fw-bold mb-0", style={"color": COLORS['model_b']}),
                html.Small("Avg Win Rate", className="text-muted"),
            ])
        ], className="text-center border-0", style={"backgroundColor": "#1a1a2e"})),
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H3("30.9%", className="fw-bold mb-0", style={"color": COLORS['accent']}),
                html.Small("Tie Rate", className="text-muted"),
            ])
        ], className="text-center border-0", style={"backgroundColor": "#1a1a2e"})),
    ], className="mb-4 g-3"),

    # Controls row
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.Label("Min. Battles", className="text-light small mb-2"),
                            dcc.Slider(
                                id='lb-min-battles',
                                min=10, max=500, step=10, value=100,
                                marks={10: '10', 100: '100', 250: '250', 500: '500'},
                                tooltip={"placement": "bottom", "always_visible": False},
                            ),
                        ], md=6),
                        dbc.Col([
                            html.Label("Sort by", className="text-light small mb-2"),
                            dcc.Dropdown(
                                id='lb-sort-by',
                                options=[
                                    {'label': 'Win Rate', 'value': 'win_rate'},
                                    {'label': 'Total Battles', 'value': 'total'},
                                    {'label': 'Tie Rate', 'value': 'tie_rate'},
                                    {'label': 'Loss Rate', 'value': 'loss_rate'},
                                ],
                                value='win_rate',
                                clearable=False,
                                className="dbc", # This class helps some themes
                            ),
                        ], md=3),
                        dbc.Col([
                            html.Label("Show top N", className="text-light small mb-2"),
                            dbc.Input(
                                id='lb-top-n',
                                type='number', min=5, max=52, step=1, value=20,
                            ),
                        ], md=3),
                    ]),
                ])
            ], style={"backgroundColor": "#1a1a2e", "border": "1px solid #2d2d4e"}),
        ])
    ], className="mb-4"),

    # Charts
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Win / Tie / Loss Breakdown", className="fw-semibold"),
                dbc.CardBody([dcc.Graph(id='lb-stacked-bar', config={'displayModeBar': False})]),
            ], style={"backgroundColor": "#1a1a2e", "border": "1px solid #2d2d4e"}),
        ], md=8),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Overall Outcome Distribution", className="fw-semibold"),
                dbc.CardBody([dcc.Graph(id='lb-donut', config={'displayModeBar': False})]),
            ], style={"backgroundColor": "#1a1a2e", "border": "1px solid #2d2d4e"}),
        ], md=4),
    ], className="mb-4 g-3"),

    # Table card
    dbc.Card([
        dbc.CardHeader("Full Leaderboard Table", className="fw-semibold"),
        dbc.CardBody([html.Div(id='lb-table')]),
    ], style={"backgroundColor": "#1a1a2e", "border": "1px solid #2d2d4e"}),
])


# ── Callbacks ─────────────────────────────────────────────────────────────────
@callback(
    Output('lb-stacked-bar', 'figure'),
    Output('lb-donut', 'figure'),
    Output('lb-table', 'children'),
    Input('lb-min-battles', 'value'),
    Input('lb-sort-by', 'value'),
    Input('lb-top-n', 'value'),
)
def update_leaderboard(min_battles, sort_by, top_n):
    # Default values if input is deleted by user
    if min_battles is None: min_battles = 100
    if top_n is None: top_n = 20
    if not sort_by: sort_by = 'win_rate'
    
    stats = get_model_stats(min_battles or 50)
    filtered = stats.nlargest(top_n, sort_by).sort_values(sort_by)

    # ── Stacked bar ──
    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(
        y=filtered['model'], x=filtered['win_rate'], orientation='h',
        name='Win', marker_color=COLORS['model_a'],
        hovertemplate='<b>%{y}</b><br>Win: %{x:.1%}<extra></extra>'
    ))
    fig_bar.add_trace(go.Bar(
        y=filtered['model'], x=filtered['tie_rate'], orientation='h',
        name='Tie', marker_color=COLORS['tie'],
        hovertemplate='<b>%{y}</b><br>Tie: %{x:.1%}<extra></extra>'
    ))
    fig_bar.add_trace(go.Bar(
        y=filtered['model'], x=filtered['loss_rate'], orientation='h',
        name='Loss', marker_color=COLORS['model_b'],
        hovertemplate='<b>%{y}</b><br>Loss: %{x:.1%}<extra></extra>'
    ))
    fig_bar.update_layout(
        template=PLOTLY_TEMPLATE,
        barmode='stack', height=max(350, len(filtered) * 28),
        xaxis=dict(title='Rate', tickformat='.0%', gridcolor='#2d2d4e'),
        yaxis=dict(title=''),
        legend=dict(orientation='h', y=1.05),
        margin=dict(t=30, r=20, b=30, l=10),
    )

    # ── Donut ──
    df = load_data()
    wc = {
        'Model A Wins': int(df['winner_model_a'].sum()),
        'Model B Wins': int(df['winner_model_b'].sum()),
        'Tie':          int(df['winner_tie'].sum()),
    }
    total = sum(wc.values())
    fig_donut = go.Figure(go.Pie(
        labels=list(wc.keys()),
        values=list(wc.values()),
        hole=0.6,
        marker_colors=[COLORS['model_a'], COLORS['model_b'], COLORS['tie']],
        textinfo='label+percent',
        hovertemplate='%{label}: %{value:,}<extra></extra>',
    ))
    fig_donut.add_annotation(
        text=f'<b>{total:,}</b><br>battles',
        x=0.5, y=0.5, font_size=14, showarrow=False,
        font_color='#e0e0e0'
    )
    fig_donut.update_layout(
        template=PLOTLY_TEMPLATE,  # Use the template object here
        height=350,
        legend=dict(orientation='h', y=-0.1),
        margin=dict(t=10, b=10, l=10, r=10),
    )

    # ── Table ──
    tbl_df = stats.nlargest(top_n, sort_by).copy()
    tbl_df = tbl_df.sort_values(sort_by, ascending=False).reset_index(drop=True)
    tbl_df.index += 1

    rows = []
    for rank, row in tbl_df.iterrows():
        medal = {1: '🥇', 2: '🥈', 3: '🥉'}.get(rank, str(rank))
        rows.append(html.Tr([
            html.Td(medal),
            html.Td(row['model'], style={"fontWeight": "600"}),
            html.Td(f"{row['win_rate']:.1%}", style={"color": COLORS['model_a']}),
            html.Td(f"{row['tie_rate']:.1%}", style={"color": COLORS['tie']}),
            html.Td(f"{row['loss_rate']:.1%}", style={"color": COLORS['model_b']}),
            html.Td(f"{int(row['total']):,}"),
            html.Td(f"{int(row['avg_length']):,} chars"),
        ]))

    table = dbc.Table(
        [
            html.Thead(html.Tr([
                html.Th("#"), html.Th("Model"), html.Th("Win Rate"),
                html.Th("Tie Rate"), html.Th("Loss Rate"),
                html.Th("Battles"), html.Th("Avg Response"),
            ])),
            html.Tbody(rows),
        ],
        bordered=False, hover=True, responsive=True,
        style={"fontSize": "0.875rem"},
        className="table-dark",
    )

    return fig_bar, fig_donut, table