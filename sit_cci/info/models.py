from django.db import models

# Create your models here.
class Tag(models.Model):
    name = models.CharField(max_length=15)
    intro = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Club(models.Model):
    name = models.CharField(max_length=20)
    short_intro = models.CharField(max_length=140)
    tags = models.ManyToManyField(Tag)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name




