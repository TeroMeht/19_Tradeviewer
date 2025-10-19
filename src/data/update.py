from src.data.db_functions import get_connection_and_cursor
from src.data.db_functions import update_trade_setup, update_trade_rating  # import your existing functions

def update_trade(database_config, trade_id: int, setup: str = None, rating: int = None) -> str:

    if not trade_id:
        return "No Trade ID provided."

    messages = []

    conn, cursor = get_connection_and_cursor(database_config)
    try:
        if setup:
            update_trade_setup(trade_id, setup, cursor, conn)
            messages.append(f"Setup='{setup}'")
        if rating is not None:
            update_trade_rating(trade_id, rating, cursor, conn)
            messages.append(f"Rating={rating}")

        return f"Saved for Trade {trade_id}: {'; '.join(messages)}" if messages else "Nothing to update."

    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        conn.close()
