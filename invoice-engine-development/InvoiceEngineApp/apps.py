import decimal

from django.apps import AppConfig


class InvoiceEngineAppConfig(AppConfig):
    name = 'InvoiceEngineApp'

    def ready(self):
        setattr(decimal.DefaultContext, 'rounding', decimal.ROUND_HALF_UP)
        decimal.setcontext(decimal.DefaultContext)
