
An interactive academic platform and AI tutor built to manage student study modules, course contents, dynamic quizzes, and study tracking.

## Deployed Application URL

**Live App:** [NEXUS-DASHBOARD](https://NF1105.streamlit.app) *(Update after deployment)*

## Project Structure

```text
NEXUS-DASHBOARD/
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
├── app.py
├── ai_service.py
├── database.py
├── college_course_content.py
├── flashcard_service.py
├── quick_reference_content.py
└── quiz_service.py
```

## Technologies & AI Tools Used

- **Python 3.10+**
- **Streamlit** (UI framework)
- **OpenAI API** (AI study assistant, quiz, and flashcard generation)
- **Plotly Express & Pandas** (analytics and dashboards)
- **SQLite** (persistent storage via `database.py`)
- **VS Code** (development environment)

## Setup & Installation Instructions

### Prerequisites

- Python 3.10+ installed
- OpenAI API key

### Running Locally

1. **Clone the repository:**

   ```bash
   git clone https://github.com/NF1105/NEXUS-DASHBOARD.git
   cd NEXUS-DASHBOARD
   ```

2. **Set up a virtual environment:**

   ```bash
   python -m venv venv
   ```

   Windows (PowerShell):

   ```powershell
   .\venv\Scripts\Activate.ps1
   ```

   macOS/Linux:

   ```bash
   source venv/bin/activate
   ```

3. **Install required packages:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure your environment:**

   Copy `.env.example` to `.env` in the project root and set your key:

   ```env
   OPENAI_API_KEY=OPENAI_API_KEY=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
   ```

5. **Run the application:**

   ```bash
   streamlit run app.py
   ```
# NEXUS-DASHBOARD
