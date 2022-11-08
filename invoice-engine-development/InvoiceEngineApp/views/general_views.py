from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView


class HomePage(TemplateView):
    """The first page a website visitor will encounter."""
    template_name = 'InvoiceEngineApp/home_page.html'


@method_decorator(login_required(login_url='/login/'), name='dispatch')
class UserProfilePage(TemplateView):
    """The personal page of the user after logging in."""
    template_name = 'InvoiceEngineApp/user_profile_page.html'
