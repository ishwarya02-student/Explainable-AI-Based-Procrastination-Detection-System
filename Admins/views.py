from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from Users.models import UserActivity, ProcrastinationReport
from django.db.models import Avg, Count

def adminhome(request):
    users = User.objects.filter(is_staff=False, is_superuser=False) 
    return render(request, "Admin/adminhome.html", {"users": users})

def admin_update_userstatus(request, user_id):
    try:
        user = User.objects.get(id=user_id)
        
        # Toggle the is_active status
        user.is_active = not user.is_active
        user.save()

        # Display message based on the action
        if user.is_active:
            messages.success(request, f"User {user.username} has been activated.")
        else:
            messages.success(request, f"User {user.username} has been deactivated.")
        
        return redirect('adminhome')  # Redirect back to the admin home page
    except User.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect('adminhome')

def admin_dashboard(request):
    # 1. Fetch non-admin users
    users = User.objects.filter(is_staff=False, is_superuser=False)
    
    # 2. Global Stats
    avg_score_raw = ProcrastinationReport.objects.aggregate(Avg('procrastination_score'))['procrastination_score__avg'] or 0
    
    # FIX: If your score is already stored as 20.0 (for 20%), don't multiply by 100.
    # If it's stored as 0.20, then multiply by 100.
    if avg_score_raw <= 1.0 and avg_score_raw > 0:
        avg_procrastination = avg_score_raw * 100
    else:
        avg_procrastination = avg_score_raw

    total_logs = UserActivity.objects.count()
    
    # 3. Top Distractions
    top_distractions = (UserActivity.objects.filter(is_productive=False)
                        .values('app_name')
                        .annotate(count=Count('app_name'))
                        .order_by('-count')[:5])

    # 4. User Summary Table
    user_data = []
    for user in users:
        # Use -id to get the absolute latest entry safely
        report = ProcrastinationReport.objects.filter(user=user).order_by('-id').first()
        
        raw_val = report.procrastination_score if report else 0
        
        # Consistent scaling for the progress bars
        display_score = raw_val * 100 if raw_val <= 1.0 and raw_val > 0 else raw_val
        
        # Classification based on your 60% threshold
        if display_score > 60:
            status, color = "High Risk", "danger"
        elif display_score > 30:
            status, color = "Distracted", "warning"
        else:
            status, color = "Focused", "success"

        user_data.append({
            'profile': user,
            'score': display_score,
            'status': status,
            'color': color,
            'explanation': report.xai_explanation if report else "No data"
        })

    context = {
        'avg_procrastination': avg_procrastination,
        'total_logs': total_logs,
        'top_distractions': top_distractions,
        'user_data': user_data
    }
    return render(request, "Admin/admin_dashboard.html", context)