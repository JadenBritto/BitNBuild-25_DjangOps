from celery import Celery
from .models import ProductAnalysis, Review
from .scraper import ReviewScraper
from .sentiment_analyzer import SentimentAnalyzer

app = Celery('review_radar')

@app.task
def analyze_product_reviews(analysis_id):
    try:
        analysis = ProductAnalysis.objects.get(id=analysis_id)
        analysis.status = 'processing'
        analysis.save()
        
        # Scrape reviews
        scraper = ReviewScraper()
        reviews_data, product_name = scraper.scrape_reviews(analysis.url)
        
        if not reviews_data:
            analysis.status = 'failed'
            analysis.save()
            return
        
        analysis.product_name = product_name
        analysis.total_reviews = len(reviews_data)
        
        # Analyze sentiment
        analyzer = SentimentAnalyzer()
        analyzed_reviews = analyzer.analyze_reviews(reviews_data)
        
        # Save reviews and calculate stats
        positive_count = 0
        negative_count = 0
        neutral_count = 0
        
        for review_data in analyzed_reviews:
            Review.objects.create(
                analysis=analysis,
                text=review_data['text'],
                rating=review_data['rating'],
                sentiment=review_data['sentiment'],
                sentiment_score=review_data['sentiment_score']
            )
            
            if review_data['sentiment'] == 'positive':
                positive_count += 1
            elif review_data['sentiment'] == 'negative':
                negative_count += 1
            else:
                neutral_count += 1
        
        # Extract keywords
        positive_keywords = analyzer.extract_keywords(analyzed_reviews, 'positive')
        negative_keywords = analyzer.extract_keywords(analyzed_reviews, 'negative')
        
        # Update analysis
        analysis.positive_reviews = positive_count
        analysis.negative_reviews = negative_count
        analysis.neutral_reviews = neutral_count
        
        analysis.set_positive_keywords(positive_keywords)
        analysis.set_negative_keywords(negative_keywords)
        
        sentiment_breakdown = {
            'positive': positive_count,
            'negative': negative_count,
            'neutral': neutral_count
        }
        analysis.set_sentiment_breakdown(sentiment_breakdown)
        
        analysis.status = 'completed'
        analysis.save()
        
    except Exception as e:
        analysis.status = 'failed'
        analysis.save()
        print(f"Analysis failed: {e}")