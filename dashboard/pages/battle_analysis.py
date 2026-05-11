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

dash.register_page(__name__, path='/battle-analysis', name='Battle Analysis')

layout = html.Div([
    html.H2("📊 Battle Analysis", className="mb-1 fw-bold"),
    html.P("Does response length determine the winner? Is there a position bias?",
           className="text-muted mb-4"),

    # Section 1: Length
    dbc.Card([
        dbc.CardHeader([
            html.Span("⚖️  The Length Question", className="fw-semibold fs-5"),
            html.Small(" — Does longer always win?", className="text-muted ms-2"),
        ]),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.Label("Minimum battles per category", className="text-muted small mb-1"),
                    dcc.Slider(id='ba-min-count', min=10, max=500, step=10, value=50,
                               marks={10:'10', 100:'100', 500:'500'},
                               tooltip={"placement":"bottom","always_visible":True}),
                ], md=6),
            ], className="mb-3"),
            dbc.Row([
                dbc.Col(dcc.Graph(id='ba-length-bar', config={'displayModeBar': False}), md=7),
                dbc.Col(dcc.Graph(id='ba-length-scatter', config={'displayModeBar': False}), md=5),
            ]),
            dbc.Alert(id='ba-length-insight', color="info", className="mt-3 mb-0",
                      style={"backgroundColor": "#1a2a3a", "border": "1px solid #2a5a8a", "color": "#cce5ff"}),
        ]),
    ], className="mb-4", style={"backgroundColor": "#1a1a2e", "border": "1px solid #2d2d4e"}),

    # Section 2: Position Bias
    dbc.Card([
        dbc.CardHeader([
            html.Span("🔀  Position Bias Check", className="fw-semibold fs-5"),
            html.Small(" — Does slot A or B give an edge?", className="text-muted ms-2"),
        ]),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.Label("Min. appearances per position", className="text-muted small mb-1"),
                    dcc.Slider(id='ba-pos-min', min=10, max=200, step=10, value=50,
                               marks={10:'10',50:'50',100:'100',200:'200'},
                               tooltip={"placement":"bottom","always_visible":True}),
                ], md=5),
                dbc.Col([
                    html.Label("Highlight model (optional)", className="text-muted small mb-1"),
                    dcc.Dropdown(id='ba-highlight-model', placeholder="Select a model...",
                                 style={"backgroundColor": "#2d2d4e", "color": "#fff"},
                                 clearable=True),
                ], md=5),
            ], className="mb-3"),
            dcc.Graph(id='ba-position-scatter', config={'displayModeBar': False}),
            dbc.Alert(id='ba-position-insight', color="info", className="mt-3 mb-0",
                      style={"backgroundColor": "#1a2a3a", "border": "1px solid #2a5a8a", "color": "#cce5ff"}),
        ]),
    ], style={"backgroundColor": "#1a1a2e", "border": "1px solid #2d2d4e"}),
])


# ── Callbacks ─────────────────────────────────────────────────────────────────
@callback(
    Output('ba-highlight-model', 'options'),
    Input('ba-pos-min', 'value'),
)
def populate_model_dropdown(min_battles):
    stats = get_model_stats(min_battles or 30)
    models = sorted(stats['model'].tolist())
    return [{'label': m, 'value': m} for m in models]


@callback(
    Output('ba-length-bar', 'figure'),
    Output('ba-length-scatter', 'figure'),
    Output('ba-length-insight', 'children'),
    Input('ba-min-count', 'value'),
)
def update_length(min_count):
    df = load_data()

    length_analysis = df.groupby('length_category', observed=True).agg(
        count=('winner_model_a', 'count'),
        a_win_rate=('winner_model_a', 'mean'),
        b_win_rate=('winner_model_b', 'mean'),
        tie_rate=('winner_tie', 'mean'),
    ).reset_index()
    length_analysis = length_analysis[length_analysis['count'] >= (min_count or 10)]

    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(x=length_analysis['length_category'], y=length_analysis['a_win_rate'],
                             name='Model A Wins', marker_color=COLORS['model_a'],
                             hovertemplate='%{x}<br>Model A: %{y:.1%}<extra></extra>'))
    fig_bar.add_trace(go.Bar(x=length_analysis['length_category'], y=length_analysis['b_win_rate'],
                             name='Model B Wins', marker_color=COLORS['model_b'],
                             hovertemplate='%{x}<br>Model B: %{y:.1%}<extra></extra>'))
    fig_bar.add_trace(go.Bar(x=length_analysis['length_category'], y=length_analysis['tie_rate'],
                             name='Tie', marker_color=COLORS['tie'],
                             hovertemplate='%{x}<br>Tie: %{y:.1%}<extra></extra>'))
    fig_bar.update_layout(template=PLOTLY_TEMPLATE, barmode='stack', height=380,
                          title='Outcome Rate by Relative Response Length',
                          xaxis_title='Response A length vs Response B',
                          yaxis=dict(title='Outcome Rate', tickformat='.0%', gridcolor='#2d2d4e'),
                          legend=dict(orientation='h', y=1.08))

    # Scatter: avg length vs win rate
    stats = get_model_stats(50)
    fig_sc = px.scatter(
        stats, x='avg_length', y='win_rate', size='total',
        hover_name='model', color='win_rate',
        color_continuous_scale='Viridis',
        labels={'avg_length': 'Avg Length (chars)', 'win_rate': 'Win Rate'},
        title='Avg Response Length vs Win Rate',
    )
    z = np.polyfit(stats['avg_length'], stats['win_rate'], 1)
    x_line = np.linspace(stats['avg_length'].min(), stats['avg_length'].max(), 100)
    fig_sc.add_trace(go.Scatter(x=x_line, y=np.polyval(z, x_line),
                                mode='lines', line=dict(color='red', dash='dash'), name='Trend'))
    fig_sc.update_layout(template=PLOTLY_TEMPLATE, height=380,
                         yaxis=dict(tickformat='.0%', gridcolor='#2d2d4e'),
                         xaxis=dict(gridcolor='#2d2d4e'))


    corr = stats['avg_length'].corr(stats['win_rate'])
    insight = f"💡 Correlation between avg response length and win rate: r = {corr:.3f}. " \
              + ("Moderate positive correlation — longer models tend to win more." if abs(corr) > 0.3
                 else "Weak correlation — model identity matters more than length alone.")

    return fig_bar, fig_sc, insight


@callback(
    Output('ba-position-scatter', 'figure'),
    Output('ba-position-insight', 'children'),
    Input('ba-pos-min', 'value'),
    Input('ba-highlight-model', 'value'),
)
def update_position(min_val, highlight):
    df = load_data()
    min_val = min_val or 30

    win_a = df.groupby('model_a')['winner_model_a'].agg(['mean','count']).rename(
        columns={'mean':'win_rate_A','count':'n_A'})
    win_b = df.groupby('model_b')['winner_model_b'].agg(['mean','count']).rename(
        columns={'mean':'win_rate_B','count':'n_B'})

    pos_df = win_a.join(win_b, how='inner')
    pos_df = pos_df[(pos_df['n_A'] >= min_val) & (pos_df['n_B'] >= min_val)].copy()
    pos_df['bias'] = pos_df['win_rate_A'] - pos_df['win_rate_B']
    pos_df = pos_df.reset_index().rename(columns={'index':'model', 'model_a':'model'})
    if 'model' not in pos_df.columns:
        pos_df = pos_df.rename(columns={pos_df.columns[0]: 'model'})

    colors = [COLORS['accent'] if (highlight and row['model'] == highlight) else COLORS['model_a']
              for _, row in pos_df.iterrows()]
    sizes = [18 if (highlight and row['model'] == highlight) else 10
             for _, row in pos_df.iterrows()]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=pos_df['win_rate_A'], y=pos_df['win_rate_B'],
        mode='markers+text',
        marker=dict(size=sizes, color=colors, opacity=0.8,
                    line=dict(width=1, color='#333')),
        text=pos_df['model'],
        textposition='top center',
        textfont=dict(size=9),
        hovertemplate='<b>%{text}</b><br>Win A: %{x:.1%}<br>Win B: %{y:.1%}<extra></extra>',
        showlegend=False,
    ))

    # Diagonal
    lim = [0, 0.75]
    fig.add_shape(type='line', x0=lim[0], y0=lim[0], x1=lim[1], y1=lim[1],
                  line=dict(color='gray', dash='dash'))

    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        title='Position Bias: Win Rate in Slot A vs Slot B',
        xaxis=dict(title='Win Rate — Position A', tickformat='.0%', gridcolor='#2d2d4e', range=lim),
        yaxis=dict(title='Win Rate — Position B', tickformat='.0%', gridcolor='#2d2d4e', range=lim),
        height=480,
    )

    most_biased = pos_df.loc[pos_df['bias'].abs().idxmax(), 'model']
    bias_val = pos_df.loc[pos_df['bias'].abs().idxmax(), 'bias']
    insight = (f"💡 Most models cluster around the diagonal — position has minimal systematic effect. "
               f"Largest outlier: '{most_biased}' with a {bias_val:+.1%} A-vs-B bias.")

    return fig, insight