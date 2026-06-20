from django.shortcuts import render, redirect
from django.contrib.auth.models import User
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import UserActivity, ProcrastinationReport
from django.db.models import Sum
from django.contrib.auth.decorators import login_required

# --- 1. MASTER DICTIONARY RULES ---
# Everything is controlled from here now.
APP_RULES = {
    'distractions': ['whatsapp', 'youtube', 'facebook', 'netflix', 'instagram', 'prime video', 'twitter', 'discord', 'chrome'],
    'productive': ['visual studio code', 'vscode', 'pycharm', 'github', 'stackoverflow', 'terminal', 'teams', 'zoom', 'linkedin', 'docs', 'excel']
}

def classify_activity(window_title):
    """
    Unified helper to scan the window title for keywords.
    Used by both the Receiver (POST) and the Dashboard (GET).
    """
    title_lower = window_title.lower()
    
    # Check for distractions first
    for word in APP_RULES['distractions']:
        if word in title_lower:
            return False 
            
    # Check for work apps
    for word in APP_RULES['productive']:
        if word in title_lower:
            return True 
            
    # Default to True (Productive) if unknown
    return True

# --- 2. USER HOME ---
def userhome(request):
    return render(request, 'User/userhome.html', {'user': request.user})

def get_current_session_user(request):
    if request.user.is_authenticated:
        return JsonResponse({"username": request.user.username})
    return JsonResponse({"username": None}, status=401)

# --- 3. TRACKER RECEIVER ---
@csrf_exempt
def receive_activity(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            username = data.get('username')
            user = User.objects.get(username=username)
            
            app_name = data.get('app_name', 'Unknown')
            window_title = data.get('window_title', '')
            
            # Apply Dictionary Logic
            is_prod = classify_activity(window_title)
            
            try:
                duration = int(data.get('duration', 30))
            except (ValueError, TypeError):
                duration = 30
            
            # Create Log
            UserActivity.objects.create(
                user=user,
                app_name=app_name,
                window_title=window_title,
                duration_seconds=duration,
                is_productive=is_prod
            )
            
            print(f"--- LOGGED: {app_name} | Productive: {is_prod} ---")
            return JsonResponse({"status": "success"}, status=201)
            
        except User.DoesNotExist:
            return JsonResponse({"status": "error", "message": "User not found"}, status=404)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)
            
    return JsonResponse({"status": "error", "message": "Only POST allowed"}, status=405)

# --- 4. AI DASHBOARD ---
@login_required(login_url='/')
def user_dashboard(request):
    user = request.user
    
    # Get top 20 logs for the feed
    recent_activities = UserActivity.objects.filter(user=user).order_by('-timestamp')[:20]
    
    # SYNC: Re-classify existing logs in the dashboard view to match current dictionary rules
    for activity in recent_activities:
        activity.is_productive = classify_activity(activity.window_title)
        activity.save()

    # Stats for Chart (Overall)
    dist_count = UserActivity.objects.filter(user=user, is_productive=False).count()
    prod_count = UserActivity.objects.filter(user=user, is_productive=True).count()
    total = dist_count + prod_count

    # KPI: Total wasted time in the current visible window (top 20)
    recent_ids = [a.id for a in recent_activities]
    total_wasted_sec = UserActivity.objects.filter(
        user=user, 
        is_productive=False, 
        id__in=recent_ids
    ).aggregate(Sum('duration_seconds'))['duration_seconds__sum'] or 0
    
    wasted_min = round(total_wasted_sec / 60, 1)
    
    # Procrastination Score
    score = (dist_count / total * 100) if total > 0 else 0
    
    # XAI Explanation Logic
    if score > 60:
        explanation = f"Critically High Procrastination. You have wasted {wasted_min} minutes recently. Focus is required."
    elif score > 20:
        explanation = f"Moderate Procrastination. {wasted_min} minutes lost to non-work apps. Context switching is reducing your efficiency."
    else:
        explanation = "Excellent Productivity! You have spent minimal time on distractions. Keep up the deep work."

    # Update or Create the AI Report
    report, _ = ProcrastinationReport.objects.update_or_create(
        user=user,
        defaults={'procrastination_score': score, 'xai_explanation': explanation}
    )

    context = {
        'activities': recent_activities, 
        'report': report,
        'prod_count': prod_count,
        'dist_count': dist_count,
        'wasted_min': wasted_min,
    }
    return render(request, 'User/user_dashboard.html', context)