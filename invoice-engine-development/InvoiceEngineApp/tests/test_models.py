from django.test import TestCase
from InvoiceEngineApp.models import *
from model_bakery import baker
import datetime


class TenancyTest(TestCase):
    def setUp(self):
        self.tenancy = baker.make(Tenancy)
        self.name = str(self.tenancy)

    def test_creation(self):
        # print(self.tenancy.get_details())
        self.assertEqual(self.name, str(self.tenancy))
        self.assertIsNone(self.tenancy.date_next_prolongation)
        self.assertEqual(Tenancy.objects.all().count(), 1)
        self.assertEqual(self.tenancy.days_until_invoice_expiration, 14)
        self.assertEqual(self.tenancy.number_of_contracts, 0)
        self.assertEqual(self.tenancy.last_invoice_number, 0)

    def test_update(self):
        obj = Tenancy.objects.get(company_id=self.tenancy.company_id)
        obj.date_next_prolongation = datetime.date(2021, 10, 13)
        obj.days_until_invoice_expiration = 134
        obj.save()

        self.assertNotEqual(self.tenancy.date_next_prolongation, obj.date_next_prolongation)
        self.assertNotEqual(self.tenancy.days_until_invoice_expiration, obj.days_until_invoice_expiration)
        self.assertEqual(Tenancy.objects.count(), 1)

    def test_delete(self):
        obj = Tenancy.objects.get(company_id=self.tenancy.company_id)
        obj.delete()
        obj = Tenancy.objects.filter(company_id=self.tenancy.company_id)
        self.assertEqual(len(obj), 0)


class ContractTypeTest(TestCase):
    def setUp(self):
        self.contracttype = baker.make(
            ContractType,
            code=3,
            description='A description',
            gl_debit='Debit',
            gl_credit='Credit',
        )

    def test_creation(self):
        self.assertEqual(self.contracttype.code, 3)
        self.assertEqual(self.contracttype.description, 'A description')
        self.assertEqual(self.contracttype.gl_debit, 'Debit')
        self.assertEqual(self.contracttype.gl_credit, 'Credit')
        self.assertEqual(ContractType.objects.all().count(), 1)

    def test_delete(self):
        obj = ContractType.objects.get(contract_type_id=self.contracttype.contract_type_id)
        obj.delete()
        obj = ContractType.objects.filter(contract_type_id=self.contracttype.contract_type_id)
        self.assertEqual(len(obj), 0)

    def test_update(self):
        obj = ContractType.objects.get(contract_type_id=self.contracttype.contract_type_id)
        obj.code = 4
        obj.description = 'description'
        obj.gl_debit = 'UpCredit'
        obj.gl_credit = 'credit'

        obj.save()

        self.assertNotEqual(obj.description, self.contracttype.description)
        self.assertNotEqual(obj.gl_debit, self.contracttype.gl_debit)
        self.assertNotEqual(obj.gl_credit, self.contracttype.gl_credit)
        self.assertEqual(ContractType.objects.count(), 1)


class BaseComponentTest(TestCase):
    def setUp(self):
        self.base_component = baker.make(
            BaseComponent,
            code=23,
            description='This is a test description',
            gl_debit='Debit',
            gl_credit='Credit',
            gl_dimension='Dimension',
            unit_id=None
        )

    def test_creation(self):
        self.assertEqual(self.base_component.code, 23)
        self.assertEqual(self.base_component.description, 'This is a test description')
        self.assertEqual(self.base_component.gl_debit, 'Debit')
        self.assertEqual(self.base_component.gl_credit, 'Credit')
        self.assertEqual(self.base_component.gl_dimension, 'Dimension')
        self.assertIsNone(self.base_component.unit_id)
        self.assertEqual(Tenancy.objects.all().count(), 1)

    def test_delete(self):
        obj = BaseComponent.objects.get(base_component_id=self.base_component.base_component_id)
        obj.delete()
        obj = BaseComponent.objects.filter(base_component_id=self.base_component.base_component_id)
        self.assertEqual(len(obj), 0)

    def test_update(self):
        obj = BaseComponent.objects.get(base_component_id=self.base_component.base_component_id)
        obj.code = 214
        obj.description = "Update Description"
        obj.gl_debit = "UpdateDe"
        obj.gl_credit = "UpdateC"
        obj.gl_dimension = "UpdateD"
        obj.unit_id = "10"

        obj.save()

        self.assertNotEqual(obj.description, self.base_component.description)
        self.assertNotEqual(obj.gl_debit, self.base_component.gl_debit)
        self.assertNotEqual(obj.gl_credit, self.base_component.gl_credit)
        self.assertNotEqual(obj.gl_dimension, self.base_component.gl_dimension)
        self.assertNotEqual(obj.unit_id, self.base_component.unit_id)
        self.assertEqual(BaseComponent.objects.count(), 1)


class VATRateTest(TestCase):
    def setUp(self):
        self.vatrate = baker.make(
            VATRate,
            type=5,
            description='VATRate description',
            start_date=datetime.date(2021, 5, 24),
            end_date=None,
            percentage=9.0,
            gl_account='Account',
            gl_dimension='Dimension',
        )

    def test_creation(self):
        self.assertEqual(self.vatrate.type, 5)
        self.assertEqual(self.vatrate.description, 'VATRate description')
        self.assertEqual(self.vatrate.start_date, datetime.date(2021, 5, 24))
        self.assertIsNone(self.vatrate.end_date)
        self.assertEqual(self.vatrate.percentage, 9.0)
        self.assertEqual(self.vatrate.gl_account, 'Account')
        self.assertEqual(self.vatrate.gl_dimension, 'Dimension')
        self.assertEqual(Tenancy.objects.all().count(), 1)

    def test_delete(self):
        obj = VATRate.objects.get(vat_rate_id=self.vatrate.vat_rate_id)
        obj.delete()
        obj = VATRate.objects.filter(vat_rate_id=self.vatrate.vat_rate_id)
        self.assertEqual(len(obj), 0)

    def test_update(self):
        obj = VATRate.objects.get(vat_rate_id=self.vatrate.vat_rate_id)
        obj.type = 6
        obj.description = 'VATRate test description'
        obj.start_date = datetime.date(2021, 8, 24)
        obj.end_date = datetime.date(2022, 5, 20)
        obj.percentage = 21.0
        obj.gl_account = 'account'
        obj.gl_dimension = 'dimension'

        obj.save()

        self.assertNotEqual(obj.description, self.vatrate.description)
        self.assertNotEqual(obj.start_date, self.vatrate.start_date)
        self.assertNotEqual(obj.end_date, self.vatrate.end_date)
        self.assertNotEqual(obj.percentage, self.vatrate.percentage)
        self.assertNotEqual(obj.gl_account, self.vatrate.gl_account)
        self.assertNotEqual(obj.gl_dimension, self.vatrate.gl_dimension)
        self.assertEqual(VATRate.objects.count(), 1)


class ContractTest(TestCase):
    def setUp(self):
        self.contract = baker.make(
            Contract,
            invoicing_period='M',
            invoicing_amount_of_days=31,
            external_customer_id=1,
            start_date=datetime.date(2021, 5, 26),
            end_date=datetime.date(2025, 5, 26),
            date_prev_prolongation=datetime.date(2021, 5, 26),
            date_next_prolongation=datetime.date(2021, 6, 26),
            balance=1500.0,
            base_amount=500.0,
            vat_amount=120.0,
            total_amount=2320,
            gl_dimension_1='Dimension1',
            gl_dimension_2='Dimension2',
            status='A',
            termination_date=datetime.date(2027, 5, 26)
        )

    def test_creation(self):
        self.assertEqual(self.contract.external_customer_id, 1)
        self.assertEqual(self.contract.status, 'A')
        self.assertEqual(self.contract.invoicing_period, 'M')
        self.assertEqual(self.contract.invoicing_amount_of_days, 31)
        self.assertEqual(self.contract.start_date, datetime.date(2021, 5, 26))
        self.assertEqual(self.contract.end_date, datetime.date(2025, 5, 26))
        self.assertEqual(self.contract.termination_date, datetime.date(2027, 5, 26))
        self.assertEqual(self.contract.date_prev_prolongation, datetime.date(2021, 5, 26))
        self.assertEqual(self.contract.date_next_prolongation, datetime.date(2021, 6, 26))
        self.assertEqual(self.contract.gl_dimension_1, 'Dimension1')
        self.assertEqual(self.contract.gl_dimension_2, 'Dimension2')
        self.assertEqual(self.contract.balance, 1500.0)
        self.assertEqual(self.contract.base_amount, 500.0)
        self.assertEqual(self.contract.vat_amount, 120.0)
        self.assertEqual(self.contract.total_amount, 2320)
        self.assertEqual(Contract.objects.count(), 1)

    def test_delete(self):
        self.assertEqual(Contract.objects.all().count() - 1, 0)

    def test_update(self):
        obj = Contract.objects.get(contract_id=self.contract.contract_id)
        obj.external_customer_id = 3
        obj.status = 'T'
        obj.invoicing_period = 'Q'
        obj.invoicing_amount_of_days = 15
        obj.start_date = datetime.date(2021, 5, 28)
        obj.end_date = datetime.date(2025, 5, 22)
        obj.termination_date = datetime.date(2027, 4, 26)
        obj.date_prev_prolongation = datetime.date(2021, 5, 28)
        obj.date_next_prolongation = datetime.date(2021, 6, 12)
        obj.gl_dimension_1 = 'dimension1'
        obj.gl_dimension_2 = 'dimension2'
        obj.balance = 1000.0
        obj.base_amount = 400.0
        obj.vat_amount = 20.0
        obj.total_amount = 1420

        obj.save()

        self.assertNotEqual(obj.external_customer_id, self.contract.external_customer_id)
        self.assertNotEqual(obj.status, self.contract.status)
        self.assertNotEqual(obj.invoicing_period, self.contract.invoicing_period)
        self.assertNotEqual(obj.invoicing_amount_of_days, self.contract.invoicing_amount_of_days)
        self.assertNotEqual(obj.start_date, self.contract.start_date)
        self.assertNotEqual(obj.end_date, self.contract.end_date)
        self.assertNotEqual(obj.termination_date, self.contract.termination_date)
        self.assertNotEqual(obj.date_prev_prolongation, self.contract.date_prev_prolongation)
        self.assertNotEqual(obj.date_next_prolongation, self.contract.date_next_prolongation)
        self.assertNotEqual(obj.gl_dimension_1, self.contract.gl_dimension_1)
        self.assertNotEqual(obj.gl_dimension_2, self.contract.gl_dimension_2)
        self.assertNotEqual(obj.balance, self.contract.balance)
        self.assertNotEqual(obj.base_amount, self.contract.base_amount)
        self.assertNotEqual(obj.vat_amount, self.contract.vat_amount)
        self.assertNotEqual(obj.total_amount, self.contract.total_amount)
        self.assertEqual(Contract.objects.all().count(), 1)


class ComponentTest(TestCase):
    def setUp(self):
        self.component = baker.make(
            Component,
            description='This is a description',
            start_date=datetime.date(2021, 5, 24),
            end_date=None,
            date_prev_prolongation=None,
            date_next_prolongation=datetime.date(2021, 8, 24),
            base_amount=25.0,
            vat_amount=9.0,
            total_amount=156.6,
            unit_id=None,
            unit_amount=None,
            number_of_units=None,
        )

    def test_creation(self):
        self.assertEqual(self.component.description, 'This is a description')
        self.assertEqual(self.component.start_date, datetime.date(2021, 5, 24))
        self.assertIsNone(self.component.end_date)
        self.assertIsNone(self.component.date_prev_prolongation)
        self.assertEqual(self.component.date_next_prolongation, datetime.date(2021, 8, 24))
        self.assertEqual(self.component.base_amount, 25.0)
        self.assertEqual(self.component.vat_amount, 9.0)
        self.assertEqual(self.component.total_amount, 156.6)
        self.assertIsNone(self.component.unit_id)
        self.assertIsNone(self.component.unit_amount)
        self.assertIsNone(self.component.number_of_units)
        self.assertEqual(Component.objects.all().count(), 1)

    def test_delete(self):
        obj = Component.objects.get(component_id=self.component.component_id)
        obj.delete()
        obj = Component.objects.filter(component_id=self.component.component_id)
        self.assertEqual(len(obj), 0)

    def test_update(self):
        obj = Component.objects.get(component_id=self.component.component_id)
        obj.description = 'A description'
        obj.start_date = datetime.date(2021, 8, 26)
        obj.end_date = datetime.date(2025, 5, 24)
        obj.date_prev_prolongation = datetime.date(2021, 6, 25)
        obj.date_next_prolongation = datetime.date(2021, 8, 25)
        obj.base_amount = 23.0
        obj.vat_amount = 21.0
        obj.total_amount = 1346
        obj.unit_id = 'F'
        obj.unit_amount = 120
        obj.number_of_units = 10

        obj.save()

        self.assertNotEqual(obj.description, self.component.description)
        self.assertNotEqual(obj.start_date, self.component.start_date)
        self.assertNotEqual(obj.end_date, self.component.end_date)
        self.assertNotEqual(obj.date_prev_prolongation, self.component.date_prev_prolongation)
        self.assertNotEqual(obj.date_next_prolongation, self.component.date_next_prolongation)
        self.assertNotEqual(obj.base_amount, self.component.base_amount)
        self.assertNotEqual(obj.vat_amount, self.component.vat_amount)
        self.assertNotEqual(obj.total_amount, self.component.total_amount)
        self.assertNotEqual(obj.unit_id, self.component.unit_id)
        self.assertNotEqual(obj.unit_amount, self.component.unit_amount)
        self.assertNotEqual(obj.number_of_units, self.component.number_of_units)
        self.assertEqual(Component.objects.count(), 1)


class ContractPersonTest(TestCase):
    def setUp(self):
        self.contract_person = baker.make(
            ContractPerson,
            type='A',
            start_date=datetime.date(2021, 5, 26),
            end_date=None,
            name='Tom',
            address='Somewhere on the earth',
            city='Gotham city',
            payment_method='D',
            iban='IBAN 1234 5678',
            mandate=None,
            email='Tom@email.com',
            percentage_of_total=59.3,
            payment_day=31
        )

    def test_creation(self):
        self.assertEqual(self.contract_person.type, 'A')
        self.assertEqual(self.contract_person.start_date, datetime.date(2021, 5, 26))
        self.assertIsNone(self.contract_person.end_date)
        self.assertEqual(self.contract_person.name, 'Tom')
        self.assertEqual(self.contract_person.address, 'Somewhere on the earth')
        self.assertEqual(self.contract_person.city, 'Gotham city')
        self.assertEqual(self.contract_person.payment_method, 'D')
        self.assertEqual(self.contract_person.iban, 'IBAN 1234 5678')
        self.assertIsNone(self.contract_person.mandate)
        self.assertEqual(self.contract_person.email, 'Tom@email.com')
        self.assertEqual(self.contract_person.percentage_of_total, 59.3)
        self.assertEqual(self.contract_person.payment_day, 31)
        self.assertEqual(ContractPerson.objects.all().count(), 1)

    def test_delete(self):
        obj = ContractPerson.objects.get(contract_person_id=self.contract_person.contract_person_id)
        obj.delete()
        obj = ContractPerson.objects.filter(contract_person_id=self.contract_person.contract_person_id)
        self.assertEqual(len(obj), 0)

    def test_update(self):
        obj = ContractPerson.objects.get(contract_person_id=self.contract_person.contract_person_id)
        obj.type = 'B'
        obj.start_date = datetime.date(2021, 5, 27)
        obj.end_date = datetime.date(2025, 5, 27)
        obj.name = 'Mike'
        obj.address = 'Somewhere'
        obj.city = 'city'
        obj.payment_method = 'E'
        obj.iban = 'IBAN 5678 1234'
        obj.mandate = 2
        obj.email = 'Mike@email.com'
        obj.percentage_of_total = 60.0
        obj.payment_day = 32

        obj.save()

        self.assertNotEqual(obj.type, self.contract_person.type)
        self.assertNotEqual(obj.start_date, self.contract_person.start_date)
        self.assertNotEqual(obj.end_date, self.contract_person.end_date)
        self.assertNotEqual(obj.name, self.contract_person.name)
        self.assertNotEqual(obj.address, self.contract_person.address)
        self.assertNotEqual(obj.city, self.contract_person.city)
        self.assertNotEqual(obj.payment_method, self.contract_person.payment_method)
        self.assertNotEqual(obj.iban, self.contract_person.iban)
        self.assertNotEqual(obj.mandate, self.contract_person.mandate)
        self.assertNotEqual(obj.email, self.contract_person.email)
        self.assertNotEqual(obj.percentage_of_total, self.contract_person.percentage_of_total)
        self.assertNotEqual(obj.payment_day, self.contract_person.payment_day)
        self.assertEqual(ContractPerson.objects.count(), 1)


class InvoiceTest(TestCase):
    def setUp(self):
        self.invoice = baker.make(
            Invoice,
            external_customer_id=10,
            description='A description',
            base_amount=1500.0,
            vat_amount=9.0,
            total_amount=2000,
            balance=3000,
            date=datetime.date(2021, 5, 26),
            expiration_date=datetime.date(2022, 5, 26),
            invoice_number=1600,
            gl_account='account'
        )

    def test_creation(self):
        self.assertEqual(self.invoice.external_customer_id, 10)
        self.assertEqual(self.invoice.description, 'A description')
        self.assertEqual(self.invoice.base_amount, 1500.0)
        self.assertEqual(self.invoice.vat_amount, 9.0)
        self.assertEqual(self.invoice.total_amount, 2000)
        self.assertEqual(self.invoice.balance, 3000)
        self.assertEqual(self.invoice.date, datetime.date(2021, 5, 26))
        self.assertEqual(self.invoice.expiration_date, datetime.date(2022, 5, 26))
        self.assertEqual(self.invoice.invoice_number, 1600)
        self.assertEqual(self.invoice.gl_account, 'account')
        self.assertEqual(Invoice.objects.all().count(), 1)

    def test_delete(self):
        obj = Invoice.objects.get(invoice_id=self.invoice.invoice_id)
        obj.delete()
        obj = Invoice.objects.filter(invoice_id=self.invoice.invoice_id)
        self.assertEqual(len(obj), 0)

    def test_update(self):
        obj = Invoice.objects.get(invoice_id=self.invoice.invoice_id)
        obj.external_customer_id = 9
        obj.description = 'Description'
        obj.base_amount = 2500.0
        obj.vat_amount = 21.0
        obj.total_amount = 4000
        obj.balance = 5000
        obj.date = datetime.date(2021, 5, 27)
        obj.expiration_date = datetime.date(2022, 5, 27)
        obj.invoice_number = 1500
        obj.gl_account = 'An Account'

        obj.save()

        self.assertNotEqual(obj.external_customer_id, self.invoice.external_customer_id)
        self.assertNotEqual(obj.description, self.invoice.description)
        self.assertNotEqual(obj.base_amount, self.invoice.base_amount)
        self.assertNotEqual(obj.vat_amount, self.invoice.vat_amount)
        self.assertNotEqual(obj.total_amount, self.invoice.total_amount)
        self.assertNotEqual(obj.balance, self.invoice.balance)
        self.assertNotEqual(obj.date, self.invoice.date)
        self.assertNotEqual(obj.expiration_date, self.invoice.expiration_date)
        self.assertNotEqual(obj.invoice_number, self.invoice.invoice_number)
        self.assertNotEqual(obj.gl_account, self.invoice.gl_account)
        self.assertEqual(Invoice.objects.count(), 1)


class InvoiceLineTest(TestCase):
    def setUp(self):
        self.invoice_line = baker.make(
            InvoiceLine,
            description='This is a description',
            vat_type=None,
            base_amount=1200.0,
            vat_amount=200.2,
            total_amount=4000.0,
            gl_account='Account',
            gl_dimension_base_component='Component',
            gl_dimension_contract_1='Contract1',
            gl_dimension_contract_2='Contract2',
            gl_dimension_vat=None,
            unit_price=None,
            unit_id=None,
            number_of_units=None,
        )


    def test_creation(self):
        self.assertEqual(self.invoice_line.description, 'This is a description')
        self.assertIsNone(self.invoice_line.vat_type)
        self.assertEqual(self.invoice_line.base_amount, 1200.0)
        self.assertEqual(self.invoice_line.vat_amount, 200.2)
        self.assertEqual(self.invoice_line.total_amount, 4000.0)
        self.assertEqual(self.invoice_line.gl_account, 'Account')
        self.assertEqual(self.invoice_line.gl_dimension_base_component, 'Component')
        self.assertEqual(self.invoice_line.gl_dimension_contract_1, 'Contract1')
        self.assertEqual(self.invoice_line.gl_dimension_contract_2, 'Contract2')
        self.assertIsNone(self.invoice_line.gl_dimension_vat)
        self.assertIsNone(self.invoice_line.unit_price)
        self.assertIsNone(self.invoice_line.unit_id)
        self.assertIsNone(self.invoice_line.number_of_units)
        self.assertEqual(InvoiceLine.objects.all().count(), 1)

    def test_delete(self):
        obj = InvoiceLine.objects.get(invoice_line_id=self.invoice_line.invoice_line_id)
        obj.delete()
        obj = InvoiceLine.objects.filter(invoice_line_id=self.invoice_line.invoice_line_id)
        self.assertEqual(len(obj), 0)

    def test_update(self):
        obj = InvoiceLine.objects.get(invoice_line_id=self.invoice_line.invoice_line_id)
        obj.description = 'A description'
        obj.vat_type = 2
        obj.base_amount = 1800.0
        obj.vat_amount = 300.2
        obj.total_amount = 5000.0
        obj.gl_account = 'account'
        obj.gl_dimension_base_component = 'component'
        obj.gl_dimension_contract_1 = 'contract1'
        obj.gl_dimension_contract_2 = 'contract2'
        obj.gl_dimension_vat = 'DiVAT'
        obj.unit_price = 200
        obj.unit_id = 'Unit'
        obj.number_of_units = 100

        obj.save()

        self.assertNotEqual(obj.description, self.invoice_line.description)
        self.assertNotEqual(obj.vat_type, self.invoice_line.vat_type)
        self.assertNotEqual(obj.base_amount, self.invoice_line.base_amount)
        self.assertNotEqual(obj.vat_amount, self.invoice_line.vat_amount)
        self.assertNotEqual(obj.total_amount, self.invoice_line.total_amount)
        self.assertNotEqual(obj.gl_account, self.invoice_line.gl_account)
        self.assertNotEqual(obj.gl_dimension_base_component,
                            self.invoice_line.gl_dimension_base_component)
        self.assertNotEqual(obj.gl_dimension_contract_1,
                            self.invoice_line.gl_dimension_contract_1)
        self.assertNotEqual(obj.gl_dimension_contract_2,
                            self.invoice_line.gl_dimension_contract_2)
        self.assertNotEqual(obj.gl_dimension_vat, self.invoice_line.gl_dimension_vat)
        self.assertNotEqual(obj.unit_price, self.invoice_line.unit_price)
        self.assertNotEqual(obj.unit_id, self.invoice_line.unit_id)
        self.assertNotEqual(obj.number_of_units, self.invoice_line.number_of_units)
        self.assertEqual(InvoiceLine.objects.count(), 1)
