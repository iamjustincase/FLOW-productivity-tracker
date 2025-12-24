# config_manager.py (v1.1 - The "Correct Default" Fix)

# --- Imports ---
import json  # Reason: To read and write the .json file.
import os    # Reason: To check if the config.json file exists.

# --- Constants ---
# Defines the constant name for the configuration file.
CONFIG_FILE = "config.json"

# --- Utility Function ---
def get_default_config():
    """ 
    Utility: Returns the hard-coded default config if file is missing.
    This function now contains the full, correct V1 configuration.
    """
    return {
      "PROCESS_RULES": {
        "Code.exe": "Productive",
        "pycharm64.exe": "Productive",
        "idea64.exe": "Productive",
        "WINWORD.EXE": "Productive",
        "EXCEL.EXE": "Productive",
        "powershell.exe": "Productive",
        "Postman.exe": "Productive",
        "GitHub Desktop.exe": "Productive",
        "Spotify.exe": "Distraction-Low",
        "Discord.exe": "Distraction-Medium",
        "chrome.exe": "Check-Title",
        "msedge.exe": "Check-Title",
        "firefox.exe": "Check-Title"
      },
      "PRODUCTIVE_KEYWORDS": [
        "visual studio code",
        "pycharm",
        "google gemini",
        "docs.google.com",
        "stackoverflow.com",
        "github.com",
        "geeksforgeeks",
        "w3schools",
        "tutorialspoint",
        "medium.com"
      ],
      "DISTRACTION_LEVELS": {
        "Low": [
          "Apple Music"
        ],
        "Medium": [
          "- youtube",
          "reddit -",
          "twitter",
          " x ",
          "facebook",
          "instagram",
          "9gag"
        ],
        "High": [
          "porn",
          "xvideos",
          "phub"
        ]
      },
      "STUDY_KEYWORDS": [
        "dbms",
        "toc",
        "data structures",
        "dsa",
        "algorithms",
        "operating systems",
        "os",
        "computer networks",
        "cn",
        "machine learning",
        "artificial intelligence",
        "ai",
        "sql tutorial",
        "java tutorial",
        "c++ tutorial",
        "python tutorial",
        "javascript tutorial",
        "lecture",
        "tutorial",
        "course",
        "mit",
        "freecodecamp",
        "crash course",
        "full course",
        "study with me",
        "heapsort",
        "bellman ford"
      ],
      "IGNORE_TITLES": [
        "task switching",
        "search",
        "start",
        "new tab"
      ]
    }

# --- Core Logic ---
def load_config():
    """
    Core Logic: Reads the config.json file and returns it as a dictionary.
    This is what the app calls on startup.
    """
    if not os.path.exists(CONFIG_FILE):
        print(f"Warning: {CONFIG_FILE} not found. Checking for defaults.")
        # Try to load from config.example.json first
        if os.path.exists("config.example.json"):
             try:
                with open("config.example.json", 'r') as f:
                    default_data = json.load(f)
                save_config(default_data) # Create the real config file
                return default_data
             except:
                 pass # Fallback to hardcoded defaults
        
        print("Creating default config from internal defaults.")
        save_config(get_default_config())

    try:
        with open(CONFIG_FILE, 'r') as f:
            config_data = json.load(f)
        return config_data
    except json.JSONDecodeError:
        print(f"ERROR: {CONFIG_FILE} is corrupted. Loading defaults.")
        return get_default_config()
    except Exception as e:
        print(f"Failed to load config: {e}")
        return get_default_config()

# --- Utility Function ---
def save_config(config_data):
    """
    Utility: Saves the given dictionary to the config.json file.
    This is called by the "Save" button in the Settings window.
    """
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config_data, f, indent=2) 
        print("Config saved successfully.")
        return True
    except Exception as e:
        print(f"ERROR: Failed to save config: {e}")
        return False