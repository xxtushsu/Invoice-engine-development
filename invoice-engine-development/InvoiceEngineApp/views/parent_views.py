from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import Http404
from django.urls import reverse
from django.views.generic import (
    ListView,
    CreateView,
    UpdateView,
    DeleteView,
)

from InvoiceEngineApp.models import Tenancy


class TenancyAccessMixin(LoginRequiredMixin):
    # Redirect to the login page if the user is not logged in.
    login_url = '/login/'
    kwargs = None

    def dispatch(self, request, *args, **kwargs):
        """"Perform a check whether this user has access to this tenancy."""
        tenancy_qs = Tenancy.objects.filter(
            company_id=self.kwargs.get('company_id'),
            tenancy_id=request.user.username
        )
        if not tenancy_qs.exists():
            raise Http404("No Tenancy matches the given query.")

        return super().dispatch(request, *args, **kwargs)


class ParentListView(TenancyAccessMixin, ListView):
    """This class defines common methods of ListViews used in this project."""
    paginate_by = 10

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(
            tenancy_id=self.kwargs.get('company_id')
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['company_id'] = self.kwargs.get('company_id')
        return context


class ParentCreateView(TenancyAccessMixin, CreateView):
    """This class defines common methods of CreateViews used in
    this project.
    """
    template_name = 'InvoiceEngineApp/display_form.html'
    list_page = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return_page = [self.list_page]
        return_page.extend(self.kwargs.values())
        context['list_page'] = return_page
        return context

    def form_valid(self, form):
        with transaction.atomic():
            form.instance.create(self.kwargs)
            return super().form_valid(form)

    def get_success_url(self):
        return reverse(self.list_page, args=self.kwargs.values())


class ParentUpdateView(TenancyAccessMixin, UpdateView):
    """This class defines common methods of UpdateViews used
    in this project.
    """
    template_name = 'InvoiceEngineApp/display_form.html'
    list_page = None
    is_contract = False

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if not obj.can_update():
            raise Http404("This action is not allowed.")
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return_page = [self.list_page]
        return_page.extend(self.kwargs.values())
        if self.is_contract:
            context['list_page'] = return_page
        else:
            context['list_page'] = return_page[:-1]
        return context

    def get_success_url(self):
        args = []
        args.extend(self.kwargs.values())
        if not self.is_contract:
            args = args[:-1]
        return reverse(self.list_page, args=args)


class ParentDeleteView(TenancyAccessMixin, DeleteView):
    """This class defines common methods of DeleteViews used
    in this project.
    """
    template_name = 'InvoiceEngineApp/delete.html'
    list_page = None
    success_page = None
    is_contract = False

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if not obj.can_delete():
            raise Http404("This action is not allowed.")
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return_page = [self.list_page]
        return_page.extend(self.kwargs.values())
        if self.is_contract:
            context['list_page'] = return_page
        else:
            context['list_page'] = return_page[:-1]
        return context

    def get_success_url(self):
        args = []
        args.extend(self.kwargs.values())
        if not self.is_contract:
            args = args[:-1]
        return reverse(self.success_page, args=args)
