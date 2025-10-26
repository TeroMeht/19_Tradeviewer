from dash import Input, Output, State, no_update
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from src.data.db_functions import get_connection_and_cursor, fetch_marketdata, fetch_trade_info, fetch_trade_executions
from src.utils.helper_functions import align_execution_times_to_intraday

def create_intraday_plot_component(df_intraday : pd.DataFrame, 
                                   df_executions: pd.DataFrame)-> go.Figure:
    if not df_intraday.empty:

        fig_intraday = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.02,
            row_heights=[0.6, 0.2, 0.2],
            subplot_titles=[f'Intraday Price & Indicators']
        )

        # Candlestick
        fig_intraday.add_trace(go.Candlestick(
            x=df_intraday['Time'],
            open=df_intraday['Open'],
            high=df_intraday['High'],
            low=df_intraday['Low'],
            close=df_intraday['Close'],
            name='OHLC'
        ), row=1, col=1)

        # VWAP
        if 'VWAP' in df_intraday.columns:
            fig_intraday.add_trace(go.Scatter(
                x=df_intraday['Time'],
                y=df_intraday['VWAP'],
                mode='lines',
                line=dict(color='red', width=1.5),
                name='VWAP'
            ), row=1, col=1)

        # EMA9
        if 'EMA9' in df_intraday.columns:
            fig_intraday.add_trace(go.Scatter(
                x=df_intraday['Time'],
                y=df_intraday['EMA9'],
                mode='lines',
                line=dict(color='blue', width=0.8),
                name='EMA9'
            ), row=1, col=1)

        # Execution markers
        if df_executions is not None and not df_executions.empty:
            color_map = {
                'BUYTOOPEN': 'blue',
                'BUYTOCLOSE': 'blue',
                'SELLTOCLOSE': 'red',
                'SELLTOOPEN': 'red',
            }
            symbol_map = {
                'BUYTOOPEN': 'triangle-up',
                'BUYTOCLOSE': 'triangle-up',
                'SELLTOCLOSE': 'triangle-down',
                'SELLTOOPEN': 'triangle-down',
            }
            colors = df_executions['Side'].map(color_map).fillna('black')
            symbols = df_executions['Side'].map(symbol_map).fillna('circle')
            price_col = 'AvgPrice' if 'AvgPrice' in df_executions.columns else 'Price'

            fig_intraday.add_trace(go.Scatter(
                x=df_executions['Time'],
                y=df_executions[price_col],
                mode='markers',
                marker=dict(color=colors, size=15, symbol=symbols),
                name='Executions'
            ), row=1, col=1)

        # Volume
        fig_intraday.add_trace(go.Bar(
            x=df_intraday['Time'],
            y=df_intraday['Volume'],
            marker_color='blue',
            name='Volume'
        ), row=2, col=1)

        # Relatr
        if 'Relatr' in df_intraday.columns:
            fig_intraday.add_trace(go.Scatter(
                x=df_intraday['Time'],
                y=df_intraday['Relatr'],
                mode='lines',
                line=dict(color='green', width=2),
                name='Relatr'
            ), row=3, col=1)

            # Add horizontal lines
            for y_val in [0, 0.5, -0.5]:
                fig_intraday.add_shape(
                    type='line',
                    x0=df_intraday['Time'].min(),
                    x1=df_intraday['Time'].max(),
                    y0=y_val,
                    y1=y_val,
                    line=dict(color='black', width=1, dash='dash'),
                    xref='x3', yref='y3',
                )

        # Layout
        fig_intraday.update_layout(
            height=800,
            showlegend=False,
            xaxis3=dict(title='Time'),
            yaxis=dict(title='Price'),
            yaxis2=dict(title='Volume'),
            yaxis3=dict(title='Relatr'),
            xaxis_rangeslider_visible=False,
        )
    else:
        fig_intraday = go.Figure()
        fig_intraday.update_layout(title="No intraday data available")

    return fig_intraday

# --- Callback registration ---
def register_intraday_chart_callback(app, database_config):
    @app.callback(
        Output("intraday-chart", "figure"),
        Input("fetch-button", "n_clicks"),
        State("trade-id-input", "value"),

    )
    def update_intraday_chart(n_clicks, trade_id):
        if not trade_id:
            return go.Figure()

        conn, cur = get_connection_and_cursor(database_config)
        try:
            df_intraday = fetch_marketdata(trade_id, cur, "marketdataintrad")
            trade_info = fetch_trade_info(trade_id, cur, "trades")
            executions = fetch_trade_executions(trade_info, cur, "executions")

            exec= align_execution_times_to_intraday(executions, df_intraday)
        finally:
            cur.close()
            conn.close()

        return create_intraday_plot_component(df_intraday,exec )
