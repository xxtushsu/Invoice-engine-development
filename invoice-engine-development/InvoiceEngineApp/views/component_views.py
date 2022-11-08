from django.http import HttpResponseRedirect

from InvoiceEngineApp.forms import ComponentForm
from InvoiceEngineApp.models import Component
from InvoiceEngineApp.views.parent_views import (
    ParentCreateView,
    ParentUpdateView,
    ParentDeleteView
)


class ComponentCreateView(ParentCreateView):
    form_class = ComponentForm
    list_page = "contract_details"

    def get_form(self, form_class=None):
        """Overloaded to filter the selection of base components & VAT rates
        based on the tenancy.
        """
        form = super().get_form()
        form.filter_selectors(self.kwargs.get('company_id'))
        return form

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.create(self.kwargs)
        return HttpResponseRedirect(self.get_success_url())


class ComponentUpdateView(ParentUpdateView):
    """A component can only be updated when it has not been invoiced yet."""
    model = Component
    form_class = ComponentForm
    list_page = "contract_details"
    pk_url_kwarg = 'component_id'
    is_contract = False
    end_date = None
    start_date = None

    def get_form(self, form_class=None):
        """Overloaded to filter the selection of contract types based on the
        tenancy.
        """
        form = super().get_form()
        form.filter_selectors(self.object.tenancy_id)
        if not self.object.is_draft():
            form.disable_fields()
        return form

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.select_related('contract')

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        obj.remove_from_contract()
        self.end_date = obj.end_date
        self.start_date = obj.start_date
        return obj

    def form_valid(self, form):
        """Overload the form valid function to perform additional logic in the
        form.
        """
        if form.instance.is_draft():
            form.instance.update()
        if form.instance.end_date != self.end_date:
            form.instance.change_end_date(self.end_date)
        if form.instance.start_date != self.start_date:
            form.instance.change_start_date(self.start_date)
        return super().form_valid(form)


class ComponentDeleteView(ParentDeleteView):
    """A component can only be deleted when it has not been invoiced yet."""
    model = Component
    list_page = "contract_details"
    success_page = "contract_details"
    pk_url_kwarg = 'component_id'
    is_contract = True
