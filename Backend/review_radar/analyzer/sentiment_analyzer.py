from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
from textblob import TextBlob
import nltk
from collections import Counter
import re
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

class SentimentAnalyzer:
    def __init__(self):
        self.setup_models()
        self.download_nltk_data()
    
    def setup_models(self):
        try:
            # Use a lightweight sentiment model
            model_name = "cardiffnlp/twitter-roberta-base-sentiment-latest"
            self.sentiment_pipeline = pipeline(
                "sentiment-analysis",
                model=model_name,
                tokenizer=model_name,
                max_length=512,
                truncation=True
            )
        except Exception as e:
            print(f"Error loading transformer model: {e}")
            # Fallback to TextBlob
            self.sentiment_pipeline = None
    
    def download_nltk_data(self):
        try:
            nltk.download('punkt', quiet=True)
            nltk.download('stopwords', quiet=True)
            nltk.download('vader_lexicon', quiet=True)
        except:
            pass
    
    def clean_text(self, text):
        # Remove special characters and normalize
        text = re.sub(r'[^a-zA-Z\s]', '', text)
        text = text.lower().strip()
        return text
    
    def analyze_sentiment_transformer(self, text):
        try:
            if self.sentiment_pipeline:
                result = self.sentiment_pipeline(text)[0]
                label = result['label']
                score = result['score']
                
                # Map labels to standard format
                if 'POSITIVE' in label.upper() or 'POS' in label.upper():
                    return 'positive', score
                elif 'NEGATIVE' in label.upper() or 'NEG' in label.upper():
                    return 'negative', score
                else:
                    return 'neutral', score
        except:
            pass
        
        return None, 0
    
    def analyze_sentiment_textblob(self, text):
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity
        
        if polarity > 0.1:
            return 'positive', abs(polarity)
        elif polarity < -0.1:
            return 'negative', abs(polarity)
        else:
            return 'neutral', abs(polarity)
    
    def analyze_reviews(self, reviews):
        results = []
        
        for review in reviews:
            text = review['text']
            rating = review.get('rating', 0)
            
            # Try transformer model first, fallback to TextBlob
            sentiment, score = self.analyze_sentiment_transformer(text)
            if not sentiment:
                sentiment, score = self.analyze_sentiment_textblob(text)
            
            # Use rating as additional signal
            if rating > 0:
                if rating >= 4 and sentiment != 'positive':
                    sentiment = 'positive'
                elif rating <= 2 and sentiment != 'negative':
                    sentiment = 'negative'
            
            results.append({
                'text': text,
                'rating': rating,
                'sentiment': sentiment,
                'sentiment_score': score
            })
        
        return results
    
    def extract_keywords(self, reviews, sentiment_filter=None, top_k=10):
        # Filter reviews by sentiment if specified
        if sentiment_filter:
            texts = [r['text'] for r in reviews if r['sentiment'] == sentiment_filter]
        else:
            texts = [r['text'] for r in reviews]
        
        if not texts:
            return []
        
        try:
            # Use TF-IDF to extract keywords
            vectorizer = TfidfVectorizer(
                max_features=100,
                stop_words='english',
                ngram_range=(1, 2),
                min_df=2
            )
            
            tfidf_matrix = vectorizer.fit_transform(texts)
            feature_names = vectorizer.get_feature_names_out()
            
            # Get average TF-IDF scores
            mean_scores = np.mean(tfidf_matrix.toarray(), axis=0)
            
            # Sort by score
            keyword_scores = list(zip(feature_names, mean_scores))
            keyword_scores.sort(key=lambda x: x[1], reverse=True)
            
            return [{'word': word, 'score': float(score)} for word, score in keyword_scores[:top_k]]
            
        except Exception as e:
            print(f"Error extracting keywords: {e}")
            # Fallback to simple word frequency
            all_words = []
            for text in texts:
                words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
                all_words.extend(words)
            
            # Remove common stop words
            stop_words = {'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 'how', 'its', 'may', 'new', 'now', 'old', 'see', 'two', 'who', 'boy', 'did', 'she', 'use', 'way', 'with', 'this', 'that', 'have', 'from', 'they', 'know', 'want', 'been', 'good', 'much', 'some', 'time', 'very', 'when', 'come', 'here', 'just', 'like', 'long', 'make', 'many', 'over', 'such', 'take', 'than', 'them', 'well', 'were'}
            filtered_words = [word for word in all_words if word not in stop_words and len(word) > 3]
            
            word_freq = Counter(filtered_words)
            return [{'word': word, 'score': count} for word, count in word_freq.most_common(top_k)]