from django.shortcuts import render
from django.views import View
from .models import Patient, Chat, Message
from django.http import JsonResponse
import openai
import os
import spacy
from neo4j import GraphDatabase

MAX_MESSAGES = 100  # Define maximum messages to store

nlp = spacy.load("en_core_web_sm")

class KnowledgeGraph:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
    
    def close(self):
        self.driver.close()
    
    def add_entity(self, patient, key, value):
        with self.driver.session() as session:
            session.run("""
                MATCH (p:Patient {email: $email})
                MERGE (p)-[:HAS]->(:Entity {key: $key, value: $value})
            """, email=patient.email, key=key, value=value)

# Initialize KnowledgeGraph
kg = KnowledgeGraph("bolt://localhost:7687", "neo4j", "your_password")

def extract_entities(message):
    doc = nlp(message)
    entities = {}
    for ent in doc.ents:
        entities[ent.label_] = ent.text
    return entities

def get_ai_response(message, patient):
    openai.api_key = os.getenv("GEMINI_API_KEY")
    
    prompt = f"""
    You are an AI assistant for a patient named {patient.first_name} {patient.last_name}.
    The patient may ask about their health, care plan, or request changes to appointments or treatments.
    Respond appropriately to health-related inquiries.
    If the patient requests to change an appointment or treatment, acknowledge and notify the doctor.
    Ignore unrelated, sensitive, or controversial topics.
    
    Patient: {message}
    AI:
    """
    
    response = openai.Completion.create(
        engine="gemini",
        prompt=prompt,
        max_tokens=150,
        n=1,
        stop=None,
        temperature=0.7,
    )
    
    ai_response = response.choices[0].text.strip()
    
    # Detect appointment/treatment requests
    if any(keyword in message.lower() for keyword in ["reschedule", "change", "modify"]):
        notify_doctor(patient, message)
        ai_response = f"I will convey your request to Dr. {patient.doctor_name}."
    
    return ai_response
    
    response = openai.Completion.create(
        engine="gemini",
        prompt=prompt,
        max_tokens=150,
        n=1,
        stop=None,
        temperature=0.7,
    )
    
    ai_response = response.choices[0].text.strip()
    
    # Detect appointment/treatment requests
    if "reschedule" in message.lower() or "change" in message.lower():
        notify_doctor(patient, message)
    
    return ai_response

def notify_doctor(patient, request_message):
    # Implement notification logic, e.g., log the request or send an email
    notification = f"Patient {patient.first_name} {patient.last_name} is requesting: {request_message}"
    # For simplicity, print the notification
    print(notification)
    # Alternatively, save to a model or send an email

class ChatView(View):
    def get(self, request):
        return render(request, 'chat/chat.html')

class SendMessageView(View):
    def post(self, request):
        patient = Patient.objects.first()  # Assuming one patient
        chat, created = Chat.objects.get_or_create(patient=patient)
        message_content = request.POST.get('message')
        Message.objects.create(chat=chat, sender='patient', content=message_content)
        
        response, notification = process_message(message_content, patient)
        Message.objects.create(chat=chat, sender='bot', content=response)
        
        # Trim messages if exceeding MAX_MESSAGES
        message_count = chat.messages.count()
        if message_count > MAX_MESSAGES:
            excess = message_count - MAX_MESSAGES
            chat.messages.order_by('timestamp')[:excess].delete()
        
        return JsonResponse({'response': response, 'notification': notification})

def process_message(message, patient):
    # Extract entities from the message
    entities = extract_entities(message)
    
    # Add entities to the knowledge graph
    for key, value in entities.items():
        kg.add_entity(patient, key, value)
    
    openai.api_key = os.getenv("GEMINI_API_KEY")
    
    prompt = f"""
    You are an AI assistant for a patient named {patient.first_name} {patient.last_name}.
    The patient may ask about their health, care plan, or request changes to appointments or treatments.
    Respond appropriately to health-related inquiries.
    If the patient requests to change an appointment or treatment, acknowledge and notify the doctor.
    Ignore unrelated, sensitive, or controversial topics.
    
    Extracted entities: {entities}
    
    Patient: {message}
    AI:
    """
    
    response = openai.Completion.create(
        engine="gemini",
        prompt=prompt,
        max_tokens=150,
        n=1,
        stop=None,
        temperature=0.7,
    )
    
    ai_response = response.choices[0].text.strip()
    notification = ""
    
    if any(keyword in message.lower() for keyword in ["reschedule", "change", "modify"]):
        notify_doctor(patient, message)
        ai_response = f"I will convey your request to Dr. {patient.doctor_name}."
        requested_time = extract_requested_time(message)
        notification = f"Patient {patient.first_name} is requesting an appointment change to {requested_time}."
    
    return ai_response, notification

def extract_requested_time(message):
    # Simple extraction logic; can be enhanced with NLP
    import re
    match = re.search(r'(\w+day) at (\d{1,2} ?[APMapm]{2})', message)
    if match:
        return f"{match.group(1)} at {match.group(2)}"
    return "the requested time"

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