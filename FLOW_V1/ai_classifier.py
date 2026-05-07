# ai_classifier.py (v1.1 - The "Packager" Fix)

# --- Imports ---
import joblib  # Reason: To load the pre-trained .joblib model file.
import os      # Reason: To check if the model file exists.
import sys     # Reason: To check if we are in "packaged" mode.

# --- Core Logic: Helper Function for PyInstaller ---
def resource_path(relative_path):
    """
    Utility: Get the absolute path to a resource, which works for
    both development ("live") and PyInstaller ("frozen") modes.
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

# --- Core Logic: Load the Model ---
# Use the new helper function to find the model
MODEL_FILE = resource_path('ai_model.joblib')

def load_model():
    """
    Utility: Loads the pre-trained model file from disk.
    """
    # 1. Check if the model file exists at the path.
    if not os.path.exists(MODEL_FILE):
        print(f"FATAL ERROR: '{MODEL_FILE}' not found at {MODEL_FILE}.")
        print("Please run 'python ai_trainer.py' first to create the model.")
        return None
    
    try:
        # 2. Load the file from disk into memory.
        model = joblib.load(MODEL_FILE)
        print("AI text classification model loaded successfully.")
        return model
    except Exception as e:
        print(f"Error loading AI model: {e}")
        return None

# Load the model *once* when the app starts.
ai_model = load_model()

# --- Core Logic: Predict Category ---
def predict_category(title):
    """
    Core Logic: Predicts if a title is productive (1) or distracting (0).
    This is called by the "fast" classifier in main.py.
    """
    # 1. Make sure the model loaded correctly.
    if ai_model is None:
        return None # Model failed to load, so we can't predict

    try:
        # 2. 'model.predict()' is extremely fast (no lag).
        prediction = ai_model.predict([title])
        
        # 3. The result is an array, so we get the first item.
        return prediction[0]
        
    except Exception as e:
        print(f"AI prediction error: {e}")
        return None