import os
import re
import json
from enum import Enum
from pathlib import Path
import emoji 
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

class SentimentLabel(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative" 
    NEUTRAL = "neutral"

class SentimentAnalyzer:
    def __init__(self, use_socialsent=True, subreddit=None, 
                 pos_threshold=0.01, neg_threshold=-0.01,
                 negation_window=2, negation_flip_weight=1.0,
                 socialsent_weight=0.3):
        self.use_socialsent = use_socialsent
        self.subreddit = subreddit
        self.pos_threshold = pos_threshold
        self.neg_threshold = neg_threshold
        self.negation_window = negation_window
        self.negation_flip_weight = negation_flip_weight
        self.socialsent_weight = socialsent_weight
        
        self.positive_words = set()
        self.negative_words = set()
        self.socialsent_lexicon = {}
        self.subreddit_mapping = {}
        
        self.load_lexicons()
        
        self.negation_words = {
            "not", "never", "no", "neither", "nor", "none", "nobody", 
            "nothing", "nowhere", "hardly", "barely", "scarcely",
            "without", "lack", "lacking"
        }
        
        self.intensifiers = {
            "very": 1.5, "extremely": 2.0, "absolutely": 1.8,
            "really": 1.3, "incredibly": 1.8, "totally": 1.5,
            "completely": 1.7, "utterly": 1.8, "highly": 1.4,
            "super": 1.5, "especially": 1.3
        }
        
        self.diminishers = {
            "slightly": 0.5, "somewhat": 0.6, "barely": 0.3,
            "hardly": 0.3, "kinda": 0.5, "sorta": 0.5,
            "little": 0.5, "bit": 0.6, "mildly": 0.5
        }
    
    def load_lexicons(self):
        try:
            current_dir = Path(__file__).parent
            project_root = current_dir.parent
            lex_dir = project_root / 'data' / 'opinion-lexicon-English'

            # Positive words
            pos_file = os.path.join(lex_dir, 'positive-words.txt')
            with open(pos_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith(';'):
                        self.positive_words.add(line.lower())
            
            # Negative words
            neg_file = os.path.join(lex_dir, 'negative-words.txt')
            with open(neg_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith(';'):
                        self.negative_words.add(line.lower())
            
            # Remove overlapping words (in the Liu & Hu lexicon)
            overlap = self.positive_words.intersection(self.negative_words)
            if overlap:
                print(f"Found {len(overlap)} overlapping words, removing them: {sorted(list(overlap))}")
                self.positive_words -= overlap
                self.negative_words -= overlap

            # Add Reddit-specific sentiment words
            for w in ["fun", "funny", "excited", "love", "happy", "good", "cool", "amazing"]:
                self.negative_words.discard(w)  
                self.positive_words.add(w)

            for w in ["sad", "very_sad", "angry", "bad", "disgust", "suspicious", "shock", "disappointed"]:
                self.positive_words.discard(w)
                self.negative_words.add(w)

            print(f"Loaded Liu & Hu: {len(self.positive_words)} positive, {len(self.negative_words)} negative words")

            if self.use_socialsent:
                self.load_socialsent_lexicons()

        except Exception as e:
            print(f"Error loading lexicons: {e}")
            raise

    def load_socialsent_lexicons(self):
        try:
            current_dir = Path(__file__).parent
            project_root = current_dir.parent
            socialsent_dir = project_root / 'data' / 'socialsent'
            
            if not socialsent_dir.exists():
                print("SocialSent directory not found. Run setup_socialsent.py first.")
                self.use_socialsent = False
                return
            
            mapping_file = socialsent_dir / 'subreddit_mapping.json'
            if mapping_file.exists():
                with open(mapping_file, 'r') as f:
                    self.subreddit_mapping = json.load(f)
            
            # Determine which lexicon to use
            lexicon_name = None
            if self.subreddit and self.subreddit in self.subreddit_mapping:
                lexicon_name = self.subreddit_mapping[self.subreddit]
            else:
                lexicon_name = 'reddit_general'
            
            lexicon_file = socialsent_dir / f'{lexicon_name}.json'
            if lexicon_file.exists():
                with open(lexicon_file, 'r') as f:
                    self.socialsent_lexicon = json.load(f)
                print(f"Loaded SocialSent lexicon '{lexicon_name}': {len(self.socialsent_lexicon)} words")
            else:
                # Fallback to general lexicon
                general_file = socialsent_dir / 'reddit_general.json'
                if general_file.exists():
                    with open(general_file, 'r') as f:
                        self.socialsent_lexicon = json.load(f)
                    print(f"Loaded SocialSent general lexicon: {len(self.socialsent_lexicon)} words")
                else:
                    print("No SocialSent lexicons found. Using Liu & Hu only.")
                    self.use_socialsent = False
                    
        except Exception as e:
            print(f"Error loading SocialSent: {e}")
            self.use_socialsent = False

    def clean_english_text(self, text: str) -> str:
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()

         # Phase 2: replace common Reddit abbreviations / slang
        slang_replacements = {
            # Laughter / humor
            "lol": "funny",
            "lmao": "funny",
            "rofl": "funny",
            "lmfao": "funny",
            "hehe": "funny",
            "haha": "funny",
            "jk": "joke",
            
            # Affirmation / agreement
            "ikr": "agree",        # I know, right
            "fr": "truth",         # for real
            "ngl": "honest",       # not gonna lie
            "tbh": "honest",       # to be honest
            "imo": "opinion",      # in my opinion
            "imho": "opinion",     # in my humble opinion
            "bet": "agree",        # okay / yes
            "ye": "yes",           # yes
            
            # Surprise / excitement
            "pog": "excited",      # amazing / cool
            "poggers": "excited",  # amazing / cool
            "omg": "surprise",     # oh my god
            "wtf": "shock",        # what the f***
            "bruh": "surprised",
            "dang": "surprised",
            "damn": "surprised",
            
            # Negatives / criticism
            "sus": "suspicious",
            "cap": "lie",           # false
            "no cap": "truth",      # real
            "rip": "sad",           # rest in peace
            "smh": "disappointed",  # shaking my head
            
            # Actions / social
            "hmu": "contact",      # hit me up
            "wyd": "asking",       # what are you doing
            "brb": "returning",    # be right back
            "gtg": "leave",        # got to go
            "afk": "away",         # away from keyboard
            
            # Intensifiers / emphasis
            "af": "very",          
            "frfr": "truth",       # for real for real
            "lowkey": "slightly",  # subtle emphasis
            "highkey": "very",     # strong emphasis
            "big yikes": "embarrassed", 
            
            # Emotions / feelings
            "sadge": "sad",
            "pogchamp": "excited",
            "feelsbadman": "sad",
            "feelsgoodman": "happy",
            "tfw": "feeling",      # that feeling when
            
            # Random / trending
            "yeet": "throw",
            "sus": "suspicious",
            "vibe": "feeling",
            "vibes": "feeling",
            "bussin": "good",
            "lit": "excited",
            "flex": "showoff",
            "stan": "support",
            "cap": "lie",
            "no cap": "truth",
            "slaps": "good",
            "drip": "style",
            "shook": "surprised",
            "poggers": "amazing",
        }

        for k, v in slang_replacements.items():
            text = re.sub(rf"\b{k}\b", v, text)

        text = emoji.demojize(text)         
        emoji_map = {
            ":grinning_face:": "happy",
            ":grinning_face_with_smiling_eyes:": "happy",
            ":smiling_face_with_heart_eyes:": "love",
            ":smiling_face_with_sunglasses:": "cool",
            ":thumbs_up:": "good",
            ":thumbs_down:": "bad",
            ":crying_face:": "sad",
            ":loudly_crying_face:": "very_sad",
            ":angry_face:": "angry",
            ":face_with_tears_of_joy:": "funny",
            ":clapping_hands:": "applause",
            ":fire:": "excited",
            ":sparkles:": "excited",
            ":thinking_face:": "thinking",
            ":poop:": "disgust",
        }

        # Replace emoji codes with words
        for e, word in emoji_map.items():
            text = text.replace(e, word)

        # Remove URLs
        text = re.sub(r'http\S+|www\S+|https\S+', '', text)
        
        # Remove special characters 
        text = re.sub(r'[^a-zA-Z_\s]', '', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def get_word_sentiment_score(self, word: str) -> float:
        liu_hu_score = 0.0
        socialsent_score = 0.0
        
        # Get Liu & Hu score (binary: +1, -1, or 0)
        if word in self.positive_words:
            liu_hu_score = 1.0
        elif word in self.negative_words:
            liu_hu_score = -1.0
        
        # Get SocialSent score (continuous: -1 to +1)
        if self.use_socialsent and word in self.socialsent_lexicon:
            socialsent_score = self.socialsent_lexicon[word]
        
        # Combine scores
        if not self.use_socialsent:
            return liu_hu_score
        
        if liu_hu_score != 0 and socialsent_score != 0:
            return (1 - self.socialsent_weight) * liu_hu_score + self.socialsent_weight * socialsent_score
        elif liu_hu_score != 0:
            return liu_hu_score
        elif socialsent_score != 0:
            return socialsent_score
        else:
            return 0.0
    
    def analyze_sentiment(self, text: str):
        cleaned = self.clean_english_text(text)
        if not cleaned:
            return SentimentLabel.NEUTRAL

        words = cleaned.split()

        filtered_words = [word for word in words if word not in ENGLISH_STOP_WORDS]

        pos_total = 0.0
        neg_total = 0.0

        for i, word in enumerate(filtered_words):
            base_score = self.get_word_sentiment_score(word)
            
            if base_score == 0:
                continue
            
            modifier = 1.0            
            for j in range(max(0, i-2), i):
                if j < len(filtered_words):
                    prev_word = filtered_words[j] 
                    if prev_word in self.intensifiers:
                        modifier *= self.intensifiers[prev_word]
                    elif prev_word in self.diminishers:
                        modifier *= self.diminishers[prev_word]
            
            negated = any(
                filtered_words[j] in self.negation_words
                for j in range(max(0, i-self.negation_window), i)
            )
            
            if negated:
                base_score = -base_score * self.negation_flip_weight
            
            final_score = base_score * modifier
            if final_score > 0:
                pos_total += final_score
            else:
                neg_total += final_score

        total_sentiment = pos_total + neg_total

        if pos_total > 0 and neg_total > 0 and abs(total_sentiment) < 0.1:
            return SentimentLabel.MIXED 

        if total_sentiment >= self.pos_threshold:
            return SentimentLabel.POSITIVE
        elif total_sentiment <= self.neg_threshold:
            return SentimentLabel.NEGATIVE
        else:
            return SentimentLabel.NEUTRAL


def analyze_post_and_comments(data: dict, subreddit: str = None, 
                              analyzer_params: dict = None) -> dict:
    params = analyzer_params or {}
    analyzer = SentimentAnalyzer(subreddit=subreddit, **params)
    post = data.get("post", {})
    comments = data.get("comments", [])

    # Analyze sentiment for each comment
    comment_sentiments = []
    for comment in comments:
        body = comment.get("body", "")
        sentiment_label = analyzer.analyze_sentiment(body)
        comment_sentiments.append({
            "comment_id": comment.get("id", ""),
            "body": body,
            "sentiment": sentiment_label.value,
            "score": comment.get("score", 0)
        })

    # Sentiment group counts
    sentiment_counts = {
        "positive": 0,
        "negative": 0,
        "neutral": 0
    }

    for com_sent in comment_sentiments:
        sentiment_counts[com_sent["sentiment"]] += 1

    total_comments = len(comment_sentiments)

    # Calculate groups for result
    groups = []
    for label, count in sentiment_counts.items():
        proportion = count / total_comments if total_comments > 0 else 0.0
        groups.append({
            "label": label,
            "count": count,
            "proportion": proportion
        })

    # Overall sentiment
    if total_comments == 0:
        overall_sentiment = "neutral"
    else:
        max_sentiment = max(sentiment_counts.items(), key=lambda x: x[1])
        overall_sentiment = max_sentiment[0]

    # Calculate controversy
    pos_count = sentiment_counts["positive"]
    neg_count = sentiment_counts["negative"]
    controversy = 0.0
    if total_comments > 0:
        controversy = (pos_count * neg_count) / (total_comments ** 2)

    # Extract keywords from comments
    keywords = extract_keywords(comments, analyzer)

    # Find notable comments
    notable_comments = find_notable_comments(comment_sentiments)

    return {
        "post_title": post.get("title", ""),
        "overall_sentiment": overall_sentiment,
        "groups": groups,
        "controversy": controversy,
        "keywords": keywords,
        "notable_comments": notable_comments
    }


def extract_keywords(comments: list, analyzer: SentimentAnalyzer, top_n: int = 10) -> list:
    # Extract top keywords from comments for result
    word_freq = {}

    for comment in comments:
        body = comment.get("body", "")
        cleaned = analyzer.clean_english_text(body)
        words = cleaned.split()

        for word in words:
            if len(word) > 3 and word not in ENGLISH_STOP_WORDS:
                word_freq[word] = word_freq.get(word, 0) + 1

    # Sort by frequency and return top N
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    return [word for word, freq in sorted_words[:top_n]]


def find_notable_comments(comment_sentiments: list) -> list:
    notable_comments = []
    
    sentiment_labels = {
        "positive": [],
        "negative": [],
        "neutral": [],
        "mixed": []
    }

    # Sort comments into sentiments
    for sentiment in comment_sentiments:
        sentiment_labels[sentiment["sentiment"]].append(sentiment)

    # Get top comment from each sentiment by score
    for sentiment_label, comments in sentiment_labels.items():
        if comments:
            sorted_comments = sorted(comments, key=lambda x: x["score"], reverse=True)
            top_comment = sorted_comments[0]

            # Create snippet of the first 150 chars
            body = top_comment["body"]
            snippet = body[:150] + "..." if len(body) > 150 else body

            notable_comments.append({
                "comment_id": top_comment["comment_id"],
                "snippet": snippet,
                "sentiment": sentiment_label,
                "score": top_comment["score"]
            })

    return notable_comments

if __name__ == "__main__":
    analyzer = SentimentAnalyzer()
    print("Sentiment analyzer ready!")    