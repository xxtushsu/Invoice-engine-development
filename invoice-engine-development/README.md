### This is a django-based web-application run in a docker environment. The application uses postgreSQL as a database system.

#### Prerequisits
To run the application, Docker needs to be installed on your system. See https://www.docker.com/products/docker-desktop for the installer. On Windows, you can simply run the installer.

#### To run application:
 - Open a terminal window
 - Navigate to the folder containing the dockerfile (the folder this file is in)
 - Use `docker-compose up` to start the containers
	* if docker complains, try using `docker-compose build first`
 - When running, use `docker-compose exec web python manage.py migrate` to register changes in models.py
 - For first time use, use `docker-compose exec web manage.py createsuperuser` to register an admin that can use the localhost:8000/admin site
 - You can then use the admin site to add other users -- note that a username must be a positive integer, as it doubles as the tenancy_id in the Tenancy table

#### Benchmarking
For benchmarking, a file named 'benchmark.py' is included in the root folder. This file contains the following functions:
- `generate_benchmark_data(args)` to fill the database with contracts. Note that this function will create its own support objects (contract types, etc.) in any case; even if there are support files in the database already. It is possible to specify the following parameters:
	* Number of Contract Types
	* Number of Base Components
	* Number of VAT Rates
	* Number of Contracts
	* Maximum number of Contract Persons per Contract (must be true divisor of 100)
	* Maximum number of Components per Contract
- `clear_database()` to remove everything(!) from the database in a quick manner
- `clear_invoices()` to remove all invoices from the database so that run_invoice_engine() can be used again without having to generate new benchmarking data
- `clear_contracts_and_invoices()` to remove all contracts and invoices, so the setup-files need not be removed in testing
- `run_invoice_engine()` to measure the speed of the invoicing process

Run these functions in the web container from the manage.py shell: 

`docker-compose exec python manage.py shell`

In the shell, run the following commands:
- `import benchmark`
- `benchmark.function_name(arg)`
- `exit()` when you're done

Do note that if you make changes to benchmark.py, you have to restart the manage.py shell.

The last benchmark (13 Jun 2021) took 8 min for 50000 contracts with 2.5 components on average each (see the following command: `benchmark.generate_benchmark_data(10, 13, 4, 50000, 4, 5)`).

#### Testing
Use "python manage.py test" to run tests.

#### Deployment
The application has not been deployed.

#### Looking ahead
Some ideas for future development are:
- Using a job manager such as Celery to improve robustness of the invoicing process
	* Alternatively, use a job scheduler to make sure the invoice engine runs every day
- Reduce duplicate code in the templates
- Implement an export page where the user can export full tables, or a selection of entries between two dates
- Implement the contract person type (currently it does nothing)
	* There should be three possibilities: payer, non-payer, other
- Improve the interface for managing contract persons
	* Add javascript to make it responsive, so the user need not go back and forth between pages to add new persons
- Remove the Euro sign (€) in front of None values