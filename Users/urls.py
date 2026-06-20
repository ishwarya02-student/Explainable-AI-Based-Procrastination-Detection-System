from django.urls import path
from Users.views import *

urlpatterns = [
    path('userhome/', userhome, name='userhome'),
    path('get_session_user/', get_current_session_user, name='get_session_user'),
    path('receive_activity/', receive_activity, name='receive_activity'),
    path('dashboard/', user_dashboard, name='user_dashboard'),
]