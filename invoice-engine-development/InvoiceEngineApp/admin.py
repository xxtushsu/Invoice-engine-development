from django.contrib import admin
from InvoiceEngineApp.models import (
    Tenancy,
)


class TenancyAdmin(admin.ModelAdmin):
    fields = ('tenancy_id', 'name')
    list_display = ('tenancy_id', 'name')


admin.site.register(Tenancy, TenancyAdmin)
