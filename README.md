# 🏊 Swim Benchmarking AI App

This project is an **AI-powered app** that helps swimmers, coaches, and recruiters understand where a swimmer stands compared to others.

You can enter a swimmer's **age**, **event**, **gender**, and **swim time**, and the app will tell you:
- Their percentile ranking (e.g., top 40% of peers)
- Their skill category (Beginner → Elite)
- How close they are to USA Swimming standards (B, A, AA, AAA, AAAA)
- Insights about college readiness

---

## 📌 How the App Works

1. The swimmer (or coach) enters:
- Event (e.g., 100 Free)
- Age (e.g., 16)
- Gender (optional, e.g., M or F)
- Time (e.g., 1:03.00)

2. The app looks up two kinds of data:
- Standards (e.g., USA Swimming motivational times for that event/age)
- Peer results (swim times from other swimmers of the same age/event)

3. The AI compares the input time against the database and calculates:
- Percentile rank (how fast compared to others)
- Standard level (B, A, AA, etc.)
- Suggested goals (e.g., “You need to drop 2.1 seconds to hit AA”)

4. The result is shown in a chat-style interface, like ChatGPT:

  ```
    🏊 Your time of 1:03.00 puts you in the top 45% of girls age 16 in the 100 Free (SCY).
    🎯 You’re 2.1 seconds away from the B standard.
    🏫 Competitive for some Division 3 schools.
  ```

---

## ⚙️ Setup Instructions
Follow these steps. No advanced coding knowledge needed!

### 1. Install Python
Make sure you have Python 3.10+ installed.
Check by running:
```bash
python --version
```

### 2. Clone the Repository
Download the project from GitHub:
```bash
git clone https://github.com/dlnracke/AI-Agent.git
cd AI-Agent
```

### 3. Create a Virtual Environment
This keeps your project’s libraries separate:

```bash
python -m venv venv
source venv/bin/activate   # Mac/Linux
venv\Scripts\activate      # Windows
```

### 4. Install Requirements

```bash
pip install -r requirements.txt
```

### 5. Add Environment Variables
Copy .env.example → .env and fill in your Supabase URL and API Key.
Example:
```ini
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-secret-api-key
```

### 6. Run the app
```bash
python main.py
```
---

## 🛠️ Tech Stack
- Python 3.10+
- Supabase (database & APIs)
- Agno framework (AI agent with tools)

---

