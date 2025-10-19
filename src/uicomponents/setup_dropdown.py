from dash import html, dcc

def render():
    """
    Returns the Setup dropdown component for trade controls.
    """
    return dcc.Dropdown(
        id="setup-dropdown",
        options=[
            {'label': 'Extreme Reversal', 'value': 'Extreme Reversal'},
            {'label': 'No setup', 'value': 'No setup'},
            {'label': 'ORB', 'value': 'ORB'},
            {'label': 'Swing trade exit', 'value': 'Swing trade exit'},
            {'label': 'Reversal', 'value': 'Reversal'},
            {'label': 'Reversal short', 'value': 'Reversal short'},
            {'label': 'Parabolic short', 'value': 'Parabolic short'},
            {'label': 'Swing trade', 'value': 'Swing trade'},
            {'label': 'VWAP continuation', 'value': 'VWAP continuation'},
            {'label': 'Other', 'value': 'Other'},
        ],
        placeholder="Choose a setup",
        style={"width": "200px", "display": "inline-block", "verticalAlign": "middle"},
    )