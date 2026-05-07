# ai_trainer.py (v1.3 - 80/20 Train-Test Split & Better Data)

# --- Imports ---
import joblib  # To save the model
import numpy as np # To calculate the average/std of scores

# --- sklearn Imports ---
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.pipeline import make_pipeline
from sklearn.model_selection import cross_val_score # To test the model
from data_manager import get_ai_feedback # Import feedback function
import os

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
    ("*big algorithm - Notepad", 1),
    ("Notepad - engineering notes", 1),
    ("Notepad - math homework", 1),
    ("Notepad - python code snippet", 1),
    ("circuit analysis - Notepad", 1),
    ("study schedule - Notepad", 1),
    ("project requirements.txt - Notepad", 1),
    ("*parseval - Notepad", 1),
    ("*fourier series - Notepad", 1),
    ("*laplace transform - Notepad", 1),
    ("*maxwell equations - Notepad", 1),
    ("*quantum mechanics - Notepad", 1),
    ("*organic chemistry - Notepad", 1),
    ("*microprocessors - Notepad", 1),
    ("*data structures - Notepad", 1),
    ("Python tutorial video", 1),
    ("Machine learning lecture", 1),
    ("DBMS full course", 1),
    ("DSA tips and tricks", 1),
    ("Calculus tutorial", 1),
    ("Physics Wallah - Motion lecture", 1),
    ("Unacademy - UPSC course", 1),




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
    ("*elden - Notepad", 0),
    ("*clash of clans - Notepad", 0),
    ("*clash of clans base alignment - Notepad", 0),
    ("*bgmi fps trick - Notepad", 0),
    ("Amazon.in : dumbell set - Google Chrome", 0),
    ("Amazon.in Shopping Cart - Google Chrome", 0),
    ("WhatsApp", 0),
    ("*movies to watch - Notepad", 0),
    ("*games to play - Notepad", 0),
    ("*sexy videos - Notepad", 0),
    ("*porn - Notepad", 0),
    ("*sexy - Notepad", 0),
    ("*love letter - Notepad", 0),
    ("*shopping list - Notepad", 0),
    ("*random stuff - Notepad", 0),
    ("*chat - Notepad", 0),
    ("*social media links - Notepad", 0),
    ("sexy", 0),
    ("porn", 0),
    ("hot girls", 0),
    ("nude", 0),
    ("adult", 0),
    ("dating", 0),
    ("tinder", 0),
    ("instagram", 0),
    ("facebook", 0),
    ("youtube shorts", 0),
    ("tik tok", 0),
    ("reels", 0),
    ("adult videos", 0),
    ("pornography", 0),
    ("xxx videos", 0),

    # --- Neutral (2) ---
    ("Untitled - Notepad", 2),
    ("Notepad", 2),
    ("New Tab", 2),
    ("Settings", 2),
    ("Control Panel", 2),
    ("Calculator", 2),
    ("File Explorer", 2),
    ("My Computer", 2),
    ("Desktop", 2),
    ("Downloads", 2),
    ("Recycle Bin", 2),
    ("* - Notepad", 2),
    ("*a - Notepad", 2),
    ("*ad - Notepad", 2),
    ("*cat - Notepad", 2),
    ("*i - Notepad", 2),
    ("*p - Notepad", 2),
    ("*v - Notepad", 2),
    ("Google Search", 2),
    ("Search", 2),
]

# --- 1b. Load User Feedback ---
print("Checking for user feedback in database...")
try:
    feedback_data = get_ai_feedback()
    if feedback_data:
        print(f"Adding {len(feedback_data)} pieces of user feedback to training set.")
        for title, cat_str in feedback_data:
            # Map "Productive" -> 1, "Distraction" -> 0, "Neutral" -> 2
            if cat_str == "Productive": label = 1
            elif cat_str == "Distraction": label = 0
            else: label = 2
            train_data.append((title, label))
    else:
        print("No user feedback found yet.")
except Exception as e:
    print(f"Could not load feedback: {e}")

# --- 1c. Add specific edge cases for 'alakh pandey' etc.
train_data.extend([
    ("alakh pandey physics lectures", 1),
    ("physics wallah alakh pandey", 1),
    ("alakh pandey chemistry", 1),
    ("coding ninja tutorials", 1),
    ("whiteboard coding practice", 1),
    ("LeetCode - Problem Solving", 1),
    ("YouTube - MrBeast burger", 0),
    ("Minecraft parkour", 0),
    ("Roblox gameplay", 0),
    ("adult videos porn", 0),
    ("porn videos", 0),
    ("sexy adult clips", 0),
    ("Minecraft hardcore tutorial", 0),
    ("Minecraft lecture", 0),
    ("COD tips and tricks", 0),
    ("Valo gameplay hacks", 0),
    ("Cooking tutorial", 0),
    ("Movie recap video", 0),
    ("GTA 5 funny moments", 0),
])

# --- 2. Core Logic: Data Preparation ---
# Separate the data into titles (X) and labels (y)
X = [item[0] for item in train_data]
y = [item[1] for item in train_data]

# --- 3. Core Logic: Model Creation ---
# Word-level features are better for meaning.
model = make_pipeline(
    TfidfVectorizer(analyzer='word', ngram_range=(1, 3)),
    LinearSVC(dual=False)
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
