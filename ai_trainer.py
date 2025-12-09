# ai_trainer.py (v1.3 - 80/20 Train-Test Split & Better Data)

# --- Imports ---
import joblib  # To save the model
import numpy as np # To calculate the average/std of scores

# --- sklearn Imports ---
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import cross_val_score # To test the model

print("Starting AI model training...")

# --- 1. Core Logic: Training Data ---
# This dataset is now much larger to fix the bugs you found.
train_data = [
    # --- Productive (1) ---
    ("Python tutorial for beginners", 1),
    ("GeeksforGeeks Data Structures", 1),
    ("CS50 Lecture on Algorithms", 1),
    ("How to use Git and GitHub", 1),
    ("Database Management Systems (DBMS) full course", 1),
    ("Theory of Computation (TOC) explained", 1),
    ("React JS crash course", 1),
    ("My School Portal Login", 1),
    ("Project documentation - Google Docs", 1),
    ("Stack Overflow - How to fix error", 1),
    ("Visual Studio Code - main.py", 1),
    ("PyCharm - my_project", 1),
    ("ECE 301 Homework 4 - Google Docs", 1),
    ("Understanding Python Classes and Objects", 1),
    ("How to build a linked list in C++", 1),
    ("MIT 6.006: Introduction to Algorithms (Fall 2011)", 1),
    ("My Resume - Microsoft Word", 1),
    ("Python Pandas DataFrame tutorial", 1),
    ("SQL Joins Explained", 1),
    ("Java Full Course for Beginners", 1),
    ("GitHub - my-project-repo", 1),
    ("AWS EC2 instance setup guide", 1),
    ("Reading documentation on MDN", 1),
    ("How to use Figma - UI/UX Design", 1),
    ("Linear Algebra: Vector Spaces", 1),
    ("*dsa - Notepad", 1),
    ("*heapsort algorithm - Notepad", 1),
    ("binary search tree implementation", 1),
    ("Operating Systems: Processes vs Threads", 1),
    ("neural networks explained", 1),
    ("What is REST API?", 1),
    ("ECE project ideas", 1),
    ("Computer Networks lecture", 1),
    ("Google Gemini - Google Chrome", 1),
    ("Understanding Kubernetes and Docker", 1),
    ("*bellman ford algorithm testing - Notepad", 1),
    ("*alakh pandey lecture - Notepad", 1),
    ("*sanchit kumar dbms lectures - Notepad", 1),
    ("*big algorithm - Notepad", 1),

    # --- Distraction (0) ---
    ("Top 10 funny cat videos", 0),
    ("MrBeast new video", 0),
    ("Gaming stream highlights", 0),
    ("Spotify - Chillhop Beats", 0),
    ("Reddit - r/all", 0),
    ("Instagram feed", 0),
    ("Netflix - New Movie trailer", 0),
    ("Lofi hip hop radio - beats to relax/study to", 0), 
    ("CS:GO matchmaking", 0),
    ("Funny moments compilation", 0),
    ("Twitch - Asmongold stream", 0),
    ("Discord - General Chat", 0),
    ("Twitter / X", 0),
    ("Facebook", 0),
    ("Amazon.com - Shopping", 0),
    ("best gaming gear 2025", 0),
    ("Valorant gameplay", 0),
    ("PewDiePie new video", 0),
    ("How to get rich quick", 0),
    ("League of Legends cinematic", 0),
    ("Meme compilation 2025", 0),
    ("Anitrendz", 0),
    ("MyAnimeList", 0),
    ("Steam Store", 0),
    ("Lethal Company - Funny Moments", 0),
    ("ambient study music", 0),
    ("CS:GO funny moments", 0),
    ("Twitch stream VOD", 0),
    ("Anime opening compilation", 0),
    ("Learn Python in 10 minutes", 0),
    ("Shopping for new shoes", 0),
    ("FC 24 Ultimate Team", 0),
    ("Elden Ring boss fight no-hit run", 0),
    ("Untitled - Notepad", 0),
    ("Search", 0),
    ("*elden - Notepad", 0),
    ("*clash of clans - Notepad", 0),
    ("*clash of clans base alignment - Notepad", 0),
    ("*bgmi fps trick - Notepad", 0),
    ("Amazon.in : dumbell set - Google Chrome", 0),
    ("Amazon.in Shopping Cart - Google Chrome", 0),
    ("WhatsApp", 0),
    ("*alakh pandey lectures - Notepad", 0), # 'lectures' (plural) could be a playlist
]

# --- 2. Core Logic: Data Preparation ---
# Separate the data into titles (X) and labels (y)
X = [item[0] for item in train_data]
y = [item[1] for item in train_data]

# --- 3. Core Logic: Model Creation ---
# This is the same pipeline as before.
model = make_pipeline(
    TfidfVectorizer(),
    MultinomialNB()
)

# --- 4. Core Logic: Cross-Validation Test ---
print("\n--- AI CROSS-VALIDATION TEST ---")
print(f"Testing model on {len(X)} examples using 5-fold validation...")

# This automatically does the 80/20 split 5 times and gives us the average
scores = cross_val_score(model, X, y, cv=5, n_jobs=-1) # n_jobs=-1 uses all CPU cores

print("\n--- TEST RESULTS ---")
print(f"Scores on each of the 5 tests: {scores}")
print(f"Average Accuracy: {np.mean(scores) * 100:.2f}%")
print("--------------------")

# --- 5. Core Logic: Final Model Training ---
print("\n--- FINAL MODEL TRAINING ---")
print("Re-training model on 100% of the data...")
model.fit(X, y) # Train on ALL X and y

# 6. Save the final, fully-trained model to a file
model_filename = 'ai_model.joblib'
joblib.dump(model, model_filename)

print(f"Final, fully-trained model saved to {model_filename}!")