from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse

from InvoiceEngineApp.forms import (
    ContractForm,
    ContractSearchForm,
)
from InvoiceEngineApp.models import Contract
from InvoiceEngineApp.views.parent_views import (
    ParentListView,
    ParentCreateView,
    ParentUpdateView,
    ParentDeleteView,
)


def get_contract_qs(username, company_id, contract_id):
    return Contract.objects.filter(
        tenancy__tenancy_id=username,
        tenancy_id=company_id,
        contract_id=contract_id
    )


def get_details_page(company_id, contract_id):
    return HttpResponseRedirect(
        reverse(
            "contract_details",
            args=[
                company_id,
                contract_id
            ]
        )
    )


@login_required(login_url='/login/')
def contract_activation_view(request, company_id, contract_id):
    """View function to set the status of the contract to ACTIVE, so
    it can be invoiced in the future.
    """
    qs = get_contract_qs(request.user.username, company_id, contract_id)
    contract = get_object_or_404(qs)

    if contract.can_activate():
        contract.activate()

    return get_details_page(company_id, contract_id)


@login_required(login_url='/login/')
def contract_ending_view(request, company_id, contract_id):
    """View function to set the status of the contract to ACTIVE, so
    it can be invoiced in the future.
    """
    qs = get_contract_qs(request.user.username, company_id, contract_id)
    qs.select_related('tenancy')
    contract = get_object_or_404(qs)

    if contract.can_end():
        contract.end()

    return get_details_page(company_id, contract_id)


class ContractListView(ParentListView):
    template_name = 'InvoiceEngineApp/contract_list.html'
    form_class = ContractSearchForm
    model = Contract
    ordering = ['date_next_prolongation']

    def get_context_data(self, **kwargs):
        """Add the search form to the context data."""
        context = super().get_context_data(**kwargs)
        context['form'] = self.form_class(self.request.GET)
        return context

    def get_queryset(self):
        """Filter the queryset based on the submitted search form."""
        # Get the contract list filtered by tenancy
        qs = super().get_queryset()
        form = self.form_class(self.request.GET)

        # Filter the contract list further by user input
        if form.is_valid():
            return form.filter_queryset(qs)
        return qs


class ContractCreateView(ParentCreateView):
    form_class = ContractForm
    list_page = "contract_list"

    def get_form(self, form_class=None):
        """Overloaded to filter the selection of contract types based on the
        tenancy.
        """
        form = super().get_form()
        form.filter_selectors(self.kwargs.get('company_id'))
        return form


class ContractDetailView(ParentListView):
    """DetailView for contract.  It is implemented as a ListView because
    is has to list all invoices corresponding to the contract.
    """
    template_name = 'InvoiceEngineApp/contract_details.html'
    ordering = ['-date']
    object = None

    def get_object(self, queryset=Contract.objects.all()):
        qs = queryset.filter(
            contract_id=self.kwargs.get('contract_id'),
        )
        return get_object_or_404(qs)

    def get_queryset(self):
        self.object = self.get_object()
        return self.object.get_invoices()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['object'] = self.object
        return context


class ContractUpdateView(ParentUpdateView):
    model = Contract
    form_class = ContractForm
    list_page = "contract_details"
    pk_url_kwarg = 'contract_id'
    is_contract = True

    def get_form(self, form_class=None):
        """Overloaded to filter the selection of contract types based on the
        tenancy.
        """
        form = super().get_form()
        form.filter_selectors(self.object.tenancy_id)
        if not self.object.is_draft():
            form.disable_fields()
        return form

    def form_valid(self, form):
        """Overload the form valid function to perform additional logic in the
        form.
        """
        form.instance.update()
        return super().form_valid(form)


class ContractDeleteView(ParentDeleteView):
    model = Contract
    list_page = "contract_details"
    success_page = "contract_list"
    pk_url_kwarg = 'contract_id'
    is_contract = True
