import { useState } from "react";
import styles from "./Home.module.scss";
import { analyzeRedditUrl } from "../../api/api";
import type { AnalyzeResponse } from "../../api/api";
import { FaArrowUp } from "react-icons/fa";

const Home = () => {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showRawJson, setShowRawJson] = useState(false);
  const [copySuccess, setCopySuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!url.trim()) {
      setError("Please enter a Reddit URL");
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);
    setShowRawJson(false);

    try {
      const data = await analyzeRedditUrl(url);
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  const handleCopyToClipboard = async () => {
    if (!result) return;

    try {
      await navigator.clipboard.writeText(JSON.stringify(result, null, 2));
      setCopySuccess(true);
      setTimeout(() => setCopySuccess(false), 2000);
    } catch (err) {
      console.error("Failed to copy:", err);
    }
  };

  return (
    <div className={styles.home}>
      <h1>Welcome to the Reddit Sentiment Analyzer</h1>
      <p>Analyze the sentiment of Reddit posts and comments easily!</p>

      <form onSubmit={handleSubmit} className={styles.form}>
        <input
          type="text"
          className={styles.searchInput}
          placeholder="Enter Reddit URL"
          value={url}
          onChange={e => setUrl(e.target.value)}
          disabled={loading}
        />
        <button
          type="submit"
          className={styles.analyzeButton}
          disabled={loading}
        >
          {loading ? "Analyzing..." : "Analyze Sentiment"}
        </button>
      </form>

      {loading && (
        <div className={styles.loadingContainer}>
          <div className={styles.spinner}></div>
          <p>Analyzing sentiment...</p>
        </div>
      )}

      {error && (
        <div className={styles.error}>
          <p>Error: {error}</p>
        </div>
      )}

      {result && (
        <div className={styles.result}>
          <h2 className={styles.resultTitle}>{result.post_title}</h2>
          <a
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            className={styles.redditLink}
          >
            <button className={styles.linkButton}>View on Reddit</button>
          </a>
          <div className={styles.overallSentiment}>
            Overall Sentiment:{" "}
            <span className={styles[result.overall_sentiment]}>
              {result.overall_sentiment.toUpperCase()}
            </span>
          </div>
          <div className={styles.controversy}>
            Controversy Score: <span>{result.controversy.toFixed(2)}</span>
          </div>

          <h3>Sentiment Distribution:</h3>
          <div className={styles.sentimentGroups}>
            {result.groups.map(group => (
              <div
                key={group.label}
                className={`${styles.sentimentCard} ${styles[group.label]}`}
              >
                <div className={styles.cardLabel}>
                  {group.label.toUpperCase()}
                </div>
                <div className={styles.cardCount}>{group.count}</div>
                <div className={styles.cardProportion}>
                  {(group.proportion * 100).toFixed(1)}%
                </div>
              </div>
            ))}
          </div>

          <div className={styles.keywordsSection}>
            <h3>Top Keywords:</h3>
            <div className={styles.keywords}>
              {result.keywords.map(keyword => (
                <span key={keyword} className={styles.keywordTag}>
                  {keyword}
                </span>
              ))}
            </div>
          </div>

          <div className={styles.notableComments}>
            <h3>Notable Comments:</h3>
            {result.notable_comments.map(comment => (
              <div key={comment.comment_id} className={styles.comment}>
                <div className={styles.commentHeader}>
                  <span
                    className={`${styles.commentSentiment} ${
                      styles[comment.sentiment]
                    }`}
                  >
                    {comment.sentiment}
                  </span>
                  <span className={styles.commentScore}>
                    <FaArrowUp /> {comment.score}
                  </span>
                </div>
                <p className={styles.commentSnippet}>{comment.snippet}</p>
              </div>
            ))}
          </div>

          <div className={styles.rawJsonSection}>
            <button
              className={styles.toggleJsonButton}
              onClick={() => setShowRawJson(!showRawJson)}
            >
              {showRawJson ? "Hide Raw JSON" : "Show Raw JSON"}
            </button>

            {showRawJson && (
              <div className={styles.jsonContainer}>
                <button
                  className={styles.copyButton}
                  onClick={handleCopyToClipboard}
                >
                  {copySuccess ? "Copied!" : "Copy to Clipboard"}
                </button>
                <pre className={styles.jsonPre}>
                  {JSON.stringify(result, null, 2)}
                </pre>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default Home;
