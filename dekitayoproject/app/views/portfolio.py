
from django.shortcuts import render

# ポートフォリオ用画面

def portfolio(request):

    return render (request, 'app/portfolio.html')