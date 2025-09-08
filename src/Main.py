import dash
from dash import *

import pandas as pd
import numpy as np
import helpers.BuildHTML as BHT

from common.ReadConfigsIn import *
from helpers.DBfunctions import *
from ui.PlotData import *



# Create Dash app
app = dash.Dash(__name__)
app.title = "Candlestick Dashboard"

database_config = read_database_config(filename="database.ini", section="postgresql")



# --- Layout ---
app.layout = html.Div([
    BHT.build_header(),
    BHT.build_status_display(),
    BHT.build_chart_row(),
    BHT.build_intraday_and_table_row(),
    BHT.build_error_display()
])





# Match execution data to 2 min chart
def align_execution_times_to_intraday(df_executions: pd.DataFrame, df_intraday: pd.DataFrame) -> pd.DataFrame:

    if df_executions.empty or df_intraday.empty:
        return df_executions.copy()

    # Helper function to convert time or datetime to seconds from midnight
    def to_seconds(t):
        if pd.isnull(t):
            return np.nan
        if isinstance(t, pd.Timestamp) or isinstance(t, pd._libs.tslibs.timestamps.Timestamp):
            t = t.time()
        return t.hour * 3600 + t.minute * 60 + t.second

    # Convert intraday and exec times to seconds from midnight as numpy arrays
    intraday_secs = np.array([to_seconds(t) for t in df_intraday['Time']])
    exec_secs = np.array([to_seconds(t) for t in df_executions['Time']])

    def find_nearest_time(exec_sec):
        # Find index of closest intraday time
        idx = np.abs(intraday_secs - exec_sec).argmin()
        return df_intraday['Time'].iloc[idx]

    aligned_times = [find_nearest_time(t) for t in exec_secs]

    df_aligned = df_executions.copy()
    df_aligned['Time'] = aligned_times

    return df_aligned

def align_execution_times_to_30mins(df_executions: pd.DataFrame, df_30min: pd.DataFrame) -> pd.DataFrame:
    if df_executions.empty or df_30min.empty:
        return df_executions.copy()

    # Convert to seconds since midnight
    def to_seconds(t):
        if pd.isnull(t):
            return np.nan
        if isinstance(t, pd.Timestamp):
            t = t.time()
        return t.hour * 3600 + t.minute * 60 + t.second

    intraday_secs = np.array([to_seconds(t) for t in df_30min['Date']])
    exec_secs = np.array([to_seconds(t) for t in df_executions['Time']])

    aligned_times = []
    for exec_sec in exec_secs:
        idx = np.abs(intraday_secs - exec_sec).argmin()
        aligned_time = df_30min['Date'].iloc[idx].time()  # Only use the time
        aligned_times.append(aligned_time)

    df_aligned = df_executions.copy()
    df_aligned['Time'] = aligned_times  # Replace only Time
    # Date remains untouched

    return df_aligned




# Trades table
def generate_table(dataframe, max_rows=15):
    return dash_table.DataTable(
        id='trade-table',
        columns=[{"name": i, "id": i} for i in dataframe.columns],
        data=dataframe.to_dict('records'),
        sort_action='native',
        page_size=max_rows,
        page_action='native',
        fixed_rows={'headers': True},
        
        # Retain pagination, sort, and filter states across sessions
        persistence=True,  
        persistence_type='session',  # or 'local' if you want it persistent across browser restarts
        persisted_props=['page_current', 'sort_by', 'filter_query'],  
        
        style_table={
            'border': '1px solid #e1e1e1',
            'backgroundColor': 'white',
        },
        style_cell={
            'textAlign': 'center',
            'padding': '2px',
            'backgroundColor': 'white',
            'color': '#333',
            'border': '1px solid #f0f0f0',
            'fontFamily': 'Arial, sans-serif',
            'fontSize': '12px',
        },
        style_header={
            'backgroundColor': '#f8f8f8',
            'color': '#333',
            'fontWeight': 'bold',
            'border': '1px solid #ddd',
            'fontSize': '12px',
        },
        style_data_conditional=[
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': '#f9f9f9',
            },
            {
                'if': {'state': 'selected'},
                'backgroundColor': '#d0e6f7',
                'border': '1px solid #a6c8ff',
            },
            {
                'if': {'state': 'active'},
                'backgroundColor': '#cce4ff',
                'border': '1px solid #8bbfff',
            }
        ],
        style_as_list_view=True,
    )


def update_trade_setup(trade_id: int, setup: str, conn):
    with conn.cursor() as cursor:
        cursor.execute(
            'UPDATE trades SET "Setup" = %s WHERE "TradeId" = %s;',
            (setup, trade_id)
        )
        conn.commit()

def update_trade_rating(trade_id: int, rating: int, conn):
    with conn.cursor() as cursor:
        cursor.execute(
            'UPDATE trades SET "Rating" = %s WHERE "TradeId" = %s;',
            (rating, trade_id)
        )
        conn.commit()


@app.callback(
    Output('trade-id-input', 'value'),
    Input('trade-table', 'active_cell'),
    State('trade-table', 'derived_viewport_data'),
    prevent_initial_call=True
)
def update_trade_id_input(active_cell, visible_data):
    if active_cell and visible_data:
        row_index = active_cell['row']
        column_id = active_cell['column_id']

        if column_id == 'TradeId' and 0 <= row_index < len(visible_data):
            trade_id = visible_data[row_index]['TradeId']
           # print(f"Selected TradeId: {trade_id}")
            return trade_id

    return dash.no_update


# Callback function (correct signature)
@app.callback(
    Output('daily-chart', 'figure'),
    Output('chart30mins', 'figure'),           # Added output for 30min chart
    Output('intraday-chart', 'figure'),
    Output('relative-volume-display', 'children'),
    Output('error-message', 'children'),
    Output('trade-data-table', 'children'),
    Input('fetch-button', 'n_clicks'),
    State('trade-id-input', 'value'),
    State('setup-dropdown', 'value'),
    prevent_initial_call=True
)
def update_chart(n_clicks, trade_id,setup):
    if n_clicks == 0:
        raise dash.exceptions.PreventUpdate
    if not trade_id:
        return go.Figure(), go.Figure(), go.Figure(), "", "Please enter a valid Trade ID."

    connection, cursor= get_connection_and_cursor(database_config)
    try:
        # Fetch price data
        df_daily = fetch_marketdata(trade_id, cursor, table_name="marketdatad")
        df_intraday = fetch_marketdata(trade_id, cursor, table_name="marketdataintrad")
        df_30min = fetch_marketdata30mins(trade_id, cursor, table_name="marketdata30mins")

        # Fetch trade details
        trade_info = fetch_trade_info(trade_id, cursor, table_name="trades")
        df_relative_volume = fetch_relative_volume(trade_id, cursor)
       

        trade_executions = fetch_trade_executions(trade_info, cursor, table_name="executions")
        

        df_rvol_trades = fetch_trades_with_rvol(cursor, "trades", "marketdatad")
        trade_table = generate_table(df_rvol_trades)

    finally:
        cursor.close()
        connection.close()

    if df_daily.empty and df_intraday.empty:
        return go.Figure(), go.Figure(), f"No data found for TradeId {trade_id}"

    symbol = trade_info.get("Symbol", "Unknown Symbol")
    trade_date = trade_info.get("Date")
    date_str = trade_date.strftime("%Y-%m-%d") if trade_date else "Unknown Date"
    setup = trade_info.get("Setup", "No Setup")

    relative_volume = df_relative_volume['RelativeVolume'].iloc[0]
    trade_details_text = (
        f"TradeId: {trade_id} | Symbol: {symbol} | Date: {date_str} | Setup: {setup} | Relative Volume: {relative_volume:.2f}"
    )
  #  print(trade_details_text)


    # Align timestamps
    df_executions_aligned = align_execution_times_to_intraday(trade_executions, df_intraday)
    df_executions_aligned30min = align_execution_times_to_30mins(trade_executions, df_30min)



    fig_intraday = plot_intraday_chart(df_intraday,df_executions_aligned, symbol, trade_id, date_str)
    fig_daily = plot_daily_chart(df_daily, trade_executions, symbol, trade_id, date_str)
    fig_30min = plot_30min_chart(df_30min, df_executions_aligned30min,symbol, trade_id)




    return fig_daily, fig_30min, fig_intraday, trade_details_text, "",trade_table



@app.callback(
    Output('save-status-message', 'children'),
    Input('save-setup-button', 'n_clicks'),
    Input('save-rating-button', 'n_clicks'),
    State('trade-id-input', 'value'), 
    State('setup-dropdown', 'value'),
    State('rating-input', 'value'),
    prevent_initial_call=True
)
def save_trade_info(setup_clicks, rating_clicks, trade_id, setup, rating):
    if not trade_id:
        raise dash.exceptions.PreventUpdate

    ctx = callback_context
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    messages = []

    try:
        conn, cur = get_connection_and_cursor(database_config)


        if triggered_id == 'save-setup-button':
            if setup:
                update_trade_setup(trade_id, setup, conn)
                messages.append(f"Setup: '{setup}'")
            else:
                messages.append("⚠️ No setup selected.")

        elif triggered_id == 'save-rating-button':
            if rating is not None:
                update_trade_rating(trade_id, rating, conn)
                messages.append(f"Rating: '{rating}'")
            else:
                messages.append("⚠️ No rating provided.")

        conn.close()

        return f"✅ Saved for Trade ID {trade_id}: " + " ".join(messages)

    except Exception as e:
        return f"❌ Error: {str(e)}"






if __name__ == '__main__':
    app.run(debug=True)
