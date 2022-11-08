import datetime as dt
import decimal as dc

from django.test import TestCase
from InvoiceEngineApp.models import Contract, Invoice, InvoiceLine, Collection, \
    GeneralLedgerPost
from model_bakery import baker


class ContractMethodsTest(TestCase):
    def setUp(self):
        self.contract = baker.make(
            'Contract'
        )

    def test_compute_date_next_prolongation(self):
        # Test month
        self.contract.invoicing_period = Contract.MONTH
        date = self.contract.compute_date_next_prolongation(
            dt.date(2020, 1, 31)
        )
        self.assertEqual(date, dt.date(2020, 2, 29))

        date = self.contract.compute_date_next_prolongation(
            dt.date(2020, 8, 4)
        )
        self.assertEqual(date, dt.date(2020, 9, 4))

        # Test quarter
        self.contract.invoicing_period = Contract.QUARTER
        date = self.contract.compute_date_next_prolongation(
            dt.date(2020, 1, 31)
        )
        self.assertEqual(date, dt.date(2020, 4, 30))

        # Test half year
        self.contract.invoicing_period = Contract.HALF_YEAR
        date = self.contract.compute_date_next_prolongation(
            dt.date(2020, 1, 31)
        )
        self.assertEqual(date, dt.date(2020, 7, 31))

        # Test year
        self.contract.invoicing_period = Contract.YEAR
        date = self.contract.compute_date_next_prolongation(
            dt.date(2020, 2, 29)
        )
        self.assertEqual(date, dt.date(2021, 2, 28))

        # Test custom
        self.contract.invoicing_period = Contract.CUSTOM
        self.contract.invoicing_amount_of_days = 13
        date = self.contract.compute_date_next_prolongation(
            dt.date(2020, 1, 31)
        )
        self.assertEqual(date, dt.date(2020, 2, 13))


class ComponentMethodsTest(TestCase):
    def setUp(self):
        self.component = baker.make(
            'Component',
            contract__invoicing_period=Contract.MONTH,
            contract__start_date=dt.date(2020, 1, 1),
            contract__end_date=None,
            contract__date_next_prolongation=dt.date(2021, 5, 1),
            contract__date_prev_prolongation=dt.date(2021, 4, 1),
            vat_rate__start_date=dt.date(2020, 1, 1),
            vat_rate__end_date=None,
            vat_rate__percentage=dc.Decimal(20),
            vat_rate__type=25,
            date_next_prolongation=dt.date(2021, 4, 1),
            date_prev_prolongation=dt.date(2021, 3, 1),
            start_date=dt.date(2020, 1, 1),
            end_date=dt.date(2021, 10, 1),
            base_amount=dc.Decimal(50),
            vat_amount=dc.Decimal(10),
            total_amount=dc.Decimal(60),
            unit_id=None,
            unit_amount=None,
            number_of_units=None
        )

    def test_invoice_normal(self):
        """Method to test whether the output of the invoice() method of the
        Component class is correct. The output consists of one invoice line,
        and one or more GeneralLedgerPosts. The method also changes the
        component and the invoice passed to the method.
        """
        # Test a normal period (no start or end during the period)
        invoice = baker.make(
            'Invoice',
            tenancy=self.component.tenancy,
            contract=self.component.contract
        )
        new_gl_posts = []
        new_invoice_lines = []
        self.component.invoice(
            next_id=1,
            invoice=invoice,
            new_invoice_lines=new_invoice_lines,
            new_gl_posts=new_gl_posts
        )

        # Check if the Invoice was updated correctly
        self.assertEqual(invoice.base_amount, 50)
        self.assertEqual(invoice.vat_amount, 10)
        self.assertEqual(invoice.total_amount, 60)
        self.assertEqual(invoice.balance, 60)

        # Check if the Contract was updated correctly
        self.assertEqual(invoice.contract.balance, 60)

        # Check if the InvoiceLine is correct
        self.assertEqual(new_invoice_lines.__len__(), 1)
        invoice_line = new_invoice_lines[0]
        self.assertEqual(invoice_line.base_amount, 50)
        self.assertEqual(invoice_line.vat_amount, 10)
        self.assertEqual(invoice_line.total_amount, 60)
        self.assertIsNone(invoice_line.unit_price)
        self.assertEqual(invoice_line.vat_type, 25)

        # Check if the GeneralLedgerPosts are correct
        normal_gl_post = new_gl_posts[0]
        vat_gl_post = new_gl_posts[1]
        self.assertEqual(normal_gl_post.amount_credit, 50)
        self.assertEqual(vat_gl_post.amount_credit, 10)

        self.assertEqual(self.component.date_next_prolongation, dt.date(2021, 5, 1))

    def test_invoice_no_VAT(self):
        """Method to test the invoice() method of the Component class.
        The scenario is a component which does not have an associated VAT rate.
        """
        self.component.vat_rate = None
        self.component.vat_amount = 0
        self.component.total_amount = dc.Decimal('50')
        invoice = baker.make(
            'Invoice',
            tenancy=self.component.tenancy,
            contract=self.component.contract
        )
        new_gl_posts = []
        new_invoice_lines = []
        self.component.invoice(
            next_id=1,
            invoice=invoice,
            new_invoice_lines=new_invoice_lines,
            new_gl_posts=new_gl_posts
        )

        # Check if the Invoice was updated correctly
        self.assertEqual(invoice.base_amount, 50)
        self.assertEqual(invoice.vat_amount, 0)
        self.assertEqual(invoice.total_amount, 50)
        self.assertEqual(invoice.balance, 50)

        # Check if the Contract was updated correctly
        self.assertEqual(invoice.contract.balance, 50)

        # Check if the InvoiceLine is correct
        self.assertEqual(new_invoice_lines.__len__(), 1)
        invoice_line = new_invoice_lines[0]
        self.assertEqual(invoice_line.base_amount, 50)
        self.assertEqual(invoice_line.vat_amount, 0)
        self.assertEqual(invoice_line.total_amount, 50)
        self.assertIsNone(invoice_line.unit_price)
        self.assertIsNone(invoice_line.vat_type)

        # Check if the GeneralLedgerPosts are correct
        self.assertEqual(new_gl_posts.__len__(), 1)
        normal_gl_post = new_gl_posts[0]
        self.assertEqual(normal_gl_post.amount_credit, 50)

        self.assertEqual(self.component.date_next_prolongation, dt.date(2021, 5, 1))

    def test_invoice_unit(self):
        """Method to test the invoice() method of the Component class.
        The scenario is a component which uses unit amount.
        """
        self.component.base_amount = None
        self.component.unit_amount = dc.Decimal('25')
        self.component.number_of_units = dc.Decimal('2')
        self.component.unit_id = '105'
        invoice = baker.make(
            'Invoice',
            tenancy=self.component.tenancy,
            contract=self.component.contract
        )
        new_gl_posts = []
        new_invoice_lines = []
        self.component.invoice(
            next_id=1,
            invoice=invoice,
            new_invoice_lines=new_invoice_lines,
            new_gl_posts=new_gl_posts
        )

        # Check if the Invoice was updated correctly
        self.assertEqual(invoice.base_amount, 50)
        self.assertEqual(invoice.vat_amount, 10)
        self.assertEqual(invoice.total_amount, 60)
        self.assertEqual(invoice.balance, 60)

        # Check if the Contract was updated correctly
        self.assertEqual(invoice.contract.balance, 60)

        # Check if the InvoiceLine is correct
        self.assertEqual(new_invoice_lines.__len__(), 1)
        invoice_line = new_invoice_lines[0]
        self.assertIsNone(invoice_line.base_amount)
        self.assertEqual(invoice_line.vat_amount, 10)
        self.assertEqual(invoice_line.total_amount, 60)
        self.assertEqual(invoice_line.unit_price, 25)
        self.assertEqual(invoice_line.vat_type, 25)

        # Check if the GeneralLedgerPosts are correct
        normal_gl_post = new_gl_posts[0]
        vat_gl_post = new_gl_posts[1]
        self.assertEqual(normal_gl_post.amount_credit, 50)
        self.assertEqual(vat_gl_post.amount_credit, 10)

        self.assertEqual(self.component.date_next_prolongation, dt.date(2021, 5, 1))

    def test_invoice_start(self):
        """Method to test the invoice() method of the Component class.
        The scenario is a component that starts halfway through a period.
        """
        invoice = baker.make(
            'Invoice',
            tenancy=self.component.tenancy,
            contract=self.component.contract
        )
        new_gl_posts = []
        new_invoice_lines = []
        self.component.date_next_prolongation = dt.date(2021, 4, 14)
        self.component.invoice(
            next_id=1,
            invoice=invoice,
            new_invoice_lines=new_invoice_lines,
            new_gl_posts=new_gl_posts
        )

        # Check if the Invoice was updated correctly
        self.assertEqual(invoice.base_amount, dc.Decimal('28.33'))
        self.assertEqual(invoice.vat_amount, dc.Decimal('5.67'))
        self.assertEqual(invoice.total_amount, dc.Decimal('34'))
        self.assertEqual(invoice.balance, dc.Decimal('34'))

        # Check if the Contract was updated correctly
        self.assertEqual(invoice.contract.balance, dc.Decimal('34'))

        # Check if the InvoiceLine is correct
        self.assertEqual(new_invoice_lines.__len__(), 1)
        invoice_line = new_invoice_lines[0]
        self.assertEqual(invoice_line.base_amount, dc.Decimal('28.33'))
        self.assertEqual(invoice_line.vat_amount, dc.Decimal('5.67'))
        self.assertEqual(invoice_line.total_amount, dc.Decimal('34'))
        self.assertIsNone(invoice_line.unit_price)
        self.assertEqual(invoice_line.vat_type, 25)

        # Check if the GeneralLedgerPosts are correct
        normal_gl_post = new_gl_posts[0]
        vat_gl_post = new_gl_posts[1]
        self.assertEqual(normal_gl_post.amount_credit, dc.Decimal('28.33'))
        self.assertEqual(vat_gl_post.amount_credit, dc.Decimal('5.67'))

        self.assertEqual(self.component.date_next_prolongation, dt.date(2021, 5, 1))

    def test_invoice_end(self):
        """Method to test the invoice() method of the Component class.
        The scenario is a component that ends halfway through a period.
        """
        invoice = baker.make(
            'Invoice',
            tenancy=self.component.tenancy,
            contract=self.component.contract
        )
        new_gl_posts = []
        new_invoice_lines = []
        self.component.end_date = dt.date(2021, 4, 17)
        self.component.invoice(
            next_id=1,
            invoice=invoice,
            new_invoice_lines=new_invoice_lines,
            new_gl_posts=new_gl_posts
        )

        # Check if the Invoice was updated correctly
        self.assertEqual(invoice.base_amount, dc.Decimal('28.33'))
        self.assertEqual(invoice.vat_amount, dc.Decimal('5.67'))
        self.assertEqual(invoice.total_amount, dc.Decimal('34'))
        self.assertEqual(invoice.balance, dc.Decimal('34'))

        # Check if the Contract was updated correctly
        self.assertEqual(invoice.contract.balance, dc.Decimal('34'))

        # Check if the InvoiceLine is correct
        self.assertEqual(new_invoice_lines.__len__(), 1)
        invoice_line = new_invoice_lines[0]
        self.assertEqual(invoice_line.base_amount, dc.Decimal('28.33'))
        self.assertEqual(invoice_line.vat_amount, dc.Decimal('5.67'))
        self.assertEqual(invoice_line.total_amount, dc.Decimal('34'))
        self.assertIsNone(invoice_line.unit_price)
        self.assertEqual(invoice_line.vat_type, 25)

        # Check if the GeneralLedgerPosts are correct
        normal_gl_post = new_gl_posts[0]
        vat_gl_post = new_gl_posts[1]
        self.assertEqual(normal_gl_post.amount_credit, dc.Decimal('28.33'))
        self.assertEqual(vat_gl_post.amount_credit, dc.Decimal('5.67'))

        self.assertIsNone(self.component.date_next_prolongation)

    def test_get_amounts_between_dates(self):
        """Method to test the get_amounts_between_dates() method of
        the Component class.
        """
        # Get the costs for 9 days of February and 12 days of March
        base, vat, total, unit = self.component.get_amounts_between_dates(
            dt.date(2021, 2, 20),
            dt.date(2021, 3, 13)
        )
        self.assertEqual(base, dc.Decimal('16.07') + dc.Decimal('19.35'))
        self.assertEqual(vat, dc.Decimal('3.21') + dc.Decimal('3.87'))
        self.assertEqual(total, dc.Decimal('42.50'))
        self.assertEqual(unit, 0)

        # Test 4 full periods
        base, vat, total, unit = self.component.get_amounts_between_dates(
            dt.date(2020, 1, 1),
            dt.date(2020, 5, 1)
        )
        self.assertEqual(base, 200)
        self.assertEqual(vat, 40)
        self.assertEqual(total, 240)
        self.assertEqual(unit, 0)

        # Test with a quarter
        # 57 days of period 1, all of period 2, 8 days of period 3
        # 91 days in period 1, 91 days in period 2, 92 days in period 3
        self.component.contract.invoicing_period = Contract.QUARTER
        base, vat, total, unit = self.component.get_amounts_between_dates(
            dt.date(2020, 2, 4),
            dt.date(2020, 7, 9)
        )
        self.assertEqual(base, dc.Decimal('31.32') + 50 + dc.Decimal('4.35'))
        self.assertEqual(vat, dc.Decimal('6.26') + 10 + dc.Decimal('0.87'))
        self.assertEqual(total, dc.Decimal('102.8'))
        self.assertEqual(unit, 0)

        # Test with unit amount instead of base
        self.component.base_amount = None
        self.component.unit_amount = dc.Decimal(30)
        self.component.number_of_units = 5
        self.component.vat_amount = 30
        self.component.unit_id = "102"
        base, vat, total, unit = self.component.get_amounts_between_dates(
            dt.date(2020, 2, 4),
            dt.date(2020, 7, 9)
        )
        self.assertEqual(base, 0)
        self.assertEqual(vat, dc.Decimal('18.79') + 30 + dc.Decimal('2.61'))
        self.assertEqual(total, dc.Decimal('308.4'))
        self.assertEqual(unit, dc.Decimal('18.79') + 30 + dc.Decimal('2.61'))

    def test_create_correction_invoice(self):
        baker.make(
            "ContractPerson",
            contract_id=self.component.contract_id,
            percentage_of_total=100,
            start_date=dt.date(2020, 1, 1),
            end_date=None,
            payment_day=1
        )

        self.component.create_correction_invoice(
            dt.date(2020, 1, 1),
            dt.date(2020, 2, 1),
            -1
        )

        invoice = Invoice.objects.get(contract_id=self.component.contract_id)
        invoice_line = InvoiceLine.objects.get(invoice=invoice)
        collection = Collection.objects.get(invoice=invoice)
        gl_posts = list(GeneralLedgerPost.objects.all())

        # Check if the Invoice is correct
        self.assertEqual(invoice.base_amount, -50)
        self.assertEqual(invoice.vat_amount, -10)
        self.assertEqual(invoice.total_amount, -60)
        self.assertEqual(invoice.balance, -60)

        # Check if the Contract was updated correctly
        self.assertEqual(self.component.contract.balance, -60)

        # Check if the InvoiceLine is correct
        self.assertEqual(invoice_line.base_amount, -50)
        self.assertEqual(invoice_line.vat_amount, -10)
        self.assertEqual(invoice_line.total_amount, -60)
        self.assertEqual(invoice_line.unit_price, 0)
        self.assertEqual(invoice_line.vat_type, 25)

        # Check if the collection is correct
        self.assertEqual(collection.amount, -60)

        # Check if the GeneralLedgerPosts are correct
        self.assertEqual(gl_posts.__len__(), 3)
        normal_gl_post = gl_posts[0]
        vat_gl_post = gl_posts[1]
        invoice_gl_post = gl_posts[2]
        self.assertEqual(normal_gl_post.amount_credit, -50)
        self.assertEqual(vat_gl_post.amount_credit, -10)
        self.assertEqual(invoice_gl_post.amount_debit, -60)

    def test_create(self):
        contract = baker.make(
            "Contract",
            contract_id=1,
            base_component__unit_id=None,
            start_date=dt.date(2020, 1, 2),
            date_prev_prolongation=dt.date(2020, 6, 2),
            date_next_prolongation=dt.date(2020, 7, 2),
            invoicing_period=Contract.MONTH,
            end_date=None,
            status=Contract.ACTIVE
        )

        baker.make(
            "ContractPerson",
            contract_id=self.component.contract_id,
            percentage_of_total=100,
            start_date=dt.date(2020, 1, 2),
            end_date=None,
            payment_day=1
        )

        old_component = baker.make(
            "Component",
            tenancy=contract.tenancy,
            contract=contract,
            base_component__unit_id=None,
            base_amount=dc.Decimal(50),
            vat_amount=dc.Decimal(10),
            total_amount=dc.Decimal(60),
            unit_id=None,
            unit_amount=None,
            number_of_units=None,
            vat_rate__percentage=dc.Decimal(20),
            start_date=dt.date(2020, 1, 2),
            end_date=None,
            date_prev_prolongation=dt.date(2020, 6, 2),
            date_next_prolongation=dt.date(2020, 7, 2)
        )

        new_component = baker.prepare(
            "Component",
            base_component=old_component.base_component,
            vat_rate=old_component.vat_rate,
            base_amount=dc.Decimal(100),
            unit_amount=None,
            number_of_units=None,
            start_date=dt.date(2020, 2, 2),
            end_date=None,
        )

        new_component.create(
            {'contract_id': 1, 'company_id': contract.tenancy_id}
        )

        self.assertEqual(new_component.date_next_prolongation, dt.date(2020, 7, 2))

        invoice = Invoice.objects.get(contract_id=1)
        contract = Contract.objects.get(contract_id=1)
        invoice_lines = list(InvoiceLine.objects.all())
        collection = Collection.objects.get(invoice=invoice)
        gl_posts = list(GeneralLedgerPost.objects.all())

        # Check if the Invoice is correct
        self.assertEqual(invoice.base_amount, 250)
        self.assertEqual(invoice.vat_amount, 50)
        self.assertEqual(invoice.total_amount, 300)
        self.assertEqual(invoice.balance, 300)

        # Check if the Contract was updated correctly
        self.assertEqual(contract.balance, 300)

        # Check if the InvoiceLines are correct
        self.assertEqual(invoice_lines.__len__(), 2)
        new_line = invoice_lines[0]
        self.assertEqual(new_line.base_amount, 500)
        self.assertEqual(new_line.vat_amount, 100)
        self.assertEqual(new_line.total_amount, 600)
        self.assertEqual(new_line.unit_price, 0)

        old_line = invoice_lines[1]
        self.assertEqual(old_line.base_amount, -250)
        self.assertEqual(old_line.vat_amount, -50)
        self.assertEqual(old_line.total_amount, -300)
        self.assertEqual(old_line.unit_price, 0)

        # Check if the collection is correct
        self.assertEqual(collection.amount, 300)

        # Check if the GeneralLedgerPosts are correct
        self.assertEqual(gl_posts.__len__(), 5)
        container_credit = [500, 100, -250, -50]
        for post in gl_posts:
            if post.amount_credit:
                container_credit.remove(post.amount_credit)
            else:
                self.assertEqual(post.amount_debit, 300)

        self.assertListEqual(container_credit, [])
