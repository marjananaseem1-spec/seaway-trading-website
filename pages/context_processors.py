from django.conf import settings


def site(request):
    return {
        "site_www_url": settings.SITE_WWW_URL,
        "site_domain": settings.SITE_DOMAIN,
    }
