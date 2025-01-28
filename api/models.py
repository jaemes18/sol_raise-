from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone
import ipfshttpclient
import json
from django.utils.timezone import now
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import models
from django.contrib.auth.models import User

class CustomUser(AbstractUser):
    wallet_address = models.CharField(max_length=255, unique=True, null=True, blank=True)
    groups = models.ManyToManyField(
        Group,
        related_name="custom_user_groups",
        blank=True
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name="custom_user_permissions",
        blank=True
    )

class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=200, null=False, blank=False)
    last_name = models.CharField(max_length=200, null=False, blank=False)
    contact_address = models.CharField(max_length=200, null=False, blank=False)
    national_id = models.FileField(upload_to='uploads/national_ids/%Y/%m/%d/', null=False, blank=False)
    ROLE_CHOICES = (
        ('creator', 'Creator'),
        ('backer', 'Backer'),
    )
    role = models.CharField(max_length=100, choices=ROLE_CHOICES)
    wallet_address = models.CharField(max_length=255, null=True, blank=True)
    wallet_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"


class Project(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    title = models.CharField(max_length=255)
    description = models.TextField()
    funding_goal = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)  # Default added here
    current_funding = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    deadline = models.DateTimeField()
    status = models.CharField(max_length=100, choices=STATUS_CHOICES, default='pending')
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    total_platform_fee = models.DecimalField(max_digits=12, decimal_places=6, default=0.00)
    files = models.FileField(upload_to='projects/%Y/%m/%d/', null=True, blank=True)

    def __str__(self):
        return self.title

    def progress(self):
        """Return the funding progress as a percentage."""
        return (self.current_funding / self.funding_goal) * 100 if self.funding_goal > 0 else 0


class Contribution(models.Model):
    PAYMENT_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    )

    project = models.ForeignKey(Project, related_name="contributions", on_delete=models.CASCADE)
    backer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_hash = models.CharField(max_length=255, unique=True)
    payment_status = models.CharField(max_length=200, choices=PAYMENT_STATUS_CHOICES, default='pending')
    verified = models.BooleanField(default=False)
    date = models.DateTimeField(auto_now_add=True)
    platform_fee = models.DecimalField(max_digits=12, decimal_places=6, default=0.0000)

    def __str__(self):
        return f"{self.backer} - {self.amount} to {self.project.title}"



class Milestone(models.Model):
    project = models.ForeignKey(Project, related_name="milestones", on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField()
    target_amount = models.DecimalField(max_digits=12, decimal_places=2)
    completed = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.project.title} - {self.title}"

    def check_completion(self):
        """Check if the milestone has met its funding goal."""
        total_funding = self.project.contributions.aggregate(models.Sum('amount'))['amount__sum'] or 0
        return total_funding >= self.target_amount


class Reward(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    reward_name = models.CharField(max_length=255)
    reward_description = models.TextField()
    reward_amount = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return self.reward_name

class BackerProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rewards_claimed = models.ManyToManyField(Reward, blank=True)

    def __str__(self):
        return f"Profile of {self.user.username}"

class CreatorProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    projects_created = models.ManyToManyField(Project, related_name="creators", blank=True)

    def __str__(self):
        return f"Profile of {self.user.username} (Creator)"


class ChatReason(models.Model):
    REASONS = [
        ('help', 'I need help with a project'),
        ('report', 'I would like to report an issue with a project'),
        ('question', 'I have a question about the project\'s details'),
        ('bug', 'I encountered a bug or error in the project'),
        ('suggestion', 'I would like to suggest an improvement to the project'),
        ('collaboration', 'I want to discuss a collaboration or partnership'),
        ('inquiry', 'I have a general inquiry about the project'),
        ('feature', 'I want to discuss a feature request'),
        ('feedback', 'I have feedback on the project'),
        ('support', 'I need support with the project delivery'),
    ]

    reason = models.CharField(max_length=200, choices=REASONS)
    project = models.ForeignKey('Project', on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f"{self.get_reason_display()} - {self.user.username}"


class Message(models.Model):
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="messages_received", on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    reason = models.ForeignKey(ChatReason, on_delete=models.CASCADE)
    parent_message = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies')
    read = models.BooleanField(default=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='report', null=True, blank=True)

    def __str__(self):
        return f"Message from {self.sender} to {self.receiver} - {self.reason}"







