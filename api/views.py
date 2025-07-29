from django.http import JsonResponse, StreamingHttpResponse
from django.shortcuts import render
from .models import Message
from google import genai
from google.genai import types
import json

# اتصال به کلاینت Gemini
client = genai.Client(api_key='AIzaSyDWlXakRLBFGaU4NU95xd7uOl6CST85tA0')

# ابزار سرچ (اختیاری)
grounding_tool = types.Tool(
    google_search=types.GoogleSearch()
)

# تنظیمات ایمنی
safety = [
    types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_NONE"),
    types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_NONE"),
    types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_NONE"),
    types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_NONE"),
]

# هیستوری و چت گلوبال
history = []
chat = ''

# اینیت کردن چت Gemini با هیستوری دیتابیس
def init(request):
    global chat
    messages = Message.objects.all()

    for message in messages:
        if message.role != 'system':
            history.append({
                "role": message.role,
                "parts": [{"text": message.content}]
            })

    system_msg = Message.objects.get(role='system')
    chat = client.chats.create(
        model="gemini-2.5-flash",
        history=history,
        config=types.GenerateContentConfig(
            system_instruction=system_msg.content,
            safety_settings=safety,
            tools=[grounding_tool]
        )
    )

    return JsonResponse({'status': 'success'})


def response_streaming_view(request):
    global chat
    body = json.loads(request.body)
    user_message = body.get("message")
    response_stream = chat.send_message_stream(user_message)

    def event_stream():
        full_text = ''
        for chunk in response_stream:
            text = chunk.text
            full_text += text
            yield f"data: {json.dumps({'text': text})}\n\n"

        # ذخیره در دیتابیس در صورت نیاز
        if '--important' in full_text and '--nosave' not in user_message:
            Message.objects.create(role='user', content=user_message)
            Message.objects.create(role='model', content=full_text)

    response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
    response['X-Accel-Buffering'] = 'no'  # این خط کلیدی است
    response['Cache-Control'] = 'no-cache' # برای اطمینان بیشتر
    return response