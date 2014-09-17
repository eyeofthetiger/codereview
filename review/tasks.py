from __future__ import absolute_import

from celery import shared_task

@shared_task
def due_date_reached(assignment):
    print "Due date reached"

@shared_task
def open_date_reached(assignment):
    print "Open date reached"

@shared_task
def due_date_tomorrow(assignment):
    print "Due date tomorrow"