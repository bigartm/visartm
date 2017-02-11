import datetime
from django import template

register = template.Library()

@register.simple_tag(takes_context=True)
def color_theme(context):
	try:
		return context['request'].COOKIES["color_theme"]
	except:
		return "default"
		
@register.simple_tag(takes_context=True)
def temporal_spectrum(context):
	try:
		return context['request'].COOKIES["temporal_spectrum"]
	except:
		return 'false'