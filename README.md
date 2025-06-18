# Smart Expense Splitter

A Splitwise-like expense splitter built with Flask (backend) and Vue.js (frontend SPA).

## Local Development

1. Install dependencies:
    ```
    pip install -r requirements.txt
    ```

2. Run the app:
    ```
    python app.py
    ```

3. Visit [http://localhost:8899](http://localhost:8899) in your browser.

## Deployment (Render)

- Push this repo to GitHub.
- Create a new **Web Service** on [Render](https://render.com/).
- Set the build command:  
  ```
  pip install -r requirements.txt
  ```
- Set the start command:  
  ```
  gunicorn app:app
  ```
- No database setup is needed (uses SQLite).
- After deployment, visit your app and click "Initialize DB" in the UI to add sample data.

**Note:** Data is not persistent on Render free tier (SQLite file is lost on redeploy/restart). 