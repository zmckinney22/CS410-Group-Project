# Download and setup SocialSent Reddit community-specific sentiment lexicons
import os
import json
import zipfile
import urllib.request
import sys
from pathlib import Path

# URL to Stanford NLP's SocialSent subreddit lexicons dataset
REDDIT_LEXICONS_URL = "https://nlp.stanford.edu/projects/socialsent/files/socialsent_subreddits.zip"

# Define project directory structure
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / 'data'
SOCIALSENT_DIR = DATA_DIR / 'socialsent'
TEMP_DIR = DATA_DIR / 'temp'

def download_file(url, destination):
    """
    Download a file from URL with progress bar display
    """
    print(f"Downloading from {url}...")
    
    def report_progress(block_num, block_size, total_size):
        """Display download progress as percentage bar"""
        downloaded = block_num * block_size
        percent = min(100, downloaded * 100 / total_size)
        bar_length = 50
        filled = int(bar_length * downloaded / total_size)
        bar = '=' * filled + '-' * (bar_length - filled)
        sys.stdout.write(f'\r[{bar}] {percent:.1f}%')
        sys.stdout.flush()
    
    urllib.request.urlretrieve(url, destination, reporthook=report_progress)
    print("\nDownload complete!")

def extract_zip(zip_path, extract_to):
    """
    Extract contents of a zip file
    """
    print(f"Extracting {zip_path}...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
    print("Extraction complete!")

def convert_lexicon_to_json(input_path, output_path):
    """
    Convert SocialSent text lexicon files to JSON format
    Handles different text formats and normalizes sentiment scores
    """
    lexicon = {}
    
    try:
        with open(input_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                
                # Try different separators (tab, multiple spaces, single space)
                parts = None
                if '\t' in line:
                    parts = line.split('\t')
                elif '  ' in line:  # multiple spaces
                    parts = line.split()
                elif ' ' in line:
                    parts = line.split(' ', 1)
                
                # Parse word and sentiment score
                if parts and len(parts) >= 2:
                    word = parts[0].strip()
                    try:
                        score = float(parts[1].strip())
                        lexicon[word] = score
                    except ValueError:
                        continue
        
        # Normalize scores if they're not in [-1, 1] range
        if lexicon:
            scores = list(lexicon.values())
            max_abs = max(abs(s) for s in scores)
            if max_abs > 10:  # Scores seem unnormalized
                print(f"  Normalizing scores (max={max_abs:.2f})")
                lexicon = {w: s/max_abs for w, s in lexicon.items()}
        
        # Save as JSON for easy loading
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(lexicon, f, indent=2)
        
        return len(lexicon)
    
    except Exception as e:
        print(f"  Error converting {input_path}: {e}")
        return 0

def create_subreddit_mapping():
    """
    Maps specific subreddits to the closest available community lexicon
    """
    # Map common subreddits to corresponding or similar SocialSent lexicons
    mapping = {
        # Technical communities
        'python': 'programming',
        'learnprogramming': 'programming',
        'webdev': 'programming',
        
        # General discussion
        'AskReddit': 'funny',
        'unpopularopinion': 'changemyview',
        'ChangeMyView': 'changemyview',
        
        # Entertainment
        'movies': 'movies',
        'gaming': 'gaming',
        
        # News/Politics
        'politics': 'politics',
        'news': 'news',
        'AmItheAsshole': 'relationships',
    }
    
    # Save mapping for use by sentiment analyzer
    mapping_file = SOCIALSENT_DIR / 'subreddit_mapping.json'
    with open(mapping_file, 'w') as f:
        json.dump(mapping, f, indent=2)
    
    print(f"\nCreated subreddit mapping at {mapping_file}")
    return mapping

def setup_socialsent():
    """
    Main setup function to download, extract, and process SocialSent lexicons
    """
    print("=" * 70)
    print("SocialSent Reddit Lexicons Setup")
    print("=" * 70)
    
    # Create necessary directories
    SOCIALSENT_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)    
    zip_path = TEMP_DIR / 'socialsent_subreddits.zip'
    
    # Download lexicons zip file
    if not zip_path.exists():
        print("\n1. Downloading Reddit community lexicons...")
        download_file(REDDIT_LEXICONS_URL, zip_path)
    else:
        print(f"\n1. Using existing download: {zip_path}")
    
    # Extract the zip file
    print("\n2. Extracting lexicons...")
    extract_to = TEMP_DIR / 'socialsent_extracted'
    extract_to.mkdir(exist_ok=True)
    extract_zip(zip_path, extract_to)
    
    # Convert all lexicon files to JSON format
    print("\n3. Converting lexicons to JSON...")
    lexicon_files = list(extract_to.rglob('*'))
    # Filter to only actual files (not directories or hidden files)
    lexicon_files = [f for f in lexicon_files if f.is_file() and not f.name.startswith('.')]
    
    print(f"Found {len(lexicon_files)} lexicon files")
    
    converted_count = 0
    for lex_file in lexicon_files:
        subreddit_name = lex_file.stem  # Get filename without extension
        output_file = SOCIALSENT_DIR / f"{subreddit_name}.json"
        
        word_count = convert_lexicon_to_json(lex_file, output_file)
        if word_count > 0:
            converted_count += 1
            print(f"  {subreddit_name}: {word_count} words")
    
    print(f"\nConverted {converted_count} lexicons successfully!")
    
    # Create mapping from specific subreddits to lexicons
    print("\n4. Creating subreddit mapping...")
    mapping = create_subreddit_mapping()
    
    # Create a general Reddit lexicon by averaging across communities
    print("\n5. Creating general Reddit lexicon...")
    create_general_lexicon()
    
    # Clean up temporary files to save space
    print("\n6. Cleaning up temporary files...")
    if zip_path.exists():
        os.remove(zip_path)
    print("  Removed zip file")
    
    print("\n" + "=" * 70)
    print("Setup complete!")
    print("=" * 70)
    print(f"\nLexicons saved to: {SOCIALSENT_DIR}")
    print(f"Total lexicons: {converted_count}")

def create_general_lexicon():
    """
    Create a general Reddit lexicon by averaging scores across diverse subreddits
    This provides a fallback lexicon when subreddit-specific ones aren't available
    """
    # Select diverse popular subreddits for balanced general lexicon
    subreddits_to_average = [
        'AskReddit', 'funny', 'pics', 'todayilearned', 'worldnews',
        'videos', 'IAmA', 'gaming', 'movies', 'Music'
    ]
    
    word_scores = {}  # Sum of scores for each word
    word_counts = {}  # Count of how many subreddits have each word
    
    # Accumulate scores from each subreddit
    for subreddit in subreddits_to_average:
        lex_file = SOCIALSENT_DIR / f"{subreddit}.json"
        if lex_file.exists():
            with open(lex_file, 'r') as f:
                lexicon = json.load(f)
            
            for word, score in lexicon.items():
                if word not in word_scores:
                    word_scores[word] = 0
                    word_counts[word] = 0
                word_scores[word] += score
                word_counts[word] += 1
    
    # Calculate average score for each word
    general_lexicon = {
        word: word_scores[word] / word_counts[word]
        for word in word_scores
    }
    
    # Save general lexicon
    output_file = SOCIALSENT_DIR / 'reddit_general.json'
    with open(output_file, 'w') as f:
        json.dump(general_lexicon, f, indent=2)
    
    print(f"  reddit_general: {len(general_lexicon)} words (averaged from {len(subreddits_to_average)} subreddits)")

def check_installation():
    """
    Check if SocialSent lexicons are already installed
    """
    if not SOCIALSENT_DIR.exists():
        return False
    
    # Check if we have at least a few lexicon files
    json_files = list(SOCIALSENT_DIR.glob('*.json'))
    if len(json_files) < 5: # Need at least a few lexicons
        return False
    
    return True

if __name__ == "__main__":
    # Check if already installed and prompt for reinstall
    if check_installation():
        print("SocialSent lexicons appear to be already installed.")
        print(f"Location: {SOCIALSENT_DIR}")
        print(f"Found {len(list(SOCIALSENT_DIR.glob('*.json')))} lexicon files")
        
        response = input("\nDo you want to re-download and reinstall? (y/n): ")
        if response.lower() != 'y':
            print("Skipping installation.")
            sys.exit(0)
    
    # Run setup process
    try:
        setup_socialsent()
    except Exception as e:
        print(f"\nError during setup: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)