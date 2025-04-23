from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from core import views as core_views
from .views import my_profile, my_ideas, post_idea, edit_idea, delete_idea, search, view_idea, save_idea, saved_ideas_list, toggle_saved_idea, view_user_profile

urlpatterns = [
    path('', search, name='home'),
    path('set-language/', core_views.set_language, name='set_language'),
    path('register/', views.register, name='register'),
    path('terms/', views.terms, name='terms'),
    path('login/', auth_views.LoginView.as_view(template_name='users/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('profile/', my_profile, name='profile'),
    path('my-ideas/', my_ideas, name='my_ideas'),
    path("post_idea/", post_idea, name="post_idea"),
    path("edit_idea/<int:idea_id>/", edit_idea, name="edit_idea"),
    path("delete_idea/<int:idea_id>/", delete_idea, name="delete_idea"),
    path('search/', search, name='search'),
    path('ideas/<int:idea_id>/', view_idea, name='view_idea'),
    path('ideas/<int:idea_id>/save/', save_idea, name='save_idea'),
    path('saved-ideas/', saved_ideas_list, name='saved_ideas'),
    path('ideas/<int:idea_id>/toggle-save/', toggle_saved_idea, name='toggle_saved_idea'),
    path('users/<int:user_id>/', view_user_profile, name='view_user_profile'),
    path('inbox/', views.inbox, name='inbox'),
    path('inbox/<int:user_id>/', views.conversations, name='conversations'),
]
