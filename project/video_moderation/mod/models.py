from django.db import models

# Create your models here.
from django.db import models


class Mod(models.Model):
    STATUS_CHOICES = (
        ('unproccessed', 'Unprocessed'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    name = models.CharField(max_length=200)
    pub_date = models.DateTimeField('date published')
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='unproccessed')
    url = models.URLField(max_length=250)
