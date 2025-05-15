from django.core.management import call_command
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "PO.settings")  # settings 경로 수정
django.setup()

def update_bizinfo():
    call_command("update_bizinfo")

if __name__ == "__main__":
    update_bizinfo()
