from django.shortcuts import render
from django.http import JsonResponse
import markdown
from . import LLM_model
import random
# from gradio_client import Client
import os
import csv 

def index(request):
    if request.method == 'POST':
        message = request.POST.get('message') + ".please also provide videos links."
        print(message)
        print(type(message))
        response = LLM_model.ask_Query(message)
        response = markdown.markdown(response)
        # client = Client("https://28dd0fd555d026ac2a.gradio.live")
        # result = client.predict(message)
        return JsonResponse({'message': message, 'response': response})
    
    file_path = 'transcripts/transcripts.csv'

    message = None  # Variable to store message

    # Check if the file exists
    if not os.path.exists(file_path):
        message = 'No data found request admin to provide some data.'
    else:
        # Read CSV and check if it contains rows
        with open(file_path, mode='r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            rows = list(reader)

            if len(rows) <= 1:  # Only header or no data
                message = 'No data found request admin to provide some data.'

    return render(request, 'chatbot.html', {'message': message})
