"""
NOTE! This *should* really be in it's own repo where a variety of clients can be made available
to API partners to use, this being the Python implementation. For the sake of this demonstration,
it can just be included the demo app.
"""
import hashlib
import hmac
import json
import os
import requests

from dotenv import load_dotenv

load_dotenv()

class ApiClientError(Exception):
    """Error raised when there is specifically an error in using the API."""

    pass


class ApiSecurityError(Exception):
    """Error raised when there is specifically an error in establishing API security."""

    pass


class FileImporterApiClient():
    """Client that will communicate with the File Importer API."""

    def __init__(self):
        try:
            self.api_partner_id = os.environ['API_PARTNER_ID']
            self.file_importer_url = os.environ['FILE_IMPORTER_URL']
            self.file_importer_secret = os.environ['FILE_IMPORTER_SECRET']
        except KeyError:
            raise Exception(
                "Please ensure that both 'FILE_IMPORTER_URL' and 'FILE_IMPORTER_SECRET' are "
                "present in the .env file in the root of this application")

    def import_transaction_data(self, transaction_data, ignore_errors, ignore_first_row):
        IMPORT_TRANSACTION_URL = f'{self.file_importer_url}/api/v1/transactions/import'

        post_data = {
            'api_partner_id': self.api_partner_id,
            'ignore_errors': ignore_errors,
            'ignore_first_row': ignore_first_row,
            'transaction_data': transaction_data
            }

        post_data['security_hash'] = self._generate_security_hash(
            post_data, self.file_importer_secret)

        try:
            response = requests.post(IMPORT_TRANSACTION_URL, json=post_data)
        except Exception as e:
            raise ApiClientError('The API appears to be unreachable')

        if response.status_code == 200:
            successfully_imported = response.json()['success']
            message = response.json()['message']
            errors = response.json()['errors']

            return (successfully_imported, message, errors)
        elif response.status_code == 403:
            raise ApiSecurityError(f'The security hash was rejected by the API')
        else:
            raise ApiClientError(
                f'Unexpected response from the API - status code: {response.status_code}, '
                f'body: {response.content}')

    def query_transaction_data(self, country_code, query_date):
        QUERY_TRANSACTION_URL = f'{self.file_importer_url}/api/v1/transactions/query'
        get_data = {
            'api_partner_id': self.api_partner_id,
            'country_code': country_code,
            'query_date': query_date
        }

        get_data['security_hash'] = self._generate_security_hash(
            get_data, self.file_importer_secret)

        try:
            response = requests.get(QUERY_TRANSACTION_URL, json=get_data)
        except Exception as e:
            raise ApiClientError('The API appears to be unreachable')

        transactions = None
        errors = None
        if response.status_code == 200:
            transactions = response.json()['transactions']

            return (transactions, errors)
        elif response.status_code == 400:
            errors = response.json()['errors']
            return (transactions, errors)
        elif response.status_code == 403:
            raise ApiSecurityError(f'The security hash was rejected by the API')
        else:
            raise ApiClientError(
                f'Unexpected response from the API - status code: {response.status_code}, '
                f'body: {response.content}')

    @staticmethod
    def _generate_security_hash(data, secret):
        # Encode all of the hashing components into bytes
        byte_key = secret.encode()
        message = json.dumps(data, sort_keys=True).encode()

        return hmac.new(byte_key, message, hashlib.sha256).hexdigest()
