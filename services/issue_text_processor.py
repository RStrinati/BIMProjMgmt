"""
Issue Text Processor Service

Provides natural language processing for issue titles, descriptions, and comments.
Performs text cleaning, keyword extraction, and sentiment analysis.
"""

import re
import sys
import os
from collections import Counter
from typing import List, Dict, Tuple, Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Optional NLP libraries (will fall back to basic processing if not available)
try:
    import nltk
    from nltk.corpus import stopwords
    from nltk.tokenize import word_tokenize
    from nltk.stem import PorterStemmer
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False
    print("⚠️  NLTK not available - using basic text processing")

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("⚠️  scikit-learn not available - TF-IDF disabled")


class IssueTextProcessor:
    """
    Processes issue text for categorization and analysis.
    """
    
    def __init__(self):
        """Initialize the text processor with stopwords and stemmer."""
        self.stemmer = None
        self.stop_words = set()
        
        if NLTK_AVAILABLE:
            try:
                self.stop_words = set(stopwords.words('english'))
                self.stemmer = PorterStemmer()
            except LookupError:
                print("⚠️  NLTK data not found. Run: python -m nltk.downloader stopwords punkt")
                self._init_basic_stopwords()
        else:
            self._init_basic_stopwords()
    
    def _init_basic_stopwords(self):
        """Initialize basic stopwords if NLTK not available."""
        self.stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'is', 'are', 'was', 'were', 'been', 'be', 'have', 'has',
            'had', 'do', 'does', 'did', 'will', 'would', 'should', 'could', 'may',
            'might', 'must', 'can', 'this', 'that', 'these', 'those', 'i', 'you',
            'he', 'she', 'it', 'we', 'they', 'what', 'which', 'who', 'when', 'where',
            'why', 'how', 'all', 'each', 'every', 'both', 'few', 'more', 'most',
            'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same',
            'so', 'than', 'too', 'very', 's', 't', 'just', 'now', 'issue'
        }
    
    def clean_text(self, text: Optional[str]) -> str:
        """
        Clean and normalize text.
        
        Args:
            text: Input text to clean
            
        Returns:
            Cleaned and normalized text
        """
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove URLs
        text = re.sub(r'http\S+|www\S+', '', text)
        
        # Remove email addresses
        text = re.sub(r'\S+@\S+', '', text)
        
        # Preserve important patterns before cleaning
        # e.g., "<300mm" should stay as a unit
        text = re.sub(r'<\s*(\d+)\s*mm', r'less_than_\1mm', text)
        
        # Remove special characters but keep spaces and hyphens
        text = re.sub(r'[^a-z0-9\s\-_]', ' ', text)
        
        # Replace multiple spaces with single space
        text = re.sub(r'\s+', ' ', text)
        
        # Strip leading/trailing whitespace
        text = text.strip()
        
        return text
    
    def tokenize(self, text: str) -> List[str]:
        """
        Tokenize text into words.
        
        Args:
            text: Input text
            
        Returns:
            List of tokens
        """
        if NLTK_AVAILABLE:
            try:
                return word_tokenize(text)
            except:
                pass
        
        # Basic tokenization
        return text.split()
    
    def remove_stopwords(self, tokens: List[str]) -> List[str]:
        """
        Remove stopwords from token list.
        
        Args:
            tokens: List of tokens
            
        Returns:
            Filtered list of tokens
        """
        return [token for token in tokens if token not in self.stop_words and len(token) > 2]
    
    def stem_tokens(self, tokens: List[str]) -> List[str]:
        """
        Apply stemming to tokens.
        
        Args:
            tokens: List of tokens
            
        Returns:
            Stemmed tokens
        """
        if self.stemmer:
            return [self.stemmer.stem(token) for token in tokens]
        return tokens
    
    def extract_keywords(self, text: str, top_n: int = 10) -> List[Tuple[str, float]]:
        """
        Extract keywords from text using frequency analysis.
        
        Args:
            text: Input text
            top_n: Number of top keywords to return
            
        Returns:
            List of (keyword, score) tuples
        """
        # Clean and tokenize
        cleaned = self.clean_text(text)
        tokens = self.tokenize(cleaned)
        
        # Remove stopwords
        filtered = self.remove_stopwords(tokens)
        
        # Extract n-grams (1-3 words)
        ngrams = []
        for i in range(len(filtered)):
            # Unigrams
            ngrams.append(filtered[i])
            # Bigrams
            if i < len(filtered) - 1:
                ngrams.append(f"{filtered[i]} {filtered[i+1]}")
            # Trigrams
            if i < len(filtered) - 2:
                ngrams.append(f"{filtered[i]} {filtered[i+1]} {filtered[i+2]}")
        
        # Count frequency
        counter = Counter(ngrams)
        
        # Calculate scores (normalized frequency)
        total = sum(counter.values())
        if total == 0:
            return []
        
        keywords = [(word, count / total) for word, count in counter.most_common(top_n)]
        
        return keywords
    
    def extract_keywords_tfidf(self, documents: List[str], top_n: int = 10) -> List[List[Tuple[str, float]]]:
        """
        Extract keywords using TF-IDF across multiple documents.
        
        Args:
            documents: List of text documents
            top_n: Number of top keywords per document
            
        Returns:
            List of keyword lists, one per document
        """
        if not SKLEARN_AVAILABLE or not documents:
            # Fall back to frequency-based extraction
            return [self.extract_keywords(doc, top_n) for doc in documents]
        
        try:
            # Clean documents
            cleaned_docs = [self.clean_text(doc) for doc in documents]
            
            # Create TF-IDF vectorizer
            vectorizer = TfidfVectorizer(
                max_features=100,
                ngram_range=(1, 3),
                stop_words='english'
            )
            
            # Fit and transform
            tfidf_matrix = vectorizer.fit_transform(cleaned_docs)
            feature_names = vectorizer.get_feature_names_out()
            
            # Extract keywords for each document
            results = []
            for doc_idx in range(len(documents)):
                # Get scores for this document
                doc_scores = tfidf_matrix[doc_idx].toarray()[0]
                
                # Get top keywords
                top_indices = doc_scores.argsort()[-top_n:][::-1]
                keywords = [(feature_names[idx], doc_scores[idx]) for idx in top_indices if doc_scores[idx] > 0]
                
                results.append(keywords)
            
            return results
        
        except Exception as e:
            print(f"⚠️  TF-IDF extraction failed: {e}")
            return [self.extract_keywords(doc, top_n) for doc in documents]
    
    def analyze_sentiment(self, text: str) -> float:
        """
        Analyze sentiment of text (simple rule-based approach).
        
        Args:
            text: Input text
            
        Returns:
            Sentiment score from -1.0 (negative) to +1.0 (positive)
        """
        if not text:
            return 0.0
        
        text = text.lower()
        
        # Positive indicators
        positive_words = {
            'resolved', 'resolved', 'fixed', 'completed', 'approved', 'clarified',
            'confirmed', 'agreed', 'accepted', 'satisfactory', 'good', 'excellent',
            'successful', 'working', 'ok', 'correct', 'proper'
        }
        
        # Negative indicators
        negative_words = {
            'critical', 'urgent', 'major', 'serious', 'severe', 'blocking', 'blocker',
            'failed', 'failure', 'error', 'incorrect', 'wrong', 'issue', 'problem',
            'clash', 'conflict', 'missing', 'incomplete', 'unresolved', 'rejected',
            'unacceptable', 'poor', 'bad', 'difficult', 'cannot', 'impossible'
        }
        
        # Count occurrences
        tokens = self.tokenize(text)
        positive_count = sum(1 for token in tokens if token in positive_words)
        negative_count = sum(1 for token in tokens if token in negative_words)
        
        # Calculate score
        total = positive_count + negative_count
        if total == 0:
            return 0.0
        
        score = (positive_count - negative_count) / total
        
        # Clamp to [-1, 1]
        return max(-1.0, min(1.0, score))
    
    def calculate_urgency_score(self, text: str, priority: Optional[str] = None) -> float:
        """
        Calculate urgency score based on text content and priority.
        
        Args:
            text: Issue text (title + description)
            priority: Issue priority if available
            
        Returns:
            Urgency score from 0.0 (low) to 1.0 (high)
        """
        if not text:
            return 0.3  # Default low urgency
        
        text = text.lower()
        score = 0.0
        
        # High urgency keywords
        high_urgency = {
            'critical': 0.3,
            'urgent': 0.3,
            'asap': 0.3,
            'immediate': 0.3,
            'emergency': 0.35,
            'blocking': 0.25,
            'blocker': 0.25,
            'severe': 0.2,
            'major': 0.15
        }
        
        # Medium urgency keywords
        medium_urgency = {
            'important': 0.1,
            'priority': 0.1,
            'significant': 0.1,
            'requires attention': 0.15
        }
        
        # Check for urgency keywords
        for keyword, weight in high_urgency.items():
            if keyword in text:
                score += weight
        
        for keyword, weight in medium_urgency.items():
            if keyword in text:
                score += weight
        
        # Priority boost
        if priority:
            priority = priority.lower()
            if priority in ['critical', 'high', 'urgent']:
                score += 0.3
            elif priority in ['medium', 'normal']:
                score += 0.1
        
        # Clamp to [0, 1]
        return min(1.0, score)
    
    def calculate_complexity_score(self, text: str, comment_count: int = 0) -> float:
        """
        Estimate issue complexity based on text and metadata.
        
        Args:
            text: Issue text (title + description)
            comment_count: Number of comments on the issue
            
        Returns:
            Complexity score from 0.0 (simple) to 1.0 (complex)
        """
        if not text:
            return 0.3
        
        score = 0.0
        text = text.lower()
        
        # Complexity indicators
        complexity_keywords = {
            'multi-discipline': 0.2,
            'multiple': 0.15,
            'coordinated': 0.15,
            'coordination': 0.15,
            'redesign': 0.2,
            'significant': 0.15,
            'major': 0.15,
            'complex': 0.2,
            'various': 0.1,
            'several': 0.1,
            'all': 0.1,
            'entire': 0.15
        }
        
        for keyword, weight in complexity_keywords.items():
            if keyword in text:
                score += weight
        
        # Length factor (longer text = more complex)
        word_count = len(text.split())
        if word_count > 100:
            score += 0.2
        elif word_count > 50:
            score += 0.1
        elif word_count > 20:
            score += 0.05
        
        # Comment count factor (more discussion = more complex)
        if comment_count > 10:
            score += 0.2
        elif comment_count > 5:
            score += 0.15
        elif comment_count > 2:
            score += 0.1
        
        # Clamp to [0, 1]
        return min(1.0, score)
    
    def combine_text_fields(self, title: Optional[str], description: Optional[str], 
                           comments: Optional[str] = None) -> str:
        """
        Combine multiple text fields for analysis.
        
        Args:
            title: Issue title
            description: Issue description
            comments: Latest comment or concatenated comments
            
        Returns:
            Combined text
        """
        parts = []
        
        if title:
            # Title is most important, include it twice for weighting
            parts.append(title)
            parts.append(title)
        
        if description:
            parts.append(description)
        
        if comments:
            parts.append(comments)
        
        return " ".join(parts)


def download_nltk_data():
    """Download required NLTK data if not present."""
    if not NLTK_AVAILABLE:
        print("❌ NLTK not installed. Install with: pip install nltk")
        return False
    
    try:
        import nltk
        print("Downloading NLTK data...")
        nltk.download('stopwords', quiet=True)
        nltk.download('punkt', quiet=True)
        print("✓ NLTK data downloaded successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to download NLTK data: {e}")
        return False


# Example usage and testing
if __name__ == "__main__":
    print("=" * 70)
    print("Issue Text Processor - Test")
    print("=" * 70)
    print()
    
    # Initialize processor
    processor = IssueTextProcessor()
    
    # Test examples
    test_issues = [
        {
            "title": "Hydraulic Issue - Hydraulic pipework clearance to civil drainage <300mm",
            "description": "The hydraulic pipework does not have sufficient clearance to the civil drainage system. Minimum 300mm clearance required.",
            "priority": "high"
        },
        {
            "title": "Electrical Issue - clash",
            "description": "Electrical conduit clashes with structural beam in Zone 5",
            "priority": "medium"
        },
        {
            "title": "STR v. ELE - Peno misalignment",
            "description": "Electrical penetration through structural slab is misaligned. Requires coordination between structural and electrical teams.",
            "priority": "high"
        }
    ]
    
    print("Processing test issues...\n")
    
    for idx, issue in enumerate(test_issues, 1):
        print(f"Issue {idx}: {issue['title']}")
        print("-" * 70)
        
        # Combine text
        combined = processor.combine_text_fields(
            issue['title'],
            issue.get('description'),
            None
        )
        
        # Extract keywords
        keywords = processor.extract_keywords(combined, top_n=5)
        print(f"Keywords: {', '.join([f'{kw}({score:.2f})' for kw, score in keywords])}")
        
        # Analyze sentiment
        sentiment = processor.analyze_sentiment(combined)
        print(f"Sentiment: {sentiment:.2f}")
        
        # Calculate urgency
        urgency = processor.calculate_urgency_score(combined, issue.get('priority'))
        print(f"Urgency: {urgency:.2f}")
        
        # Calculate complexity
        complexity = processor.calculate_complexity_score(combined, comment_count=2)
        print(f"Complexity: {complexity:.2f}")
        
        print()
    
    print("=" * 70)
    print("✓ Test complete")
