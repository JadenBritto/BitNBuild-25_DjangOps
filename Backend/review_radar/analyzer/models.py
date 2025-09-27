from django.db import models
from django.contrib.auth.models import User
import json

class ProductAnalysis(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    url = models.URLField(max_length=500)
    product_name = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Analysis Results
    total_reviews = models.IntegerField(default=0)
    positive_reviews = models.IntegerField(default=0)
    negative_reviews = models.IntegerField(default=0)
    neutral_reviews = models.IntegerField(default=0)
    
    # Store JSON data
    positive_keywords = models.TextField(blank=True)  # JSON
    negative_keywords = models.TextField(blank=True)  # JSON
    sentiment_breakdown = models.TextField(blank=True)  # JSON
    
    def get_positive_keywords(self):
        return json.loads(self.positive_keywords) if self.positive_keywords else []
    
    def set_positive_keywords(self, keywords):
        self.positive_keywords = json.dumps(keywords)
    
    def get_negative_keywords(self):
        return json.loads(self.negative_keywords) if self.negative_keywords else []
    
    def set_negative_keywords(self, keywords):
        self.negative_keywords = json.dumps(keywords)
    
    def get_sentiment_breakdown(self):
        return json.loads(self.sentiment_breakdown) if self.sentiment_breakdown else {}
    
    def set_sentiment_breakdown(self, breakdown):
        self.sentiment_breakdown = json.dumps(breakdown)

class Review(models.Model):
    analysis = models.ForeignKey(ProductAnalysis, on_delete=models.CASCADE, related_name='reviews')
    text = models.TextField()
    rating = models.IntegerField(null=True, blank=True)
    sentiment = models.CharField(max_length=20, blank=True)
    sentiment_score = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
