from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
	user = models.OneToOneField(User, related_name='profile')
	first_name = models.TextField(null=True, blank=True)
	last_name = models.TextField(null=True, blank=True)
	assessor_rating = models.IntegerField(default = 0)
	
	def get_profile(user):
		try:
			return Profile.objects.get(user=user)
		except:
			profile = Profile()
			profile.user = user
			return profile
