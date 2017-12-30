from django.conf import settings


def context(request):

    return {
        'YANDEX_METRIKA_ID': settings.YANDEX_METRIKA_ID,
        'APP_VERSION': settings.APP_VERSION,
        'CURRENT_YEAR': 2018,
        'SCHEME': request.is_secure() and 'https' or 'http'
    }
