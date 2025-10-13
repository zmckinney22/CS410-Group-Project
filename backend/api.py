from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

import reddit
import sentiment

router = APIRouter(prefix="/api")

# --- Models ---

class SentimentLabel(str, Enum):
    positive = "positive"
    negative = "negative"
    neutral  = "neutral"
    mixed    = "mixed"

# Grouping for each sentiment, with counts and a proportion for each
class SentimentGroup(BaseModel):
    label: SentimentLabel
    count: int
    proportion: float

class NotableComment(BaseModel):
    comment_id: str
    snippet: str
    sentiment: SentimentLabel
    relevance: float
    score: int
    
class AnalysisResult(BaseModel):
    post_title: str
    overall_sentiment: SentimentLabel
    groups: list[SentimentGroup]
    controversy: float  
    keywords: list[str]
    notable: dict[str, list[NotableComment]]
    
    
# --- Endpoints ---

@router.get("/health")
def health():
    return {"status": "ok"}
    
@router.post("/analyze", response_model=AnalysisResult)
def analyze(req: str):
# Takes a Http url to a Reddit post

    # get text data
    try:
        data = reddit.fetch_post_and_comments(req)  
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Reddit fetch failed: {e}")

    # process text
    try:
        result = sentiment.get_summary(data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")
    
    return AnalysisResult(result)
        