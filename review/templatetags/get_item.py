from django import template

register = template.Library()

@register.filter(name='get_item')
def get_item(dictionary, key):
	""" Returns the item in dictionary at key, or None if that key doesnt exist 
		in the dictionary.
	"""
	return dictionary.get(key)