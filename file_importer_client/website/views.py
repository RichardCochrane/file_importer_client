from django.shortcuts import render, redirect
from django.urls import reverse
from io import TextIOWrapper

from website.lib import ApiClientError, ApiSecurityError, FileImporterApiClient


def home_view(request):
    missing_file = request.GET.get('missing_file')
    return render(
        request,
        'home.html',
        {
            'missing_file': missing_file
        })


def import_transaction_file_view(request):
    if 'vat_file' not in request.FILES:
        return redirect(f'{reverse("home_view")}?missing_file=true')

    # The TextIOWrapper will automatically read and convert the lines to unicode (from byte strings)
    transaction_data = TextIOWrapper(request.FILES['vat_file'], encoding='utf-8').readlines()

    # Split out the rows into columns and strip off unnecessary whitespace
    clean_transaction_data = [row.strip().split(',') for row in transaction_data]

    ignore_errors = request.POST.get('ignore_errors', 'off') == 'on'
    ignore_first_row = request.POST.get('ignore_first_row', 'off') == 'on'

    api_client = FileImporterApiClient()

    try:
        success, message, errors = api_client.import_transaction_data(
            clean_transaction_data, ignore_errors, ignore_first_row)
        state = 'successful_attempt'
    except ApiSecurityError:
        success, message, errors = (None, None, None)
        state = 'security_fail'
    except ApiClientError:
        success, message, errors = (None, None, None)
        state = 'server_error'

    return render(
        request,
        'import_result.html',
        {
            'import_errors': errors[:20] if errors else [],
            'message': message,
            'success': success,
            'state': state
        })


def transaction_query_view(request):

    country_code = request.GET.get('country_code')
    query_date = request.GET.get('query_date')

    if not all([country_code, query_date]):
        errors = []
        if not country_code:
            errors.append('missing_country_code=true')

        if not query_date:
            errors.append('missing_query_date=true')

        return redirect(f'{reverse("home_view")}?{"&".join(errors)}')

    api_client = FileImporterApiClient()

    errors = None
    message = None
    transactions = None
    try:
        transactions, errors = api_client.query_transaction_data(country_code, query_date)
        if transactions:
            message = (
                f'There were {len(transactions)} transaction(s) for {country_code} on {query_date}')
        elif errors:
            message = ('The transactions could not be queried for the following reasons:')
        else:
            message = f'There were no transactions for {country_code} on {query_date}'

        state = 'successful_attempt'
    except ApiSecurityError:
        state = 'security_fail'
    except ApiClientError:
        state = 'server_error'

    return render(
        request,
        'query_result.html',
        {
            'errors': errors,
            'message': message,
            'state': state,
            'transactions': transactions
        })
