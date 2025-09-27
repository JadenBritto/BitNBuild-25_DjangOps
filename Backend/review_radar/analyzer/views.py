from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from .models import ProductAnalysis
from .tasks import analyze_product_reviews
import json

def home(request):
    return render(request, 'analyzer/home.html')

@method_decorator(csrf_exempt, name='dispatch')
class AnalyzeView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            url = data.get('url')
            
            if not url:
                return JsonResponse({'error': 'URL is required'}, status=400)
            
            # Create analysis record
            analysis = ProductAnalysis.objects.create(url=url)
            
            # Start background task
            analyze_product_reviews.delay(analysis.id)
            
            return JsonResponse({
                'success': True,
                'analysis_id': analysis.id,
                'message': 'Analysis started'
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

def analysis_status(request, analysis_id):
    analysis = get_object_or_404(ProductAnalysis, id=analysis_id)
    
    data = {
        'id': analysis.id,
        'status': analysis.status,
        'product_name': analysis.product_name,
        'total_reviews': analysis.total_reviews,
        'created_at': analysis.created_at.isoformat()
    }
    
    if analysis.status == 'completed':
        data.update({
            'positive_reviews': analysis.positive_reviews,
            'negative_reviews': analysis.negative_reviews,
            'neutral_reviews': analysis.neutral_reviews,
            'positive_keywords': analysis.get_positive_keywords(),
            'negative_keywords': analysis.get_negative_keywords(),
            'sentiment_breakdown': analysis.get_sentiment_breakdown()
        })
    
    return JsonResponse(data)

def dashboard(request, analysis_id):
    analysis = get_object_or_404(ProductAnalysis, id=analysis_id)
    return render(request, 'analyzer/dashboard.html', {'analysis': analysis})

def analysis_list(request):
    analyses = ProductAnalysis.objects.all().order_by('-created_at')
    return render(request, 'analyzer/analysis_list.html', {'analyses': analyses})
