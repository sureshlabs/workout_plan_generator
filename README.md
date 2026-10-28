# 🏋️ Workout Plan Generator

An AI-powered workout planning application built with **Python, Streamlit, and the Groq API**. It generates personalized weekly workout plans based on fitness goals, experience level, workout availability, available equipment, and physical limitations.

## 📌 Project Overview

The Workout Plan Generator uses a Large Language Model (LLM) to create practical, structured workout plans tailored to individual preferences. It focuses on prompt engineering, structured user inputs, error handling, and a simple interactive interface.

This project was developed as part of the **Codebasics AI Engineering Cohort assignment**.

## ✨ Features

- **Personalized Workout Plans:** Generate workout plans based on fitness goals and experience levels.
- **Multiple Fitness Goals:** Build muscle, lose fat, improve general fitness, or improve endurance.
- **Flexible Workout Schedule:** Choose between 1 and 7 workout days per week.
- **Equipment Selection:** Supports no equipment, home dumbbells, full gym access, cardio and strength equipment, and resistance bands.
- **Injury and Limitation Awareness:** Provide optional information about injuries or exercise restrictions.
- **Regenerate Workout Plans:** Generate different workout variations while preserving the selected preferences.
- **Swap an Exercise:** Replace an individual exercise with a suitable alternative.
- **Markdown Formatting:** Display workout plans with headings, exercise names, sets, repetitions, durations, and rest periods.
- **Download Workout Plans:** Download the latest workout plan as a Markdown (`.md`) file.
- **Session State Management:** Retain the current plan and user preferences across Streamlit reruns.
- **Error Handling:** Handle missing inputs, API failures, rate limits, connection errors, and empty AI responses with user-friendly messages.

## 🛠️ Technology Stack

| Technology                 | Purpose                                               |
| -------------------------- | ----------------------------------------------------- |
| Python                     | Application logic and prompt construction             |
| Streamlit                  | Interactive web interface                             |
| Groq API                   | LLM-powered workout plan generation                   |
| Groq Python SDK            | Communication with the Groq API                       |
| python-dotenv              | Load environment variables from a `.env` file         |
| Regular Expressions (`re`) | Exercise extraction, validation, and Markdown cleanup |

## 📂 Project Structure

```text
WorkoutPlanGenerator/
├── app.py              # Streamlit application and workout logic
├── .env                # API configuration (not committed)
├── .gitignore          # Excludes secrets and generated files
├── requirements.txt    # Python dependencies
└── README.md           # Project documentation
```

## ⚙️ Prerequisites

Before running the application, ensure you have:

- Python 3.10 or later, compatible with the dependencies you install
- A Groq API key
- An internet connection
- `pip` installed

## 🚀 Installation and Setup

### 1. Clone the repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd WorkoutPlanGenerator
```

### 2. Create a virtual environment

**Windows (PowerShell):**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root:

```dotenv
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=openai/gpt-oss-20b
```

Replace `your_groq_api_key` with your actual Groq API key. Confirm that the configured model is available to your Groq account.

**Security:** Never commit your `.env` file or expose your API key in source code, screenshots, or public repositories.

### 5. Run the application

```bash
streamlit run app.py
```

Streamlit will display a local URL, usually:

```text
http://localhost:8501
```

Open the URL in your browser to use the application.

## 📝 How to Use

1. Select your fitness goal.
2. Choose your experience level: Beginner, Intermediate, or Advanced.
3. Select the number of workout days per week.
4. Choose your available equipment.
5. Optionally describe injuries or physical limitations.
6. Click **Generate Workout Plan**.
7. Review the generated weekly plan.
8. Use **Regenerate Plan** to request another variation.
9. Use **Swap an Exercise** to replace an individual exercise.
10. Click **Download Workout Plan (.md)** to save the latest version.
