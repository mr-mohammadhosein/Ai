from django.db import models

class Message(models.Model):
    role = models.CharField(max_length=10)
    content = models.TextField()

    def __str__(self):
        return f"{self.role} - {self.content[:55]}..."