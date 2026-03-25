from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

class Topic(models.Model):
    topic_name = models.CharField(max_length=100)
    interest_factor = models.IntegerField(default=5)
    userkey = models.ForeignKey("User", on_delete=models.CASCADE)

class User(AbstractUser):
    interests = models.ManyToManyField(Topic)
    expeditions = models.ManyToManyField("Expedition")
    onboarded = models.BooleanField(default=False)
    tokens_used = models.IntegerField(default=0)
    account_created_at = models.DateTimeField(default=timezone.now)
    isAdmin = models.BooleanField(default=False)
    lessons_completed = models.IntegerField(default=0)
    conversations = models.ManyToManyField("Conversation")

class Chapter(models.Model):
    chapter_name = models.CharField(max_length=222)
    userkey = models.ForeignKey("User", on_delete=models.CASCADE)

class Expedition(models.Model):
    expedition_name = models.CharField(max_length=109)
    chapters = models.ManyToManyField(Chapter)
    current_knowledge_level = models.IntegerField(default=0)
    lessons_completed = models.IntegerField(default=0)
    chapters_completed = models.IntegerField(default=0)
    userkey = models.ForeignKey("User", on_delete=models.CASCADE)

class MentorshipPost(models.Model):
    post = models.CharField(max_length=150)
    userkey = models.ForeignKey("User", on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)

class Message(models.Model):
    message = models.CharField(max_length=500)
    sent_at = models.DateTimeField(default=timezone.now)

class Conversation(models.Model):
    user1 = models.ForeignKey("User", on_delete=models.CASCADE, related_name="user1")
    user2 = models.ForeignKey("User", on_delete=models.CASCADE, related_name="user2")
    messages = models.ManyToManyField(Message)
    has_unread = models.BooleanField(default=False)