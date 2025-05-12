from django.urls import path
from .views import BusinessProfileView, BusinessPublicProfileView

urlpatterns = [
    path('profile/', BusinessProfileView.as_view(), name='business_profile'),
    path('<int:pk>/', BusinessPublicProfileView.as_view(), name='business_public_profile'),
]

