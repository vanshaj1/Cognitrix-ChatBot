#******************************************************Using YoutubeTranscriptAPI*******************************************
from django.shortcuts import render
from youtube_transcript_api import YouTubeTranscriptApi
from django.http import JsonResponse
import re
import os
import requests
import csv
import frontend.LLM_model as LLM
from dotenv import load_dotenv


# Load environment variables from a .env file
load_dotenv()

# Add your YouTube Data API key here
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

# Helper function to extract video ID or playlist ID
def extract_video_or_playlist_id(youtube_url):
    video_regex = r"(?<=v=)[^&]+"
    playlist_regex = r"(?<=list=)[^&]+"

    video_match = re.search(video_regex, youtube_url)
    playlist_match = re.search(playlist_regex, youtube_url)

    if playlist_match:
        return {'playlist_id': playlist_match.group(0)}
    elif video_match:
        return {'video_id': video_match.group(0)}
    return None

# Function to save transcript to Excel
def save_transcript_to_csv(video_id, transcript_text, video_link, playlist_name):
    file_path = 'transcripts/transcripts.csv'
    
    # Create the directory if it doesn't exist
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # Check if the file exists
    file_exists = os.path.exists(file_path)

    # Open the CSV file in append mode
    with open(file_path, mode='a', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)

        # Write headers if the file is new
        if not file_exists:
            writer.writerow(['Playlist Name', 'Video ID', 'Transcript', 'Video Link', 'Video Link + Transcript'])

        # Format the combined value with line breaks
        combined_value = f"Link: {video_link}\nTranscript: {transcript_text}"

        # Append the row data
        writer.writerow([playlist_name, video_id, transcript_text, video_link, combined_value])

    print(f"Transcript saved to {file_path}")

# Function to get all video IDs from a YouTube playlist
def get_video_ids_from_playlist(playlist_id):
    base_url = 'https://www.googleapis.com/youtube/v3/playlistItems'
    params = {
        'part': 'contentDetails',
        'playlistId': playlist_id,
        'maxResults': 50,
        'key': YOUTUBE_API_KEY
    }

    video_ids = []
    next_page_token = None

    while True:
        if next_page_token:
            params['pageToken'] = next_page_token

        response = requests.get(base_url, params=params)
        data = response.json()

        if 'items' in data:
            video_ids += [item['contentDetails']['videoId'] for item in data['items']]

        next_page_token = data.get('nextPageToken')
        if not next_page_token:
            break

    return video_ids

def get_transcript(request):
    if request.method == 'POST':
        youtube_link = request.POST.get('youtubeLink')
        extracted_ids = extract_video_or_playlist_id(youtube_link)

        if not extracted_ids:
            return JsonResponse({'error': 'Invalid YouTube URL'}, status=400)

        try:
            if 'playlist_id' in extracted_ids:
                # It's a playlist URL
                playlist_id = extracted_ids['playlist_id']
                playlist_name = youtube_link.split('=')[1]  # Extract playlist name from URL
                video_ids = get_video_ids_from_playlist(playlist_id)

                print('Youtube API Call')
                print(video_ids)

                print('YoutubeTranscript API call')

                for video_id in video_ids:
                    try:
                        transcript = YouTubeTranscriptApi.get_transcript(video_id)
                        transcript_text = " ".join([entry['text'] for entry in transcript])
                        video_url = f"https://www.youtube.com/watch?v={video_id}"
                        save_transcript_to_csv(video_id, transcript_text, video_url, playlist_name)
                    except Exception as e:
                        print(f"Error getting transcript for video {video_id}: {str(e)}")
                
                LLM.init_LLM()
                return JsonResponse({'message': f'Transcripts for {len(video_ids)} videos saved successfully!'})

            elif 'video_id' in extracted_ids:
                # It's a single video URL
                video_id = extracted_ids['video_id']
                transcript = YouTubeTranscriptApi.get_transcript(video_id)
                transcript_text = " ".join([entry['text'] for entry in transcript])
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                save_transcript_to_csv(video_id, transcript_text, video_url, "")
                LLM.init_LLM()
                return JsonResponse({'message': 'Transcript successfully saved!'})
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
        
    # LLM.init_LLM()
    return JsonResponse({'error': 'Invalid request method'}, status=400)

def remove_playlist(request, playlist_name):
    file_path = 'transcripts/transcripts.csv'

    if not os.path.exists(file_path):
        return JsonResponse({'error': 'CSV file does not exist'}, status=404)

    rows_to_keep = []

    # Read the CSV file and filter out rows matching the playlist_name
    with open(file_path, mode='r', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        headers = next(reader)  # Read the header row
        for row in reader:
            if row[0] != playlist_name:  # Keep rows that don't match the playlist name
                rows_to_keep.append(row)

    # Clear the CSV by opening it in write mode and writing back only the filtered rows
    with open(file_path, mode='w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers)  # Write the header row
        writer.writerows(rows_to_keep)  # Write the filtered rows


    isEmpty = False  # Variable to store message
    # Read CSV and check if it contains rows
    with open(file_path, mode='r', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        rows = list(reader)

        if len(rows) <= 1:  # Only header or no data
            isEmpty = True
    
    # if isEmpty == False:
    #     LLM.init_LLM()

    return JsonResponse({'message': f'Playlist "{playlist_name}" removed successfully!'})

def index(request):
   # Load the playlists to display on the homepage
    playlists = []
    file_path = 'transcripts/transcripts.csv'

    if os.path.exists(file_path):
        with open(file_path, mode='r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            next(reader)  # Skip the header row
            for row in reader:
                playlists.append(row[0])  # Append the playlist name (first column)

    return render(request, 'transcripts/index.html', {'playlists': set(playlists)})  # Return unique playlist names


#**********************************************Using service account*******************************************
# from django.shortcuts import render
# from django.http import JsonResponse
# import os
# import re
# import requests
# from google.oauth2.service_account import Credentials
# from googleapiclient.discovery import build
# from googleapiclient.errors import HttpError
# import csv
# from dotenv import load_dotenv

# # Load environment variables
# load_dotenv()

# # # Add your YouTube Data API key here
# # YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

# SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']

# # Path to your service account JSON key file
# SERVICE_ACCOUNT_FILE = './service_account_file.json'

# # Authenticate using the service account
# def authenticate_youtube_api():
#     credentials = Credentials.from_service_account_file(
#         SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    
#     # Build the YouTube API client with the authenticated credentials
#     youtube = build('youtube', 'v3', credentials=credentials)
#     return youtube

# # Helper function to extract video ID or playlist ID
# def extract_video_or_playlist_id(youtube_url):
#     video_regex = r"(?<=v=)[^&]+"
#     playlist_regex = r"(?<=list=)[^&]+"

#     video_match = re.search(video_regex, youtube_url)
#     playlist_match = re.search(playlist_regex, youtube_url)

#     if playlist_match:
#         return {'playlist_id': playlist_match.group(0)}
#     elif video_match:
#         return {'video_id': video_match.group(0)}
#     return None


# def get_video_ids_from_playlist(playlist_id, youtube_client):
#     """Retrieve all video IDs from a given playlist."""
#     try:
#         video_ids = []
#         request = youtube_client.playlistItems().list(
#             part="contentDetails",
#             playlistId=playlist_id,
#             maxResults=50
#         )
#         while request:
#             response = request.execute()
#             video_ids += [item['contentDetails']['videoId'] for item in response.get('items', [])]
#             request = youtube_client.playlistItems().list_next(request, response)
#         return video_ids
#     except HttpError as e:
#         raise Exception(f"An error occurred: {e}")

# def fetch_captions(video_id, youtube_client):
#     """Fetch captions for a video using YouTube Data API."""
#     try:
#         captions = youtube_client.captions().list(
#             part="snippet",
#             videoId=video_id
#         ).execute()
#         caption_id = None
#         for caption in captions.get('items', []):
#             if caption['snippet']['language'] == 'en':  # Fetch English captions
#                 caption_id = caption['id']
#                 break

#         if not caption_id:
#             return "No English captions available"

#         # Download the caption text
#         caption_response = youtube_client.captions().download(
#             id=caption_id,
#             tfmt="srt"  # Fetch in SubRip Subtitle format
#         ).execute()

#         return caption_response.decode("utf-8")
#     except HttpError as e:
#         if e.resp.status == 404:
#             return "Captions not found"
#         else:
#             raise Exception(f"An error occurred: {e}")

# def save_transcript_to_csv(video_id, transcript_text, video_link, playlist_name):
#     """Save transcript to a CSV file."""
#     file_path = 'transcripts/transcripts.csv'
#     os.makedirs(os.path.dirname(file_path), exist_ok=True)

#     file_exists = os.path.exists(file_path)
#     with open(file_path, mode='a', newline='', encoding='utf-8') as csvfile:
#         writer = csv.writer(csvfile)
#         if not file_exists:
#             writer.writerow(['Playlist Name', 'Video ID', 'Transcript', 'Video Link', 'Video Link + Transcript'])

#         combined_value = f"Link: {video_link}\nTranscript: {transcript_text}"
#         writer.writerow([playlist_name, video_id, transcript_text, video_link, combined_value])

# def get_transcript(request):
#     """Main function to handle transcript fetching."""
#     if request.method == 'POST':
#         youtube_link = request.POST.get('youtubeLink')
#         extracted_ids = extract_video_or_playlist_id(youtube_link)

#         if not extracted_ids:
#             return JsonResponse({'error': 'Invalid YouTube URL'}, status=400)

#         try:
#             youtube_client = authenticate_youtube_api()
#             if 'playlist_id' in extracted_ids:
#                 playlist_id = extracted_ids['playlist_id']
#                 playlist_name = youtube_link.split('=')[1]
#                 video_ids = get_video_ids_from_playlist(playlist_id, youtube_client)

#                 for video_id in video_ids:
#                     video_url = f"https://www.youtube.com/watch?v={video_id}"
#                     transcript_text = fetch_captions(video_id, youtube_client)
#                     save_transcript_to_csv(video_id, transcript_text, video_url, playlist_name)

#                 return JsonResponse({'message': f'Transcripts for {len(video_ids)} videos saved successfully!'})

#             elif 'video_id' in extracted_ids:
#                 video_id = extracted_ids['video_id']
#                 video_url = f"https://www.youtube.com/watch?v={video_id}"
#                 transcript_text = fetch_captions(video_id, youtube_client)
#                 save_transcript_to_csv(video_id, transcript_text, video_url, "")
#                 return JsonResponse({'message': 'Transcript successfully saved!'})

#         except Exception as e:
#             return JsonResponse({'error': str(e)}, status=500)

#     return JsonResponse({'error': 'Invalid request method'}, status=400)

# def remove_playlist(request, playlist_name):
#     file_path = 'transcripts/transcripts.csv'

#     if not os.path.exists(file_path):
#         return JsonResponse({'error': 'CSV file does not exist'}, status=404)

#     rows_to_keep = []

#     # Read the CSV file and filter out rows matching the playlist_name
#     with open(file_path, mode='r', encoding='utf-8') as csvfile:
#         reader = csv.reader(csvfile)
#         headers = next(reader)  # Read the header row
#         for row in reader:
#             if row[0] != playlist_name:  # Keep rows that don't match the playlist name
#                 rows_to_keep.append(row)

#     # Clear the CSV by opening it in write mode and writing back only the filtered rows
#     with open(file_path, mode='w', newline='', encoding='utf-8') as csvfile:
#         writer = csv.writer(csvfile)
#         writer.writerow(headers)  # Write the header row
#         writer.writerows(rows_to_keep)  # Write the filtered rows


#     isEmpty = False  # Variable to store message
#     # Read CSV and check if it contains rows
#     with open(file_path, mode='r', encoding='utf-8') as csvfile:
#         reader = csv.reader(csvfile)
#         rows = list(reader)

#         if len(rows) <= 1:  # Only header or no data
#             isEmpty = True
    
# #     if isEmpty == False:
# #         LLM.init_LLM()

#     return JsonResponse({'message': f'Playlist "{playlist_name}" removed successfully!'})

# def index(request):
#    # Load the playlists to display on the homepage
#     playlists = []
#     file_path = 'transcripts/transcripts.csv'

#     if os.path.exists(file_path):
#         with open(file_path, mode='r', encoding='utf-8') as csvfile:
#             reader = csv.reader(csvfile)
#             next(reader)  # Skip the header row
#             for row in reader:
#                 playlists.append(row[0])  # Append the playlist name (first column)

#     return render(request, 'transcripts/index.html', {'playlists': set(playlists)})  # Return unique playlist names


#*******************************************Uisg ptube**************************************
# from pytube import YouTube
# import os
# import csv
# import re
# from django.shortcuts import render
# from django.http import JsonResponse
# import requests
# import frontend.LLM_model as LLM
# from dotenv import load_dotenv


# # Load environment variables from a .env file
# load_dotenv()

# # Add your YouTube Data API key here
# YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

# # Helper function to extract video ID or playlist ID
# def extract_video_or_playlist_id(youtube_url):
#     video_regex = r"(?<=v=)[^&]+"
#     playlist_regex = r"(?<=list=)[^&]+"

#     video_match = re.search(video_regex, youtube_url)
#     playlist_match = re.search(playlist_regex, youtube_url)

#     if playlist_match:
#         return {'playlist_id': playlist_match.group(0)}
#     elif video_match:
#         return {'video_id': video_match.group(0)}
#     return None


# # Function to save transcript to CSV
# def save_transcript_to_csv(video_id, transcript_text, video_link, playlist_name):
#     file_path = 'transcripts/transcripts.csv'
    
#     # Create the directory if it doesn't exist
#     os.makedirs(os.path.dirname(file_path), exist_ok=True)

#     # Check if the file exists
#     file_exists = os.path.exists(file_path)

#     # Open the CSV file in append mode
#     with open(file_path, mode='a', newline='', encoding='utf-8') as csvfile:
#         writer = csv.writer(csvfile)

#         # Write headers if the file is new
#         if not file_exists:
#             writer.writerow(['Playlist Name', 'Video ID', 'Transcript', 'Video Link', 'Video Link + Transcript'])

#         # Format the combined value with line breaks
#         combined_value = f"Link: {video_link}\nTranscript: {transcript_text}"

#         # Append the row data
#         writer.writerow([playlist_name, video_id, transcript_text, video_link, combined_value])

#     print(f"Transcript saved to {file_path}")

# # Function to get transcript using ptube
# def get_transcript_from_video(video_id):
#     try:
#         video = YouTube(f"https://www.youtube.com/watch?v={video_id}")
#         captions = video.captions
#         print(captions)
#         if captions:
#             # Print available languages
#             available_languages = captions.keys()
#             print(f"Available languages: {available_languages}")
            
#             # Check if automated English captions are available
#             if 'a.en' in available_languages:  # 'a.en' stands for automated English subtitles
#                 # Fetch the automated English subtitles
#                 subtitle = captions['a.en']
                
#                 # Generate SRT (SubRip Subtitle) format from the subtitle
#                 srt_caption = subtitle.generate_srt_captions()
                
#                 return srt_caption
#             return captions
#         else:
#             return "No transcript available"
#     except Exception as e:
#         print(f"Error fetching transcript: {e}")
#         return None


# def get_video_ids_from_playlist(playlist_id):
#     base_url = 'https://www.googleapis.com/youtube/v3/playlistItems'
#     params = {
#         'part': 'contentDetails',
#         'playlistId': playlist_id,
#         'maxResults': 50,
#         'key': YOUTUBE_API_KEY
#     }

#     video_ids = []
#     next_page_token = None

#     while True:
#         if next_page_token:
#             params['pageToken'] = next_page_token

#         response = requests.get(base_url, params=params)
#         data = response.json()

#         if 'items' in data:
#             video_ids += [item['contentDetails']['videoId'] for item in data['items']]

#         next_page_token = data.get('nextPageToken')
#         if not next_page_token:
#             break

#     return video_ids


# def get_transcript(request):
#     if request.method == 'POST':
#         youtube_link = request.POST.get('youtubeLink')
#         extracted_ids = extract_video_or_playlist_id(youtube_link)

#         if not extracted_ids:
#             return JsonResponse({'error': 'Invalid YouTube URL'}, status=400)

#         try:
#             if 'playlist_id' in extracted_ids:
#                 # It's a playlist URL
#                 playlist_id = extracted_ids['playlist_id']
#                 playlist_name = youtube_link.split('=')[1]  # Extract playlist name from URL
                
#                 # Retrieve video IDs from the playlist (similar to the previous method)
#                 video_ids = get_video_ids_from_playlist(playlist_id)

#                 for video_id in video_ids:
#                     transcript_text = get_transcript_from_video(video_id)
#                     if transcript_text:
#                         video_url = f"https://www.youtube.com/watch?v={video_id}"
#                         save_transcript_to_csv(video_id, transcript_text, video_url, playlist_name)

#                 return JsonResponse({'message': f'Transcripts for {len(video_ids)} videos saved successfully!'})

#             elif 'video_id' in extracted_ids:
#                 # It's a single video URL
#                 video_id = extracted_ids['video_id']
#                 transcript_text = get_transcript_from_video(video_id)
#                 if transcript_text:
#                     video_url = f"https://www.youtube.com/watch?v={video_id}"
#                     save_transcript_to_csv(video_id, transcript_text, video_url, "")
#                     return JsonResponse({'message': 'Transcript successfully saved!'})
            
#         except Exception as e:
#             return JsonResponse({'error': str(e)}, status=500)
        
#     return JsonResponse({'error': 'Invalid request method'}, status=400)




# def remove_playlist(request, playlist_name):
#     file_path = 'transcripts/transcripts.csv'

#     if not os.path.exists(file_path):
#         return JsonResponse({'error': 'CSV file does not exist'}, status=404)

#     rows_to_keep = []

#     # Read the CSV file and filter out rows matching the playlist_name
#     with open(file_path, mode='r', encoding='utf-8') as csvfile:
#         reader = csv.reader(csvfile)
#         headers = next(reader)  # Read the header row
#         for row in reader:
#             if row[0] != playlist_name:  # Keep rows that don't match the playlist name
#                 rows_to_keep.append(row)

#     # Clear the CSV by opening it in write mode and writing back only the filtered rows
#     with open(file_path, mode='w', newline='', encoding='utf-8') as csvfile:
#         writer = csv.writer(csvfile)
#         writer.writerow(headers)  # Write the header row
#         writer.writerows(rows_to_keep)  # Write the filtered rows


#     isEmpty = False  # Variable to store message
#     # Read CSV and check if it contains rows
#     with open(file_path, mode='r', encoding='utf-8') as csvfile:
#         reader = csv.reader(csvfile)
#         rows = list(reader)

#         if len(rows) <= 1:  # Only header or no data
#             isEmpty = True
    
#     if isEmpty == False:
#         LLM.init_LLM()

#     return JsonResponse({'message': f'Playlist "{playlist_name}" removed successfully!'})

# def index(request):
#    # Load the playlists to display on the homepage
#     playlists = []
#     file_path = 'transcripts/transcripts.csv'

#     if os.path.exists(file_path):
#         with open(file_path, mode='r', encoding='utf-8') as csvfile:
#             reader = csv.reader(csvfile)
#             next(reader)  # Skip the header row
#             for row in reader:
#                 playlists.append(row[0])  # Append the playlist name (first column)

#     return render(request, 'transcripts/index.html', {'playlists': set(playlists)})  # Return unique playlist names




#***********************************OAuth*****************************************
# from google_auth_oauthlib.flow import InstalledAppFlow
# from googleapiclient.discovery import build
# from django.shortcuts import render
# from django.http import JsonResponse
# import os
# import re
# import requests
# from googleapiclient.errors import HttpError
# from google.oauth2.credentials import Credentials
# import csv
# from dotenv import load_dotenv

# # Load environment variables
# load_dotenv()

# # Add your YouTube Data API key here
# # YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

# # Path to your service account JSON key file
# SECRET_ACCOUNT_FILE = './oAuth.json'
# TOKEN_FILE = "./token.json"
# # Set up the OAuth 2.0 scopes
# SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']

# # Function to authenticate using OAuth 2.0
# def authenticate_oauth():
#     if not os.path.exists(TOKEN_FILE):
#         try:
#             flow = InstalledAppFlow.from_client_secrets_file(
#                 SECRET_ACCOUNT_FILE,
#                 scopes=["https://www.googleapis.com/auth/youtube.upload",
#                         "https://www.googleapis.com/auth/youtube.force-ssl"]
#             )
#             credentials = flow.run_local_server(port=0)
#             # Save the credentials for future use
#             with open(TOKEN_FILE, "w") as credentials_file:
#                 credentials_file.write(credentials.to_json())
#             return build("youtube", "v3", credentials=credentials)
#         except Exception as e:
#             print(f"Failed to authenticate with {SECRET_ACCOUNT_FILE}: {e}")
#     else:
#         try:
#             credentials = Credentials.from_authorized_user_file(TOKEN_FILE)
#             return build("youtube", "v3", credentials=credentials)
#         except Exception as e:
#             print(f"Failed to load stored credentials from {TOKEN_FILE}: {e}")

# # Helper function to extract video ID or playlist ID
# def extract_video_or_playlist_id(youtube_url):
#     video_regex = r"(?<=v=)[^&]+"
#     playlist_regex = r"(?<=list=)[^&]+"

#     video_match = re.search(video_regex, youtube_url)
#     playlist_match = re.search(playlist_regex, youtube_url)

#     if playlist_match:
#         return {'playlist_id': playlist_match.group(0)}
#     elif video_match:
#         return {'video_id': video_match.group(0)}
#     return None


# def get_video_ids_from_playlist(playlist_id, youtube_client):
#     """Retrieve all video IDs from a given playlist."""
#     try:
#         video_ids = []
#         request = youtube_client.playlistItems().list(
#             part="contentDetails",
#             playlistId=playlist_id,
#             maxResults=50
#         )
#         while request:
#             response = request.execute()
#             video_ids += [item['contentDetails']['videoId'] for item in response.get('items', [])]
#             request = youtube_client.playlistItems().list_next(request, response)
#         return video_ids
#     except HttpError as e:
#         raise Exception(f"An error occurred: {e}")

# def fetch_captions(video_id, youtube_client):
#     """Fetch captions for a video using YouTube Data API."""
#     try:
#         captions = youtube_client.captions().list(
#             part="snippet",
#             videoId=video_id
#         ).execute()
#         caption_id = None
#         for caption in captions.get('items', []):
#             if caption['snippet']['language'] == 'en':  # Fetch English captions
#                 caption_id = caption['id']
#                 break

#         if not caption_id:
#             return "No English captions available"

#         # Download the caption text
#         caption_response = youtube_client.captions().download(
#             id=caption_id,
#             tfmt="srt"  # Fetch in SubRip Subtitle format
#         ).execute()

#         return caption_response.decode("utf-8")
#     except HttpError as e:
#         if e.resp.status == 404:
#             return "Captions not found"
#         else:
#             raise Exception(f"An error occurred: {e}")

# def save_transcript_to_csv(video_id, transcript_text, video_link, playlist_name):
#     """Save transcript to a CSV file."""
#     file_path = 'transcripts/transcripts.csv'
#     os.makedirs(os.path.dirname(file_path), exist_ok=True)

#     file_exists = os.path.exists(file_path)
#     with open(file_path, mode='a', newline='', encoding='utf-8') as csvfile:
#         writer = csv.writer(csvfile)
#         if not file_exists:
#             writer.writerow(['Playlist Name', 'Video ID', 'Transcript', 'Video Link', 'Video Link + Transcript'])

#         combined_value = f"Link: {video_link}\nTranscript: {transcript_text}"
#         writer.writerow([playlist_name, video_id, transcript_text, video_link, combined_value])

# def get_transcript(request):
#     """Main function to handle transcript fetching."""
#     if request.method == 'POST':
#         youtube_link = request.POST.get('youtubeLink')
#         extracted_ids = extract_video_or_playlist_id(youtube_link)

#         if not extracted_ids:
#             return JsonResponse({'error': 'Invalid YouTube URL'}, status=400)

#         try:
#             youtube_client = authenticate_oauth()
#             if 'playlist_id' in extracted_ids:
#                 playlist_id = extracted_ids['playlist_id']
#                 playlist_name = youtube_link.split('=')[1]
#                 video_ids = get_video_ids_from_playlist(playlist_id, youtube_client)

#                 for video_id in video_ids:
#                     video_url = f"https://www.youtube.com/watch?v={video_id}"
#                     transcript_text = fetch_captions(video_id, youtube_client)
#                     save_transcript_to_csv(video_id, transcript_text, video_url, playlist_name)

#                 return JsonResponse({'message': f'Transcripts for {len(video_ids)} videos saved successfully!'})

#             elif 'video_id' in extracted_ids:
#                 video_id = extracted_ids['video_id']
#                 video_url = f"https://www.youtube.com/watch?v={video_id}"
#                 transcript_text = fetch_captions(video_id, youtube_client)
#                 save_transcript_to_csv(video_id, transcript_text, video_url, "")
#                 return JsonResponse({'message': 'Transcript successfully saved!'})

#         except Exception as e:
#             return JsonResponse({'error': str(e)}, status=500)

#     return JsonResponse({'error': 'Invalid request method'}, status=400)

# def remove_playlist(request, playlist_name):
#     file_path = 'transcripts/transcripts.csv'

#     if not os.path.exists(file_path):
#         return JsonResponse({'error': 'CSV file does not exist'}, status=404)

#     rows_to_keep = []

#     # Read the CSV file and filter out rows matching the playlist_name
#     with open(file_path, mode='r', encoding='utf-8') as csvfile:
#         reader = csv.reader(csvfile)
#         headers = next(reader)  # Read the header row
#         for row in reader:
#             if row[0] != playlist_name:  # Keep rows that don't match the playlist name
#                 rows_to_keep.append(row)

#     # Clear the CSV by opening it in write mode and writing back only the filtered rows
#     with open(file_path, mode='w', newline='', encoding='utf-8') as csvfile:
#         writer = csv.writer(csvfile)
#         writer.writerow(headers)  # Write the header row
#         writer.writerows(rows_to_keep)  # Write the filtered rows


#     isEmpty = False  # Variable to store message
#     # Read CSV and check if it contains rows
#     with open(file_path, mode='r', encoding='utf-8') as csvfile:
#         reader = csv.reader(csvfile)
#         rows = list(reader)

#         if len(rows) <= 1:  # Only header or no data
#             isEmpty = True
    
# #     if isEmpty == False:
# #         LLM.init_LLM()

#     return JsonResponse({'message': f'Playlist "{playlist_name}" removed successfully!'})

# def index(request):
#    # Load the playlists to display on the homepage
#     playlists = []
#     file_path = 'transcripts/transcripts.csv'

#     if os.path.exists(file_path):
#         with open(file_path, mode='r', encoding='utf-8') as csvfile:
#             reader = csv.reader(csvfile)
#             next(reader)  # Skip the header row
#             for row in reader:
#                 playlists.append(row[0])  # Append the playlist name (first column)

#     return render(request, 'transcripts/index.html', {'playlists': set(playlists)})  # Return unique playlist names