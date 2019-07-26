from django.db import models


class Question(models.Model):
    STATUS_CHOICES = (
        ('unproccessed', 'Unprocessed'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    question_text = models.CharField(max_length=200)
    pub_date = models.DateTimeField('date published')
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='unproccessed')


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice_text = models.CharField(max_length=200)
    votes = models.IntegerField(default=0)