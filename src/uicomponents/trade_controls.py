from dash import html, dcc,Input, Output, State, callback_context
from . import setup_dropdown  # modular dropdown

import dash
from src.data import update  # our new module

def render():
    """
    Returns the Trade Controls component (UI only).
    """
    return html.Div(
        className="trade-controls",
        children=[
            html.Label("TradeId:", style={"marginRight": "4px"}),
            dcc.Input(id="trade-id-input", type="number", value=6175, debounce=True, style={"width": "100px"}),

            html.Button("Fetch Data", id="fetch-button", n_clicks=0, style={"marginLeft": "4px"}),

            html.Label("Select Setup:", style={"marginLeft": "12px", "marginRight": "4px"}),
            setup_dropdown.render(),  # modular dropdown

            html.Button("Save Setup", id="save-setup-button", n_clicks=0, style={"marginLeft": "4px"}),

            html.Label("Rating:", style={"marginLeft": "12px", "marginRight": "4px"}),
            dcc.Input(id="rating-input", type="number", min=1, max=5, step=1, style={"width": "60px"}),

            html.Button("Save Rating", id="save-rating-button", n_clicks=0, style={"marginLeft": "4px"}),
        ],
    )




def register_callbacks(app, database_config):
    @app.callback(
        Output("save-status-message", "children"),
        Input("save-setup-button", "n_clicks"),
        Input("save-rating-button", "n_clicks"),
        State("trade-id-input", "value"),
        State("setup-dropdown", "value"),
        State("rating-input", "value"),
        prevent_initial_call=True,
    )
    def update_trade_callback(setup_clicks, rating_clicks, trade_id, setup, rating):
        ctx = callback_context
        if not ctx.triggered or not trade_id:
            raise dash.exceptions.PreventUpdate

        triggered = ctx.triggered[0]["prop_id"].split(".")[0]

        # Only pass the value relevant to the button clicked
        setup_value = setup if triggered == "save-setup-button" else None
        rating_value = rating if triggered == "save-rating-button" else None

        return update.update_trade(database_config, trade_id, setup_value, rating_value)