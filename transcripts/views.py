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
    
    if isEmpty == False:
        LLM.init_LLM()

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
