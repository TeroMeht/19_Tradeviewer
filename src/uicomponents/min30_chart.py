from dash import Input, Output, State, no_update
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from src.data.db_functions import get_connection_and_cursor, fetch_marketdata30mins, fetch_trade_info, fetch_trade_executions
from src.utils.helper_functions import align_execution_times_to_30mins

def create_30min_plot_component(df_30min: pd.DataFrame, 
                                df_executions: pd.DataFrame)-> go.Figure:
    if not df_30min.empty:
        df_30min = df_30min.copy()
        # Format datetime as date+time string without seconds (for cleaner labels)
        df_30min['DateStr'] = df_30min['Date'].dt.strftime('%Y-%m-%d %H:%M')

        fig_30min = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.02,
            row_heights=[0.7, 0.2],
            subplot_titles=[f'30-Minutes']
        )

        fig_30min.add_trace(go.Candlestick(
            x=df_30min['DateStr'],
            open=df_30min['Open'],
            high=df_30min['High'],
            low=df_30min['Low'],
            close=df_30min['Close'],
            name='OHLC 30min'
        ), row=1, col=1)

        if 'EMA65' in df_30min.columns:
            fig_30min.add_trace(go.Scatter(
                x=df_30min['DateStr'],
                y=df_30min['EMA65'],
                mode='lines',
                line=dict(color='blue', width=1.5),
                name='EMA65'
            ), row=1, col=1)

        # ➕ Execution markers (30min)
        if df_executions is not None and not df_executions.empty:
            df_executions = df_executions.copy()
            # Combine Date and Time as string (same format as df_30min DateStr)
            df_executions['DateTimeStr'] = df_executions.apply(
                lambda row: f"{row['Date'].strftime('%Y-%m-%d')} {row['Time'].strftime('%H:%M')}", axis=1
            )

            color_map = {'BUYTOOPEN': 'blue', 'BUYTOCLOSE': 'blue', 'SELLTOCLOSE': 'red', 'SELLTOOPEN': 'red'}
            symbol_map = {'BUYTOOPEN': 'triangle-up', 'BUYTOCLOSE': 'triangle-up', 'SELLTOCLOSE': 'triangle-down', 'SELLTOOPEN': 'triangle-down'}
            colors = df_executions['Side'].map(color_map).fillna('black')
            symbols = df_executions['Side'].map(symbol_map).fillna('circle')
            price_col = 'AvgPrice' if 'AvgPrice' in df_executions.columns else 'Price'

            fig_30min.add_trace(go.Scatter(
                x=df_executions['DateTimeStr'],
                y=df_executions[price_col],
                mode='markers',
                marker=dict(color=colors, size=12, symbol=symbols),
                name='Executions'
            ), row=1, col=1)

        fig_30min.add_trace(go.Bar(
            x=df_30min['DateStr'],
            y=df_30min['Volume'],
            marker_color='blue',
            name='Volume 30min'
        ), row=2, col=1)

        fig_30min.update_layout(
            height=600,
            showlegend=False,
            xaxis=dict(
                type='category',
                tickangle=45,
                tickfont=dict(size=15),
                showticklabels=False
            ),
            xaxis2=dict(
                type='category',
                tickangle=45,
                tickfont=dict(size=15),
                showticklabels=False
            ),
            yaxis=dict(title='Price'),
            yaxis2=dict(title='Volume'),
            xaxis_rangeslider_visible=False,
        )
    else:
        fig_30min = go.Figure()
        fig_30min.update_layout(title="No 30-minute data available")

    return fig_30min

# --- Callback registration ---
def register_30min_chart_callback(app, database_config):
    @app.callback(
        Output("chart30mins", "figure"),
        Input("fetch-button", "n_clicks"),
        State("trade-id-input", "value"),
    )
    def update_30min_chart(n_clicks, trade_id):
        if not trade_id:
            return go.Figure()

        conn, cur = get_connection_and_cursor(database_config)
        try:
            df_30min = fetch_marketdata30mins(trade_id, cur, "marketdata30mins")
            trade_info = fetch_trade_info(trade_id, cur, "trades")
            executions = fetch_trade_executions(trade_info, cur, "executions")
        finally:
            cur.close()
            conn.close()

        # --- Align executions to 30min bars ---
        executions_aligned = align_execution_times_to_30mins(executions, df_30min)


        return create_30min_plot_component(df_30min, executions_aligned)