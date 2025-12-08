from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from enum import Enum

import reddit
import sentiment

router = APIRouter(prefix="/api")

# --- Models ---

class SentimentGroup(BaseModel):
    """Represents count and proportion of comments for each sentiment label"""
    label: str
    count: int
    proportion: float

class NotableComment(BaseModel):
    """Top-scored comment from each sentiment category with preview snippet"""
    comment_id: str
    snippet: str
    sentiment: str
    score: int

class AnalysisResult(BaseModel):
    """Complete sentiment analysis result for a Reddit post"""
    post_title: str
    overall_sentiment: str
    groups: list[SentimentGroup]
    controversy: float
    keywords: list[str]
    notable_comments: list[NotableComment]

class AnalyzeRequest(BaseModel):
    """Request body containing Reddit post URL to analyze"""
    url: str

# --- Endpoints ---

@router.get("/health")
def health():
    """Health check endpoint to verify API is running"""
    return {"status": "ok"}

@router.post("/analyze", response_model=AnalysisResult)
def analyze(req: AnalyzeRequest):
    """
    Main endpoint: Analyze sentiment of a Reddit post and its comments
    
    Takes a Reddit URL, fetches post and comments, performs sentiment analysis,
    and returns overall sentiment, distribution, controversy score, keywords,
    and notable comments from each sentiment category.
    """
    # Example analyze:
    # Response:
    # {
    #     "post_title": "Help with Python decorators",
    #     "overall_sentiment": "positive",
    #     "groups": [
    #         {"label": "positive", "count": 42, "proportion": 0.70},
    #         {"label": "neutral", "count": 15, "proportion": 0.25},
    #         {"label": "negative", "count": 3, "proportion": 0.05}
    #     ],
    #     "controversy": 0.035,
    #     "keywords": ["decorator", "function", "python", "wrapper", "syntax"],
    #     "notable_comments": [...]
    # }

    # Fetch post and comments from Reddit API
    try:
        # {"post": post, "comments": comments}
        data = reddit.fetch_post_and_comments(req.url)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Reddit fetch failed: {e}")

    # Run sentiment analysis on fetched data
    try:
        result = sentiment.analyze_post_and_comments(data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")

    return result
    