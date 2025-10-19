import psycopg2
import pandas as pd

# Return connection and cursor
def get_connection_and_cursor(database_config):
    """Create and return a database connection and cursor."""
    conn = psycopg2.connect(**database_config)
    if not conn:
        raise Exception("Failed to connect to database.")
    cur = conn.cursor()
    return conn, cur


# Data fetch codes

def fetch_marketdata(trade_id: int,cursor,table_name: str) -> pd.DataFrame:
    try:

        query = f'SELECT * FROM "{table_name}" WHERE "TradeId" = %s ORDER BY "Date";'
        cursor.execute(query, (trade_id,))
        rows = cursor.fetchall()
        colnames = [desc[0] for desc in cursor.description]
        df = pd.DataFrame(rows, columns=colnames)

        if df.empty:
            return df

        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.dropna(subset=['Date'])

        for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        df = df.dropna(subset=['Open', 'High', 'Low', 'Close', 'Volume'])

        return df

    except Exception as e:
        print(f"Error fetching data for TradeId {trade_id}: {e}")
        return pd.DataFrame()

def fetch_trade_info(trade_id: int, cursor, table_name: str) -> dict:
    try:
        query = f'''
            SELECT "Symbol", "Date", "Setup", "Rating"
            FROM "{table_name}"
            WHERE "TradeId" = %s
            LIMIT 1;
        '''
        cursor.execute(query, (trade_id,))
        result = cursor.fetchone()

        if result:
            symbol, date, setup, rating = result
            return {
                "Symbol": symbol,
                "Date": pd.to_datetime(date),
                "Setup": setup,
                "Rating": rating
            }
        else:
            return {}

    except Exception as e:
        print(f"Error fetching trade info for TradeId {trade_id}: {e}")
        return {}

def fetch_intraday_data(trade_id: int, cursor, table_name: str) -> pd.DataFrame:
    try:
        query = f'SELECT * FROM "{table_name}" WHERE "TradeId" = %s ORDER BY "Time";'
        cursor.execute(query, (trade_id,))
        rows = cursor.fetchall()
        colnames = [desc[0] for desc in cursor.description]
        df = pd.DataFrame(rows, columns=colnames)

        if df.empty:
            return df

        df['Time'] = pd.to_datetime(df['Time'], errors='coerce')
        df = df.dropna(subset=['Time'])

        # List of columns to convert to numeric, including VWAP and EMA9
        numeric_cols = ['Open', 'High', 'Low', 'Close', 'Volume', 'VWAP', 'EMA9','Relatr']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')


        return df

    except Exception as e:
        print(f"Error fetching intraday data for TradeId {trade_id}: {e}")
        return pd.DataFrame()

def fetch_relative_volume(trade_id: int, cursor) -> pd.DataFrame:
    """
    Given a trade_id, fetch the Symbol and Date from trades table,
    then query marketdatad for RelativeVolume where Symbol and Date match.
    Returns a DataFrame with the relevant data.
    """
    try:
        # Step 1: Get Symbol and Date from trades
        query_trade = 'SELECT "Symbol", "Date" FROM "trades" WHERE "TradeId" = %s LIMIT 1;'
        cursor.execute(query_trade, (trade_id,))
        result = cursor.fetchone()
        
        if not result:
            return pd.DataFrame()  # No trade found
        
        symbol, date = result
        
        # Step 2: Query marketdatad using Symbol and Date for RelativeVolume
        query_marketdatad = '''
            SELECT "Date", "RelativeVolume" 
            FROM "marketdatad" 
            WHERE "Symbol" = %s AND "Date" = %s
            ORDER BY "Date"
            LIMIT 1;
        '''
        cursor.execute(query_marketdatad, (symbol, date))
        rows = cursor.fetchall()
        colnames = [desc[0] for desc in cursor.description]
        
        df = pd.DataFrame(rows, columns=colnames)
        
        # Convert columns to proper types
        if not df.empty:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            df['RelativeVolume'] = pd.to_numeric(df['RelativeVolume'], errors='coerce')
            df = df.dropna(subset=['Date', 'RelativeVolume'])
        
        return df
    
    except Exception as e:
        print(f"Error fetching RelativeVolume for TradeId {trade_id}: {e}")
        return pd.DataFrame()

def fetch_marketdata30mins(trade_id: int, cursor,table_name:str) -> pd.DataFrame:
    try:
        query = f'''
            SELECT "Symbol", "Date", "Open", "High", "Low", "Close", "Volume", "EMA65", "TradeId"
            FROM "{table_name}"
            WHERE "TradeId" = %s
            ORDER BY "Date";
        '''
        cursor.execute(query, (trade_id,))
        rows = cursor.fetchall()
        colnames = [desc[0] for desc in cursor.description]
        df = pd.DataFrame(rows, columns=colnames)

        if df.empty:
            return df

        # Parse timestamp
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df = df.dropna(subset=['Date'])

        # Convert price and volume columns
        for col in ['Open', 'High', 'Low', 'Close', 'Volume','EMA65']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        return df

    except Exception as e:
        print(f"Error fetching 30-min data for TradeId {trade_id}: {e}")
        return pd.DataFrame()

def fetch_trade_executions(trade_info: dict, cursor, table_name: str) -> pd.DataFrame:

    try:
        symbol = trade_info.get("Symbol")
        trade_date = trade_info.get("Date")

        if not symbol or not trade_date:
            print(" Missing Symbol or Date in trade_info.")
            return pd.DataFrame()

        # Convert date to string in YYYYMMDD format (if it's a datetime object)
        if isinstance(trade_date, pd.Timestamp):
            trade_date_str = trade_date.strftime("%Y%m%d")
        else:
            trade_date_str = str(trade_date)

        query = f"""
            SELECT * FROM {table_name}
            WHERE "Symbol" = %s AND "Date" = %s
            ORDER BY "Time" ASC
        """

        cursor.execute(query, (symbol, trade_date_str))
        rows = cursor.fetchall()

        # Get column names
        colnames = [desc[0] for desc in cursor.description]

        return pd.DataFrame(rows, columns=colnames)

    except Exception as e:
        print(f" Error fetching trade executions: {e}")
        return pd.DataFrame()

def fetch_trades_with_rvol(cursor, trades_table: str, marketdatad_table: str) -> pd.DataFrame:
    query = f"""
        SELECT
            t.*,
            m."RelativeVolume"
        FROM {trades_table} t
        LEFT JOIN LATERAL (
            SELECT "RelativeVolume", "Date"
            FROM {marketdatad_table} m
            WHERE m."TradeId" = t."TradeId"
            ORDER BY m."Date" DESC
            LIMIT 1
        ) m ON TRUE
        WHERE m."RelativeVolume" > 0
        ORDER BY m."Date" DESC;
    """
    cursor.execute(query)
    columns = [desc[0] for desc in cursor.description]
    data = cursor.fetchall()
    return pd.DataFrame(data, columns=columns)



def update_trade_setup(trade_id: int, setup: str, cursor, conn) -> None:
    query = 'UPDATE "trades" SET "Setup" = %s WHERE "TradeId" = %s;'
    cursor.execute(query, (setup, trade_id))
    conn.commit()
  
def update_trade_rating(trade_id: int, rating: int, cursor, conn) -> None:
    query = 'UPDATE "trades" SET "Rating" = %s WHERE "TradeId" = %s;'
    cursor.execute(query, (rating, trade_id))
    conn.commit()