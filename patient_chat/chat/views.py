from django.shortcuts import render
from django.views import View
from .models import Patient, Chat, Message
from django.http import JsonResponse
import openai
import os

class ChatView(View):
    def get(self, request):
        return render(request, 'chat/chat.html')

class SendMessageView(View):
    def post(self, request):
        patient = Patient.objects.first()  # Assuming one patient
        chat, created = Chat.objects.get_or_create(patient=patient)
        message_content = request.POST.get('message')
        Message.objects.create(chat=chat, sender='patient', content=message_content)
        
        # Process AI response here
        response = get_ai_response(message_content, patient)
        Message.objects.create(chat=chat, sender='bot', content=response)
        
        return JsonResponse({'response': response})

def get_ai_response(message, patient):
    # Integrate with LLM (e.g., Gemini)
    openai.api_key = os.getenv("GEMINI_API_KEY")
    
    prompt = f"Patient Name: {patient.first_name} {patient.last_name}\nMessage: {message}\nResponse:"
    
    response = openai.Completion.create(
        engine="gemini",
        prompt=prompt,
        max_tokens=150,
        n=1,
        stop=None,
        temperature=0.7,
    )
    
    return response.choices[0].text.strip()