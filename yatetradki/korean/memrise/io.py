import netrc

from requests import get


def get_page(url):
    return get(url).content


def read_credentials_from_netrc():
    rc = netrc.netrc()
    username, _account, password = rc.hosts['memrise']
    return username, password
