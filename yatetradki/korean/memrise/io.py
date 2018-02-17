import netrc


from requests import get
import yaml


def get_page(url):
    return get(url).content


def read_credentials_from_netrc():
    rc = netrc.netrc()
    username, _account, password = rc.hosts['memrise']
    return username, password


def read_course_collection(filename):
    with open(filename) as file_:
        courses = yaml.load(file_)['courses']
        return [(pair['filename'], pair['course_url']) for pair in courses]
