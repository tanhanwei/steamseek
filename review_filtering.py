import re
from collections import Counter
import nltk
from typing import List, Dict, Tuple, Any
from config import *

class ReviewFilter:
    def __init__(self):
        # Download required NLTK data if not already present
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt')

    def detect_non_review_content(self, text: str) -> Tuple[bool, str]:
        """
        Detects various types of non-review content.
        Returns (is_valid_review, reason_if_invalid)
        """
        if not text or not isinstance(text, str):
            return False, "Empty or invalid text"

        text_lower = text.lower()

        # Check for recipes
        recipe_score = sum(indicator in text_lower 
                         for indicator in RECIPE_INDICATORS)
        if recipe_score >= 2:
            return False, "Recipe detected"

        # Check for ASCII art
        for pattern in ASCII_ART_PATTERNS:
            if re.search(pattern, text):
                return False, "ASCII art detected"

        # Check for known copypasta
        if any(text_lower.startswith(start) 
               for start in KNOWN_COPYPASTA_STARTS):
            return False, "Common copypasta detected"

        # Check special character ratio
        total_chars = len(text)
        if total_chars > 0:
            special_chars = sum(1 for c in text 
                              if not c.isalnum() and not c.isspace())
            if special_chars / total_chars > 0.3:
                return False, "Excessive special characters"

        # Check for repetitive content
        words = text_lower.split()
        if len(words) > 10:
            word_counts = Counter(words)
            most_common_count = word_counts.most_common(1)[0][1]
            if most_common_count > len(words) * 0.3:
                return False, "Repetitive content"

        # Check for off-topic content
        if any(indicator in text_lower 
               for indicator in OFF_TOPIC_INDICATORS):
            return False, "Off-topic promotion"

        return True, None

    def analyze_review_structure(self, text: str) -> float:
        """
        Analyzes review structure and returns a confidence score (0-1).
        """
        if not text:
            return 0.0

        # Split into sentences
        sentences = nltk.sent_tokenize(text)
        words = text.lower().split()
        word_count = len(words)

        # Check various structural features
        features = {
            'has_sentences': any(
                sent[0].isupper() and sent.endswith(('.', '!', '?'))
                for sent in sentences
            ),
            'has_game_terms': len(set(words).intersection(GAME_RELATED_TERMS)) >= 2,
            'has_reasonable_length': MIN_REVIEW_WORDS <= word_count <= MAX_REVIEW_WORDS,
            'has_proper_formatting': True
        }

        # Check word distribution if enough words
        if word_count > 0:
            word_freq = Counter(words)
            max_freq = max(word_freq.values())
            features['has_normal_word_distribution'] = max_freq <= word_count * 0.15
        else:
            features['has_normal_word_distribution'] = False

        # Calculate weighted score
        weights = {
            'has_sentences': 0.3,
            'has_game_terms': 0.3,
            'has_reasonable_length': 0.2,
            'has_normal_word_distribution': 0.1,
            'has_proper_formatting': 0.1
        }

        return sum(weights[feature] for feature, present in features.items() 
                  if present)

    def calculate_review_score(self, 
                             review: Dict[str, Any], 
                             is_niche_game: bool = False) -> float:
        """
        Calculates a review's quality score, adapting to niche vs. popular games.
        """
        text = review.get('review', '')
        if not text:
            return 0.0

        word_count = len(text.split())
        
        # Start with base score from structural analysis
        score = self.analyze_review_structure(text)

        if is_niche_game:
            # For niche games, focus more on content quality
            if 100 <= word_count <= 1000:
                score *= 2.0
            elif word_count > 1000:
                score *= 1.5

            # Check for detailed gameplay discussion
            gameplay_patterns = [
                (r'(?i)the gameplay (consists|involves|features)', 2.0),
                (r'(?i)you can (use|craft|build|fight|play)', 1.5),
                (r'(?i)(unique|special|different) (feature|aspect|mechanic)', 1.8),
                (r'(?i)compared to (other|similar) games', 1.5),
                (r'(?i)what makes this (game|different|special)', 1.8),
                (r'(?i)hours (of gameplay|played|in-game)', 1.3)
            ]

            for pattern, multiplier in gameplay_patterns:
                if re.search(pattern, text):
                    score *= multiplier
        else:
            # For popular games, consider community metrics more
            votes_up = review.get('votes_up', 0)
            score *= (1 + min(votes_up, 100) / 100)  # Cap at 2x multiplier

        # Common adjustments for all reviews
        score = self.adjust_score_for_content_quality(score, text)
        
        return score

    def adjust_score_for_content_quality(self, score: float, text: str) -> float:
        """
        Makes final adjustments to review score based on content quality.
        """
        text_lower = text.lower()

        # Penalize low-quality indicators
        low_quality_patterns = [
            r'(?i)(garbage|trash|waste|rubbish)$',
            r'(?i)^(yes|no|maybe)$',
            r'(?i)(broken|dead) game$',
            r'\b[A-Z]{4,}\b',
            r'!{3,}'
        ]

        for pattern in low_quality_patterns:
            if re.search(pattern, text):
                score *= 0.5

        # Reward structured criticism
        structured_patterns = [
            r'(?i)pros?[:,]',
            r'(?i)cons?[:,]',
            r'(?i)on the (positive|negative) side',
            r'(?i)however|nevertheless|although'
        ]

        for pattern in structured_patterns:
            if re.search(pattern, text):
                score *= 1.4

        return score

    def filter_reviews(self, 
                      reviews: List[Dict[str, Any]], 
                      max_reviews: int = MAX_REVIEWS_PER_GAME) -> List[Dict[str, Any]]:
        """
        Main function to filter and select the best reviews.
        """
        if not reviews:
            return []

        # Analyze if this is a niche game
        total_reviews = len(reviews)
        total_votes = sum(review.get('votes_up', 0) for review in reviews)
        avg_votes = total_votes / total_reviews if total_reviews > 0 else 0
        is_niche = total_reviews < 20 or avg_votes < 5

        filtered_reviews = []
        
        for review in reviews:
            text = review.get('review', '')
            
            # Skip empty reviews
            if not text.strip():
                continue

            # Check for non-review content
            is_valid, reason = self.detect_non_review_content(text)
            if not is_valid:
                continue

            # Calculate confidence and quality scores
            confidence_score = self.analyze_review_structure(text)
            if confidence_score >= MIN_CONFIDENCE_SCORE:
                quality_score = self.calculate_review_score(
                    review, 
                    is_niche_game=is_niche
                )
                review['confidence_score'] = confidence_score
                review['quality_score'] = quality_score
                filtered_reviews.append(review)

        # Sort by quality score and return top reviews
        filtered_reviews.sort(key=lambda x: x['quality_score'], reverse=True)
        return filtered_reviews[:max_reviews]
