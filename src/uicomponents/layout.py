from dash import Dash, html, dcc
from src.uicomponents import (
    trade_controls,
    daily_chart,
    min30_chart,
    intraday_chart,
    trade_info,
    trades_table,
)

def create_layout(app: Dash, database_config: dict) -> html.Div:
    """
    Create the main layout for the Trade Viewer dashboard.
    Combines multiple chart and control components into a cohesive structure.
    """

    # --- Register callbacks ---
    trade_controls.register_callbacks(app, database_config)
    trade_info.register_callbacks(app, database_config)
    daily_chart.register_daily_chart_callback(app, database_config)
    min30_chart.register_30min_chart_callback(app, database_config)
    intraday_chart.register_intraday_chart_callback(app, database_config)
    trades_table.register_callbacks(app, database_config)

    # --- Instantiate components ---
    trade_controls_component = trade_controls.render()
    trade_header_component = trade_info.render()
    trade_table_component = trades_table.render()

    # --- Top Chart Row: Daily + 30min ---
    top_chart_row = html.Div(
        [
            dcc.Graph(id="daily-chart", style={"height": "600px", "width": "100%"}),
            dcc.Graph(id="chart30mins", style={"height": "600px", "width": "100%"}),
        ],
        style={
            "display": "flex",
            "justifyContent": "center",
            "alignItems": "stretch",
            "gap": "5px",
        },
    )

    # --- Trade Section (header + controls + table) ---
    trade_section = html.Div(
        [
            trade_header_component,
            trade_controls_component,
            trade_table_component,
        ],
        className="trade-section",
        style={
            "width": "100%",
            "padding": "5px",
            "boxSizing": "border-box",
        },
    )

    # --- Bottom Row: Intraday Chart + Trade Section ---
    bottom_row = html.Div(
        [
            html.Div(
                dcc.Graph(id="intraday-chart", style={"height": "600px", "width": "100%"}),
                style={
                    "flex": "1",
                    "padding": "5px",
                    "boxSizing": "border-box",
                },
            ),
            html.Div(
                trade_section,
                style={
                    "flex": "1",
                    "padding": "5px",
                    "boxSizing": "border-box",
                },
            ),
        ],
        style={
            "display": "flex",
            "justifyContent": "center",
            "alignItems": "stretch",
            "gap": "5px",
            "marginTop": "5px",
        },
    )

    # --- Status & Error Messages ---
    status_display = html.Div(
        [
            html.Div(id="relative-volume-display", style={"fontSize": 20, "textAlign": "left"}),
            html.Div(id="save-status-message", style={"color": "green", "marginTop": "4px"}),
            html.Div(id="error-message", style={"color": "red", "marginTop": "4px"}),
        ]
    )

    # --- Full Layout ---
    return html.Div(
        className="app-div",
        children=[
            html.H1(app.title),
            status_display,
            top_chart_row,
            bottom_row,
        ],
    )
