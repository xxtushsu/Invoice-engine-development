from InvoiceEngineApp.forms import BaseComponentForm
from InvoiceEngineApp.models import BaseComponent
from InvoiceEngineApp.views.parent_views import (
    ParentListView,
    ParentCreateView,
    ParentUpdateView,
    ParentDeleteView,
)


class BaseComponentListView(ParentListView):
    template_name = 'InvoiceEngineApp/base_component_list.html'
    model = BaseComponent
    ordering = ['unit_id']


class BaseComponentCreateView(ParentCreateView):
    form_class = BaseComponentForm
    list_page = "base_component_list"


class BaseComponentUpdateView(ParentUpdateView):
    model = BaseComponent
    form_class = BaseComponentForm
    list_page = "base_component_list"
    pk_url_kwarg = 'base_component_id'


class BaseComponentDeleteView(ParentDeleteView):
    model = BaseComponent
    list_page = "base_component_list"
    success_page = "base_component_list"
    pk_url_kwarg = 'base_component_id'
