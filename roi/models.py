from django.db import models 
 
class ROIMetric(models.Model): 
    model_version = models.CharField(max_length=20) 
    period = models.CharField(max_length=20) # e.g. "Last 30 Days" 
    simulated_profit_usd = models.FloatField() 
    risk_reduction_pct = models.FloatField() 
    calculated_at = models.DateTimeField(auto_now_add=True) 
 
    def __str__(self): 
        return f"ROI for Version {self.model_version}: ${self.simulated_profit_usd}"
