# trade_header.py
from dash import html, Input, Output, State, no_update
from src.data.db_functions import get_connection_and_cursor, fetch_trade_info, fetch_relative_volume

# --- Render function ---
def render():
    """
    Returns the placeholder Div for the trade header.
    The content will be updated via callback.
    """
    return html.Div(id="trade-header", style={
        "fontSize": "18px",
        "fontWeight": "bold",
        "marginBottom": "6px"
    })


# --- Callback registration ---
def register_callbacks(app, database_config):
    """
    Updates the trade header when the Fetch Data button is clicked or trade-id changes.
    """
    @app.callback(
        Output("trade-header", "children"),
        Input("fetch-button", "n_clicks"),
        State("trade-id-input", "value"),
    )
    def update_trade_header(n_clicks, trade_id):
        if not trade_id:
            return no_update

        conn, cur = get_connection_and_cursor(database_config)
        try:
            trade_info = fetch_trade_info(trade_id, cur, "trades")
            df_rvol = fetch_relative_volume(trade_id, cur)
        finally:
            conn.close()

        if not trade_info:
            return f"Trade {trade_id} not found."

        symbol = trade_info.get("Symbol", "Unknown")
        date_str = trade_info.get("Date").strftime("%Y-%m-%d") if trade_info.get("Date") else "Unknown"
        setup = trade_info.get("Setup", "No Setup")
        rating = trade_info.get("Rating", "N/A")  # <-- added rating safely

        # Fetch RVOL
        rvol = df_rvol["RelativeVolume"].iloc[0] if not df_rvol.empty else float("nan")

        # Construct header text with rating
        header_text = (
            f"TradeId: {trade_id} | {symbol} | Date: {date_str} | "
            f"Setup: {setup} | RVOL: {rvol:.2f} | Rating: {rating}"
        )

        return header_text