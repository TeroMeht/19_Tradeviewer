from plotly.subplots import make_subplots
import plotly.graph_objects as go
import pandas as pd

# Graph plottinf codes
def plot_daily_chart(df_daily, df_executions,symbol, trade_id, date_str):
    fig_daily = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.02,
        row_heights=[0.7, 0.2],
        subplot_titles=[f'Daily']
    )

    if not df_daily.empty:
        # Create a date-only string column for x-axis
        df_daily = df_daily.copy()
        df_daily['DateStr'] = df_daily['Date'].dt.strftime('%Y-%m-%d')

        fig_daily.add_trace(go.Candlestick(
            x=df_daily['DateStr'],
            open=df_daily['Open'],
            high=df_daily['High'],
            low=df_daily['Low'],
            close=df_daily['Close'],
            name='OHLC Daily'
        ), row=1, col=1)

        # ➕ Add execution markers (Daily)
        if df_executions is not None and not df_executions.empty:
            df_executions = df_executions.copy()
            # Convert execution dates to string dates too
            df_executions['DateStr'] = pd.to_datetime(df_executions['Date']).dt.strftime('%Y-%m-%d')

            color_map = {'BUYTOOPEN': 'blue', 'BUYTOCLOSE': 'blue', 'SELLTOCLOSE': 'red', 'SELLTOOPEN': 'red'}
            symbol_map = {'BUYTOOPEN': 'triangle-up', 'BUYTOCLOSE': 'triangle-up', 'SELLTOCLOSE': 'triangle-down', 'SELLTOOPEN': 'triangle-down'}
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
            xaxis=dict(
                type='category',
                tickangle=45,
                tickfont=dict(size=10),
            ),
            xaxis2=dict(
                type='category',
                tickangle=45,
                tickfont=dict(size=10),
            ),
            yaxis=dict(title='Price'),
            yaxis2=dict(title='Volume'),
            xaxis_rangeslider_visible=False,
        )
    else:
        fig_daily = go.Figure()
        fig_daily.update_layout(title="No daily data available")

    return fig_daily

def plot_30min_chart(df_30min, df_executions,symbol, trade_id):
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

def plot_intraday_chart(df_intraday, df_executions, symbol, trade_id, date_str):
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
                line=dict(color='red', width=2),
                name='VWAP'
            ), row=1, col=1)

        # EMA9
        if 'EMA9' in df_intraday.columns:
            fig_intraday.add_trace(go.Scatter(
                x=df_intraday['Time'],
                y=df_intraday['EMA9'],
                mode='lines',
                line=dict(color='purple', width=1),
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
            for y_val in [0, 0.4, -0.4]:
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

