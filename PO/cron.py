from django.core.management import call_command

def update_bizinfo():
    call_command("update_bizinfo")  # = python manage.py update_bizinfo
