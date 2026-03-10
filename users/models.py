from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    COACH_MODE_CHOICES = [
        ('strict', 'Дисципліна'),
        ('empathetic', 'Підтримка'),
        ('balanced', 'Збалансований')
    ]

    coach_mode = models.CharField(
        max_length=10,
        choices=COACH_MODE_CHOICES,
        default='balanced',
        verbose_name='Режим коуча'
    )

    agent_memory_profile = models.TextField(
        blank=True,
        help_text='Згенероване AI резюме користувача'
    )

    def __str__(self):
        return self.username

