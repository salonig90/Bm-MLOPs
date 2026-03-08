from django.shortcuts import render

def blog_list(request):
    """
    Renders the list of educational blog posts.
    """
    return render(request, 'blogs/list.html')

def drift_detection_blog(request):
    """
    Renders the specific blog post about Drift Detection and BTCUSD pathing.
    """
    return render(request, 'blogs/drift_detection.html')
