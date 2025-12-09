# Reddit Sentiment Analysis - CS410-Group-Project

## Authors
- Jaejung Ha
- Hsinya Hsu
- Shubhi Bhatia
- Nick King
- Zachary McKinney

## Running the Project

### Demo Notebook (project_demo.ipynb)

The easiest way to see our project in action is through the Jupyter notebook, which demonstrates the complete sentiment analysis pipeline.

#### 1. Get Reddit API Credentials
- Sign in to Reddit at https://www.reddit.com
- Go to https://www.reddit.com/prefs/apps
- Click "Create App" or "Create Another App"
- Select "script" as the app type
- Fill in the name and description (anything works)
- Set redirect URI to `http://localhost:8080` (required but not used)
- Click "Create app"
- Note your `client_id` (under the app name), `client_secret`, and the app name (for user agent)

#### 2. Add Your Credentials to the Notebook
Open `project_demo.ipynb`.

In the first code cell, replace the placeholder values:
```python
REDDIT_CLIENT_ID = "your_client_id_here"
REDDIT_CLIENT_SECRET = "your_client_secret_here"
REDDIT_USER_AGENT = "YourAppName/1.0"  # Use your app name
```

#### 3. Run All Cells
- Click "Kernel" → "Restart & Run All" (or "Run All" in VS Code)
- The notebook will automatically:
  - Install dependencies
  - Collect Reddit data
  - Perform sentiment analysis
  - Run model evaluation

### Running the Frontend Locally

To run the web application frontend on your local machine (connects to our hosted backend):
```bash
cd frontend
npm install
npm run dev
```
The web app will start on `http://localhost:5173`

### Live Demo

Try our deployed application without any setup:
**https://zmckinney22.github.io/CS410-Group-Project/**

## Citations
Minqing Hu and Bing Liu. "Mining and Summarizing Customer Reviews." 
Proceedings of the ACM SIGKDD International Conference on Knowledge 
Discovery and Data Mining (KDD-2004), Aug 22-25, 2004, Seattle, 
Washington, USA