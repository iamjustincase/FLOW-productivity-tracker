# FLOW (Focus - Learn - Organise - Work)

![Status](https://img.shields.io/badge/Status-Ready%20to%20Package-success)
![Version](https://img.shields.io/badge/Version-v1.8.2-blue)
![Python](https://img.shields.io/badge/Python-3.12-yellow)

FLOW is a desktop productivity tracker built in Python that monitors active window titles and processes to classify user activity as "Productive", "Distracting", or "Neutral". It features a real-time dashboard, a daily focus score, and an AI-powered classification engine.

## Demo & Screenshots

[![Watch the Demo](https://img.youtube.com/vi/vXpPmesqkN8/0.jpg)](https://youtu.be/vXpPmesqkN8)
*Click the image above to watch the demo video.*

### Dashboard
![Dashboard](assets/screenshots/1.png)

### Productive State
![Productive](assets/screenshots/2%20-%20productive.png)

### Distracted State
![Distracted](assets/screenshots/3%20-%20distractive.png)

### Study Mode Prompt
![Study Mode](assets/screenshots/5%20-%20studymode%20prompt%20productive.png)

## Features

*   **Real-time Dashboard**: View your current status and daily stats instantly.
*   **AI-Powered Classification**: Uses a Naive Bayes classifier to detect productive apps even without manual rules.
*   **Study Mode & Smart Prompts**: Enforce focus during lectures. Detects lecture videos and prompts you to enter Study Mode.
*   **Daily Focus Score**: dynamic score based on your activity ratio and remaining time.
*   **Multi-threaded Architecture**: Ensures the UI never freezes, even during heavy data processing.

## Installation

1.  Clone the repository.
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Run the application:
    ```bash
    python main.py
    ```

## Usage

1.  **Dashboard**: The main window shows your current activity category and daily stats.
2.  **Study Mode**: Click "Start Study Mode" to block distractions. Any non-productive app will trigger an alert.
3.  **Settings**: Customize your experience by adding specific process names (e.g., `code.exe`) or keywords to the whitelist/blacklist.
4.  **History**: View your 7-day focus history.

## Roadmap

### V1 (Current)
*   **Status**: Core tracking, AI, and GUI are complete. Ready for packaging.
*   **Version**: v1.8.2

### V2 (Planned)
*   **Major Tech Switch**: Rewrite the entire UI in **PyQt** (moving away from FreeSimpleGUI) to eliminate lag and improve aesthetics.
*   **New "Killer" Feature**: **Webcam-based AI** to detect when you lose focus.
    *   Detects gaze direction (looking away).
    *   Detects phone usage.
*   **AI Libraries**: Integration of **OpenCV** and **MediaPipe**.

## Technical Architecture

The application uses a **Tiered Multi-Threaded Architecture**:
*   **Main Thread**: Handles UI rendering (FreeSimpleGUI).
*   **Fast Worker (0.5s)**: Checks window titles for immediate "Live Status" updates.
*   **Slow Worker (5.0s)**: Handles heavy process ID lookups, database logging, and AI classification.

## Project Structure

*   `main.py`: Entry point and GUI logic.
*   `focus_engine.py`: Statistics and scoring logic.
*   `ai_classifier.py`: AI model wrapper.
*   `data_manager.py`: Database interactions.
*   `config_manager.py`: Configuration management.
*   `assets/`: Icons and resources.
*   `docs/`: Project analysis and reports.
