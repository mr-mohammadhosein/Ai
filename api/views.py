from django.shortcuts import render
from google import genai
from .models import Message
from django.http import JsonResponse, HttpResponse
from google.genai import types
import json

client = genai.Client(api_key='AIzaSyDWlXakRLBFGaU4NU95xd7uOl6CST85tA0')

grounding_tool = types.Tool(
    google_search=types.GoogleSearch()
)


safety=[
            types.SafetySetting(
                category="HARM_CATEGORY_HARASSMENT",
                threshold="BLOCK_NONE",  # Block none
            ),
            types.SafetySetting(
                category="HARM_CATEGORY_HATE_SPEECH",
                threshold="BLOCK_NONE",  # Block none
            ),
            types.SafetySetting(
                category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
                threshold="BLOCK_NONE",  # Block none
            ),
            types.SafetySetting(
                category="HARM_CATEGORY_DANGEROUS_CONTENT",
                threshold="BLOCK_NONE",  # Block none
            ),
        ]

history = []

chat = ''

def init(request):
    global chat
    messages = Message.objects.all()

    for message in messages:
        if message.role != 'system':
            history.append({"role": message.role, "parts": [{"text": message.content}]})
    print(Message.objects.get(role='system'))
    chat = client.chats.create(model="gemini-2.5-flash", history=history, config=types.GenerateContentConfig(system_instruction=Message.objects.get(role='system').content, safety_settings=safety, tools=[grounding_tool]))
    return JsonResponse({'status': 'success'})



def response(request):
    global chat
    body = json.loads(request.body)
    user_message = body.get("message")
    response = chat.send_message(user_message)
    if '--important' in response.text and '--nosave' not in user_message:
        Message.objects.create(role='user', content=user_message)
        Message.objects.create(role='model', content=response.text)
    return JsonResponse(
        {"response": response.text},
        json_dumps_params={'ensure_ascii': False}
    )