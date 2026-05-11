import pandas as pd
import numpy as np
from functools import lru_cache
from pathlib import Path

# Resolve the data file relative to this module regardless of where the
# Python process is launched from.
_DATA_PATH = Path(__file__).resolve().parent.parent / 'lmsys-chatbot-arena' / 'train.csv'

COLORS = {
    'model_a': '#636EFA',
    'model_b': '#EF553B',
    'tie':     '#00CC96',
    'accent':  '#FFA15A',
    'neutral': '#AB63FA',
    'bg':      '#0f0f1a',
    'card':    '#1a1a2e',
    'border':  '#2d2d4e',
}

PLOTLY_TEMPLATE = dict(
    layout=dict(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#e0e0e0', family='Inter, sans-serif'),
        colorway=[COLORS['model_a'], COLORS['model_b'], COLORS['tie'], COLORS['accent'], COLORS['neutral']],
        xaxis=dict(gridcolor='#2d2d4e', linecolor='#2d2d4e', zerolinecolor='#2d2d4e'),
        yaxis=dict(gridcolor='#2d2d4e', linecolor='#2d2d4e', zerolinecolor='#2d2d4e'),
        legend=dict(bgcolor='rgba(0,0,0,0)', bordercolor='#2d2d4e'),
        margin=dict(t=50, r=20, b=40, l=20),
    )
)

@lru_cache(maxsize=1)
def load_data():
    df = pd.read_csv(_DATA_PATH)

    # Derived columns
    df['response_a_length'] = df['response_a'].str.len()
    df['response_b_length'] = df['response_b'].str.len()
    df['prompt_length']     = df['prompt'].str.len()
    df['length_ratio']      = df['response_a_length'] / (df['response_b_length'] + 1)
    df['unordered_pair']    = df.apply(
        lambda r: ' vs '.join(sorted([r['model_a'], r['model_b']])), axis=1
    )

    bins   = [0, 0.5, 0.75, 1.0, 1.33, 2.0, 100]
    labels = ['A much shorter', 'A shorter', 'Similar', 'A slightly longer', 'A longer', 'A much longer']
    df['length_category'] = pd.cut(df['length_ratio'], bins=bins, labels=labels)

    return df


@lru_cache(maxsize=1)
def get_model_stats(min_battles=50):
    df = load_data()
    records = []
    for _, row in df.iterrows():
        records.append({'model': row['model_a'], 'won': row['winner_model_a'], 'tied': row['winner_tie']})
        records.append({'model': row['model_b'], 'won': row['winner_model_b'], 'tied': row['winner_tie']})

    perf = pd.DataFrame(records)
    stats = perf.groupby('model').agg(
        total=('won', 'count'),
        wins=('won', 'sum'),
        ties=('tied', 'sum')
    ).reset_index()

    stats['win_rate']  = stats['wins']  / stats['total']
    stats['tie_rate']  = stats['ties']  / stats['total']
    stats['loss_rate'] = 1 - stats['win_rate'] - stats['tie_rate']

    # Average response length per model
    df2 = load_data()
    lengths = []
    for model in stats['model']:
        as_a = df2[df2['model_a'] == model]['response_a_length']
        as_b = df2[df2['model_b'] == model]['response_b_length']
        combined = pd.concat([as_a, as_b])
        lengths.append({'model': model, 'avg_length': combined.mean(), 'median_length': combined.median()})
    len_df = pd.DataFrame(lengths)
    stats  = stats.merge(len_df, on='model')

    return stats[stats['total'] >= min_battles].copy()