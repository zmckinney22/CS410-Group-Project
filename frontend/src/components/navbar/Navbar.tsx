import styles from "./Navbar.module.scss";

const Navbar = () => {
  return (
    <nav className={styles.navbar}>
      <h2 className={styles.title}>Reddit Sentiment Analyzer</h2>
      <ul className={styles.navLinks}>
        <li className={styles.navItem}>Home</li>
        <li className={styles.navItem}>About</li>
        <li className={styles.navItem}>Contact</li>
      </ul>
    </nav>
  );
};

export default Navbar;
