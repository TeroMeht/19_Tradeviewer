from dash import Input, Output, State, no_update

# --- Register Callbacks ---
def register_callbacks(app):
    """
    Handles interaction between the trade table and trade ID input.
    Other components (header, table, charts) now have their own callbacks.
    """
    @app.callback(
        Output("trade-id-input", "value"),
        Input("trade-table", "active_cell"),
        State("trade-table", "derived_viewport_data"),
    )
    def update_trade_id_input(active_cell, visible_data):
        """
        When a user clicks a row in the trade table, update the Trade ID input box.
        """
        if active_cell and visible_data:
            row_index = active_cell["row"]
            column_id = active_cell["column_id"]

            if column_id == "TradeId" and 0 <= row_index < len(visible_data):
                return visible_data[row_index]["TradeId"]

        return no_update