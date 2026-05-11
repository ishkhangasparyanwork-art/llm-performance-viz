import dash
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data_utils import load_data, get_model_stats, COLORS, PLOTLY_TEMPLATE

dash.register_page(__name__, path='/head-to-head', name='Head-to-Head')

ALL_MODELS = sorted(
    list(set(load_data()['model_a'].tolist()) | set(load_data()['model_b'].tolist()))
)

layout = html.Div([
    html.H2("⚔️  Head-to-Head Arena", className="mb-1 fw-bold"),
    html.P("Explore direct matchups between any two models, and uncover the tie puzzle.",
           className="text-muted mb-4"),

    # H2H selector card
    dbc.Card([
        dbc.CardHeader("🔍  Pick Two Models", className="fw-semibold"),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.Label("Model 1", className="text-muted small mb-1"),
                    dcc.Dropdown(id='h2h-model1',
                                 options=[{'label': m, 'value': m} for m in ALL_MODELS],
                                 value='gpt-4-1106-preview',
                                 clearable=False,
                                 style={"backgroundColor": "#2d2d4e"}),
                ], md=4),
                dbc.Col([
                    html.Div("VS", className="text-center fw-bold fs-3 mt-3",
                             style={"color": COLORS['accent']}),
                ], md=1, className="d-flex align-items-center justify-content-center"),
                dbc.Col([
                    html.Label("Model 2", className="text-muted small mb-1"),
                    dcc.Dropdown(id='h2h-model2',
                                 options=[{'label': m, 'value': m} for m in ALL_MODELS],
                                 value='claude-2.1',
                                 clearable=False,
                                 style={"backgroundColor": "#2d2d4e"}),
                ], md=4),
                dbc.Col([
                    html.Br(),
                    dbc.Button("Compare!", id='h2h-btn', color="primary",
                               className="w-100 mt-1", n_clicks=0),
                ], md=3),
            ]),
            html.Div(id='h2h-kpis', className="mt-3"),
        ]),
    ], className="mb-4", style={"backgroundColor": "#1a1a2e", "border": "1px solid #2d2d4e"}),

    dbc.Row([
        dbc.Col(dcc.Graph(id='h2h-bar', config={'displayModeBar': False}), md=5),
        dbc.Col(dcc.Graph(id='h2h-length-box', config={'displayModeBar': False}), md=7),
    ], className="mb-4 g-3"),

    # Dominance matrix
    dbc.Card([
        dbc.CardHeader("🗺️  Dominance Matrix — Top N Models", className="fw-semibold"),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.Label("Number of models (by battle count)", className="text-muted small mb-1"),
                    dcc.Slider(id='h2h-matrix-n', min=5, max=20, step=1, value=12,
                               marks={5:'5', 10:'10', 15:'15', 20:'20'},
                               tooltip={"placement":"bottom","always_visible":True}),
                ], md=6),
            ], className="mb-3"),
            dcc.Graph(id='h2h-matrix', config={'displayModeBar': False}),
            html.P("🟢 Green = row model wins more against column model. 🔴 Red = row model loses more.",
                   className="text-muted small mt-2 mb-0"),
        ]),
    ], className="mb-4", style={"backgroundColor": "#1a1a2e", "border": "1px solid #2d2d4e"}),

    # Tie puzzle
    dbc.Card([
        dbc.CardHeader("🤝  The Tie Puzzle", className="fw-semibold"),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.Label("Min. battles per pair", className="text-muted small mb-1"),
                    dcc.Slider(id='h2h-tie-min', min=10, max=100, step=5, value=30,
                               marks={10:'10', 30:'30', 60:'60', 100:'100'},
                               tooltip={"placement":"bottom","always_visible":True}),
                ], md=5),
                dbc.Col([
                    html.Label("Show top N pairs", className="text-muted small mb-1"),
                    dbc.Input(id='h2h-tie-topn', type='number', min=5, max=30, value=15,
                              style={"backgroundColor": "#2d2d4e", "color": "#e0e0e0",
                                     "border": "1px solid #4d4d6e"}),
                ], md=3),
            ], className="mb-3"),
            dbc.Row([
                dbc.Col(dcc.Graph(id='h2h-tie-pairs', config={'displayModeBar': False}), md=7),
                dbc.Col(dcc.Graph(id='h2h-tie-scatter', config={'displayModeBar': False}), md=5),
            ]),
        ]),
    ], style={"backgroundColor": "#1a1a2e", "border": "1px solid #2d2d4e"}),
])


# ── Callbacks ─────────────────────────────────────────────────────────────────
@callback(
    Output('h2h-kpis', 'children'),
    Output('h2h-bar', 'figure'),
    Output('h2h-length-box', 'figure'),
    Input('h2h-btn', 'n_clicks'),
    Input('h2h-model1', 'value'),
    Input('h2h-model2', 'value'),
)
def update_h2h(_n_clicks, m1, m2):
    df = load_data()
    if not m1 or not m2:
        return "", go.Figure(), go.Figure()

    mask = ((df['model_a'] == m1) & (df['model_b'] == m2)) | \
           ((df['model_a'] == m2) & (df['model_b'] == m1))
    sub = df[mask].copy()

    if len(sub) == 0:
        no_data = dbc.Alert(f"No direct battles found between {m1} and {m2}.", color="warning")
        return no_data, go.Figure(), go.Figure()

    # Normalise: count wins for each model regardless of position
    m1_wins = int(
        sub.loc[sub['model_a'] == m1, 'winner_model_a'].sum() +
        sub.loc[sub['model_b'] == m1, 'winner_model_b'].sum()
    )
    m2_wins = int(
        sub.loc[sub['model_a'] == m2, 'winner_model_a'].sum() +
        sub.loc[sub['model_b'] == m2, 'winner_model_b'].sum()
    )
    ties = int(sub['winner_tie'].sum())
    total = len(sub)

    # KPIs
    kpis = dbc.Row([
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H4(f"{total}", className="fw-bold mb-0", style={"color": COLORS['accent']}),
            html.Small("Total battles", className="text-muted"),
        ]), style={"backgroundColor": "#12122a"}), md=3),
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H4(f"{m1_wins} ({m1_wins/total:.0%})", className="fw-bold mb-0",
                    style={"color": COLORS['model_a']}),
            html.Small(m1[:22], className="text-muted"),
        ]), style={"backgroundColor": "#12122a"}), md=3),
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H4(f"{m2_wins} ({m2_wins/total:.0%})", className="fw-bold mb-0",
                    style={"color": COLORS['model_b']}),
            html.Small(m2[:22], className="text-muted"),
        ]), style={"backgroundColor": "#12122a"}), md=3),
        dbc.Col(dbc.Card(dbc.CardBody([
            html.H4(f"{ties} ({ties/total:.0%})", className="fw-bold mb-0",
                    style={"color": COLORS['tie']}),
            html.Small("Ties", className="text-muted"),
        ]), style={"backgroundColor": "#12122a"}), md=3),
    ], className="g-2")

    # Bar chart
    fig_bar = go.Figure([
        go.Bar(x=[m1[:20], m2[:20], 'Tie'],
               y=[m1_wins, m2_wins, ties],
               marker_color=[COLORS['model_a'], COLORS['model_b'], COLORS['tie']],
               hovertemplate='%{x}: %{y}<extra></extra>'),
    ])
    fig_bar.update_layout(template=PLOTLY_TEMPLATE,
                          title=f'Battle Outcomes', height=350,
                          yaxis=dict(title='Wins', gridcolor='#2d2d4e'),
                          xaxis=dict(gridcolor='#2d2d4e'))

    # Response length box
    m1_lengths, m2_lengths = [], []
    for _, row in sub.iterrows():
        if row['model_a'] == m1:
            m1_lengths.append(row['response_a_length'])
            m2_lengths.append(row['response_b_length'])
        else:
            m1_lengths.append(row['response_b_length'])
            m2_lengths.append(row['response_a_length'])

    fig_box = go.Figure([
        go.Box(y=m1_lengths, name=m1[:20], marker_color=COLORS['model_a'],
               boxmean=True),
        go.Box(y=m2_lengths, name=m2[:20], marker_color=COLORS['model_b'],
               boxmean=True),
    ])
    fig_box.update_layout(template=PLOTLY_TEMPLATE,
                          title='Response Length Distribution',
                          yaxis=dict(title='Length (chars)', gridcolor='#2d2d4e'),
                          height=350)

    return kpis, fig_bar, fig_box


@callback(
    Output('h2h-matrix', 'figure'),
    Input('h2h-matrix-n', 'value'),
)
def update_matrix(top_n):
    top_n = top_n or 12
    df = load_data()
    stats = get_model_stats(30)
    top_models = stats.nlargest(top_n, 'total')['model'].tolist()

    wins_mat  = pd.DataFrame(0.0, index=top_models, columns=top_models)
    count_mat = pd.DataFrame(0,   index=top_models, columns=top_models)

    for _, row in df.iterrows():
        a, b = row['model_a'], row['model_b']
        if a not in top_models or b not in top_models:
            continue
        count_mat.loc[a, b] += 1
        count_mat.loc[b, a] += 1
        if row['winner_model_a'] == 1:
            wins_mat.loc[a, b] += 1
        elif row['winner_model_b'] == 1:
            wins_mat.loc[b, a] += 1

    wr_matrix = (wins_mat / count_mat.replace(0, np.nan)).round(2)

    fig = go.Figure(go.Heatmap(
        z=wr_matrix.values,
        x=wr_matrix.columns.tolist(),
        y=wr_matrix.index.tolist(),
        colorscale='RdYlGn', zmid=0.5, zmin=0, zmax=1,
        hovertemplate='<b>%{y}</b> vs <b>%{x}</b><br>Win Rate: %{z:.0%}<extra></extra>',
        colorbar=dict(title='Win Rate'),
    ))
    fig.update_layout(template=PLOTLY_TEMPLATE,
                      title=f'Head-to-Head Win Rate Matrix (Top {top_n})',
                      xaxis=dict(tickangle=-40, title='Opponent'),
                      yaxis=dict(title='Model'),
                      height=520)
    return fig


@callback(
    Output('h2h-tie-pairs', 'figure'),
    Output('h2h-tie-scatter', 'figure'),
    Input('h2h-tie-min', 'value'),
    Input('h2h-tie-topn', 'value'),
)
def update_ties(min_battles, top_n):
    df = load_data()
    top_n = top_n or 15
    min_battles = min_battles or 20

    pair_stats = df.groupby('unordered_pair').agg(
        total=('winner_tie', 'count'), ties=('winner_tie', 'sum')
    ).reset_index()
    pair_stats['tie_rate'] = pair_stats['ties'] / pair_stats['total']
    pair_stats = pair_stats[pair_stats['total'] >= min_battles]

    top_pairs = pair_stats.nlargest(top_n, 'tie_rate').sort_values('tie_rate')

    fig_pairs = go.Figure(go.Bar(
        y=top_pairs['unordered_pair'], x=top_pairs['tie_rate'],
        orientation='h',
        marker=dict(color=top_pairs['tie_rate'], colorscale='Teal', showscale=True),
        customdata=top_pairs['total'],
        hovertemplate='<b>%{y}</b><br>Tie Rate: %{x:.1%}<br>Battles: %{customdata}<extra></extra>',
    ))
    fig_pairs.update_layout(template=PLOTLY_TEMPLATE,
                            title=f'Top {top_n} Pairs by Tie Rate',
                            xaxis=dict(title='Tie Rate', tickformat='.0%', gridcolor='#2d2d4e'),
                            yaxis=dict(title=''),
                            height=420)

    # Tie rate vs win rate scatter
    stats = get_model_stats(30)
    fig_sc = px.scatter(stats, x='tie_rate', y='win_rate', size='total',
                        hover_name='model', color='total', color_continuous_scale='Plasma',
                        labels={'tie_rate': 'Tie Rate', 'win_rate': 'Win Rate', 'total': 'Battles'},
                        title='Tie Rate vs Win Rate')
    fig_sc.update_layout(template=PLOTLY_TEMPLATE, height=420,
                         xaxis=dict(tickformat='.0%', gridcolor='#2d2d4e'),
                         yaxis=dict(tickformat='.0%', gridcolor='#2d2d4e'))

    return fig_pairs, fig_sc