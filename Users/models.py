from django.db import models
from django.contrib.auth.models import User

class UserActivity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    app_name = models.CharField(max_length=255)
    window_title = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    duration_seconds = models.IntegerField(default=30) # The tracker sends 30s pings
    is_productive = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.username} - {self.app_name}"

class ProcrastinationReport(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    procrastination_score = models.FloatField() # e.g., 0.0 to 1.0
    xai_explanation = models.TextField() # The "Explainable" part (e.g., "High YouTube usage")
    top_distraction = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"Report for {self.user.username} on {self.date}"
    
class AppCategory(models.Model):
    app_name = models.CharField(max_length=100, unique=True)
    is_productive = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.app_name} - {'Productive' if self.is_productive else 'Distraction'}"