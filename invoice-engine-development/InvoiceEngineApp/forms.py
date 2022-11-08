import datetime

from django import forms
from django.db.models import Func

from InvoiceEngineApp import models


class TenancySubscriberForm(forms.ModelForm):
    """A form for the user to update a tenancy."""
    class Meta:
        model = models.Tenancy
        exclude = [
            'tenancy_id', 'name',
            'number_of_contracts', 'last_invoice_number'
        ]


class ContractTypeForm(forms.ModelForm):
    """A form for the user to set the fields of a contract type.
    Tenancy is added automatically.
    """
    class Meta:
        model = models.ContractType
        exclude = ['tenancy']


class BaseComponentForm(forms.ModelForm):
    """A form for the user to set the fields of a base component.
    Tenancy is added automatically.
    """
    class Meta:
        model = models.BaseComponent
        exclude = ['tenancy']


class VATRateForm(forms.ModelForm):
    """A form for the user to set the fields of a VAT rate.
    Tenancy is added automatically.
    """
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        if end_date and end_date < start_date:
            raise forms.ValidationError(
                "End date should be on or after start date."
            )

        percentage = cleaned_data.get("percentage")
        if percentage > 100.0:
            raise forms.ValidationError(
                "Percentage should be in the range of 0.0% to 100.0%."
            )

    class Meta:
        model = models.VATRate
        exclude = ['tenancy', 'successor_vat_rate']


class ContractForm(forms.ModelForm):
    """A form for the user to set the fields of a contract.
    Tenancy is added automatically.
    The user can choose contract type from a drop-down menu.
    """
    def filter_selectors(self, company_id):
        self.fields['contract_type'].queryset = \
            models.ContractType.objects.filter(
                tenancy_id=company_id
            )

    def disable_fields(self):
        for field in self.fields:
            self.fields[field].disabled = True
        self.fields['termination_date'].disabled = False

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('invoicing_period') == self.instance.CUSTOM:
            if not cleaned_data.get('invoicing_amount_of_days'):
                raise forms.ValidationError(
                    "Fill in the amount of days to invoice."
                )
        else:
            if cleaned_data.get('invoicing_amount_of_days'):
                raise forms.ValidationError(
                    "Only fill in the amount of days to invoice if choosing "
                    "Custom invoicing period."
                )

        start_date = cleaned_data.get('start_date')
        term_date = cleaned_data.get('termination_date')
        if start_date and term_date and start_date > term_date:
            raise forms.ValidationError(
                "Termination date must be on or after start date."
            )

    class Meta:
        model = models.Contract
        exclude = [
            'tenancy', 'date_next_prolongation',
            'balance', 'base_amount', 'vat_amount', 'total_amount',
            'date_prev_prolongation', 'status', 'end_date'
        ]


class ContractSearchForm(forms.Form):
    """The form the user can use to search contracts in the contracts
    list page.
    Takes one or more inputs, and filters the queryset based on this.
    """
    name = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'John Doe'})
    )
    address = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Groningen'})
    )
    contract_type = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'size': 10, 'placeholder': 'rent'})
    )
    period = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={'size': 8, 'placeholder': 'month'})
    )
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'size': 8, 'placeholder': '2021-01-01'})
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'size': 8, 'placeholder': '2021-01-01'})
    )
    next_invoice_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'size': 8, 'placeholder': '2021-01-01'})
    )
    total_amount = forms.FloatField(
        required=False,
        widget=forms.TextInput(
            attrs={'size': 8,
                   'style': 'text-align: right',
                   'placeholder': '1000.00'
                   }
        )
    )
    balance = forms.FloatField(
        required=False,
        widget=forms.TextInput(
            attrs={'size': 8,
                   'style': 'text-align: right',
                   'placeholder': '1000.00'
                   }
        )
    )

    def filter_queryset(self, qs):
        class Round2(Func):
            function = "ROUND"
            template = "%(function)s(%(expressions)s::numeric, 2)"

            def __rand__(self, other):
                pass

            def __ror__(self, other):
                pass

        if self.cleaned_data.get('contract_type'):
            qs = qs.filter(
                contract_type__description__icontains=self.cleaned_data.get(
                    'contract_type'
                )
            )
        if self.cleaned_data.get('period'):
            # Use only the first letter of the period
            qs = qs.filter(
                invoicing_period__istartswith=self.cleaned_data.get(
                    'period'
                )[0]
            )
        if self.cleaned_data.get('start_date'):
            qs = qs.filter(
                start_date=self.cleaned_data.get(
                    'start_date'
                )
            )
        if self.cleaned_data.get('end_date'):
            qs = qs.filter(
                end_date=self.cleaned_data.get(
                    'end_date'
                )
            )
        if self.cleaned_data.get('next_invoice_date'):
            qs = qs.filter(
                date_next_prolongation=self.cleaned_data.get(
                    'next_invoice_date'
                )
            )
        if self.cleaned_data.get('total_amount'):
            qs = qs.annotate(rounded_total=Round2('total_amount')).filter(
                rounded_total=self.cleaned_data.get(
                    'total_amount'
                )
            )
        if self.cleaned_data.get('balance'):
            qs = qs.annotate(rounded_balance=Round2('balance')).filter(
                rounded_balance=self.cleaned_data.get(
                    'balance'
                )
            )
        if self.cleaned_data.get('name'):
            qs = qs.filter(
                contractperson__name__icontains=self.cleaned_data.get(
                    'name'
                )
            )
        if self.cleaned_data.get('address'):
            # Filter both the address and the city
            qs = qs.filter(
                contractperson__address__icontains=self.cleaned_data.get(
                    'address'
                )
            ) | qs.filter(
                contractperson__city__icontains=self.cleaned_data.get(
                    'address'
                )
            )

        return qs


class ComponentForm(forms.ModelForm):
    """A form for the user to set the fields of a component."""
    def filter_selectors(self, company_id):
        """Filter the querysets of the selectors for base component
        and VAT rate based on the tenancy and the VAT rate's end date.
        """
        self.fields['base_component'].queryset = \
            models.BaseComponent.objects.filter(
                tenancy_id=company_id
            )
        self.fields['vat_rate'].queryset = \
            models.VATRate.objects.filter(
                tenancy_id=company_id
            )

    def disable_fields(self):
        for field in self.fields:
            self.fields[field].disabled = True
        self.fields['start_date'].disabled = False
        self.fields['end_date'].disabled = False

    def clean(self):
        cleaned_data = super().clean()
        base_amount = cleaned_data.get("base_amount")
        unit_id = cleaned_data.get("base_component").unit_id
        unit_amount = cleaned_data.get("unit_amount")
        number_of_units = cleaned_data.get("number_of_units")

        # Check that using base amount or units is mutually exclusive
        if unit_id:
            if base_amount:
                raise forms.ValidationError(
                    "Please specify unit amount and number of units for unit "
                    + unit_id.__str__()
                    + ". Do not specify base amount."
                )
            if not unit_amount or not number_of_units:
                raise forms.ValidationError(
                    "Please specify unit amount and number of units for unit "
                    + unit_id.__str__() + "."
                )
        else:
            if not base_amount:
                raise forms.ValidationError(
                    "Please specify a base amount for this component."
                )
            if unit_amount or number_of_units:
                raise forms.ValidationError(
                    "Please specify a base amount for this component. "
                    "Do not specify unit amount and number of units."
                )

        # Check that end date is after start date
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError(
                "Start date cannot be after end date."
            )

        if self.instance.contract_id is not None:
            if start_date and not self.instance.contract.is_draft():
                if start_date < self.instance.contract.start_date:
                    raise forms.ValidationError(
                        "Start date cannot be before the contract's" 
                        "start date."
                    )

            if end_date and self.instance.contract.is_terminated():
                if end_date > self.instance.contract.termination_date:
                    raise forms.ValidationError(
                        "End date cannot be after the contract's" 
                        "termination date."
                    )

    class Meta:
        model = models.Component
        exclude = [
            'contract', 'vat_amount', 'total_amount', 'tenancy',
            'date_next_prolongation', 'unit_id', 'date_prev_prolongation',
        ]


class ContractPersonFormSet(forms.BaseModelFormSet):
    contract = None
    restricted = False

    def set_contract(self, contract):
        self.contract = contract
        if not self.contract.is_draft():
            self.restricted = True

    def clean(self):
        super().clean()
        none_valid = True
        contract_start_percentage = 0
        for form in self.forms:
            if self._should_delete_form(form) \
                    or (form.empty_permitted and not form.has_changed()):
                continue

            none_valid = False
            cleaned_data = form.clean()
            payment_method = cleaned_data.get("payment_method")
            iban = cleaned_data.get("iban")
            mandate = cleaned_data.get("mandate")

            if payment_method == models.ContractPerson.DIRECT_DEBIT:
                if not iban or not mandate:
                    raise forms.ValidationError(
                        "Please provide an iban and a mandate."
                    )
            else:
                if iban or mandate:
                    raise forms.ValidationError(
                        "Only fill in IBAN & mandate in case of Direct Debit"
                        "payment method."
                    )

            start_date = cleaned_data.get("start_date")
            end_date = cleaned_data.get("end_date")
            if end_date and start_date and end_date < start_date:
                raise forms.ValidationError(
                    "End date should be after start date."
                )

            if end_date:
                end_date += datetime.timedelta(days=1)

            if not start_date:
                continue

            if start_date <= self.contract.start_date \
                    and (not end_date or end_date >= self.contract.start_date):
                contract_start_percentage \
                    += cleaned_data.get('percentage_of_total')

            percentage_start = 0
            percentage_end = 0
            for second_form in self.forms:
                if self._should_delete_form(second_form) \
                        or (second_form.empty_permitted
                            and not second_form.has_changed()) \
                        or not second_form.instance.start_date:
                    continue

                if second_form.instance.start_date <= start_date \
                        and (not second_form.instance.end_date
                             or start_date <= second_form.instance.end_date):
                    percentage_start += second_form.instance.percentage_of_total

                if end_date and second_form.instance.start_date <= end_date \
                        and (not second_form.instance.end_date
                             or end_date <= second_form.instance.end_date):
                    percentage_end += second_form.instance.percentage_of_total
                elif not end_date and not second_form.instance.end_date:
                    percentage_end += second_form.instance.percentage_of_total

            if percentage_start > 100:
                raise forms.ValidationError(
                    'Total of all persons exceeding 100% by '
                    + (percentage_start - 100).__str__()
                    + '% on '
                    + start_date.__str__()
                )
            elif percentage_start < 100:
                raise forms.ValidationError(
                    'Total of all persons smaller than 100% by '
                    + (100 - percentage_start).__str__()
                    + '% on '
                    + start_date.__str__()
                )

            if percentage_end > 100:
                raise forms.ValidationError(
                    'Total of all persons exceeding 100% by '
                    + (percentage_end - 100).__str__()
                    + '% '
                    + ("on " + end_date.__str__()
                       if end_date else "at the end.")
                )
            elif percentage_end < 100:
                raise forms.ValidationError(
                    'Total of all persons smaller than 100% by '
                    + (100 - percentage_end).__str__()
                    + "% "
                    + ("on " + end_date.__str__()
                       if end_date else "at the end.")
                )

        if none_valid:
            raise forms.ValidationError(
                'Please do not delete all persons.'
            )

        if contract_start_percentage > 100:
            raise forms.ValidationError(
                'Total of all persons exceeding 100% by '
                + (contract_start_percentage - 100).__str__()
                + '% '
                + "on " + self.contract.start_date.__str__()
            )
        elif contract_start_percentage < 100:
            raise forms.ValidationError(
                'Total of all persons smaller than 100% by '
                + (100 - contract_start_percentage).__str__()
                + "% "
                + "on " + self.contract.start_date.__str__()
            )
