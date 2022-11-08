from django.urls import path
from InvoiceEngineApp.views.general_views import *
from InvoiceEngineApp.views.tenancy_views import *
from InvoiceEngineApp.views.contract_type_views import *
from InvoiceEngineApp.views.base_component_views import *
from InvoiceEngineApp.views.vat_rate_views import *
from InvoiceEngineApp.views.contract_views import *
from InvoiceEngineApp.views.component_views import *
from InvoiceEngineApp.views.contract_person_views import *
from InvoiceEngineApp.views.invoice_views import *


urlpatterns = [
    # General pages.
    path('', HomePage.as_view()),
    path('profile/', UserProfilePage.as_view(), name='profile'),

    # Exporting urls.
    path('profile/tenancies/<int:company_id>/invoices/export',
         export_invoices,
         name='export_invoices'),
    path('profile/tenancies/<int:company_id>/glposts/export',
         export_glposts,
         name='export_glposts'),
    path('profile/tenancies/<int:company_id>/collections/export',
         export_collections,
         name='export_collections'),

    # Tenancy pages.
    path('profile/tenancies/',
         TenancyListView.as_view(),
         name='tenancy_list'),
    path('profile/tenancies/<int:company_id>/',
         TenancyDetailView.as_view(),
         name='tenancy_details'),
    path('profile/tenancies/<int:company_id>/update/',
         TenancyUpdateView.as_view(),
         name='tenancy_update'),

    # This path is for testing the invoice_contracts button!
    path('profile/tenancies/<int:company_id>/invoice_contracts/',
         invoice_contracts_view,
         name='invoice_contracts'
         ),

    # Contract type pages.
    path('profile/tenancies/<int:company_id>/contract_types/',
         ContractTypeListView.as_view(),
         name='contract_type_list'
         ),
    path('profile/tenancies/<int:company_id>/contract_types/create/',
         ContractTypeCreateView.as_view(),
         name='contract_type_create'
         ),
    path('profile/tenancies/<int:company_id>/contract_types/<int:contract_type_id>/update/',
         ContractTypeUpdateView.as_view(),
         name='contract_type_update'
         ),
    path('profile/tenancies/<int:company_id>/contract_types/<int:contract_type_id>/delete/',
         ContractTypeDeleteView.as_view(),
         name='contract_type_delete'
         ),

    # Base component pages.
    path('profile/tenancies/<int:company_id>/base_components/',
         BaseComponentListView.as_view(),
         name='base_component_list'
         ),
    path('profile/tenancies/<int:company_id>/base_components/create/',
         BaseComponentCreateView.as_view(),
         name='base_component_create'
         ),
    path('profile/tenancies/<int:company_id>/base_components/<int:base_component_id>/update/',
         BaseComponentUpdateView.as_view(),
         name='base_component_update'
         ),
    path('profile/tenancies/<int:company_id>/base_components/<int:base_component_id>/delete/',
         BaseComponentDeleteView.as_view(),
         name='base_component_delete'
         ),

    # VAT rate pages.
    path('profile/tenancies/<int:company_id>/vat_rates/',
         VATRateListView.as_view(),
         name='vat_rate_list'
         ),
    path('profile/tenancies/<int:company_id>/vat_rates/create/',
         VATRateCreateView.as_view(),
         name='vat_rate_create'
         ),
    path('profile/tenancies/<int:company_id>/vat_rates/<int:vat_rate_id>/update/',
         VATRateUpdateView.as_view(),
         name='vat_rate_update'
         ),
    path('profile/tenancies/<int:company_id>/vat_rates/<int:vat_rate_id>/delete/',
         VATRateDeleteView.as_view(),
         name='vat_rate_delete'
         ),

    # Contract pages.
    path('profile/tenancies/<int:company_id>/contracts/',
         ContractListView.as_view(),
         name='contract_list'
         ),
    path('profile/tenancies/<int:company_id>/contracts/create/',
         ContractCreateView.as_view(),
         name='contract_create'
         ),
    path('profile/tenancies/<int:company_id>/contracts/<int:contract_id>/',
         ContractDetailView.as_view(),
         name='contract_details'
         ),
    path('profile/tenancies/<int:company_id>/contracts/<int:contract_id>/update/',
         ContractUpdateView.as_view(),
         name='contract_update'
         ),
    path('profile/tenancies/<int:company_id>/contracts/<int:contract_id>/delete/',
         ContractDeleteView.as_view(),
         name='contract_delete'
         ),
    path('profile/tenancies/<int:company_id>/contracts/<int:contract_id>/activate/',
         contract_activation_view,
         name='contract_activate'
         ),
    path('profile/tenancies/<int:company_id>/contracts/<int:contract_id>/deactivate/',
         contract_ending_view,
         name='contract_end'
         ),

    # Component pages.
    path('profile/tenancies/<int:company_id>/contracts/<int:contract_id>/component/create/',
         ComponentCreateView.as_view(),
         name='component_create'
         ),
    path('profile/tenancies/<int:company_id>/contracts/<int:contract_id>/component/<int:component_id>/update/',
         ComponentUpdateView.as_view(),
         name='component_update'
         ),
    path('profile/tenancies/<int:company_id>/contracts/<int:contract_id>/component/<int:component_id>/delete/',
         ComponentDeleteView.as_view(),
         name='component_delete'
         ),

    # Contract person pages.
    path('profile/tenancies/<int:company_id>/contracts/<int:contract_id>/contract_person/update/',
         contract_person_update_view,
         name='contract_person_update'
         ),

    # Invoice pages.
    path('profile/tenancies/<int:company_id>/invoices/',
         InvoiceListView.as_view(),
         name='invoice_list'
         ),
    path('profile/tenancies/<int:company_id>/invoices/<int:invoice_id>/',
         InvoiceDetailView.as_view(),
         name='invoice_details'
         ),
]
