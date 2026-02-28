# Company-Specific Mock Technical Interview Agent

An AI-powered, full-stack web application that simulates realistic technical interviews. Tailor your practice sessions to specific companies, roles, levels, and round types.

![Mock Interview Agent Banner](https://via.placeholder.com/800x400.png?text=Mock+Interview+Agent)

## 🚀 Features

- **🎯 Highly Customizable:** Select your target company (e.g., Google, JPMorgan), Role (SDE, Data Analyst), Level, and Round Type (DSA, System Design, SQL, ML).
- **🤖 3-Agent AI Architecture:** Powered by specialized autonomous LLMs:
  - **The Planner:** Generates a custom difficulty rubric and topic based on the company's real-world hiring bar.
  - **The Interviewer:** Conducts the interview step-by-step. It asks a question, waits for clarification, demands time/space complexity analysis, and *never* gives away the answer.
  - **The Evaluator:** Reviews the entire transcript and code execution logs to generate a final 5-dimension scorecard and a "Hire / No Hire" verdict.
- **⚡ Live Python Sandbox:** Write and execute real Python code securely in the browser. The AI evaluates both your code logic and execution results.
- **🎨 Sleek Dark-Mode UI:** A modern, glassmorphism-inspired single-page application (SPA).

## 🛠️ Tech Stack

- **Backend:** Python, FastAPI, Uvicorn, Pydantic
- **Frontend:** Vanilla JavaScript, HTML5, CSS3 (No framework overhead)
- **AI Integration:** OpenAI Python SDK configured to use **Google Gemini's Free Tier** (Gemini 2.5/1.5 Flash), easily interchangeable with OpenAI's GPT models.
- **Code Execution:** Secure Python `subprocess` sandbox with import blocking and timeout enforcement.

## ⚙️ Quick Start Installation

### 1. Clone the repository
```bash
git clone https://github.com/Crack-er-jack/mock-interview-agent.git
cd mock-interview-agent
```

### 2. Setup the Backend Environment
Ensure you have Python 3.10+ installed.

```bash
cd backend
# Optional: Create a virtual environment
# python -m venv venv
# source venv/bin/activate  # On Windows use: venv\Scripts\activate

pip install -r requirements.txt
```

### 3. Configure API Keys
By default, this application uses the **Free** Google Gemini API.

1. Get a free API key from [Google AI Studio](https://aistudio.google.com).
2. Copy the example environment file:
   ```bash
   # From the root directory:
   cp .env.example .env
   ```
3. Open `.env` and paste your Gemini API key:
   ```env
   LLM_API_KEY=your_actual_api_key_here
   LLM_MODEL=gemini-1.5-flash
   ```
*(To use OpenAI instead, modify the `LLM_BASE_URL` and `LLM_MODEL` in the `.env` file as instructed in the comments).*

### 4. Run the Application
Start the FastAPI server:

```bash
cd backend
python -m uvicorn main:app --reload --port 8000
```

Open your browser and navigate to: **[http://localhost:8000](http://localhost:8000)**

## 🧪 Testing (Quick Test Mode)

If you want to rapidly test the UI and evaluator without burning through API rate limits (or to skip the Planner phase), you can enable Quick Test Mode.

In your `.env` file, set:
```env
QUICK_TEST_MODE=true
```
This forces the Planner to immediately return a simple 1-minute "Permutation Substring" question.

## 📁 Repository Structure

```
├── .env.example           # Environment template
├── backend/
│   ├── main.py            # FastAPI entry point
│   ├── config.py          # Settings & feature flags
│   ├── models.py          # Pydantic schemas & state
│   ├── requirements.txt
│   ├── agents/            # LLM orchestration (Planner, Interviewer, Evaluator)
│   ├── prompts/           # Specialized prompt templates
│   ├── routers/           # API endpoints (Session, Interview, Code)
│   └── sandbox/           # Subprocess code executor
└── frontend/
    ├── index.html         # SPA Shell views
    ├── style.css          # Dark glassmorphism theme
    └── app.js             # Client-side state & API calls
```

## ⚠️ Limitations & Future Work

- Currently, the sandbox only supports Python execution.
- The state is held in-memory (using a simple dictionary). In production, this should be backed by Redis or a database like PostgreSQL.
- No user authentication system yet. 

## 🤝 Contributing
Contributions, issues, and feature requests are welcome! Feel free to check the issues page.
