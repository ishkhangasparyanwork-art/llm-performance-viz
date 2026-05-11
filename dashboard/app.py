import dash
from dash import Dash, html, dcc
import dash_bootstrap_components as dbc

app = Dash(
    __name__,
    use_pages=True,
    external_stylesheets=[dbc.themes.DARKLY, dbc.icons.BOOTSTRAP],
    suppress_callback_exceptions=True,
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)

app.title = "The AI Arena"

SIDEBAR = dbc.Nav(
    [
        html.Div(
            [
                html.Div("⚔️", style={"fontSize": "2rem", "textAlign": "center"}),
                html.H5("The AI Arena", className="text-center fw-bold mt-1 mb-0",
                        style={"color": "#636EFA"}),
                html.P("LMSYS Chatbot Arena", className="text-center text-muted mb-3",
                       style={"fontSize": "0.75rem"}),
            ],
            className="py-3 border-bottom border-secondary",
        ),
        dbc.NavLink(
            [html.I(className="bi bi-trophy me-2"), "Leaderboard"],
            href="/",
            active="exact",
            className="nav-link-custom",
        ),
        dbc.NavLink(
            [html.I(className="bi bi-bar-chart-line me-2"), "Battle Analysis"],
            href="/battle-analysis",
            active="exact",
            className="nav-link-custom",
        ),
        dbc.NavLink(
            [html.I(className="bi bi-grid-3x3 me-2"), "Head-to-Head"],
            href="/head-to-head",
            active="exact",
            className="nav-link-custom",
        ),
        dbc.NavLink(
            [html.I(className="bi bi-people me-2"), "Model Explorer"],
            href="/model-explorer",
            active="exact",
            className="nav-link-custom",
        ),
        html.Hr(className="border-secondary"),
        html.Div(
            [
                html.Small("57,477 battles", className="text-muted d-block text-center"),
                html.Small("52 AI models", className="text-muted d-block text-center"),
            ],
            className="mt-2",
        ),
    ],
    vertical=True,
    pills=True,
    className="flex-column px-2",
)

app.layout = html.Div(
    [
        dcc.Store(id="model-data-store"),
        # Sidebar
        html.Div(
            SIDEBAR,
            style={
                "position": "fixed",
                "top": 0,
                "left": 0,
                "bottom": 0,
                "width": "220px",
                "backgroundColor": "#1a1a2e",
                "borderRight": "1px solid #333",
                "overflowY": "auto",
                "zIndex": 1000,
            },
        ),
        # Main content
        html.Div(
            dash.page_container,
            style={
                "marginLeft": "220px",
                "padding": "1.5rem",
                "minHeight": "100vh",
                "backgroundColor": "#0f0f1a",
            },
        ),
    ]
)

if __name__ == "__main__":
    app.run(debug=True, port=8050)