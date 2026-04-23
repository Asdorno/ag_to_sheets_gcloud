import requests
from requests_oauthlib import OAuth1
from secret_accessor import get_secret

ag_url = get_secret('AG_API_URL')
consumer_key = get_secret('AG_API_CONSUMER_KEY')
consumer_secret = get_secret('AG_API_CONSUMER_SECRET')


## Returns the XML response from the AG API containing a list of all vehicle IDs, creation timestamps, last-changed timestamps and titles.
## Raises an exception if the HTTP request fails.
def get_all_ag_vehicles_xml():
    auth = OAuth1(consumer_key, consumer_secret)
    response = requests.get(f"{ag_url}/ag_vehicle", auth=auth)

    if response.status_code != 200:
        raise Exception(f"HTTP error: {response.status_code} - {response.text}")
    return response.text


## Returns the XML response from the AG API containing detailed information about a specific vehicle identified by its ID.
## Raises an exception if the HTTP request fails.
def get_ag_vehicle_details(id: int):
    auth = OAuth1(consumer_key, consumer_secret)
    response = requests.get(f"{ag_url}/ag_vehicle/{id}", auth=auth)

    if response.status_code != 200:
        raise Exception(f"HTTP error: {response.status_code} - {response.text}")
    return response.text
