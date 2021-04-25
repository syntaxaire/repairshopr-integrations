This script will download your RepairShopr customer database and output a .csv file that
can be imported directly into a FreePBX or PBXact contact list. This contact list can be
used as a Caller ID source by enabling CID Superfecta on your inbound route and enabling
FreePBX Contact List as a Caller ID source in the CID Superfecta configuration.

You must first create an API token on your RepairShopr account that has permission to
read customers.

Enter your subdomain (the xxxx part of xxxx.repairshopr.com) and your API token into
`config.yml`. Use `config.yml.example` as a template.
```
python -m pip install pipenv
python -m pipenv sync
python -m pipenv shell
python customers.py
```