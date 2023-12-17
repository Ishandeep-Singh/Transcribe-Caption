from django.db import models
from django.contrib.auth.models import User

class UserDetail(models.Model):
    user=models.ForeignKey(User, on_delete=models.CASCADE)
    date=models.DateTimeField(auto_now=True)
    video_name=models.CharField(max_length=150, null=True)
    youtube_link_or_filename=models.CharField(max_length=150)
    language = models.CharField(max_length=150)
    STATUS_CHOICES = [
        ('processing', 'Processing'),
        ('Finished', 'Finished'),
        ('Failed', 'Failed'),
    ]
    
    status = models.CharField(
        max_length=150,
        choices=STATUS_CHOICES,
        default='processing'
    )

    # files = models.JSONField(default=dict)  # You may want to specify an upload_to path
    VTT_file_Path=models.CharField(max_length=500, null=True)
    SRT_file_Path=models.CharField(max_length=500, null=True)
    TXT_file_Path=models.CharField(max_length=500, null=True)

    def __str__(self):
        return f'{self.user.username} - {self.youtube_link_or_filename}'

    class Meta:
        verbose_name = 'User Detail'  
        verbose_name_plural = 'User Details'
