# yourapp/tasks.py
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings


def send_contact_email( name, email, budget, message, services, msubject):
    print ('celery added')
    subject = 'New contact form Submission from KEHEM'
    email_message = f"""
    New Confirm form booked with the following details:
    Name: {name}
    Email: {email}
    Subject: {msubject}
    Services: {services}
    Budget: {budget}
    Message: {message}
    """
    try:
        send_mail(
            subject,
            email_message,
            settings.EMAIL_HOST_USER,
            ['anirbansingha1@outlook.com','kehemboss@gmail.com'],
            fail_silently=False,
        )
    except Exception as e:
        # Log the error somewhere
        print ('Fail send email '+str(e))