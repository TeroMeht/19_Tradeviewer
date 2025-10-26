from dash import html, dash_table, Input, Output, State, no_update
from src.data.db_functions import get_connection_and_cursor, fetch_trades_with_rvol

def generate_table(dataframe, max_rows=15):
    """
    Generate a clean DataTable styled entirely through external CSS.
    """
    return dash_table.DataTable(
        id='trade-table',
        columns=[{"name": i, "id": i} for i in dataframe.columns],
        data=dataframe.to_dict('records'),
        sort_action='native',
        page_size=max_rows,
        page_action='native',
        fixed_rows={'headers': True},
        persistence=True,
        persistence_type='session',
        persisted_props=['page_current', 'sort_by', 'filter_query'],
        style_as_list_view=True,
        
    )


# --- Render function ---
def render():
    """
    Returns the placeholder Div for the trade table.
    The content will be updated via callback.
    """
    return html.Div(
        id="trade-data-table",
        children=[
            dash_table.DataTable(
                id="trade-table",
                columns=[],
                data=[],
                style_table={"overflowX": "auto"},
            )
        ],
        style={"width": "95%", "padding": "20px"}
    )


def register_callbacks(app, database_config):
    """
    Updates the trade table when the Fetch Data button is clicked or trade-id changes.
    """
    @app.callback(
        Output("trade-data-table", "children"),
        Input("fetch-button", "n_clicks"),
        State("trade-id-input", "value"),
    )
    def update_trade_table(n_clicks, trade_id):
        if not trade_id:
            return no_update

        conn, cur = get_connection_and_cursor(database_config)
        try:
            df_rvol_trades = fetch_trades_with_rvol(cur, "trades", "marketdatad")
        finally:
            cur.close()
            conn.close()

        if df_rvol_trades.empty:
            return html.Div("No trades available for this Trade ID.")

        
        return generate_table(df_rvol_trades)