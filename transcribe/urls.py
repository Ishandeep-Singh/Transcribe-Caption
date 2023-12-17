from django.urls import path
from transcribe.views import upload, download_file, signup, LoginPage, LogoutPage, user_details_view,delete_user_details

urlpatterns = [
    path('upload/',upload, name="upload"),
    path('download/<str:file_path>/', download_file, name='download_file'),

    path('',signup, name="signup"),
    path('login/', LoginPage, name="LoginPage"),
    path('logout/', LogoutPage, name="LogoutPage"),
    path('user_details/', user_details_view, name='user_details'),
    path('user_details/<int:id>/', delete_user_details, name='delete_user_detail'),
]
