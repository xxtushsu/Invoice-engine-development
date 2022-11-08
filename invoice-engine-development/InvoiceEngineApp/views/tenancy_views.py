import csv
import multiprocessing
import zipfile
from io import BytesIO, StringIO

from django.contrib.auth.decorators import login_required
from django.db.models import Max
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic import (
    DetailView,
    ListView,
    UpdateView
)

from InvoiceEngineApp.forms import TenancySubscriberForm
from InvoiceEngineApp.models import (
    Tenancy,
    Collection,
    Invoice,
    GeneralLedgerPost,
    ContractPerson
)


@login_required(login_url='/login/')
def export_collections(request, company_id):
    date = Invoice.objects.aggregate(Max('date')).get('date__max')
    collection_list = list(
        Collection.objects.filter(
            tenancy_id=company_id,
            tenancy__tenancy_id=request.user.username,
            invoice__date=date
        ).select_related(
            'invoice', 'contract_person'
        )
    )

    print(Collection.objects.all().exists())

    if not collection_list:
        return HttpResponseRedirect(reverse('tenancy_list'))

    field_names = [
        'name', 'address', 'city', 'payment_method', 'payment_day',
        'invoice_number', 'invoice_date', 'contract_id', 'invoice_id',
        'invoice_amount', 'mandate', 'iban', 'email', 'phone'
    ]

    zipped_file = BytesIO()
    with zipfile.ZipFile(zipped_file, 'a', zipfile.ZIP_DEFLATED) as zipped:
        for payment_method in [ContractPerson.DIRECT_DEBIT,
                               ContractPerson.EMAIL,
                               ContractPerson.SMS,
                               ContractPerson.LETTER,
                               ContractPerson.INVOICE]:
            collections = [x for x in collection_list
                           if x.payment_method == payment_method]
            if collections:
                csv_file = StringIO()
                writer = csv.writer(csv_file)
                writer.writerow(field_names)
                for collection in collections:
                    writer.writerow(collection.get_values_external_file())

                csv_file.seek(0)
                zipped.writestr(
                    date.__str__()
                    + '-'
                    + payment_method
                    + '.csv',
                    csv_file.read()
                )

    zipped_file.seek(0)
    response = HttpResponse(
        zipped_file, content_type='application/octet-stream'
    )
    response["Content-Disposition"] = \
        'attachment; filename="{}_collections.zip"'.format(date)

    return response


@login_required(login_url='/login/')
def export_invoices(request, company_id):
    return general_export(
        Invoice, company_id, request.user.username, "invoices"
    )


@login_required(login_url='/login/')
def export_glposts(request, company_id):
    return general_export(
        GeneralLedgerPost, company_id, request.user.username, "glposts"
    )


def general_export(model, company_id, tenancy_id, file_name):
    date = Invoice.objects.aggregate(Max('date')).get('date__max')
    qs = list(
        model.objects.filter(
            tenancy_id=company_id,
            tenancy__tenancy_id=tenancy_id,
            date=date
        )
    )

    if not qs:
        return HttpResponseRedirect(reverse('tenancy_list'))

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = \
        'attachment; filename="{}_{}.csv"'.format(file_name, date)

    opts = model._meta
    writer = csv.writer(response)
    field_names = [field.name for field in opts.fields]
    writer.writerow(field_names)

    for obj in qs:
        writer.writerow([getattr(obj, field) for field in field_names])

    return response


@login_required(login_url='/login/')
def invoice_contracts_view(request, company_id):
    tenancy = get_object_or_404(
        Tenancy.objects.filter(
            company_id=company_id,
            tenancy_id=request.user.username
        )
    )
    p = multiprocessing.Process(target=tenancy.invoice_contracts)
    p.start()
    p.join()
    return HttpResponseRedirect(reverse('tenancy_list'))


@method_decorator(login_required(login_url='/login/'), name='dispatch')
class TenancyListView(ListView):
    """Show the user a list of all tenancies available to them."""
    template_name = 'InvoiceEngineApp/tenancy_list.html'
    model = Tenancy
    paginate_by = 10

    def get_queryset(self):
        # The user should only see the tenancy objects associated with themselves.
        qs = super().get_queryset()
        return qs.filter(tenancy_id=self.request.user.username)


@method_decorator(login_required(login_url='/login/'), name='dispatch')
class TenancyDetailView(DetailView):
    """Show the user the details corresponding to a certain tenancy.
    This class need not check if the user has access to that tenancy, as they can only access this page for their own
    tenancies as shown through TenancyListView.
    """
    template_name = 'InvoiceEngineApp/details.html'
    extra_context = {'object_type': "tenancy", 'list_page': ["tenancy_list"]}

    def get_object(self, queryset=Tenancy.objects.all()):
        qs = Tenancy.objects.filter(company_id=self.kwargs.get('company_id'))
        return get_object_or_404(qs.filter(tenancy_id=self.request.user.username))


@method_decorator(login_required(login_url='/login/'), name='dispatch')
class TenancyUpdateView(UpdateView):
    """Allow the user to change a certain tenancy.
    This class need not check if the user has access to that tenancy, as they can only access this page for their own
    tenancies as shown through TenancyListView.
    """
    template_name = 'InvoiceEngineApp/display_form.html'
    extra_context = {'object_type': "tenancy"}
    form_class = TenancySubscriberForm

    def get_object(self, queryset=Tenancy.objects.all()):
        qs = Tenancy.objects.filter(company_id=self.kwargs.get('company_id'))
        return get_object_or_404(qs.filter(tenancy_id=self.request.user.username))

    def get_success_url(self):
        return reverse('tenancy_list')
