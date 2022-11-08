from django.db import transaction

from InvoiceEngineApp.forms import VATRateForm
from InvoiceEngineApp.models import VATRate
from InvoiceEngineApp.views.parent_views import (
    ParentListView,
    ParentCreateView,
    ParentUpdateView,
    ParentDeleteView,
)


class VATRateListView(ParentListView):
    template_name = 'InvoiceEngineApp/vat_rate_list.html'
    model = VATRate
    ordering = ['type', 'start_date']


class VATRateCreateView(ParentCreateView):
    form_class = VATRateForm
    list_page = "vat_rate_list"


class VATRateUpdateView(ParentUpdateView):
    model = VATRate
    form_class = VATRateForm
    list_page = "vat_rate_list"
    pk_url_kwarg = 'vat_rate_id'

    def form_valid(self, form):
        self.object = form.instance
        with transaction.atomic():
            self.object.update()
            return super().form_valid(form)


class VATRateDeleteView(ParentDeleteView):
    model = VATRate
    list_page = "vat_rate_list"
    success_page = "vat_rate_list"
    pk_url_kwarg = 'vat_rate_id'
