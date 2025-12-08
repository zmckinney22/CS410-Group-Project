const API_BASE_URL = "https://cs410-group-project.onrender.com";

// Adding type defs for what the API should be responding with
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

/**
 * Method to call API to analyze a Reddit URL
 * 
 * @param url the URL of the Reddit post to analyze
 * @returns JSON response from the API containing analysis results
 * @throws Error if the API request fails or returns an error status
 */
export const analyzeRedditUrl = async (url: string): Promise<AnalyzeResponse> => {
  const response = await fetch(`${API_BASE_URL}/api/analyze`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ url }),
  });

  if (!response.ok) {
    let errorMessage = `API request failed with status ${response.status}`;
    
    try {
      const errorData = await response.json();
      if (errorData.detail) {
        errorMessage = errorData.detail;
      }
    } catch {
      // Nothing
    }
    
    throw new Error(errorMessage);
  }

  return response.json();
};
