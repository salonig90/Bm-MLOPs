from django.shortcuts import render 
from .models import ABTestRun 
 
def ab_testing_index(request): 
    """ 
    Displays current and past A/B tests between model versions. 
    """ 
    active_tests = ABTestRun.objects.filter(status='Active').order_by('-start_date') 
    past_tests = ABTestRun.objects.exclude(status='Active').order_by('-start_date') 
 
    # If no data exists, create a dummy entry for demonstration 
    if not active_tests.exists() and not past_tests.exists(): 
        ABTestRun.objects.create( 
            test_name="LR vs ARIMA Saloni Base", 
            control_model_version="LR_Saloni_1.0", 
            treatment_model_version="ARIMA_Saloni_1.0", 
            control_mse=0.0045, 
            treatment_mse=0.0058, 
            improvement_pct=-28.8, 
            status='Active' 
        ) 
        active_tests = ABTestRun.objects.filter(status='Active') 
 
    context = { 
        'active_tests': active_tests, 
        'past_tests': past_tests 
    } 
    return render(request, 'ab_testing/ab_testing_index.html', context)
