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

from django.contrib.auth.decorators import user_passes_test

def is_superuser(user):
    return user.is_superuser

urlpatterns = [
    path('', user_passes_test(is_superuser)(views.index), name='index'),
    path('get-transcript/', user_passes_test(is_superuser)(views.get_transcript), name='get_transcript'),
    path('remove-playlist/<str:playlist_name>/', user_passes_test(is_superuser)(views.remove_playlist), name='remove_playlist'),  # New URL for removing playlists
    path('create-embeddings', user_passes_test(is_superuser)(views.create_embeddings), name='create_embeddings'),
]
