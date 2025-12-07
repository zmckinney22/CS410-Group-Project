"""
Unit tests for Reddit Comment Sentiment Analysis.

This test suite validates the sentiment analysis functionality including:
- Lexicon loading and initialization
- English text preprocessing  
- Basic sentiment classification
- Edge cases and error handling

Author: Hsinya Hsu
"""

import os
import sys

current_dir = os.path.dirname(__file__)
backend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'backend')
sys.path.insert(0, backend_path) 

from sentiment import SentimentAnalyzer, SentimentLabel

class TestSentimentAnalyzer:
    """Test cases for SentimentAnalyzer class."""
    
    def __init__(self):
        """Initialize fresh analyzer for each test."""
        self.analyzer = SentimentAnalyzer()
    
    def test_lexicon_loading(self):
        """Test that sentiment lexicons are properly loaded."""
        print("Testing lexicon loading...")
        
        # Verify lexicons are loaded
        assert len(self.analyzer.positive_words) > 0
        assert len(self.analyzer.negative_words) > 0
        
        # Check sample words from Liu and Hu lexicon
        assert 'excellent' in self.analyzer.positive_words
        assert 'terrible' in self.analyzer.negative_words
        
        # Ensure no overlap between positive and negative words
        common_words = self.analyzer.positive_words.intersection(self.analyzer.negative_words)
        assert len(common_words) == 0, f"Found {len(common_words)} words in both lexicons"
        
        print("Lexicon loading tests passed")
        return True
    
    def test_text_cleaning_english(self):
        """Test English text preprocessing functionality."""
        print("Testing text cleaning...")
        
        test_cases = [
            # (input, expected_output)
            ("Hello WORLD!", "hello world"),
            ("Check this: http://example.com", "check this"),
            ("Multiple   spaces   here", "multiple spaces here"),
            ("Special @#$ chars removed", "special chars removed"),
            ("Line\nbreaks\nhere", "line breaks here"),
            ("", ""),
            (None, ""),
            ("123 numbers 456", "numbers"),
        ]
        
        for input_text, expected in test_cases:
            result = self.analyzer.clean_english_text(input_text)
            assert result == expected, f"Failed for: '{input_text}' -> '{result}', expected: '{expected}'"
        
        print("Text cleaning tests passed")
        return True
    
    def test_analyze_sentiment_basic(self):
        """Test basic sentiment analysis on simple English phrases."""
        print("Testing basic sentiment analysis...")
        
        test_cases = [
            ("I love this!", "positive"),
            ("This is terrible", "negative"),
            ("It’s okay, not bad", "positive"),  
            ("", "neutral"),
        ]
        
        for text, expected_label in test_cases:
            result = self.analyzer.analyze_sentiment(text)
            assert result.value == expected_label, f"Failed for: '{text}' -> '{result}', expected: '{expected_label}'"
        
        print("Basic sentiment analysis tests passed")
        return True
    
    def analyze_sentiment(self, text: str):
        """Rule-based sentiment analysis with negation (window=3) and mixed sentiment"""
        cleaned = self.analyzer.clean_english_text(text)
        if not cleaned:
            return SentimentLabel.NEUTRAL

        words = cleaned.split()
        pos_count = 0
        neg_count = 0
        window = 3  

        for i, w in enumerate(words):
            flipped = any(words[max(0, i-window):i][j] in self.analyzer.negation_words 
                    for j in range(min(window, i)))
            if w in self.analyzer.positive_words:
                if flipped:
                    neg_count += 1
                else:
                    pos_count += 1
            elif w in self.analyzer.negative_words:
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

    
    def test_analyze_sentiment_phase2(self):
        """Phase 2: Test Reddit slang, emoji, negation, and mixed sentiment"""
        print("Testing Phase 2 sentiment analysis...")
        
        debug_cases = [
            "never bad",
            "not good", 
            "no love"
        ]

        for text in debug_cases:
            print(f"\nDEBUG for '{text}':")
        cleaned = self.analyzer.clean_english_text(text)
        print(f"  Cleaned: '{cleaned}'")
        words = cleaned.split()
        print(f"  Words: {words}")
        
        for i, w in enumerate(words):
            if w in self.analyzer.positive_words:
                print(f"  '{w}' is in POSITIVE words")
            elif w in self.analyzer.negative_words:
                print(f"  '{w}' is in NEGATIVE words")
            else:
                print(f"  '{w}' is NOT in any sentiment dictionary")
            if w in self.analyzer.negation_words:
                print(f"  '{w}' is a NEGATION word")
        
        test_cases = [
            # Slang replacement
            ("lol this is fun", "positive"),         # "lol" -> "funny" -> positive
            ("brb, be right back", "neutral"),       # "brb" -> "pause" -> neutral word
            ("pog this is amazing", "positive"),     # "pog" -> "excited" -> positive

            # Emoji conversion
            ("I am 😭", "negative"),                 # crying_face -> very_sad -> negative
            ("So happy 😄", "positive"),             # grinning_face -> happy -> positive
            ("Love this 😍", "positive"),            # heart_eyes -> love -> positive

            # Negation handling
            ("not good", "negative"),
            ("never bad", "positive"),
            ("no love", "negative"),

            # Mixed sentiment
            ("good but also bad", "mixed"),
            ("I love it but hate the ending", "mixed"),
            ("funny and sad at the same time", "mixed"),
        ]

        for text, expected_label in test_cases:
            result = self.analyzer.analyze_sentiment(text)
            assert result.value == expected_label, f"Failed for: '{text}' -> '{result}', expected: '{expected_label}'"

        print("Phase 2 sentiment analysis tests passed")
        return True


def run_tests():
    print("Running Sentiment Analyzer Tests...")
    tester = TestSentimentAnalyzer() 
    try:
        tester.test_lexicon_loading()
        tester.test_text_cleaning_english()
        tester.test_analyze_sentiment_basic()
        tester.test_analyze_sentiment_phase2()
        
        print("All basic tests passed!")
        return True
        
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    

if __name__ == "__main__":
    run_tests()