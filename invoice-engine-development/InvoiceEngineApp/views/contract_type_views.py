from InvoiceEngineApp.forms import ContractTypeForm
from InvoiceEngineApp.models import ContractType
from InvoiceEngineApp.views.parent_views import (
    ParentListView,
    ParentCreateView,
    ParentUpdateView,
    ParentDeleteView,
)


class ContractTypeListView(ParentListView):
    template_name = 'InvoiceEngineApp/contract_type_list.html'
    model = ContractType
    ordering = ['code']


class ContractTypeCreateView(ParentCreateView):
    form_class = ContractTypeForm
    list_page = "contract_type_list"


class ContractTypeUpdateView(ParentUpdateView):
    model = ContractType
    form_class = ContractTypeForm
    list_page = "contract_type_list"
    pk_url_kwarg = 'contract_type_id'


class ContractTypeDeleteView(ParentDeleteView):
    model = ContractType
    list_page = "contract_type_list"
    success_page = "contract_type_list"
    pk_url_kwarg = 'contract_type_id'
