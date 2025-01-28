from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Project, Contribution
from django.core.mail import send_mail
from django.conf import settings
from .models import Contribution
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from django.core.mail import EmailMessage
from django.db.models import Sum
from django.db.models.signals import post_save, post_delete
from decimal import Decimal

@receiver(post_save, sender=Contribution)
def update_total_platform_fee(sender, instance, **kwargs):
    print(f"Contribution saved: {instance.amount} with platform fee {instance.platform_fee}")
    project = instance.project

    total_fee = project.contributions.aggregate(Sum('platform_fee'))['platform_fee__sum'] or Decimal('0.00')
    print(f"Total fee after save: {total_fee}")
    project.total_platform_fee = total_fee.quantize(Decimal('0.000000'))
    project.save()

@receiver(post_delete, sender=Contribution)
def update_total_platform_fee_on_delete(sender, instance, **kwargs):
    print(f"Contribution deleted: {instance.amount} with platform fee {instance.platform_fee}")
    project = instance.project

    total_fee = project.contributions.aggregate(Sum('platform_fee'))['platform_fee__sum'] or Decimal('0.00')
    print(f"Total fee after delete: {total_fee}")
    project.total_platform_fee = total_fee.quantize(Decimal('0.000000'))
    project.save()


@receiver(post_save, sender=Project)
def send_project_approval_email(sender, instance, created, **kwargs):
    if instance.status == 'approved' and not created:
        subject = f"Your project '{instance.title}' has been approved!"
        message = (
            f"Hi {instance.creator.username},\n\n"
            f"Congratulations! Your project titled '{instance.title}' has been approved.\n\n"
            f"Project ID: {instance.id}\n"
            f"Funding Goal: {instance.funding_goal}\n"
            f"Deadline: {instance.deadline}\n\n"
            "Thank you for using our platform!"
        )
        send_mail(
            subject=subject,
            message=message,
            from_email="no-reply@yourdomain.com",
            recipient_list=[instance.creator.email],
            fail_silently=False,
        )



@receiver(post_save, sender=Contribution)
def update_project_funding(sender, instance, created, **kwargs):
    if created and instance.verified and instance.payment_status == 'completed':
        instance.project.current_funding += instance.amount
        instance.project.save()





def generate_certificate(contribution):
    """Generate the certificate PDF and return it as a byte buffer."""
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)


    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(300, 800, "Certificate of Appreciation")


    c.setFont("Helvetica", 16)
    c.drawString(100, 750, f"Presented to: {contribution.backer.username}")


    c.drawString(100, 720, f"For supporting: {contribution.project.title}")


    c.drawString(100, 690, f"Contribution Amount: ${contribution.amount}")


    c.drawString(100, 660, f"Date: {contribution.date.strftime('%Y-%m-%d')}")


    c.setFont("Helvetica-Oblique", 10)
    c.drawString(100, 630, f"Transaction ID: {contribution.transaction_hash}")


    c.setFont("Helvetica-Bold", 12)
    c.drawString(100, 580, "_________________________")
    c.drawString(100, 560, "Authorized Signature")


    c.showPage()
    c.save()


    buffer.seek(0)

    return buffer

@receiver(post_save, sender=Contribution)
def generate_and_send_certificate(sender, instance, created, **kwargs):
    if created:

        pdf_buffer = generate_certificate(instance)


        send_certificate_email(instance)

def send_certificate_email(contribution):
    """Send the certificate details to the backer's email as text."""
    subject = "Your Certificate of Appreciation"
    body = (f"Dear {contribution.backer.username},\n\n"
            f"Thank you for your generous support of {contribution.project.title}. "
            f"Your contribution of {contribution.amount} SOL has made a significant impact.\n\n"
            f"Certificate of Appreciation\n"
            f"Presented to: {contribution.backer.username}\n"
            f"For supporting: {contribution.project.title}\n"
            f"Contribution Amount: {contribution.amount} SOL\n"
            f"Date: {contribution.date.strftime('%Y-%m-%d')}\n"
            f"Transaction ID: {contribution.transaction_hash}\n\n"
            f"Authorized Signature: ___________________________\n\n"
            "Thank you again for your support!\n\nBest regards,\nYour Crowdfunding Team")

    try:

        email = EmailMessage(
            subject=subject,
            body=body,
            from_email="no-reply@yourdomain.com",
            to=[contribution.backer.email],
        )


        email.send(fail_silently=False)

    except Exception as e:

        print(f"Error sending email: {e}")
