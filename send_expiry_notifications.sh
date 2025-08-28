#!/bin/bash
cd "$(dirname "$0")"
python manage.py send_expiry_notifications
