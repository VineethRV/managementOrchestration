FastAPI + Groq Bottom-up Agent System
------------------------------------
Requirements:
- Python 3.10+
- pip install -r requirements.txt
- Set GROQ_API_KEY environment variable

Run backend:
export GROQ_API_KEY=your_key_here
uvicorn app.main:app --reload --port 8000
