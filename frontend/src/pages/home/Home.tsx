import styles from "./Home.module.scss";

const Home = () => {
  return (
    <div className={styles.home}>
      <h1>Welcome to the Reddit Sentiment Analyser</h1>
      <p>Analyze the sentiment of Reddit posts and comments easily!</p>
      <input
        type="text"
        className={styles.searchInput}
        placeholder="Enter Reddit URL"
      />
      <button className={styles.analyzeButton}>Analyze Sentiment</button>
    </div>
  );
};

export default Home;
