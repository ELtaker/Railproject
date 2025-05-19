from django.urls import path
from .views import (
    BusinessRegisterView,
    BusinessLoginView,
    BusinessDashboardView,
    BusinessProfileView,
    BusinessPublicProfileView,
)

app_name = 'businesses'

urlpatterns = [
    path('business/register/', BusinessRegisterView.as_view(), name='business-register'),
    path('business/login/', BusinessLoginView.as_view(), name='business-login'),
    path('business/dashboard/', BusinessDashboardView.as_view(), name='business-dashboard'),
    path('profile/', BusinessProfileView.as_view(), name='business-profile'),
    path('<int:pk>/', BusinessPublicProfileView.as_view(), name='business-public-profile'),
]