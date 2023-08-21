from django.db import models
from django.conf import settings
from django.contrib.auth.models import User

# Create your models here.
class Video(models.Model):
	video_file = models.FileField(upload_to='media/')
	
class Contact(models.Model):
	id = models.AutoField(primary_key=True)
	name = models.CharField(max_length=100)
	email = models.EmailField()
	message = models.TextField()
	timestamp = models.DateTimeField(auto_now_add=True)

	def __str__(self):
		return self.name
	
class Archive(models.Model):
	archive_id = models.AutoField(primary_key=True)
	vid_name = models.TextField()
	timestamp = models.TextField()
	user = models.ForeignKey(User, on_delete=models.CASCADE, default=None)

	def __str__(self):
		return self.vid_name