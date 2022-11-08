import datetime
import random

from django.db import transaction
from model_bakery import baker
from InvoiceEngineApp.models import (
    Tenancy,
    Contract,
    Component,
    Invoice,
    ContractPerson,
    InvoiceLine,
    Collection,
    GeneralLedgerPost
)


def generate_benchmark_data(amount_of_contract_types,
                            amount_of_base_components,
                            amount_of_vat_rates,
                            amount_of_contracts,
                            max_contract_persons,
                            max_components):
    """Function to fill the database with dummy data that can be
    used to benchmark the invoicing procedure.

    A caveat of this function is that max_contract_persons must be
    a true divisor of 100.
    """
    start_time = datetime.datetime.now()
    print("started populating db at " + start_time.__str__())

    tenancy = baker.make(
        'Tenancy',
        tenancy_id=113582,
        date_next_prolongation=datetime.date.today(),
        days_until_invoice_expiration=14,
        number_of_contracts=amount_of_contracts
    )

    contract_types = []
    for i in range(amount_of_contract_types):
        contract_types.append(
            baker.make(
                'ContractType',
                tenancy=tenancy
            )
        )

    base_components = []
    for i in range(amount_of_base_components):
        base_components.append(
            baker.make(
                'BaseComponent',
                tenancy=tenancy,
                unit_id=random.choice([None, random.randint(1, 932)])
            )
        )

    vat_rates = []
    for i in range(amount_of_vat_rates):
        vat_rates.append(
            baker.make(
                'VATRate',
                tenancy=tenancy,
                percentage=(i * 10.5) % 100
            )
        )

    contracts = []
    components = []
    contract_persons = []
    total_components = 0
    total_contract_persons = 0
    for i in range(amount_of_contracts):
        if i % 1000 == 0:
            print("contract " + i.__str__())
        amount_of_components = random.randint(1, max_components)
        amount_of_contract_persons = random.randint(1, max_contract_persons)
        contract = baker.prepare(
            'Contract',
            contract_id=i,
            tenancy=tenancy,
            contract_type=random.choice(contract_types),
            status=Contract.ACTIVE,
            start_date=datetime.date(2021, 1, 1),
            date_next_prolongation=datetime.date(2021, 1, 1)
        )

        for j in range(amount_of_components):
            vat_rate = random.choice(vat_rates)
            base_component = random.choice(base_components)

            if base_component.unit_id:
                base_amount = None
                unit_amount = random.randint(20, 300)
                number_of_units = random.randint(1, 5)
                total_without_vat = unit_amount * number_of_units
            else:
                base_amount = random.randint(100, 2000)
                unit_amount = None
                total_without_vat = base_amount

            vat_amount = total_without_vat * vat_rate.percentage / 100
            total_amount = total_without_vat + vat_amount

            component = baker.prepare(
                'Component',
                component_id=total_components,
                tenancy=tenancy,
                contract=contract,
                base_component=base_component,
                vat_rate=vat_rate,
                start_date=datetime.date(2021, 1, 1),
                date_next_prolongation=datetime.date(2021, 1, 1),
                base_amount=base_amount,
                unit_amount=unit_amount,
                vat_amount=vat_amount,
                total_amount=total_amount
            )

            contract.total_amount += total_amount
            contract.base_amount += total_without_vat
            contract.vat_amount += vat_amount

            components.append(component)
            total_components += 1

        for k in range(amount_of_contract_persons):
            contract_persons.append(
                baker.prepare(
                    'ContractPerson',
                    contract_person_id=total_contract_persons,
                    tenancy=tenancy,
                    contract=contract,
                    type='P',
                    start_date=datetime.date(2021, 1, 1),
                    percentage_of_total=100 / amount_of_contract_persons,
                    payment_day=1
                )
            )

            total_contract_persons += 1

        contracts.append(contract)

    with transaction.atomic():
        print("start adding contracts & components & contract persons to db")
        Contract.objects.bulk_create(contracts)
        print("Contracts done, starting components")
        Component.objects.bulk_create(components)
        print("components done, starting contract persons")
        ContractPerson.objects.bulk_create(contract_persons)
        print("done")

    end_time = datetime.datetime.now()
    print("started populating db at " + start_time.__str__())
    print("ended populating db at " + end_time.__str__())


def clear_database():
    # This works only if on_delete=CASCADE is set for every dependent model
    print("started clearing db at " + datetime.datetime.now().__str__())
    Tenancy.objects.all().delete()
    print("ended clearing db at " + datetime.datetime.now().__str__())


def clear_invoices():
    # This method removes all invoices and invoice lines from the database
    print("started clearing invoices at " + datetime.datetime.now().__str__())
    Invoice.objects.all().delete()
    print("ended clearing invoices at " + datetime.datetime.now().__str__())


def clear_contracts_and_invoices():
    print("started clearing at " + datetime.datetime.now().__str__())
    GeneralLedgerPost.objects.all().delete()
    InvoiceLine.objects.all().delete()
    Collection.objects.all().delete()
    Invoice.objects.all().delete()
    Component.objects.all().delete()
    ContractPerson.objects.all().delete()
    Contract.objects.all().delete()
    Tenancy.objects.all().update(last_invoice_number=0, number_of_contracts=0)
    print("ended clearing at " + datetime.datetime.now().__str__())


def run_invoice_engine():
    # Get the testing tenancy and invoice their contracts
    tenancy = Tenancy.objects.get(tenancy_id=113582)

    start_time = datetime.datetime.now()
    print("started invoicing at " + start_time.__str__())

    tenancy.invoice_contracts()

    end_time = datetime.datetime.now()
    invoicing_time = end_time - start_time
    print("Done")
    print("started invoicing at " + start_time.__str__())
    print("ended invoicing at " + end_time.__str__())
    print("invoicing time was " + invoicing_time.__str__())
