from django.db import models

# Create your models here.

from django.db import models

class Patient(models.Model):
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    date_of_birth = models.DateField()
    phone_number = models.CharField(max_length=15)
    email = models.EmailField()
    medical_condition = models.TextField()
    medication_regimen = models.TextField()
    last_appointment_datetime = models.DateTimeField()
    next_appointment_datetime = models.DateTimeField()
    doctor_name = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    

class Chat(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

class Message(models.Model):
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='messages')
    sender = models.CharField(max_length=10)  # 'patient' or 'bot'
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)