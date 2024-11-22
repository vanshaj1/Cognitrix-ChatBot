# # transcripts/urls.py

# from django.urls import path
# from . import views

# urlpatterns = [
#     path('', views.index, name='index'),
#     path('get-transcript/', views.get_transcript, name='get_transcript'),
# ]

# transcripts/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('get-transcript/', views.get_transcript, name='get_transcript'),
    path('remove-playlist/<str:playlist_name>/', views.remove_playlist, name='remove_playlist'),  # New URL for removing playlists
]
