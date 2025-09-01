from django.shortcuts import render

def diary_pay(request):

    is_admin = request.session.get('is_admin', False),
    is_authenticated = request.session.get('is_authenticated', False),


    return render(request, 'diary/diary_pay.html', {'is_authenticated': is_authenticated, 'is_admin': is_admin})
