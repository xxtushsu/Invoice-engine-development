from django.shortcuts import get_object_or_404
from django.views.generic import DetailView

from InvoiceEngineApp.models import Invoice
from InvoiceEngineApp.views.parent_views import (
    ParentListView, TenancyAccessMixin,
)


class InvoiceListView(ParentListView):
    template_name = 'InvoiceEngineApp/invoice_list.html'
    model = Invoice
    ordering = ['-date']


class InvoiceDetailView(TenancyAccessMixin, DetailView):
    template_name = 'InvoiceEngineApp/invoice_details.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['list_page'] = ["invoice_list", self.kwargs.get('company_id')]
        return context

    def get_object(self, queryset=Invoice.objects.all()):
        qs = queryset.filter(
            invoice_id=self.kwargs.get('invoice_id'),
        )
        return get_object_or_404(qs)
