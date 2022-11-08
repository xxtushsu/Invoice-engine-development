import datetime as dt
import decimal as dc

from django.db import models, transaction
from django.db.models import Q, F


TWO_PLACES = dc.Decimal('.01')


def mul_f(x, y):
    """Function for multiplying a Decimal object with a float."""
    return (x * dc.Decimal(y)).quantize(TWO_PLACES)


def mul_d(x, y):
    """Function for multiplying a Decimal with an integer or a decimal."""
    return (x * y).quantize(TWO_PLACES)


def div(x, y):
    """Function for dividing a Decimal by an integer or a Decimal."""
    return (x / y).quantize(TWO_PLACES)


def get_next_invoice_id():
    """Static function to return the highest possible invoice id and invoice
    line id. Function needed because the ids are needed for other objects to
    refer to in their foreign key. This is done before the invoices and invoice
    lines are added to the database, so automatic primary keys have not been
    generated yet.
    """
    next_invoice_id = 0
    next_invoice_line_id = 0
    if Invoice.objects.exists():
        next_invoice_id = Invoice.objects.aggregate(
            models.Max('invoice_id')
        ).get('invoice_id__max') + 1

    if InvoiceLine.objects.exists():
        next_invoice_line_id = InvoiceLine.objects.aggregate(
            models.Max('invoice_line_id')
        ).get('invoice_line_id__max') + 1

    return next_invoice_id, next_invoice_line_id


class Tenancy(models.Model):
    """This class represents a company. Only a user with the same username as
    the tenancy_id has access to this company and all its data. Therefore,
    every other object (indirectly) foreign-keys to this object.
    """
    company_id = models.AutoField(primary_key=True)
    tenancy_id = models.PositiveIntegerField()
    name = models.CharField(max_length=30)
    number_of_contracts = models.PositiveIntegerField(default=0)
    last_invoice_number = models.PositiveIntegerField(default=0)
    date_next_prolongation = models.DateField(null=True, blank=True)
    days_until_invoice_expiration = models.PositiveSmallIntegerField(
        default=14
    )

    def __str__(self):
        return self.name

    def create(self, kwargs):
        pass

    def get_details(self):
        """Method to print all fields and their values."""
        return {
            'name': self.name,
            'number of contracts': self.number_of_contracts,
            'last invoice number': self.last_invoice_number,
            'date of next prolonging': self.date_next_prolongation,
            'days until invoice expiration': self.days_until_invoice_expiration
        }

    def invoice_contracts(self):
        """"Method to go over all components linked to this tenancy, and
        to create invoices, invoice lines, collections, and general ledger
        posts for each of them.

        The ids for invoices and invoice lines have to be set manually,
        because they will be linked to by other objects. It is not possible
        to link after entry into the database.
        """
        date_today = dt.date.today()

        # Load all components into memory
        # There is some inefficiency here: if for a contract
        # date_next_prolongation = 2021-01-01 and it has a component with
        # start_date = date_next_prolongation = 2021-05-01, the component
        # will be loaded into memory to discard later
        components = list(
            self.component_set.filter(
                Q(date_next_prolongation__isnull=False)
                & Q(contract__date_next_prolongation__isnull=False)
                & Q(contract__date_next_prolongation__lte=date_today)
            ).order_by(
                'contract_id'
            ).select_related(
                'contract__contract_type',
                'vat_rate__successor_vat_rate',
                'base_component'
            )
        )

        if not components:
            # There are no contracts to prolong
            return

        # Load all contract persons into memory
        contract_persons = list(
            self.contractperson_set.filter(
                Q(start_date__lte=date_today)
                & (Q(end_date__gte=date_today) | Q(end_date__isnull=True))
            ).order_by('contract_id')
        )

        # Create lists to store the generated objects
        # This is to use one single database transaction at the end
        new_invoices = []
        new_invoice_lines = []
        new_gl_posts = []
        new_collections = []

        # Set the id for the next invoice & invoice line.
        # Take the highest id that is currently in the database and add 1
        next_invoice_id, next_invoice_line_id = get_next_invoice_id()

        # Create an invoice for the first component's contract
        invoice = components[0].contract.invoice(
            date_today, next_invoice_id, self
        )
        new_invoices.append(invoice)
        next_invoice_id += 1
        previous_contract = components[0].contract_id

        # Loop over all components to create invoice lines for them
        for component in components:
            # Create a new invoice only when a new contract is reached
            # This is possible because components are ordered by contract_id
            if component.contract_id != previous_contract:
                # Invoice for contract x is finished
                # Generate collections for contract x
                while contract_persons and \
                        contract_persons[0].contract_id == invoice.contract_id:
                    contract_persons[0].invoice(self, invoice, new_collections)
                    contract_persons.pop(0)

                # Create GL posts for the finished invoice
                invoice.create_gl_post(new_gl_posts)
                invoice.contract.end_invoicing()

                # Create an invoice for the next contract
                invoice = component.contract.invoice(
                    date_today, next_invoice_id, self
                )
                new_invoices.append(invoice)
                next_invoice_id += 1

            # Create an invoice line and associated GL posts for this component
            component.invoice(
                next_invoice_line_id, invoice, new_invoice_lines, new_gl_posts
            )
            next_invoice_line_id += 1
            previous_contract = component.contract_id

        # Finish the final invoice
        while contract_persons and \
                contract_persons[0].contract_id == invoice.contract_id:
            contract_persons[0].invoice(self, invoice, new_collections)
            contract_persons.pop(0)

        invoice.create_gl_post(new_gl_posts)
        invoice.contract.end_invoicing()

        # End of main program loop
        # Save the changes made to the database in one transaction
        # If one fails, they will all fail
        with transaction.atomic():
            # Loop over the components and associated contracts to update them
            # Bulk update might overload the CPU in this case
            previous_contract = -1
            for component in components:
                if component.contract_id != previous_contract:
                    component.contract.save(
                        update_fields=[
                            'balance',
                            'date_next_prolongation',
                            'date_prev_prolongation',
                            'base_amount',
                            'vat_amount',
                            'total_amount'
                        ]
                    )

                component.save(
                    update_fields=[
                        'date_next_prolongation',
                        'date_prev_prolongation',
                        'vat_rate',
                        'vat_amount',
                        'total_amount'
                    ]
                )
                previous_contract = component.contract_id

            Invoice.objects.bulk_create(new_invoices)
            InvoiceLine.objects.bulk_create(new_invoice_lines)
            GeneralLedgerPost.objects.bulk_create(new_gl_posts)
            Collection.objects.bulk_create(new_collections)

            # Save the tenancy with the new last_invoice_number
            self.save(update_fields=['last_invoice_number'])


class TenancyDependentModel(models.Model):
    """This abstract class is inherited by models which directly refer to the
    tenancy model in their foreign key.
    """
    tenancy = models.ForeignKey(Tenancy, on_delete=models.CASCADE)

    def create(self, kwargs):
        """Method called when an instance of this class is created, to set
        the tenancy.
        """
        self.tenancy_id = kwargs.get('company_id')

    class Meta:
        abstract = True


class ContractType(TenancyDependentModel):
    """This class represents a certain type of contract, for instance for
    different kinds of rental cars for which they can make contracts.
    """
    contract_type_id = models.AutoField(primary_key=True)
    code = models.PositiveIntegerField()
    description = models.CharField(max_length=50)
    gl_debit = models.CharField(max_length=10)
    gl_credit = models.CharField(max_length=10)

    def __str__(self):
        return self.description

    def can_update(self):
        return self.can_update_or_delete()

    def can_delete(self):
        return self.can_update_or_delete()

    def can_update_or_delete(self):
        """Method to determine whether the instance can be updated
        or deleted.
        """
        return not self.contract_set.filter(
            date_prev_prolongation__isnull=False
        ).exists()


class BaseComponent(TenancyDependentModel):
    """The base component represents a basic unit for a contract line.
    In the case of a housing provider, this could for instance be one line
    specifying the rent price, and one line specifying any service costs.

    A base component always corresponds to a tenancy.
    """
    base_component_id = models.AutoField(primary_key=True)
    code = models.PositiveIntegerField()
    description = models.CharField(max_length=50)
    gl_debit = models.CharField(max_length=10)
    gl_credit = models.CharField(max_length=10)
    gl_dimension = models.CharField(max_length=10)
    unit_id = models.CharField(max_length=10, null=True, blank=True)

    def __str__(self):
        return self.description \
               + " - unit " \
               + self.unit_id.__str__() if self.unit_id else self.description

    def can_update(self):
        return self.can_update_or_delete()

    def can_delete(self):
        return self.can_update_or_delete()

    def can_update_or_delete(self):
        return not self.component_set.filter(
            date_prev_prolongation__isnull=False
        ).exists()


class VATRate(TenancyDependentModel):
    """The VAT rate defines the value added tax charged for a contract line.
    In the Netherlands, there are three types of VAT: none (0%), low (9%),
    or high (21%).

    A VAT rate always corresponds to a tenancy.
    """
    vat_rate_id = models.AutoField(primary_key=True)
    successor_vat_rate = models.OneToOneField(
        'self', null=True, on_delete=models.SET_NULL
    )
    type = models.PositiveIntegerField()
    description = models.CharField(max_length=30)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True, default=None)
    percentage = models.DecimalField(max_digits=5, decimal_places=2)
    gl_account = models.CharField(max_length=10)
    gl_dimension = models.CharField(max_length=10)

    def __str__(self):
        return "Type " \
               + self.type.__str__() \
               + ": " \
               + self.description \
               + " - " \
               + self.percentage.__str__() \
               + "%"

    def can_update(self):
        return self.can_update_or_delete()

    def can_delete(self):
        return self.can_update_or_delete()

    def can_update_or_delete(self):
        return not self.component_set.exclude(
            contract__status=Contract.DRAFT
        ).exists()

    def create(self, kwargs):
        super().create(kwargs)

        try:
            old_vat_rate = self.tenancy.vatrate_set.exclude(
                vat_rate_id=self.vat_rate_id
            ).get(
                type=self.type,
                end_date__isnull=True
            )
        except self.DoesNotExist:
            old_vat_rate = None

        if old_vat_rate:
            if old_vat_rate.can_delete():
                components = old_vat_rate.component_set.all()
                for component in components:
                    component.remove_from_contract()
                    component.vat_rate = self
                    component.update()
                old_vat_rate.delete()
            else:
                old_vat_rate.end_date = self.start_date - dt.timedelta(days=1)
                old_vat_rate.successor_vat_rate = self
                old_vat_rate.save(
                    update_fields=['successor_vat_rate', 'end_date']
                )

    def update(self):
        for component in self.component_set.all():
            component.update()

    def delete(self, using=None, keep_parents=False):
        with transaction.atomic():
            for component in self.component_set.select_related('contract'):
                component.remove_from_contract()
                component.vat_rate = self.successor_vat_rate
                component.update()
            super().delete(using, keep_parents)


class Contract(TenancyDependentModel):
    """The contract is an agreement between two parties (e.g. a company and a
    person). In this case, the person(s) agree to pay some amount per some time
    period in exchange for a service or product.
    """
    # Define options for invoicing period
    MONTH = 'M'
    QUARTER = 'Q'
    HALF_YEAR = 'H'
    YEAR = 'Y'
    CUSTOM = 'V'
    INVOICING_PERIOD_CHOICES = [
        (MONTH, 'Month'),
        (QUARTER, 'Quarter'),
        (HALF_YEAR, 'Half year'),
        (YEAR, 'Year'),
        (CUSTOM, 'Custom')
    ]

    DRAFT = 'F'
    ACTIVE = 'A'
    TERMINATED = 'T'
    ENDED = 'E'
    HISTORIC = 'H'
    STATUS_CHOICES = [
        (DRAFT, 'Draft'),
        (ACTIVE, 'Active'),
        (TERMINATED, 'Terminated'),
        (ENDED, 'Ended'),
        (HISTORIC, 'Historic')
    ]

    PERIOD = 'P'
    DAY = 'D'
    PRICING_TYPE_CHOICES = [
        (PERIOD, 'Per period'),
        (DAY, 'Per day')
    ]

    # Model fields
    contract_id = models.AutoField(primary_key=True)
    external_customer_id = models.PositiveIntegerField()
    status = models.CharField(
        max_length=1,
        choices=STATUS_CHOICES,
        default=DRAFT
    )

    contract_type = models.ForeignKey(ContractType, on_delete=models.CASCADE)
    invoicing_period = models.CharField(
        max_length=1,
        choices=INVOICING_PERIOD_CHOICES,
        default=MONTH
    )
    # Only not null if invoicing_period is custom
    invoicing_amount_of_days = models.PositiveSmallIntegerField(
        null=True, blank=True
    )

    pricing_type = models.CharField(
        max_length=1,
        choices=PRICING_TYPE_CHOICES,
        default=PERIOD
    )

    # Dates
    start_date = models.DateField(null=True, default=None, blank=True)
    end_date = models.DateField(null=True, blank=True)
    termination_date = models.DateField(null=True, blank=True)
    date_prev_prolongation = models.DateField(null=True, default=None)
    date_next_prolongation = models.DateField(null=True, default=None)

    # General ledger
    gl_dimension_1 = models.CharField(max_length=10)
    gl_dimension_2 = models.CharField(max_length=10)

    # Accumulated fields
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    base_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    vat_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    def __str__(self):
        return self.contract_type.description

    def has_components(self):
        return self.component_set.exists()

    def get_components(self):
        return self.component_set.all()

    def has_contract_persons(self):
        return self.contractperson_set.exists()

    def get_contract_persons(self):
        return self.contractperson_set.all()

    def get_invoices(self):
        return self.invoice_set.all()

    def get_period(self):
        for key, value in self.INVOICING_PERIOD_CHOICES:
            if key == self.invoicing_period:
                return value

    def get_status(self):
        for key, value in self.STATUS_CHOICES:
            if key == self.status:
                return value

    def create(self, kwargs):
        super().create(kwargs)
        self.tenancy.number_of_contracts = F('number_of_contracts') + 1
        self.tenancy.save(update_fields=['number_of_contracts'])

    def can_update(self):
        return self.is_draft() or self.is_active() or self.is_terminated()

    def update(self):
        if self.is_active():
            if self.termination_date:
                self.status = Contract.TERMINATED
        elif self.is_terminated():
            if not self.termination_date:
                self.status = Contract.ACTIVE

    def can_delete(self):
        return self.is_draft()

    def delete(self, using=None, keep_parents=False):
        self.tenancy.number_of_contracts = F('number_of_contracts') - 1
        with transaction.atomic():
            self.tenancy.save(update_fields=['number_of_contracts'])
            super().delete(using, keep_parents)

    def can_activate(self):
        """Return whether a contract can be activated for invoicing.
        This is only possible if it has contract persons, components,
        and a start date.
        """
        return (self.is_draft()
                and self.persons_percentage_is_full()
                and self.start_date
                and self.has_components())
    
    def persons_percentage_is_full(self):
        return self.contractperson_set.filter(
            start_date__lte=self.start_date
        ).aggregate(
            models.Sum('percentage_of_total')
        ).get('percentage_of_total__sum') == 100
    
    def activate(self):
        """Activate a contract so that it can be invoiced."""
        self.date_next_prolongation = self.start_date
        self.status = (Contract.TERMINATED
                       if self.termination_date else Contract.ACTIVE)
        with transaction.atomic():
            self.component_set.filter(
                start_date__lt=self.start_date
            ).update(
                start_date=self.start_date
            )
            self.component_set.update(date_next_prolongation=F('start_date'))
            self.contractperson_set.filter(
                start_date__lt=self.start_date
            ).update(
                start_date=self.start_date
            )
            self.save()

    def can_end(self):
        return self.status == Contract.TERMINATED

    def end(self):
        """End the contract. If it is ended at a date that has already
        been invoiced, send a correction invoice for the period between
        the newly set end date and the last day that was invoiced.
        """
        date_today = dt.date.today()
        self.end_date = self.termination_date
        self.status = Contract.ENDED
        components = self.component_set.filter(
            Q(end_date__isnull=True) | Q(end_date__gt=self.end_date)
        )
        persons = self.contractperson_set.filter(
            Q(start_date__lte=date_today)
            & (Q(end_date__gte=date_today) | Q(end_date__isnull=True))
        )

        if self.end_date == self.date_next_prolongation - dt.timedelta(days=1):
            # No need to invoice this contract in the future
            self.date_next_prolongation = None
            with transaction.atomic():
                components.update(end_date=self.end_date)
                persons.update(end_date=self.end_date)
                self.save(
                    update_fields=[
                        'end_date', 'status', 'date_next_prolongation'
                    ]
                )
        elif self.end_date < self.date_next_prolongation:
            # Issue a correction invoice
            invoice_id, invoice_line_id = get_next_invoice_id()
            invoice = self.create_invoice(
                date_today,
                invoice_id,
                self.tenancy
            )

            new_invoice_lines = []
            new_gl_posts = []
            new_collections = []

            components = list(components)
            for component in components:
                component.end_date = self.end_date
                component.date_next_prolongation = None
                base, vat, total, unit = component.get_amounts_between_dates(
                    self.end_date,
                    min(component.end_date + dt.timedelta(days=1),
                        self.date_next_prolongation)
                )

                component.create_invoice_line(
                    invoice_line_id,
                    invoice,
                    -base,
                    -vat,
                    -total,
                    -unit,
                    new_invoice_lines,
                    new_gl_posts
                )
                invoice_line_id += 1

            persons = list(persons)
            for person in persons:
                person.end_date = self.end_date
                person.invoice(
                    self.tenancy,
                    invoice,
                    new_collections
                )
            invoice.create_gl_post(new_gl_posts)

            self.date_next_prolongation = None

            with transaction.atomic():
                for component in components:
                    component.save(
                        update_fields=['end_date', 'date_next_prolongation']
                    )
                for person in persons:
                    person.save(update_fields=['end_date'])
                invoice.save()
                InvoiceLine.objects.bulk_create(new_invoice_lines)
                GeneralLedgerPost.objects.bulk_create(new_gl_posts)
                Collection.objects.bulk_create(new_collections)
                self.tenancy.save(update_fields=['last_invoice_number'])
                self.save(
                    update_fields=[
                        'end_date', 'status', 'date_next_prolongation'
                    ]
                )

    def is_draft(self):
        return self.status == Contract.DRAFT

    def is_active(self):
        return self.status == Contract.ACTIVE

    def is_terminated(self):
        return self.status == Contract.TERMINATED

    def is_ended(self):
        return self.status == Contract.ENDED

    def is_historic(self):
        return self.status == Contract.HISTORIC

    def remove_component(self, component):
        self.total_amount -= component.total_amount
        self.vat_amount -= component.vat_amount
        self.base_amount -= (component.total_amount - component.vat_amount)

    def compute_date_next_prolongation(self, previous_date):
        """Based on the invoicing period and the date of the last invoice,
        compute the date on which to invoice the contract next.
        """
        month = previous_date.month
        year = previous_date.year
        day = previous_date.day
        if self.invoicing_period == self.MONTH:
            month += 1
        elif self.invoicing_period == self.QUARTER:
            month += 3
        elif self.invoicing_period == self.HALF_YEAR:
            month += 6
        elif self.invoicing_period == self.YEAR:
            year += 1
        elif self.invoicing_period == self.CUSTOM:
            return previous_date + dt.timedelta(
                days=self.invoicing_amount_of_days
            )

        # Shift year by one if the 12th month is passed
        if month > 12:
            month %= 12
            year += 1

        if month == 2 and day > 28:
            # Correct for February & keep leap years into account
            # Note that there is no check for year % 100 == 0,
            # which is not a leap year unless year % 400 == 0
            day = 29 if year % 4 == 0 else 28
        elif day == 31 and month in [4, 6, 9, 11]:
            # Correct for months that have 30 days
            day = 30

        return dt.date(year, month, day)

    def invoice(self, date_today, next_id, tenancy):
        """Set the next invoicing date. If it is after the end date,
        this will be handled later. The components need the date to
        be there first.

        Also create an invoice for this contract.
        """
        self.date_prev_prolongation = self.date_next_prolongation
        while self.date_next_prolongation <= date_today:
            self.date_next_prolongation = self.compute_date_next_prolongation(
                self.date_next_prolongation
            )

        return self.create_invoice(date_today, next_id, tenancy)

    def end_invoicing(self):
        """Definitively end this contract when its end date has been passed
        by the next invoicing date. This is checked after invoicing the
        contract and its components.
        """
        if self.is_ended() and self.end_date < self.date_next_prolongation:
            self.date_next_prolongation = None

    def create_invoice(self, date_today, next_id, tenancy):
        tenancy.last_invoice_number += 1
        # Do not specify amounts (added from the invoice lines)
        return Invoice(
            invoice_id=next_id,
            tenancy=tenancy,
            contract=self,
            external_customer_id=self.external_customer_id,
            description="Invoice: " + date_today.__str__(),
            date=date_today,
            expiration_date=date_today + dt.timedelta(
                days=tenancy.days_until_invoice_expiration
            ),
            invoice_number=tenancy.last_invoice_number,
            gl_account=self.contract_type.gl_debit,
        )


class Component(TenancyDependentModel):
    """A Contract is built up of one or more components.
    These 'contract lines' specify the amounts and services.
    """
    component_id = models.AutoField(primary_key=True)
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE)
    base_component = models.ForeignKey(BaseComponent, on_delete=models.CASCADE)
    vat_rate = models.ForeignKey(
        VATRate, null=True, blank=True, on_delete=models.SET_NULL
    )
    description = models.CharField(max_length=50)
    start_date = models.DateField(null=True)
    end_date = models.DateField(null=True, blank=True)
    date_prev_prolongation = models.DateField(
        null=True, blank=True, default=None
    )
    date_next_prolongation = models.DateField(null=True, default=None)
    base_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    vat_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    unit_id = models.CharField(max_length=10, null=True, blank=True)
    unit_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    number_of_units = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return self.description

    def create(self, kwargs):
        """Also check if this component replaces an existing component.
        """
        super().create(kwargs)
        self.contract = Contract.objects.get(
            contract_id=kwargs.get('contract_id')
        )

        self.tenancy = Tenancy.objects.get(
            company_id=self.tenancy_id
        )

        self.unit_id = self.base_component.unit_id
        self.set_derived_fields()

        # Save the component because it needs a pk for a correction invoice
        self.save()

        invoice = None
        line_id = None
        new_invoice_lines = []
        new_gl_posts = []
        new_collections = []
        date_today = dt.date.today()

        if not self.is_draft():
            self.date_next_prolongation = self.start_date
            if (self.date_next_prolongation
                    < self.contract.date_next_prolongation):
                invoice_id, line_id = get_next_invoice_id()
                invoice = self.contract.create_invoice(
                    date_today,
                    invoice_id,
                    self.tenancy
                )

                base, vat, total, unit = self.get_amounts_between_dates(
                    self.date_next_prolongation,
                    self.contract.date_next_prolongation
                )

                self.create_invoice_line(
                    line_id,
                    invoice,
                    base,
                    vat,
                    total,
                    unit,
                    new_invoice_lines,
                    new_gl_posts
                )
                line_id += 1

                self.date_next_prolongation = \
                    self.contract.date_next_prolongation

        # If there is an existing component that uses the same base component,
        # this new component will replace the old one. This is known as a
        # price change.
        if self.end_date:
            components = list(
                self.contract.component_set.filter(
                    Q(base_component_id=self.base_component_id)
                    & Q(start_date__lte=self.end_date)
                    & (Q(end_date__gte=self.start_date)
                       | Q(end_date__isnull=True))
                    & ~Q(component_id=self.component_id)
                    & ~Q(start_date__isnull=True)
                )
            )
        else:
            components = list(
                self.contract.component_set.filter(
                    Q(base_component_id=self.base_component_id)
                    & (Q(end_date__gte=self.start_date)
                       | Q(end_date__isnull=True))
                    & ~Q(component_id=self.component_id)
                    & ~Q(start_date__isnull=True)
                )
            )

        invoiced_until = self.contract.date_next_prolongation
        new_component = None

        for c in components:
            if self.start_date <= c.start_date \
                    and (not self.end_date or self.end_date >= c.end_date):
                base, vat, total, unit = c.get_amounts_between_dates(
                    c.start_date,
                    min(c.end_date + dt.timedelta(days=1),
                        invoiced_until) if c.end_date else invoiced_until
                )
                c.start_date = None
                c.end_date = None
            elif self.end_date and c.end_date \
                    and self.start_date > c.start_date \
                    and self.end_date < c.end_date:
                base, vat, total, unit = c.get_amounts_between_dates(
                    self.start_date,
                    min(self.end_date + dt.timedelta(days=1),
                        invoiced_until),
                )
                c.end_date = self.start_date - dt.timedelta(days=1)
                new_component = Component(
                    tenancy_id=c.tenancy_id,
                    contract_id=c.contract_id,
                    base_component_id=c.base_component_id,
                    vat_rate_id=c.vat_rate_id,
                    description=c.description,
                    start_date=self.end_date + dt.timedelta(days=1),
                    end_date=c.end_date,
                    date_prev_prolongation=c.date_prev_prolongation,
                    date_next_prolongation=c.date_next_prolongation,
                    base_amount=c.base_amount,
                    vat_amount=c.vat_amount,
                    unit_id=c.unit_id,
                    unit_amount=c.unit_amount,
                    number_of_units=c.number_of_units
                )
            elif self.start_date > c.start_date:
                base, vat, total, unit = c.get_amounts_between_dates(
                    self.start_date,
                    min(c.end_date + dt.timedelta(days=1),
                        invoiced_until) if c.end_date else invoiced_until
                )
                c.end_date = self.start_date - dt.timedelta(days=1)
            else:
                # elif self.end_date > c.start_date:
                base, vat, total, unit = c.get_amounts_between_dates(
                    c.start_date,
                    min(self.end_date, invoiced_until)
                )
                c.start_date = self.end_date + dt.timedelta(days=1)

            if invoice:
                c.create_invoice_line(
                    line_id,
                    invoice,
                    -base,
                    -vat,
                    -total,
                    -unit,
                    new_invoice_lines,
                    new_gl_posts
                )
                line_id += 1

        if invoice:
            persons = self.contract.contractperson_set.filter(
                Q(start_date__lte=date_today)
                & (Q(end_date__gte=date_today) | Q(end_date__isnull=True))
            )
            for person in persons:
                person.invoice(self.tenancy, invoice, new_collections)

            invoice.create_gl_post(new_gl_posts)

        with transaction.atomic():
            self.contract.save()
            if invoice:
                invoice.save()
                InvoiceLine.objects.bulk_create(new_invoice_lines)
                GeneralLedgerPost.objects.bulk_create(new_gl_posts)
                Collection.objects.bulk_create(new_collections)
                for component in components:
                    component.save(update_fields=['start_date', 'end_date'])
                if new_component:
                    new_component.save()
                self.tenancy.save(update_fields=['last_invoice_number'])

    def get_amounts_between_dates(self, start_date, end_date):
        """Method that calculates the exact amount that should be paid for
        this component between two dates (including start_date, excluding
        end_date) that are not necessarily in the same period. This method
        uses the amount of days in the period and the amount of days that
        should be invoiced in the period to get the appropriate amount.
        """
        if self.contract.pricing_type == Contract.DAY:
            days = (end_date - start_date).days
            base_amount = self.base_amount * days if self.base_amount else 0
            vat_amount = self.vat_amount * days
            total_amount = self.total_amount * days
            unit_amount = self.unit_amount * days if self.unit_amount else 0

            return base_amount, vat_amount, total_amount, unit_amount

        am = 0
        am_type = self.base_amount if self.base_amount else self.unit_amount

        prev_date = self.contract.start_date
        current_date = self.contract.compute_date_next_prolongation(prev_date)
        while current_date < start_date:
            prev_date = current_date
            current_date = self.contract.compute_date_next_prolongation(prev_date)

        period_days = (current_date - prev_date).days
        invoicing_days = (current_date - start_date).days
        am += mul_f(am_type, invoicing_days / period_days)

        prev_date = current_date
        current_date = self.contract.compute_date_next_prolongation(prev_date)

        # current_date > start_date
        while current_date <= end_date:
            am += am_type

            prev_date = current_date
            current_date = self.contract.compute_date_next_prolongation(prev_date)

        period_days = (current_date - prev_date).days
        invoicing_days = (end_date - prev_date).days
        am += mul_f(am_type, invoicing_days / period_days)

        if self.base_amount:
            base_amount = am
            unit_amount = 0
            total_without_vat = am
        else:
            base_amount = 0
            unit_amount = am
            total_without_vat = mul_d(am, self.number_of_units)

        vat_amount = mul_d(
            total_without_vat,
            div(self.vat_rate.percentage, 100)
        ) if self.vat_rate else 0
        total_amount = total_without_vat + vat_amount

        return base_amount, vat_amount, total_amount, unit_amount

    def can_update(self):
        return self.contract.can_update()

    def update(self):
        if self.vat_amount and not self.vat_rate:
            self.total_amount -= self.vat_amount
            self.vat_amount = 0
        self.unit_id = self.base_component.unit_id
        self.set_derived_fields()

        with transaction.atomic():
            self.contract.save()
            self.save()

    def set_derived_fields(self):
        amount = self.base_amount
        if not amount:
            amount = mul_d(self.number_of_units, self.unit_amount)

        if self.vat_rate:
            self.vat_amount = mul_d(div(self.vat_rate.percentage, 100), amount)

        self.total_amount = amount + self.vat_amount

        # Update contract
        self.contract.total_amount += self.total_amount
        self.contract.vat_amount += self.vat_amount
        self.contract.base_amount += amount

    def can_delete(self):
        return self.contract.can_delete()

    def delete(self, using=None, keep_parents=False):
        self.remove_from_contract()

        with transaction.atomic():
            self.contract.save(
                update_fields=['total_amount', 'vat_amount', 'base_amount']
            )
            super().delete(using, keep_parents)

    def remove_from_contract(self):
        self.contract.total_amount -= self.total_amount
        self.contract.vat_amount -= self.vat_amount
        # Subtract VAT from total to prevent checking for units
        self.contract.base_amount -= (self.total_amount - self.vat_amount)

    def is_draft(self):
        return self.contract.is_draft()

    def create_correction_invoice(self, start_date, end_date, factor):
        """Create an invoice with one invoice line, specifically for
        this component. This can be needed in the case the start date
        or end date have been changed, affection already invoiced periods.
        """
        date_today = dt.date.today()
        invoice_id, invoice_line_id = get_next_invoice_id()
        invoice = self.contract.create_invoice(
            date_today,
            invoice_id,
            self.tenancy
        )
        new_invoice_lines = []
        new_gl_posts = []
        new_collections = []
        base_amount, vat_amount, total_amount, unit_amount = \
            self.get_amounts_between_dates(start_date, end_date)

        self.create_invoice_line(
            invoice_line_id,
            invoice,
            factor*base_amount,
            factor*vat_amount,
            factor*total_amount,
            factor*unit_amount,
            new_invoice_lines,
            new_gl_posts
        )

        # Create collections
        persons = self.contract.contractperson_set.filter(
            Q(start_date__lte=date_today)
            & (Q(end_date__gte=date_today) | Q(end_date__isnull=True))
        )
        for person in persons:
            person.invoice(self.tenancy, invoice, new_collections)

        invoice.create_gl_post(new_gl_posts)

        with transaction.atomic():
            invoice.save()
            InvoiceLine.objects.bulk_create(new_invoice_lines)
            GeneralLedgerPost.objects.bulk_create(new_gl_posts)
            Collection.objects.bulk_create(new_collections)
            self.tenancy.save(update_fields=['last_invoice_number'])

    def change_end_date(self, old_end_date):
        """When the end date of this component is changed, check in what
        period the new end date falls. Send a correction invoice if needed.
        """
        if self.is_draft():
            return

        if old_end_date:
            if self.end_date:
                # If an existing end date was replaced by a new one
                if self.end_date < old_end_date and self.end_date < self.contract.date_next_prolongation:
                    self.date_next_prolongation = None
                    start = self.end_date
                    end = min(old_end_date, self.contract.date_next_prolongation)
                    self.create_correction_invoice(start, end, -1)
                elif old_end_date < self.end_date and old_end_date < self.contract.date_next_prolongation:
                    self.date_next_prolongation = None \
                        if self.end_date < self.contract.date_next_prolongation \
                        else self.contract.date_next_prolongation
                    start = old_end_date
                    end = min(self.end_date, self.contract.date_next_prolongation)
                    self.create_correction_invoice(start, end, 1)
            else:
                # New end date is None
                if old_end_date < self.contract.date_next_prolongation:
                    # send positive invoice for period between old end date and next invoicing date
                    self.date_next_prolongation = self.contract.date_next_prolongation
                    self.create_correction_invoice(old_end_date, self.contract.date_next_prolongation, 1)
        else:
            # End date is changed from None to something
            if self.end_date < self.contract.date_next_prolongation:
                # Send negative invoice for period between new end date and next invoicing date
                self.date_next_prolongation = None
                self.create_correction_invoice(self.end_date, self.contract.date_next_prolongation, -1)

    def change_start_date(self, old_start_date):
        """When the start date of this component is changed, check in what
        period the new end date falls. Send a correction invoice if needed.
        """
        if self.is_draft():
            return

        if self.start_date < old_start_date and self.start_date < self.contract.date_next_prolongation:
            # Send positive invoice for period between new start date
            # and min(old start date, next invoicing date)
            start = self.start_date
            end = min(old_start_date, self.contract.date_next_prolongation)
            self.create_correction_invoice(start, end, 1)

        elif old_start_date < self.start_date and old_start_date < self.contract.date_next_prolongation:
            # Send negative invoice for period between old start date
            # and min(new start date, next invoicing date)
            start = old_start_date
            end = min(self.start_date, self.contract.date_next_prolongation)
            self.create_correction_invoice(start, end, -1)

    def create_invoice_line(self, next_id, invoice, base_amount, vat_amount,
                            total_amount, unit_amount,
                            new_invoice_lines, new_gl_posts):
        invoice_line = InvoiceLine(
            invoice_line_id=next_id,
            component=self,
            invoice=invoice,
            description=self.description,
            base_amount=base_amount,
            vat_amount=vat_amount,
            total_amount=total_amount,
            vat_type=self.vat_rate.type if self.vat_rate else None,

            gl_account=self.base_component.gl_credit,
            gl_dimension_base_component=self.base_component.gl_dimension,
            gl_dimension_contract_1=invoice.contract.gl_dimension_1,
            gl_dimension_contract_2=invoice.contract.gl_dimension_2,
            gl_dimension_vat=self.vat_rate.gl_dimension if self.vat_rate else None,

            number_of_units=self.number_of_units,
            unit_price=unit_amount,
            unit_id=self.unit_id
        )

        # To prevent doing maths with units
        invoice.base_amount += total_amount - vat_amount
        invoice.vat_amount += vat_amount
        invoice.total_amount += total_amount
        invoice.balance += total_amount
        invoice.contract.balance += total_amount

        # Create gl posts (one if no VAT, otherwise two)
        invoice_line.create_gl_posts(new_gl_posts)
        new_invoice_lines.append(invoice_line)

    def invoice(self, next_id, invoice, new_invoice_lines, new_gl_posts):
        """Method called during the normal invoicing process. Compute what needs
        to be paid based on the length of the period and the start and end date
        of this component (they may be within the invoicing period).
        """
        contract = invoice.contract
        if (contract.date_next_prolongation
                and self.date_next_prolongation >= contract.date_next_prolongation):
            return

        base_amount = self.base_amount
        unit_amount = self.unit_amount
        total_amount = self.total_amount
        vat_amount = self.vat_amount

        # Determine number of days in the normal(!) to-invoice period
        start_date_period = contract.date_prev_prolongation  # 'today'
        end_date_period = contract.date_next_prolongation - dt.timedelta(days=1)
        days_period = (end_date_period - start_date_period).days + 1

        # Determine whether the component is ending in the to-invoice period
        is_ending = (self.end_date is not None
                     and self.end_date < end_date_period)

        # Determine number of days in the actual(!) to-invoice period
        start_date_invoicing = self.date_next_prolongation
        end_date_invoicing = self.end_date if is_ending else end_date_period
        days_invoicing = (end_date_invoicing - start_date_invoicing).days + 1

        # Check if the VAT is different for this period
        if self.vat_rate \
                and self.vat_rate.end_date \
                and self.vat_rate.end_date < start_date_invoicing:
            if self.vat_rate.successor_vat_rate \
                    and (self.vat_rate.successor_vat_rate.percentage
                         != self.vat_rate.percentage):
                self.vat_rate = self.vat_rate.successor_vat_rate
                total_amount -= vat_amount
                vat_amount = mul_d(total_amount, div(self.vat_rate.percentage, 100))
                total_amount += vat_amount

                contract.total_amount -= self.vat_amount
                contract.vat_amount -= self.vat_amount

                self.vat_amount = vat_amount
                self.total_amount = total_amount

                contract.total_amount += self.vat_amount
                contract.vat_amount += self.vat_amount
            else:
                self.vat_rate = self.vat_rate.successor_vat_rate
                self.vat_amount = 0
                vat_amount = 0

        if days_period != days_invoicing and self.contract.pricing_type == Contract.PERIOD:
            vat_amount = mul_f(vat_amount, days_invoicing / days_period)
            if base_amount:
                base_amount = mul_f(base_amount, days_invoicing / days_period)
                total_amount = base_amount + vat_amount
            if unit_amount:
                unit_amount = mul_f(unit_amount, days_invoicing / days_period)
                total_amount = mul_d(unit_amount, self.number_of_units) + vat_amount

        if self.contract.pricing_type == Contract.DAY:
            if base_amount:
                base_amount *= days_invoicing
            if unit_amount:
                unit_amount *= days_invoicing
            vat_amount *= days_invoicing
            total_amount *= days_invoicing

        if is_ending:
            contract.remove_component(self)
            self.date_next_prolongation = None
        else:
            self.date_next_prolongation = contract.date_next_prolongation

        self.create_invoice_line(
            next_id, invoice, base_amount, vat_amount,
            total_amount, unit_amount,
            new_invoice_lines, new_gl_posts
        )


class ContractPerson(TenancyDependentModel):
    """A contract contains one or more contract persons."""
    DIRECT_DEBIT = 'D'
    EMAIL = 'E'
    SMS = 'S'
    LETTER = 'L'
    INVOICE = 'I'

    PAYMENT_METHOD_CHOICES = [
        (DIRECT_DEBIT, 'direct debit'),
        (EMAIL, 'email'),
        (SMS, 'sms'),
        (LETTER, 'letter'),
        (INVOICE, 'invoice')
    ]

    contract_person_id = models.AutoField(primary_key=True)
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE)
    type = models.CharField(max_length=1, null=True, default=None)
    start_date = models.DateField(null=True, default=None)
    end_date = models.DateField(null=True, blank=True, default=None)
    name = models.CharField(max_length=50, null=True, default=None)
    address = models.CharField(max_length=50, null=True, default=None)
    city = models.CharField(max_length=50, null=True, default=None)
    payment_method = models.CharField(
        max_length=1,
        choices=PAYMENT_METHOD_CHOICES,
        default=INVOICE
    )
    iban = models.CharField(max_length=17, null=True, blank=True, default=None)
    mandate = models.PositiveIntegerField(null=True, blank=True, default=None)
    email = models.EmailField(null=True, default=None)
    phone = models.CharField(max_length=15, null=True, default=None)
    percentage_of_total = models.DecimalField(max_digits=5, decimal_places=2)
    payment_day = models.PositiveIntegerField(null=True, default=1)

    def __str__(self):
        return "contract person " + self.name

    def can_delete(self):
        return not self.collection_set.exists()

    def invoice(self, tenancy, invoice, new_collections):
        """Create collection objects when the invoice has been finished."""
        new_collections.append(
            Collection(
                tenancy=tenancy,
                contract_person=self,
                invoice=invoice,
                payment_method=self.payment_method,
                payment_day=self.payment_day,
                mandate=self.mandate,
                iban=self.iban,
                amount=(self.percentage_of_total / 100) * invoice.total_amount
            )
        )


class Invoice(TenancyDependentModel):
    invoice_id = models.PositiveIntegerField(primary_key=True)
    # Ask if this should cascade
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE)
    external_customer_id = models.PositiveIntegerField()
    description = models.CharField(max_length=50)
    base_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    vat_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    date = models.DateField()
    expiration_date = models.DateField()
    invoice_number = models.PositiveIntegerField()
    gl_account = models.CharField(max_length=10)

    def get_invoice_lines(self):
        return self.invoiceline_set.all()

    def get_collections(self):
        return self.collection_set.select_related('contract_person')

    def create_gl_post(self, new_gl_posts):
        new_gl_posts.append(
            GeneralLedgerPost(
                tenancy=self.tenancy,
                invoice=self,
                invoice_line=None,
                date=self.date,
                gl_account=self.gl_account,
                gl_dimension_base_component=None,
                gl_dimension_contract_1=self.contract.gl_dimension_1,
                gl_dimension_contract_2=self.contract.gl_dimension_2,
                gl_dimension_vat=None,
                description="Debtors",
                amount_debit=self.total_amount,
                amount_credit=0.0
            )
        )


class InvoiceLine(models.Model):
    invoice_line_id = models.PositiveIntegerField(primary_key=True)
    component = models.ForeignKey(Component, on_delete=models.CASCADE)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE)
    description = models.CharField(max_length=50)
    vat_type = models.PositiveIntegerField(null=True)
    base_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True)
    vat_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    gl_account = models.CharField(max_length=10)
    gl_dimension_base_component = models.CharField(max_length=10)
    gl_dimension_contract_1 = models.CharField(max_length=10)
    gl_dimension_contract_2 = models.CharField(max_length=10)
    gl_dimension_vat = models.CharField(max_length=10, null=True)
    unit_price = models.DecimalField(max_digits=15, decimal_places=2, null=True)
    unit_id = models.CharField(max_length=10, null=True)
    number_of_units = models.DecimalField(max_digits=15, decimal_places=2, null=True)

    def create_gl_posts(self, new_gl_posts):
        total_without_vat = self.total_amount - self.vat_amount
        if total_without_vat:
            new_gl_posts.append(
                GeneralLedgerPost(
                    tenancy=self.invoice.tenancy,
                    invoice=None,  # This could be changed to invoice in needed
                    invoice_line=self,
                    date=self.invoice.date,
                    gl_account=self.gl_account,
                    gl_dimension_base_component=self.gl_dimension_base_component,
                    gl_dimension_contract_1=self.gl_dimension_contract_1,
                    gl_dimension_contract_2=self.gl_dimension_contract_2,
                    gl_dimension_vat=None,
                    description="Proceeds",
                    amount_credit=total_without_vat,
                    amount_debit=0.0
                )
            )

        # Only create a post for the general ledger for the VAT if applicable
        if self.vat_type:
            new_gl_posts.append(
                GeneralLedgerPost(
                    tenancy=self.invoice.tenancy,
                    invoice=None,
                    invoice_line=self,
                    date=self.invoice.date,
                    gl_account=self.component.vat_rate.gl_account,
                    gl_dimension_base_component=self.gl_dimension_base_component,
                    gl_dimension_contract_1=self.gl_dimension_contract_1,
                    gl_dimension_contract_2=self.gl_dimension_contract_2,
                    gl_dimension_vat=self.gl_dimension_vat,
                    description="VAT",
                    amount_credit=self.vat_amount,
                    amount_debit=0.0
                )
            )


class Collection(TenancyDependentModel):
    contract_person = models.ForeignKey(
        ContractPerson, on_delete=models.CASCADE
    )
    # Ask if this should cascade
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE)
    payment_method = models.CharField(max_length=1)
    payment_day = models.PositiveIntegerField()
    mandate = models.PositiveIntegerField(null=True)
    iban = models.CharField(max_length=17, null=True)
    amount = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    def get_values_external_file(self):
        return [
            self.contract_person.name,
            self.contract_person.address,
            self.contract_person.city,
            self.payment_method,
            self.payment_day,
            self.invoice.invoice_number,
            self.invoice.date,
            self.contract_person.contract_id,
            self.invoice_id,
            self.amount,
            self.mandate,
            self.iban,
            self.contract_person.email,
            self.contract_person.phone
        ]


class GeneralLedgerPost(TenancyDependentModel):
    invoice = models.ForeignKey(Invoice, null=True, on_delete=models.CASCADE)
    invoice_line = models.ForeignKey(
        InvoiceLine, null=True, on_delete=models.CASCADE
    )
    date = models.DateField()
    gl_account = models.CharField(max_length=10)
    gl_dimension_base_component = models.CharField(null=True, max_length=10)
    gl_dimension_contract_1 = models.CharField(max_length=10)
    gl_dimension_contract_2 = models.CharField(max_length=10)
    gl_dimension_vat = models.CharField(null=True, max_length=10)
    description = models.CharField(max_length=30)
    amount_debit = models.DecimalField(max_digits=15, decimal_places=2)
    amount_credit = models.DecimalField(max_digits=15, decimal_places=2)
