from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(['POST'])
def analyze_news(request):
    stock = request.data.get('stock')
    return Response({"message": f"Analyzing news for {stock}"})
