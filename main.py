# src/app.py
from dash import Dash
from dash_bootstrap_components.themes import BOOTSTRAP
from src.common.read_configs_in import read_database_config
from src.uicomponents.layout import create_layout
from src.uicomponents.callbacks import trade_callbacks


def main() -> None:
    # Database setup
    database_config = read_database_config(filename="database.ini", section="postgresql")

    # Dash app
    app = Dash(external_stylesheets=[BOOTSTRAP])
    app.title = "Tradeviewer Dashboard"

    # Layout
    app.layout = create_layout(app,database_config)

    # Register all callbacks
    trade_callbacks.register_callbacks(app)


    app.run()


if __name__ == "__main__":
    main()
