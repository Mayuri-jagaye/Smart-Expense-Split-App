# Smart Expense Splitter

[Live Demo on Render](https://smart-expense-split-app.onrender.com)

---

## 📚 Project Overview

Smart Expense Splitter is a Splitwise-like web application for tracking group expenses, calculating optimal settlements, and providing analytics. The backend is built with Flask and SQLAlchemy, and the frontend is a modern Vue.js SPA (served as a static file). The app is designed for easy deployment (using SQLite for demo/testing) and features a clean, interactive UI.

---

## ✨ Features

- **Add, view, edit, and delete expenses**
- **Smart category detection** for expenses
- **Automatic person extraction** from descriptions
- **Equal, percentage, and custom splits**
- **Balances and optimal settlements** calculation
- **Spending analytics** (by category, monthly summary)
- **Sample data initialization** for quick start
- **Modern Vue.js SPA** with Tailwind CSS
- **RESTful API** for integration/testing

---

## 🚀 Deployed Link

**Live App:** [https://smart-expense-split-app.onrender.com](https://smart-expense-split-app.onrender.com)

---

## 📝 Assignment Context

This project was developed as an important assignment to demonstrate full-stack web development, RESTful API design, and deployment skills. It showcases best practices in Flask backend development, Vue.js SPA integration, and cloud deployment (Render).

---

## 🗂️ Project Structure

```
/
├── app.py                # Flask backend (API + static file serving)
├── requirements.txt      # Python dependencies
├── Procfile              # For Render deployment
├── .gitignore            # Ignore Python/DB/env files
├── README.md             # This file
└── templates/
    └── index.html        # Vue.js SPA frontend
```

---

## ⚙️ Local Development

1. **Clone the repo:**
    ```
    git clone <your-repo-url>
    cd <project-folder>
    ```
2. **Install dependencies:**
    ```
    pip install -r requirements.txt
    ```
3. **Run the app:**
    ```
    python app.py
    ```
4. **Open in browser:**
    [http://localhost:8899](http://localhost:8899)
5. **Initialize DB:**
    Click "Initialize DB" in the web UI to add sample users.

---

## ☁️ Deployment (Render)

1. **Push to GitHub.**
2. **Create a new Web Service** on [Render](https://render.com/):
    - **Build command:** `pip install -r requirements.txt`
    - **Start command:** `gunicorn app:app`
3. **No DB setup needed** (uses SQLite, ephemeral on Render).
4. **After deploy:** Visit your Render URL and click "Initialize DB" in the UI.

---

## 🔗 API Endpoints

| Method | Endpoint                | Description                        |
|--------|-------------------------|------------------------------------|
| GET    | /api/expenses           | List all expenses                  |
| POST   | /api/expenses           | Add a new expense                  |
| PUT    | /api/expenses/<id>      | Update an expense                  |
| DELETE | /api/expenses/<id>      | Delete an expense                  |
| GET    | /api/people             | List all people                    |
| GET    | /api/balances           | Get balances for all people        |
| GET    | /api/settlements        | Get optimal settlements            |
| GET    | /api/analytics/categories | Category-wise spending           |
| GET    | /api/analytics/monthly  | Monthly spending summary           |
| POST   | /api/init               | Initialize DB with sample data     |

---

## 🧪 API Testing

You can test the API using the following resources:

- **Public Postman Collection (Online):**
  [Smart Expense Splitter API (Postman Cloud)](https://mayurijagaye.postman.co/workspace/Mayuri-Jagaye's-Workspace~490c7170-4d5a-47e6-87b3-9eb6edcb3114/collection/46015629-3e9daf85-c7d6-46f8-b29d-354b31537c4a?action=share&creator=46015629)
  - Open the link and use the collection directly in Postman (no need to download).
  - All endpoints are pre-configured to use the deployed API.

- **Local Postman Collection File:**
  `Smart_Expense_Splitter_API.postman_collection.json` is included in the repo for offline import into Postman.

---

## ⚠️ Notes

- **SQLite is not persistent on Render free tier.** Data will be lost on redeploy/restart.
- For production, use a managed database (Postgres, MySQL, etc).
- The app is designed for demo, learning, and assignment purposes.

---

## 👨‍💻 Author & Credits

Developed as part of an important assignment to demonstrate:
- Full-stack web development
- RESTful API design
- Cloud deployment

---

## 📬 Contact

For questions or feedback, please contact the project author. 