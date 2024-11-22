from django.shortcuts import render
from django.http import JsonResponse
import markdown
from . import LLM_model
import random
from gradio_client import Client

def index(request):
    if request.method == 'POST':
        message = request.POST.get('message') + ".please also provide videos link."
        print(message)
        print(type(message))
        response = LLM_model.ask_Query(message)
        response = markdown.markdown(response)
        # client = Client("https://28dd0fd555d026ac2a.gradio.live")
        # result = client.predict(message)
        return JsonResponse({'message': message, 'response': response})
    return render(request, 'chatbot.html')
