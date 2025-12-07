const API_BASE_URL = "https://cs410-group-project.onrender.com";

export interface SentimentGroup {
  label: "positive" | "negative" | "neutral";
  count: number;
  proportion: number;
}

export interface NotableComment {
  comment_id: string;
  snippet: string;
  sentiment: "positive" | "negative" | "neutral";
  score: number;
}

export interface AnalyzeResponse {
  post_title: string;
  overall_sentiment: "positive" | "negative" | "neutral";
  groups: SentimentGroup[];
  controversy: number;
  keywords: string[];
  notable_comments: NotableComment[];
}

export const analyzeRedditUrl = async (url: string): Promise<AnalyzeResponse> => {
  const response = await fetch(`${API_BASE_URL}/api/analyze`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ url }),
  });

  if (!response.ok) {
    throw new Error(`API request failed: ${response.statusText}`);
  }

  return response.json();
};
