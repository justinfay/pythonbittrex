#!/usr/bin/env python
"""
bittrex.com api wrapper.
"""
import ConfigParser
import hashlib
import hmac
import json
import os
import sys
import time
import urllib
import urllib2
import urlparse
import textwrap


_KEY_FILE = os.environ.get(
    'BITTREX_KEY_FILE',
    os.path.join(os.path.expanduser('~'), '.bittrex.ini'))
_config = ConfigParser.SafeConfigParser()
if not _config.read(_KEY_FILE):
    sys.stderr.write('Key file not read, private methods will not work.\n')
    API_KEY = None
    API_SECRET = None
else:
    API_KEY = _config.get('bittrex', 'key')
    API_SECRET = _config.get('bittrex', 'secret')


GET_MARKETS_URI = "https://bittrex.com/api/v1.1/public/getmarkets"
GET_CURRENCIES_URI = "https://bittrex.com/api/v1.1/public/getcurrencies"
GET_TICKER = "https://bittrex.com/api/v1.1/public/getticker"
GET_MARKET_SUMMARIES = "https://bittrex.com/api/v1.1/public/getmarketsummaries"
GET_MARKET_SUMMARY = "https://bittrex.com/api/v1.1/public/getmarketsummary"
GET_ORDERBOOK = "https://bittrex.com/api/v1.1/public/getorderbook"
GET_MARKET_HISTORY = "https://bittrex.com/api/v1.1/public/getmarkethistory"
BUY_LIMIT = "https://bittrex.com/api/v1.1/market/buylimit"
BUY_MARKET = "https://bittrex.com/api/v1.1/market/buymarket"
SELL_LIMIT = "https://bittrex.com/api/v1.1/market/selllimit"
SELL_MARKET = "https://bittrex.com/api/v1.1/market/sellmarket"
CANCEL = "https://bittrex.com/api/v1.1/market/cancel"
GET_OPEN_ORDERS = "https://bittrex.com/api/v1.1/market/getopenorders"
GET_BALANCE = "https://bittrex.com/api/v1.1/account/getbalance"
GET_BALANCES = "https://bittrex.com/api/v1.1/account/getbalances"
GET_ORDER = "https://bittrex.com/api/v1.1/account/getorder"
GET_ORDER_SUMMARY = "https://bittrex.com/api/v1.1/account/getorderhistory"


def get(url, headers=None):
    """
    Perform a HTTP get request returning the request body.
    """
    headers = headers if headers else {}
    request = urllib2.Request(url, headers=headers)
    handle = urllib2.urlopen(request)
    return handle.read()


def format_uri(uri, parameters):
    """
    Format a uri with the given query parameters `dict`.
    """
    parts = urlparse.urlsplit(uri)
    query_string = urllib.urlencode(parameters)
    return urlparse.urlunsplit((
        parts.scheme,
        parts.netloc,
        parts.path,
        query_string,
        parts.fragment))


class BittrexAPIException(Exception):
    """
    Exception when bittrex api returns a False success status.
    """


class NoAPIKeys(Exception):
    """
    Exception raised when a private method called without credentials.
    """


class BittrexAPI(object):
    """
    bittrex class which wraps the bittrex API.
    """

    def __init__(self, api_key=None, api_secret=None, raw=False):
        self._api_key = api_key
        self._api_secret = api_secret
        self._raw = raw

    def _query(self, uri, params=None, public=True):
        if public is False and not all((self._api_key, self._api_secret)):
            raise NoAPIKeys
        params = params if params else {}
        headers = {}
        if public is False:
            params.update(self._auth_params)
        uri = format_uri(uri, params)
        if public is False:
            headers = self.api_headers(uri)
        if self._raw is True:
            return get(uri, headers)
        response = json.loads(get(uri, headers))
        if not response['success']:
            raise BittrexAPIException(response)
        return response

    @property
    def _auth_params(self):
        return dict(
            apikey=self._api_key,
            nonce=int(time.time()))

    def api_sign(self, uri):
        sign = hmac.new(self._api_secret, uri, hashlib.sha512)
        return sign.hexdigest()

    def api_headers(self, uri):
        return {'apisign': self.api_sign(uri)}

    def getmarkets(self):
        return self._query(GET_MARKETS_URI, dict(), public=True)

    def getcurrencies(self):
        return self._query(GET_CURRENCIES_URI, dict(), public=True)

    def getticker(self, market):
        return self._query(GET_TICKER, dict(market=market), public=True)

    def getmarketsummaries(self):
        return self._query(GET_MARKET_SUMMARIES, dict(), public=True)

    def getmarketsummary(self, market):
        params = dict(market=market)
        return self._query(GET_MARKET_SUMMARY, params, public=True)

    def getorderbook(self, market, type_='both', depth='20'):
        params = dict(market=market, type=type_, depth=depth)
        return self._query(GET_ORDERBOOK, params, public=True)

    def getmarkethistory(self, market, count='20'):
        params = dict(market=market, count=count)
        return self._query(GET_MARKET_HISTORY, params, public=True)

    def buylimit(self, market, quantity, rate):
        params = dict(market=market, quantity=quantity, rate=rate)
        return self._query(BUY_LIMIT, params, public=False)

    def buymarket(self, market, quantity):
        params = dict(market=market, quantity=quantity)
        return self._query(BUY_MARKET, params, public=False)

    def selllimit(self, market, quantity, rate):
        params = dict(market=market, quantity=quantity, rate=rate)
        return self._query(SELL_LIMIT, params, public=False)

    def sellmarket(self, market, quantity):
        params = dict(market=market, quantity=quantity)
        return self._query(SELL_MARKET, params, public=False)

    def cancel(self, uuid):
        return self._query(CANCEL, dict(uuid=uuid), public=False)

    def getopenorders(self, market=None):
        params = dict(market=market) if market else dict()
        return self._query(GET_OPEN_ORDERS, params, public=False)

    def getbalance(self, currency):
        params = dict(currency=currency)
        return self._query(GET_BALANCE, params, public=False)

    def getorder(self, uuid):
        params = dict(uuid=uuid)
        return self._query(GET_ORDER, params, public=False)

    def getbalances(self):
        return self._query(GET_BALANCES, public=False)

    def getorderhistory(self, market=None, count=None):
        params = dict()
        if market is not None:
            params['market'] = market
        if count is not None:
            params['count'] = count
        return self._query(GET_ORDER_SUMMARY, params, public=False)


def runner(*args):
    """
    Simple runner for the bittrex api methods.
    """
    bittrex = BittrexAPI(API_KEY, API_SECRET, raw=True)
    if len(sys.argv) > 1:
        return getattr(bittrex, sys.argv[1])(*sys.argv[2:])
    return getattr(bittrex, sys.argv[1])()


def usage():
    return """Usage:
    python bittrex.py getticker [market]
                      getmarkets
                      getcurrencies
                      getticker [market]
                      getmarketsummaries
                      getmarketsummary [market]
                      getorderbook [market] [type] [depth]
                      getmarkethistory [market] [count]
                      buylimit [market] [quantity] [price]
                      buymarket [market] [quantity]
                      selllimit [market] [quantity] [price]
                      sellmarket [market] [quantity]
                      cancel [uuid]
                      getopenorders [market]
                      getbalance [currency]
                      getbalances
                      getorder [uuid]
    """


if __name__ == "__main__":
    import sys
    if len(sys.argv) == 1:
        sys.stdout.write(textwrap.dedent(usage()))
        sys.exit(1)
    response = runner(sys.argv[1:])
    sys.stdout.write(str(response) + '\n')
    sys.exit(0)
