from django.urls import path, include
from rest_framework.routers import DefaultRouter

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from . import views
from .views import  RegisterUserView,LoginView,ProjectListCreateView, ProjectDetailView,\
    Contribution,UserprofileUpdateView,ChatReasonListCreateView,MessageViewSet,ContributionsView, ContributionDetailView

router = DefaultRouter()
router.register(r'messages', MessageViewSet, basename='messages')


urlpatterns = [
    path('', include(router.urls)),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('login/', LoginView.as_view(), name='login'),
    path('register/', RegisterUserView.as_view(), name='register_user'),
    path('projects/', ProjectListCreateView.as_view(), name='project-create'),
    path('projects/<int:pk>/', ProjectDetailView.as_view(), name='project-detail'),
    path('contributions/<int:pk>/', views.ContributionDetailView.as_view(), name='contribution'),
    path('contributions/', views.ContributionsView.as_view(), name='contributions'),
    path('verify_pay/', views.contribute, name='verify-pay'),
    path('update_profile/', views.UserprofileUpdateView.as_view(), name='update-profile'),
    path('chat_reason/', views.ChatReasonListCreateView.as_view(), name='chat-reason'),
]