import os
import re
from enum import Enum
import emoji 

class SentimentLabel(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative" 
    NEUTRAL = "neutral"
    MIXED = "mixed"

class SentimentAnalyzer:
    def __init__(self):
        self.positive_words = set()
        self.negative_words = set()
        self.load_lexicons()

        for w in ["fun", "funny", "excited", "love", "happy", "good", "cool", "amazing"]:
            self.negative_words.discard(w)  
            self.positive_words.add(w)

        for w in ["sad", "very_sad", "angry", "bad", "disgust", "suspicious", "shock", "disappointed"]:
            self.positive_words.discard(w)
            self.negative_words.add(w)
  
        self.negation_words = {"not", "never", "no"}
        
    
    def load_lexicons(self):
        try:
            current_dir = os.path.dirname(__file__)
            project_root = os.path.dirname(current_dir)
            lex_dir = os.path.join(project_root, 'data', 'opinion-lexicon-English')
            
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

            print(f"Loaded {len(self.positive_words)} positive and {len(self.negative_words)} negative words")

        except Exception as e:
            print(f"Error loading lexicons: {e}")
            raise

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

        text = re.sub(r'\bbe right back\b', 'coming_back', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def analyze_sentiment(self, text: str):
        cleaned = self.clean_english_text(text)
        if not cleaned:
            return SentimentLabel.NEUTRAL

        words = cleaned.split()
        pos_count = 0
        neg_count = 0
        window = 2

        for i, w in enumerate(words):
            if w not in self.positive_words and w not in self.negative_words:
                continue
            flipped = any(prev_word in self.negation_words 
                        for prev_word in words[max(0, i-window):i])
            if w in self.positive_words:
                if flipped:
                    neg_count += 1
                else:
                    pos_count += 1
            elif w in self.negative_words:
                if flipped:
                    pos_count += 1  
                else:
                    neg_count += 1  

        if pos_count > 0 and neg_count > 0:
            return SentimentLabel.MIXED
        elif pos_count > neg_count:
            return SentimentLabel.POSITIVE
        elif neg_count > pos_count:
            return SentimentLabel.NEGATIVE
        else:
            return SentimentLabel.NEUTRAL           
      
    def load_reddit_lexicon(self, file_path, sentiment="positive"):
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith(';'):
                    if sentiment == "positive":
                        self.positive_words.add(line.lower())
                    elif sentiment == "negative":
                        self.negative_words.add(line.lower())


if __name__ == "__main__":
    analyzer = SentimentAnalyzer()
    print("Sentiment analyzer ready!")    