# main.py (Version 8.2 - Final V1 Package)

# --- Utility: Import necessary libraries ---
import FreeSimpleGUI as sg     # Reason: The GUI library
import pygetwindow as gw       # Reason: To get the active window title
import time                    # Reason: For all 'sleep' operations
import threading               # Reason: To run trackers in the background
import psutil                  # Reason: To get the .exe name from a process ID
import win32process            # Reason: To get the process ID (PID) from a window
import os                      # Reason: To get our own PID for self-checking
import sys                     # Reason: To check if we are in "packaged" mode.

# --- Utility: Import our helper files ---
import data_manager            # Reason: Handles all database saving/loading
import focus_engine            # Reason: Handles all stat calculations
import config_manager          # Reason: Handles reading/writing config.json
import ai_classifier           # Reason: To get AI predictions on window titles

# --- (THEME REMOVED FOR SPEED) ---

# --- Core Logic: Helper Function for PyInstaller ---
def resource_path(relative_path):
    """
    Utility: Get the absolute path to a resource, which works for
    both development ("live") and PyInstaller ("frozen") modes.
    
    This is CRITICAL for the .exe to find data files
    like 'ai_model.joblib'.
    """
    try:
        # PyInstaller creates a temp folder and stores its path in _MEIPASS
        # This is the "frozen" .exe path
        base_path = sys._MEIPASS
    except Exception:
        # This is the "live" .py script path (running from terminal)
        base_path = os.path.abspath(".")

    # Join the base path with our file name to get the full, correct path
    return os.path.join(base_path, relative_path)

# --- Core Logic: Load config from JSON ---
# This reads config.json on startup and stores it in a
# global variable. Other functions can "hot-reload" this.
current_config = config_manager.load_config()

# --- Global App "State" Variables ---
# These variables control the app's current state.
is_studying = False            # True if Study Mode is on
prompt_is_showing = False      # True if the "Start Study?" popup is active
snoozed_lecture_title = None # Stores the title of a snoozed lecture
is_paused = False              # True if the Pause button is active
pause_lock = threading.Lock()  # A "lock" to prevent threads from
                               # changing 'is_paused' at the same time.

# --- Shared "Current Activity" Variables ---
# These are used to pass data from the fast thread (Worker 1)
# to the slow thread (Worker 2).
current_app_title = None       # The title of the window
current_hwnd = None            # The "handle" (unique ID) of the window
activity_lock = threading.Lock() # A lock to safely write/read these variables

# --- Utility Function: 'format_time' ---
def format_time(seconds):
    """
    Utility: Converts a total number of seconds into a
    human-readable 'H:M:S' or 'M:S' string.
    """
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h > 0: return f"{h}h {m}m {s}s"
    if m > 0: return f"{m}m {s}s"
    return f"{s}s"

# --- Core Logic: 'classify_by_title_only' (The "Fast" Classifier) ---
def classify_by_title_only(window_title):
    """
    Core Logic: This is the "Quick-Check" classifier.
    It's FAST because it *only* looks at the window title.
    It now uses the AI model as a fallback.
    """
    global is_studying, prompt_is_showing, snoozed_lecture_title
    
    # Load rules from the global config (fast, in-memory)
    PRODUCTIVE_KEYWORDS = current_config.get("PRODUCTIVE_KEYWORDS", [])
    DISTRACTION_LEVELS = current_config.get("DISTRACTION_LEVELS", {})
    STUDY_KEYWORDS = current_config.get("STUDY_KEYWORDS", [])
    IGNORE_TITLES = current_config.get("IGNORE_TITLES", [])

    # --- Snooze Fix: Only check for empty title ---
    if not window_title:
        return "Idle"

    title_low = window_title.lower()
    
    # 1. Check Ignore List (e.g., "task switching")
    if title_low in IGNORE_TITLES:
        return "Neutral"

    # --- Classification Logic ---
    # 2. Check Productive Keywords (Fastest, most reliable)
    for keyword in PRODUCTIVE_KEYWORDS:
        if keyword in title_low:
            return "Productive"

    # --- # NEW LOGIC FIX ---
    # 3. Check Study Keywords (e.g., "dsa", "heapsort algorithm")
    # This MUST come before the AI check.
    for keyword in STUDY_KEYWORDS:
        if keyword in title_low:
            return "Studying" # It's a study topic, so it's good.

    # 4. Check Medium Distractions (e.g., YouTube)
    is_medium_distraction = False
    for keyword in DISTRACTION_LEVELS.get("Medium", []):
        if keyword in title_low:
            is_medium_distraction = True
            break
            
    if is_medium_distraction:
        # We already checked for "Studying" keywords.
        # If it's a "Medium" distraction and *not* "Studying",
        # then it's a distraction *unless* it's a lecture
        # we haven't categorized, so we show the prompt.
        if is_studying:
            return "Distraction-Medium"
        else:
            # Check if it *looks* like a lecture (to be safe)
            is_lecture = False
            for study_word in STUDY_KEYWORDS:
                if study_word in title_low:
                    is_lecture = True
                    break
            
            if is_lecture:
                if not prompt_is_showing and window_title != snoozed_lecture_title:
                    return "Prompt-Study-Mode" # Trigger the popup
                else:
                    return "Neutral" # It's a lecture, but we're snoozing it
            else:
                return "Distraction-Medium" # It's just a distraction

    # 5. Check High/Low Distractions
    for keyword in DISTRACTION_LEVELS.get("High", []):
        if keyword in title_low:
            return "Distraction-High"
    for keyword in DISTRACTION_LEVELS.get("Low", []):
        if keyword in title_low:
            return "Distraction-Low"

    # 6. Final Rule Check: If in Study Mode, all else is a distraction
    if is_studying:
        return "Distraction-Low"
        
    # --- # AI FIX ---
    # 7. If NO rules matched, ask the AI model.
    ai_prediction = ai_classifier.predict_category(window_title)
    
    if ai_prediction == 1:
        # AI thinks it's productive.
        print(f"AI classified '{window_title}' as Productive.")
        return "Productive" # <-- THIS IS THE FIX (was "Neutral")
    elif ai_prediction == 0:
        # AI thinks it's a distraction.
        print(f"AI classified '{window_title}' as Distraction.")
        return "Distraction-Low" 

    # 8. Default: It's just a neutral app
    return "Neutral"

# --- Core Logic: 'classify_activity' (The "Slow" Classifier) ---
def classify_activity(process_name, window_title):
    """
    Core Logic: This is the "Full, Accurate" classifier.
    It's SLOW because it uses the 'process_name' (from psutil)
    in addition to the 'window_title'.
    It now also uses the AI as a final fallback for logging.
    """
    global is_studying
    
    # Load rules from the global config
    PROCESS_RULES = current_config.get("PROCESS_RULES", {})
    PRODUCTIVE_KEYWORDS = current_config.get("PRODUCTIVE_KEYWORDS", [])
    DISTRACTION_LEVELS = current_config.get("DISTRACTION_LEVELS", {})
    STUDY_KEYWORDS = current_config.get("STUDY_KEYWORDS", [])

    # 1. Handle idle state
    if process_name is None and window_title is None: return "Idle"
    
    # 2. Check Process Rules (Most reliable)
    if process_name in PROCESS_RULES:
        category = PROCESS_RULES[process_name]
        # Return the category immediately if it's definitive
        if category == "Productive": return "Productive"
        if category == "Distraction-Low":
            return "Neutral" if is_studying else "Distraction-Low"
        if category == "Distraction-Medium": return "Distraction-Medium"
        if category == "Distraction-High": return "Distraction-High"
        if category == "Check-Title": pass # Tells logic to check title
        else: return category # e.g., "Neutral"

    # 3. Handle missing title (but we have a process name)
    if not window_title:
        return "Neutral" if not is_studying else "Distraction-Low"

    # 4. Check Title Keywords
    title_low = window_title.lower()
    for keyword in PRODUCTIVE_KEYWORDS:
        if keyword in title_low: return "Productive"
    
    # --- # NEW FIX: Check STUDY_KEYWORDS here too ---
    for keyword in STUDY_KEYWORDS:
        if keyword in title_low:
            return "Studying"
        
    is_medium_distraction = False
    for keyword in DISTRACTION_LEVELS.get("Medium", []):
        if keyword in title_low: is_medium_distraction = True; break
        
    if is_medium_distraction:
        if is_studying:
            # We already checked for "Studying"
            return "Distraction-Medium"
        else:
            # Score Fix: Log lectures as "Neutral" when not in study mode
            # We already checked for "Studying", so this is redundant,
            # but safe to leave.
            for study_word in STUDY_KEYWORDS:
                if study_word in title_low: return "Neutral"
            return "Distraction-Medium"
            
    for keyword in DISTRACTION_LEVELS.get("High", []):
        if keyword in title_low: return f"Distraction-High"
    for keyword in DISTRACTION_LEVELS.get("Low", []):
        if keyword in title_low: return "Distraction-Low"

    # 5. Check Study Mode
    if is_studying: return "Distraction-Low"
    
    # 6. AI Classification (for logging)
    # If no rules matched, ask the AI.
    ai_prediction = ai_classifier.predict_category(window_title)
    if ai_prediction == 1:
        return "Productive (AI)" # Log this as AI-found
    elif ai_prediction == 0:
        return "Distraction-Low (AI)" # Log this as AI-found

    # 7. Default
    return "Neutral"

# --- Core Logic: Helper Worker 1 'fast_tracker_thread' ---
def fast_tracker_thread(window_object, self_pid):
    """
    Core Logic: This is the "Fast" thread (Worker 1). Runs every 0.5s.
    Its ONLY job is to update the "Live Status" UI instantly.
    """
    print("Fast tracker thread (Worker 1) has started.")
    # Get the global variables this thread needs to communicate
    global current_app_title, current_hwnd, activity_lock
    global is_paused, pause_lock 
    global is_studying # Get the global study state
    
    last_distraction_category = None # State variable to prevent popup spam
    
    while True:
        # --- Pause Logic (Deadlock Fix) ---
        # 1. Check the pause state *without* holding the lock
        with pause_lock:
            paused_now = is_paused
        
        # 2. If paused, sleep and skip the loop.
        # This frees the lock for the main thread to "Resume".
        if paused_now:
            last_distraction_category = None # Reset state
            time.sleep(1.0) # Sleep to save CPU
            continue 
        
        # --- Main Tracking Logic ---
        try:
            # 1. Get active window
            app_title = None
            hwnd = None
            active_window = gw.getActiveWindow()
            if active_window:
                app_title = active_window.title
                hwnd = active_window._hWnd
                # Check if the active window is our own app
                pid = win32process.GetWindowThreadProcessId(hwnd)[1]
                if pid == self_pid:
                    continue # It's us, skip this loop
            
            # 2. Run the "Fast" classifier
            category = classify_by_title_only(app_title) 
            
            # 3. Handle "Prompt" category
            if category == "Prompt-Study-Mode":
                # Send the prompt event to the main UI
                window_object.write_event_value('-PROMPT_STUDY_MODE-', app_title)
                category = "Neutral" # Treat it as neutral for now
            
            # 4. Share data with the "Slow" thread
            with activity_lock:
                current_app_title = app_title
                current_hwnd = hwnd
            
            # 5. Send "Live Status" update to the UI
            gui_message = f"Cat: {category} | Title: {app_title if app_title else 'None'}"
            window_object.write_event_value('-UPDATE_APP-', gui_message)
            
            # 6. Lag Fix: Send popups *only* on state change
            current_category = None
            if category.startswith("Distraction-"):
                current_category = category
            
            if current_category != last_distraction_category:
                if current_category:
                    # --- # CRITICAL FIX (Silent Tracking) ---
                    # Only send a popup event if Study Mode is ON.
                    if is_studying:
                        print(f"FAST_THREAD: Sending ONE popup for {current_category}")
                        window_object.write_event_value('-DISTRACTION_EVENT-', (category, app_title if app_title else "Unknown Distraction"))
                last_distraction_category = current_category
                
            time.sleep(0.5) # This thread is fast
            
        except Exception as e:
            # Catch errors (like window closing)
            with activity_lock:
                current_app_title = None
                current_hwnd = None
            last_distraction_category = None 
            time.sleep(0.5)

# --- Core Logic: Helper Worker 2 'slow_logging_thread' ---
def slow_logging_thread(window_object):
    """
    Core Logic: This is the "Slow" thread (Worker 2). Runs every 5s.
    Its ONLY job is to do the "heavy" work:
    1. Get the .exe name (slow psutil call).
    2. Run the "slow" classifier.
    3. Save the result to the database (slow disk write).
    4. Calculate stats (slow database read).
    """
    print("Slow logging/stats thread (Worker 2) has started.")
    global current_app_title, current_hwnd, activity_lock
    global is_paused, pause_lock 
    
    last_pid = None
    last_process_name = None # Cache the last .exe name to speed things up
    
    while True:
        # --- Pause Logic (Deadlock Fix) ---
        with pause_lock:
            paused_now = is_paused
            
        if paused_now:
            time.sleep(5.0) 
            continue 

        # --- Main Logging Logic ---
        try:
            # 1. Get window data from the fast thread
            app_title = None
            hwnd = None
            with activity_lock:
                app_title = current_app_title
                hwnd = current_hwnd
            
            # 2. Get the .exe name (the "slow" part)
            process_name = None
            if hwnd:
                try:
                    pid = win32process.GetWindowThreadProcessId(hwnd)[1]
                    if pid > 0: # Check for valid PID
                        if pid == last_pid:
                            process_name = last_process_name # Use cache
                        else:
                            # The slow call:
                            process = psutil.Process(pid)
                            process_name = process.name()
                            last_pid = pid
                            last_process_name = process_name
                    else:
                        last_pid = None
                        last_process_name = None
                except Exception as e:
                    # Catch errors (e.g., "process PID not found")
                    print(f"Error during PID lookup: {e}")
                    last_pid = None
                    last_process_name = None
            else:
                last_pid = None
                last_process_name = None
            
            # 3. Run the "Slow" classifier
            category = classify_activity(process_name, app_title)
            
            # 4. Log the result to the database
            data_manager.log_event(category, app_title)
            
            # 5. Calculate all stats
            stats = focus_engine.calculate_daily_stats() 
            
            # 6. Send stats to the UI
            window_object.write_event_value('-STATS_UPDATE-', stats)
            
            time.sleep(5.0) # This thread is slow
            
        except Exception as e:
            print(f"Error in slow logging thread: {e}")
            last_pid = None
            last_process_name = None
            time.sleep(5.0)

# --- UI Function: 'create_history_window' ---
def create_history_window():
    """
    Utility: Creates and shows the 7-day history window.
    This window is "modal" (it blocks the main window).
    """
    # 1. Get the data from the focus engine
    stats_data = focus_engine.get_weekly_stats()
    
    headings = ['Date', 'Score', 'Productive Time']
    table_data = []
    
    # 2. Format the data for the UI table
    if not stats_data:
        table_data.append(["No data for last 7 days", "", ""])
    else:
        stats_data.sort(key=lambda x: x['date'], reverse=True)
        for row in stats_data:
            table_data.append([
                row['date'],
                f"{row['score']}%",
                format_time(row['prod_time_s'])
            ])

    # 3. Build the layout for the new window
    layout = [
        [sg.Text("Your 7-Day Focus History", font=("Helvetica", 16, "bold"))],
        [sg.Table(values=table_data,
                  headings=headings,
                  auto_size_columns=False,
                  col_widths=[12, 8, 15],
                  justification='left',
                  num_rows=min(len(table_data), 10),
                  key='-HISTORY_TABLE-')],
        [sg.Button("Close")]
    ]
    
    # 4. Create and show the window
    window = sg.Window("Focus History", layout, modal=True)
    
    # 5. Event loop for *this window only*
    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, "Close"):
            break
            
    window.close()

# --- UI Function: 'create_settings_window' ---
def create_settings_window():
    """
    Utility: Creates and shows the multi-tab Settings window.
    This is where users customize the app.
    """
    global current_config # We need this to "hot-reload"
    
    # --- Helper functions to convert lists to/from text blocks
    def list_to_str(lst): return "\n".join(lst)
    def str_to_list(s): return [line.strip() for line in s.split("\n") if line.strip()]

    # --- Tab 1: Process Rules ---
    # Load existing data from the config
    process_rules_data = []
    for proc, cat in current_config.get("PROCESS_RULES", {}).items():
        process_rules_data.append([proc, cat])
        
    process_tab_layout = [
        [sg.Text("Process Rules (e.g., 'Spotify.exe', 'Productive' or 'Distraction-Low')")],
        [sg.Table(values=process_rules_data, headings=["Process Name", "Category"], key='-PROC_TABLE-',
                  auto_size_columns=True, num_rows=10)],
        [sg.Text("Process:"), sg.Input(key='-PROC_ADD_NAME-', size=(20,1)),
         sg.Text("Category:"), sg.Input(key='-PROC_ADD_CAT-', size=(20,1)),
         sg.Button("Add/Update", key='-PROC_ADD-')],
        [sg.Text("Select row in table and click 'Remove':"), sg.Button("Remove Selected", key='-PROC_REMOVE-')]
    ]

    # --- Tab 2: Keyword Lists ---
    keyword_tab_layout = [
        [sg.Text("Productive Keywords (one per line)")],
        [sg.Multiline(list_to_str(current_config.get("PRODUCTIVE_KEYWORDS", [])), 
                       size=(60, 8), key='-PROD_KEYWORDS-')],
        [sg.Text("Study Keywords (one per line)")],
        [sg.Multiline(list_to_str(current_config.get("STUDY_KEYWORDS", [])), 
                       size=(60, 8), key='-STUDY_KEYWORDS-')],
        [sg.Text("Ignored Titles (one per line, exact match)")],
        [sg.Multiline(list_to_str(current_config.get("IGNORE_TITLES", [])), 
                       size=(60, 5), key='-IGNORE_TITLES-')]
    ]
    
    # --- Tab 3: Distraction Keywords ---
    dist_levels = current_config.get("DISTRACTION_LEVELS", {})
    distraction_tab_layout = [
        [sg.Text("Distraction Keywords (one per line)")],
        [sg.Text("Low Severity")],
        [sg.Multiline(list_to_str(dist_levels.get("Low", [])), size=(60, 5), key='-DIST_LOW-')],
        [sg.Text("Medium Severity")],
        [sg.Multiline(list_to_str(dist_levels.get("Medium", [])), size=(60, 8), key='-DIST_MEDIUM-')],
        [sg.Text("High Severity")],
        [sg.Multiline(list_to_str(dist_levels.get("High", [])), size=(60, 5), key='-DIST_HIGH-')]
    ]

    # --- Build the Settings Layout ---
    layout = [
        [sg.TabGroup([
            [sg.Tab("Process Rules", process_tab_layout)],
            [sg.Tab("Keyword Lists", keyword_tab_layout)],
            [sg.Tab("Distraction Keywords", distraction_tab_layout)]
        ])],
        [sg.Button("Save"), sg.Button("Cancel"), sg.Text("", key='-SAVE_STATUS-', text_color='green')]
    ]
    
    window = sg.Window("Settings", layout, modal=True, finalize=True)
    
    # --- Event Loop for Settings Window ---
    while True:
        event, values = window.read()
        
        if event in (sg.WIN_CLOSED, "Cancel"):
            break
            
        # --- Handle Process Rule Add/Update ---
        if event == '-PROC_ADD-':
            name = values['-PROC_ADD_NAME-']
            cat = values['-PROC_ADD_CAT-']
            if name and cat:
                # Check if it already exists to update it
                updated = False
                for i, row in enumerate(process_rules_data):
                    if row[0] == name:
                        process_rules_data[i][1] = cat
                        updated = True
                        break
                if not updated: # Add as a new row
                    process_rules_data.append([name, cat])
                # Refresh the table
                window['-PROC_TABLE-'].update(values=process_rules_data)
                # Clear the input boxes
                window['-PROC_ADD_NAME-'].update("")
                window['-PROC_ADD_CAT-'].update("")
        
        # --- Handle Process Rule Remove ---
        if event == '-PROC_REMOVE-':
            try:
                # Get the index of the row the user selected
                selected_row_index = values['-PROC_TABLE-'][0]
                # Remove it from our data list
                process_rules_data.pop(selected_row_index)
                # Refresh the table
                window['-PROC_TABLE-'].update(values=process_rules_data)
            except IndexError:
                sg.popup_error("No row selected to remove.")
            except Exception as e:
                sg.popup_error(f"Error removing row: {e}")
                
        # --- Handle Save ---
        if event == "Save":
            try:
                # 1. Create a new config dictionary from the UI elements
                new_config = {}
                
                # Rebuild the Process Rules dictionary
                new_config["PROCESS_RULES"] = {row[0]: row[1] for row in process_rules_data}
                
                # Rebuild the keyword lists
                new_config["PRODUCTIVE_KEYWORDS"] = str_to_list(values['-PROD_KEYWORDS-'])
                new_config["STUDY_KEYWORDS"] = str_to_list(values['-STUDY_KEYWORDS-'])
                new_config["IGNORE_TITLES"] = str_to_list(values['-IGNORE_TITLES-'])
                
                # Rebuild the distraction levels dictionary
                new_config["DISTRACTION_LEVELS"] = {
                    "Low": str_to_list(values['-DIST_LOW-']),
                    "Medium": str_to_list(values['-DIST_MEDIUM-']),
                    "High": str_to_list(values['-DIST_HIGH-'])
                }
                
                # Preserve V2 settings (if they exist) so we don't delete them
                new_config["WEBCAM_ENABLED"] = current_config.get("WEBCAM_ENABLED", False)
                new_config["WEBCAM_SENSITIVITY"] = current_config.get("WEBCAM_SENSITIVITY", {})

                # 2. Save the new config to config.json
                if config_manager.save_config(new_config):
                    # 3. "Hot-Reload" the config in the main app
                    current_config = new_config 
                    window['-SAVE_STATUS-'].update("Saved! Rules hot-reloaded.")
                else:
                    window['-SAVE_STATUS-'].update("Error saving!", text_color='red')
            except Exception as e:
                sg.popup_error(f"Failed to build config: {e}")
                
    window.close()
    
# --- UI Function: 'create_how_to_use_window' ---
def create_how_to_use_window():
    """
    Utility: Creates and shows the new "How to Use" window.
    This is the user guide you requested.
    """
    # This text uses '\n' to create new lines
    guide_text = """
Welcome to FLOW!
This app runs in the background to track your productivity.

--- HOW TO USE ---

1. Just Let it Run
The 'Live Status' shows what app FLOW sees. The timers
will update every 5 seconds.

2. Use 'Study Mode'
Click 'Start Study Mode' when you need to focus (like
for a lecture). In this mode, *only* apps and websites
on your 'Productive' or 'Study' lists are allowed.
Everything else will trigger a distraction alert.

3. Use the 'Pause' Button
Click 'Pause' when you're taking a real break (like
getting coffee). This freezes all tracking. Click 'Resume'
when you're back.

4. The Smart Lecture Prompt
If you are *not* in Study Mode and you open a lecture
on YouTube, FLOW will ask if you want to enable
Study Mode. Click 'No' to snooze the alert for that video.

5. Customize Your Rules
Click 'Settings' to teach FLOW what *you* consider
productive or distracting. You can add .exe names
(like 'photoshop.exe') or website keywords
(like 'my-school-portal.com').
"""
    
    help_layout = [
        [sg.Text("How to Use FLOW", font=("Helvetica", 16, "bold"))],
        [sg.HSeparator()],
        # Create a multiline text element that is read-only
        [sg.Text(guide_text, font=("Helvetica", 10))],
        [sg.HSeparator()],
        [sg.Button("Close")]
    ]

    # Create a modal window.
    window = sg.Window("How to Use", layout=[[sg.Column(help_layout)]], modal=True)
    
    # Simple event loop for the Help window
    while True:
        event, values = window.read()
        if event in (sg.WIN_CLOSED, "Close"):
            break
            
    window.close()

# --- Main App Startup ---
# 1. Initialize the database (creates flow_data.db if needed)
data_manager.init_database()
# 2. Get our own Process ID to ignore ourselves
self_pid = os.getpid()
print(f"Main App PID: {self_pid}")

# --- # UPDATED: GUI Layout (Using your new title) ---
# 1. Title/Logo Row - Using your exact layout
title_layout = [
    [
        # Center the column that holds the two lines of text
        sg.Column([
            [sg.Text("  F   -   L   -     O    -   W", font=("Helvetica", 24, "bold"), pad=(0, 0))],
            [sg.Text("Focus - Learn - Organise - Work", font=("Helvetica", 18, "bold", "italic"), pad=(0, 0))]
        ], pad=(0,0), element_justification='c')
    ]
]

# 2. Stats Column (Now with Predicted Score)
stats_column = [
    [sg.Text("DAILY FOCUS SCORE", font=("Helvetica", 14, "bold"), justification='c', expand_x=True)],
    [sg.Text("0%", key='-SCORE-', font=("Helvetica", 40, "bold"), justification='c', size=(10,1), expand_x=True)],
    
    # This Text element will be updated with the predicted score
    [sg.Text("Predicted End-of-Day Score: 0%", key='-PRED_SCORE-',
             font=("Helvetica", 10, "italic"), justification='c', expand_x=True)],
             
    [sg.HSeparator()],
    [sg.Text("Productive Time:", size=(15,1)), sg.Text("0m 0s", key='-PROD_TIME-')],
    [sg.Text("Distracting Time:", size=(15,1)), sg.Text("0m 0s", key='-DIST_TIME-')],
    [sg.Text("Neutral Time:", size=(15,1)), sg.Text("0m 0s", key='-NEUT_TIME-')],
]

# 3. Activity Column
activity_column = [
    [sg.Text("LIVE STATUS", font=("Helvetica", 14, "bold"))],
    [sg.Text("Watching...", key='-APP_TEXT-', size=(50, 2))], 
    [sg.HSeparator()],
    [
        sg.Text("Mode: Relaxing ☕", key='-MODE_TEXT-', font=("Helvetica", 12)),
        sg.Push(), # Pushes the button to the right
        sg.Button("Start Study Mode", key='-STUDY_TOGGLE-')
    ],
]

# 4. Button Column
button_column = [
    [
        sg.Button("Pause", key='-PAUSE_TOGGLE-', expand_x=True), 
        sg.Button("History", key='-SHOW_HISTORY-', expand_x=True),
        sg.Button("Settings", key='-SHOW_SETTINGS-', expand_x=True),
    ],
    [
        sg.Button("How to Use", key='-SHOW_HOW_TO_USE-', expand_x=True, button_color=('white', '#0073E6')),
        sg.Button("Exit", expand_x=True, button_color=('white', '#FF0000'))
    ]
]

# 5. Final Layout
# This stacks all the columns on top of each other.
layout = [
    [sg.Column(title_layout, element_justification='c', expand_x=True)], # Centered the title
    [sg.HSeparator()],
    [sg.Column(stats_column, element_justification='c')],
    [sg.HSeparator()],
    [sg.Column(activity_column, element_justification='l')],
    [sg.VPush()], # A blank "spring" to push buttons to the bottom
    [sg.Column(button_column, element_justification='c')]
]

# Create the main window
window = sg.Window("FLOW Dashboard", layout, finalize=True, size=(400, 600)) 

# --- Start The Threads ---
# These run in the background. 'daemon=True' means they will
# automatically close when the main window closes.
threading.Thread(target=fast_tracker_thread, args=(window, self_pid), daemon=True).start()
threading.Thread(target=slow_logging_thread, args=(window,), daemon=True).start()

# --- Main GUI Event Loop ---
# This is the "heart" of the app. It waits for user clicks
# or messages from the background threads.
while True:
    # This line "reads" events. It's the only line that can
    # update the UI.
    event, values = window.read()

    # --- Event: User clicks 'Exit' or 'X' ---
    if event == "Exit" or event == sg.WIN_CLOSED:
        break
        
    # --- Event: User clicks 'History' ---
    if event == '-SHOW_HISTORY-':
        create_history_window()

    # --- Event: User clicks 'Settings' ---
    if event == '-SHOW_SETTINGS-':
        create_settings_window()
        
    # --- Event: User clicks 'How to Use' ---
    if event == '-SHOW_HOW_TO_USE-':
        create_how_to_use_window()
        
    # --- Event: User clicks 'Pause/Resume' ---
    if event == '-PAUSE_TOGGLE-':
        # Use the lock to safely change the global variable
        with pause_lock:
            is_paused = not is_paused
        
        # Update the UI to show the new state
        if is_paused:
            window['-PAUSE_TOGGLE-'].update("Resume")
            window['-APP_TEXT-'].update("... PAUSED ...")
            window['-MODE_TEXT-'].update(text_color='grey') 
        else:
            window['-PAUSE_TOGGLE-'].update("Pause")
            window['-APP_TEXT-'].update("Watching...")
            # Use the default text color from the (non-existent) theme
            window['-MODE_TEXT-'].update(text_color=sg.theme_text_color())


    # --- Event: From 'fast_tracker_thread' (every 0.5s) ---
    if event == '-UPDATE_APP-':
        # Don't update the status text if the app is paused
        if not is_paused:
            window['-APP_TEXT-'].update(values[event])

    # --- Event: From 'fast_tracker_thread' (one-time) ---
    if event == '-DISTRACTION_EVENT-':
        category, title = values[event]
        level = category.split('-')[1]
        
        # Show different popups based on severity
        if level == "Low":
            sg.popup_notify("Minor distraction. Stay focused!", title=f"FLOW Alert: {title}")
        elif level == "Medium":
            sg.popup_notify("You're off track! Get back to it!", title=f"FLOW: Major Distraction: {title}")
        elif level == "High":
            # This is a *blocking* popup
            sg.popup("HIGH SEVERITY DETECTED.\nReturning to focus.", title=f"!!! FLOW CRITICAL ALERT: {title} !!!")

    # --- Event: From 'fast_tracker_thread' (lecture found) ---
    if event == '-PROMPT_STUDY_MODE-':
        if not prompt_is_showing: # Prevent spamming popups
            prompt_is_showing = True
            app_title = values[event]
            response = sg.popup_yes_no(
                f"Looks like a lecture:\n\n'{app_title}'\n\nEnable Study Mode?",
                title="Lecture Detected!"
            )
            
            if response == "Yes":
                # Toggle Study Mode on
                is_studying = True
                window['-MODE_TEXT-'].update("Mode: Studying 📚")
                window['-STUDY_TOGGLE-'].update("End Study Mode")
                snoozed_lecture_title = None # Clear any snoozes
            else:
                # User clicked "No", so snooze this lecture title
                print(f"Snoozing prompt for: {app_title}")
                snoozed_lecture_title = app_title
            
            prompt_is_showing = False # Allow new prompts

    # --- Event: From 'slow_logging_thread' (every 5s) ---
    if event == '-STATS_UPDATE-':
        # This is where the timers get updated
        stats = values[event]
        window['-SCORE-'].update(f"{stats['score']}%")
        window['-PROD_TIME-'].update(format_time(stats['prod_time_s']))
        window['-DIST_TIME-'].update(format_time(stats['dist_time_s']))
        window['-NEUT_TIME-'].update(format_time(stats['neut_time_s'])) 
        window['-PRED_SCORE-'].update(f"Predicted End-of-Day Score: {stats['predicted_score']}%")
        
    # --- Event: User clicks 'Start/End Study Mode' ---
    if event == '-STUDY_TOGGLE-':
        is_studying = not is_studying
        # --- Snooze Fix: Manually toggling mode ALWAYS clears any snooze. ---
        snoozed_lecture_title = None 
        
        # Update the UI
        if is_studying:
            window['-MODE_TEXT-'].update("Mode: Studying 📚")
            window['-STUDY_TOGGLE-'].update("End Study Mode")
        else:
            window['-MODE_TEXT-'].update("Mode: Relaxing ☕")
            window['-STUDY_TOGGLE-'].update("Start Study Mode")

# --- Cleanup ---
# Once the loop breaks, close the window.
window.close()