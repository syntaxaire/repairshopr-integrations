"""Download RepairShopr customer database and output a .csv file in FreePBX contact book format."""
import csv
import json
import pickle
import requests
import yaml


with open("config.yml", encoding='utf8') as f:
    config = yaml.safe_load(f)


def get_customers() -> list[dict]:
    """Fetch all customers through RepairShopr API."""
    page = 1
    total_pages = 1
    results = []
    url = f'https://{config["subdomain"]}.repairshopr.com/api/v1/customers'
    headers = {'accept': 'application/json',
               'Authorization': f'Bearer {config["token"]}'}
    params = {'sort': 'lastname ASC'}
    while page <= total_pages:
        params['page'] = page
        r = requests.get(url, headers=headers, params=params)
        reply = json.loads(r.content)
        page = reply['meta']['page']
        total_pages = reply['meta']['total_pages']
        print(f'Received page {page} of {total_pages} containing {len(reply["customers"])} entries')
        results.extend(reply['customers'])
        page += 1
    return results


def dump_customers():
    """Fetch all customers from API and dump to a pickle file for analysis.

    For debugging."""
    with open('customers.pkl', 'wb') as cusfile:
        pickle.dump(get_customers(), cusfile)


def load_customers() -> list[dict]:
    """Load pickled customers from disk and return them.

    For debugging."""
    with open('customers.pkl', 'rb') as cusfile:
        return pickle.load(cusfile)


def customer_to_entry(cus: dict, displayname: str) -> dict:
    """Convert from a RepairShopr customer database entry to a FreePBX contact book entry."""
    entry = {'groupname': 'RepairShopr',
             'grouptype': 'external',
             'displayname': f'RS {displayname}',
             'fname': cus['firstname'] if cus['firstname'] is not None else '',
             'lname': cus['lastname'] if cus['lastname'] is not None else '',
             # 'title': '',
             'company': cus['business_name'] if cus['business_name'] is not None else '',
             # 'address': '',
             # 'userman_username': '',
             'phone_1_number': cus['phone'],
             'phone_1_type': 'Work',
             # 'phone_1_extension': '',
             # 'phone_1_flags': '',
             'phone_2_number': cus['mobile'] if (
                  cus['mobile'] is not None and len(cus['mobile']) > 0) else '',
             'phone_2_type': 'Mobile' if (
                  cus['mobile'] is not None and len(cus['mobile']) > 0) else '',
             # 'phone_2_extension': '',
             # 'phone_2_flags': '',
             # 'phone_3_number': '',
             # 'phone_3_type': '',
             # 'phone_3_extension': '',
             # 'phone_3_flags': '',
             'email_1': cus['email'] if (
                  cus['email'] is not None and len(cus['email']) > 0) else '',
             # 'email_2': '',
             # 'email_3': '',
             }
    return entry


def rs_contact_to_entry(contact: dict, displayname: str) -> dict:
    """Convert from a RepairShopr customer contact database entry to a FreePBX contact book entry.

    The customer contact is a subfield of a RS customer that defines a person at a company."""
    entry = {'groupname': 'RepairShopr',
             'grouptype': 'external',
             'displayname': f'RS {contact["name"]} ({displayname})',
             # 'fname': '',
             # 'lname': '',
             # 'title': '',
             'company': displayname,
             # 'address': '',
             # 'userman_username': '',
             'phone_1_number': contact['phone'],
             'phone_1_type': 'Work',
             # 'phone_1_extension': '',
             # 'phone_1_flags': '',
             'phone_2_number': contact['mobile'],
             'phone_2_type': 'Mobile' if (
                     contact['mobile'] is not None and len(contact['mobile']) > 0) else '',
             # 'phone_2_extension': '',
             # 'phone_2_flags': '',
             # 'phone_3_number': '',
             # 'phone_3_type': '',
             # 'phone_3_extension': '',
             # 'phone_3_flags': '',
             'email_1': contact['email'] if (
                     contact['email'] is not None and len(contact['email']) > 0) else '',
             # 'email_2': '',
             # 'email_3': '',
             }
    if entry['phone_1_number'] is not None:
        entry['phone_1_number'] = entry['phone_1_number'].replace('-', '')
    if entry['phone_2_number'] is not None:
        entry['phone_2_number'] = entry['phone_1_number'].replace('-', '')
    return entry


def to_callerid_schema(customers: list[dict]) -> list[dict]:
    """Transform RepairShopr customer entries to a FreePBX contact book schema."""
    book = []
    for record in customers:
        if record['business_name'] is not None and len(record['business_name']) > 0:
            displayname = record['business_name']
        else:
            displayname = f'{record["firstname"]} {record["lastname"]}'.strip()
        if len(displayname) > 0 and record['phone'] is not None and len(record['phone']) > 0:
            entry = customer_to_entry(record, displayname)
            book.append(entry)
            if 'contacts' in record and record['contacts'] is not None and \
                    len(record['contacts']) > 0:
                # add business contacts as their own entries
                for contact in record['contacts']:
                    entry = rs_contact_to_entry(contact, displayname)
                    # don't add contacts that had no phone number
                    if entry['phone_1_number'] is not None and len(entry['phone_1_number']) > 0:
                        book.append(entry)
    return book


def write_csv(filename: str, data: list[dict]):
    fieldnames = [key for key in data[0].keys()]
    with open(filename, 'w', encoding='utf8', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for item in data:
            writer.writerow(item)


if __name__ == '__main__':
    cus_results = get_customers()
    transformed = to_callerid_schema(cus_results)
    write_csv('customers.csv', transformed)
