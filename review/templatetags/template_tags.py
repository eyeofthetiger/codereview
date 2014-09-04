from django import template

register = template.Library()

@register.filter(name='get_item')
def get_item(dictionary, key):
	""" Returns the item in dictionary at key, or None if that key doesnt exist 
		in the dictionary.
	"""
	return dictionary.get(key)

@register.filter(name='get_range')
def get_range(item):
  """
    Returns a range, indexed from 1, based on the length of the given object.
  """
  return range(1, len(item)+1)

@register.filter(name='get_submission_date')
def get_submission_date(dictionary, key):
  """
    Returns the submission date for a Submission in the given dictionary at the given key.
  """
  submission = dictionary.get(key)
  if submission:
  	return submission.upload_date
  return None