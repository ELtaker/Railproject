"""
Eksempel på service-funksjon for ekstern forretningslogikk.
Her kan du plassere logikk som ikke hører hjemme i modeller eller views.
"""

def send_welcome_email(user):
    """
    Sender velkomstmail til ny bruker.
    """
    from django.core.mail import send_mail
    subject = "Velkommen til Raildrops!"
    message = "Hei, og velkommen!"
    send_mail(subject, message, "noreply@raildrops.no", [user.email])
