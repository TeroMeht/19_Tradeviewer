from dash import Input, Output, State, no_update
import plotly.graph_objects as go
import pandas as pd
from src.data.db_functions import get_connection_and_cursor, fetch_marketdata, fetch_trade_info, fetch_trade_executions



def create_daily_plot_component(df_daily: pd.DataFrame, 
                                df_executions: pd.DataFrame)-> go.Figure:
    import pandas as pd
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    fig_daily = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.02,
        row_heights=[0.7, 0.2],
        subplot_titles=[f'Daily']
    )

    if not df_daily.empty:
        df_daily = df_daily.copy()
        df_daily['Date'] = pd.to_datetime(df_daily['Date'], errors='coerce')
        df_daily['DateStr'] = df_daily['Date'].dt.strftime('%Y-%m-%d')

        fig_daily.add_trace(go.Candlestick(
            x=df_daily['DateStr'],
            open=df_daily['Open'],
            high=df_daily['High'],
            low=df_daily['Low'],
            close=df_daily['Close'],
            name='OHLC Daily'
        ), row=1, col=1)

        if df_executions is not None and not df_executions.empty:
            df_executions = df_executions.copy()
            # convert to datetime safely
            df_executions['Date'] = pd.to_datetime(df_executions['Date'], errors='coerce')
            df_executions = df_executions.dropna(subset=['Date'])  # drop rows where conversion failed
            df_executions['DateStr'] = df_executions['Date'].dt.strftime('%Y-%m-%d')

            color_map = {'BUYTOOPEN': 'blue', 'BUYTOCLOSE': 'blue', 'SELLTOCLOSE': 'red', 'SELLTOOPEN': 'red'}
            symbol_map = {'BUYTOOPEN': 'triangle-up', 'BUYTOCLOSE': 'triangle-up', 
                          'SELLTOCLOSE': 'triangle-down', 'SELLTOOPEN': 'triangle-down'}
            colors = df_executions['Side'].map(color_map).fillna('black')
            symbols = df_executions['Side'].map(symbol_map).fillna('circle')
            price_col = 'AvgPrice' if 'AvgPrice' in df_executions.columns else 'Price'

            fig_daily.add_trace(go.Scatter(
                x=df_executions['DateStr'],
                y=df_executions[price_col],
                mode='markers',
                marker=dict(color=colors, size=12, symbol=symbols),
                name='Executions'
            ), row=1, col=1)

        fig_daily.add_trace(go.Bar(
            x=df_daily['DateStr'],
            y=df_daily['Volume'],
            marker_color='blue',
            name='Volume Daily'
        ), row=2, col=1)

        fig_daily.update_layout(
            height=600,
            showlegend=False,
            xaxis=dict(type='category', tickangle=45, tickfont=dict(size=10)),
            xaxis2=dict(type='category', tickangle=45, tickfont=dict(size=10)),
            yaxis=dict(title='Price'),
            yaxis2=dict(title='Volume'),
            xaxis_rangeslider_visible=False,
        )
    else:
        fig_daily = go.Figure()
        fig_daily.update_layout(title="No daily data available")

    return fig_daily

# --- Callback registration ---
def register_daily_chart_callback(app, database_config):
    @app.callback(
        Output("daily-chart", "figure"),
        Input("fetch-button", "n_clicks"),
        State("trade-id-input", "value"),
 
    )
    def update_daily_chart(n_clicks, trade_id):
        if not trade_id:
            return go.Figure()

        conn, cur = get_connection_and_cursor(database_config)
        try:
            df_daily = fetch_marketdata(trade_id, cur, "marketdatad")
            trade_info = fetch_trade_info(trade_id, cur, "trades")
            executions = fetch_trade_executions(trade_info, cur, "executions")
        finally:
            cur.close()
            conn.close()

        return create_daily_plot_component(df_daily, executions)
