# focus_engine.py (Version 2.6 - Added Score Prediction)
    
# --- Imports ---
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import data_manager

# --- Core Constant ---
POLL_INTERVAL_SECONDS = 5.0 

# --- Database Function ---
def get_today_data():
    """
    Utility: Reads all of today's log entries from the database
    and returns them as a pandas DataFrame (a data table).
    """
    conn = sqlite3.connect(data_manager.DB_FILE)
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    try:
        df = pd.read_sql_query(
            "SELECT * FROM activity_log WHERE timestamp >= ?", 
            conn, 
            params=(today_start,)
        )
        return df
    except Exception as e:
        print(f"Error reading database: {e}")
        return pd.DataFrame() 
    finally:
        conn.close()

# --- Core Logic ---
def calculate_daily_stats():
    """
    Core Logic: Reads today's data and calculates all scores and times.
    This is called by the "slow" thread every 5 seconds.
    """
    df = get_today_data()
    
    if df.empty:
        return { 
            "score": 0, 
            "prod_time_s": 0, 
            "dist_time_s": 0, 
            "neut_time_s": 0,
            "predicted_score": 0 
        } 

    # --- Calculation Logic ---
    prod_events = len(df[df['category'] == 'Productive']) + len(df[df['category'] == 'Productive (AI)'])
    study_events = len(df[df['category'] == 'Studying'])
    dist_events = len(df[df['category'].str.startswith('Distraction-')])
    neut_events = len(df[df['category'] == 'Neutral'])
    
    total_good_events = prod_events + study_events
    
    prod_time_s = total_good_events * POLL_INTERVAL_SECONDS
    dist_time_s = dist_events * POLL_INTERVAL_SECONDS
    neut_time_s = neut_events * POLL_INTERVAL_SECONDS
    
    total_focus_events = total_good_events + dist_events
    
    if total_focus_events == 0:
        score = 0
    else:
        score = (total_good_events / total_focus_events) * 100
        
    predicted_score = calculate_predicted_score(total_good_events, total_focus_events)
        
    return {
        "score": int(score),
        "prod_time_s": prod_time_s,
        "dist_time_s": dist_time_s,
        "neut_time_s": neut_time_s,
        "predicted_score": int(predicted_score)
    }

# --- Core Logic: Prediction ---
def calculate_predicted_score(total_good_events, total_focus_events):
    """
    Core Logic: Predicts the user's score at the end of an 8-hour workday
    based on their current performance.
    """
    try:
        EVENTS_IN_8_HOURS = (8 * 60 * 60) / POLL_INTERVAL_SECONDS
        
        current_scorable_events = total_good_events + total_focus_events
        if current_scorable_events == 0:
            return 0 

        current_ratio = total_good_events / current_scorable_events
        
        events_remaining = EVENTS_IN_8_HOURS - current_scorable_events
        
        if events_remaining <= 0:
            return (total_good_events / current_scorable_events) * 100

        predicted_future_good_events = events_remaining * current_ratio
        
        total_predicted_good = total_good_events + predicted_future_good_events
        total_predicted_focus_events = current_scorable_events + events_remaining
        
        predicted_score = (total_predicted_good / total_predicted_focus_events) * 100
        return predicted_score
        
    except Exception as e:
        print(f"Score prediction error: {e}")
        return 0 

# --- Feature Logic: Weekly Stats ---
def get_weekly_stats():
    """
    Feature Logic: Fetches and calculates stats for the past 7 days.
    This is called by the "History" window.
    """
    conn = sqlite3.connect(data_manager.DB_FILE)
    
    seven_days_ago = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=7)
    
    try:
        df = pd.read_sql_query(
            "SELECT timestamp, category FROM activity_log WHERE timestamp >= ?",
            conn,
            params=(seven_days_ago,)
        )
    except Exception as e:
        print(f"Error reading weekly database: {e}")
        return []
    finally:
        conn.close()

    if df.empty:
        return []

    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['date'] = df['timestamp'].dt.date
    
    def calculate_score(group):
        prod_events = len(group[group['category'] == 'Productive']) + len(df[df['category'] == 'Productive (AI)'])
        study_events = len(group[group['category'] == 'Studying'])
        dist_events = len(group[group['category'].str.startswith('Distraction-')])
        total_good = prod_events + study_events
        total_focus = total_good + dist_events
        score = (total_good / total_focus) * 100 if total_focus > 0 else 0
        return pd.Series({
            'score': int(score),
            'prod_time_s': total_good * POLL_INTERVAL_SECONDS
        })

    daily_stats = df.groupby('date').apply(calculate_score).reset_index()

    stats_list = []
    for _, row in daily_stats.iterrows():
        stats_list.append({
            'date': row['date'].strftime('%Y-%m-%d'),
            'score': row['score'],
            'prod_time_s': row['prod_time_s']
        })
        
    return stats_list