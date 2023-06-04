#!/usr/bin/env python3

# pip install --user --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
# pip install --user requests browsercookie pycookiecheat
# pip install --user --upgrade pyOpenSSL

from __future__ import print_function

import os.path
from os.path import expanduser, expandvars, dirname, exists
from os import makedirs
from json import dumps, loads
from typing import List, Tuple

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from bs4 import BeautifulSoup
from diskcache import Cache

from pycookiecheat import chrome_cookies
import requests

from revChatGPT.V1 import Chatbot

cache = Cache('/tmp/comments')

def ensure_dir(filename: str) -> str:
    path = dirname(filename)
    if not exists(path): makedirs(path)
    return filename

def expand(filename: str) -> str:
    return expandvars(expanduser(filename))

def spit(data: bytes, filename: str):
    filename = ensure_dir(expand(filename))
    with open(filename, 'wb') as f:
        f.write(data)

def slurp(filename: str) -> str:
    filename = ensure_dir(expand(filename))
    with open(filename, 'r') as f:
        return f.read()

@cache.memoize(typed=True, expire=3600)
def download_html_with_comments(doc_id: str) -> str:
    format = 'html'
    url = f'https://docs.google.com/document/d/{doc_id}/export?format={format}'
    cookies = chrome_cookies('https://docs.google.com')
    resp = requests.get(url, cookies=cookies)
    return resp.content.decode('utf-8')

def test_export():
    toyen = '1FgKHLwYvUxyVcy_GdMjyKR2sB48fQN3e7lS0CbC38ZA'
    data = download_html_with_comments(toyen)
    spit(data, 'toyen.html')
    voksne = '1hGA9JLmdaVLUVrZp3Dcz3oS9TgsleQ1ZTU8QlAxza2Q'
    data = download_html_with_comments(voksne)
    spit(data, 'voksne.html')

# If modifying these scopes, delete the file token.json.
#SCOPES = ['https://www.googleapis.com/auth/drive.metadata.readonly']
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
FILE_ID = '1hGA9JLmdaVLUVrZp3Dcz3oS9TgsleQ1ZTU8QlAxza2Q'

def html_unescape(s: str) -> str:
    return BeautifulSoup(s, 'html.parser').text

class ApiComment:
    def __init__(self, id: str, quoted: str, content: str):
        self.id = id
        self.quoted = quoted
        self.content = content
    def __repr__(self):
        return f'ApiComment(id="{self.id}", quoted="{self.quoted}", content="{self.content}")'
    @staticmethod
    def from_json(data: dict) -> List['ApiComment']:
        comments = []
        for item in data:
            id = item['id']
            quoted = item['quotedFileContent']['value']
            quoted = html_unescape(quoted)
            content = item['content']
            comments.append(ApiComment(id, quoted, content))
        return comments

@cache.memoize(typed=True, expire=3600)
def list_comments(file_id) -> List[dict]:
    """Shows basic usage of the Drive v3 API.
    Prints the names and ids of the first 10 files the user has access to.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('drive', 'v3', credentials=creds)

        comments = []
        next = None
        while True:
            results = service.comments().list(
                fileId=file_id, pageSize=100,
                includeDeleted=False, pageToken=next,
                fields="nextPageToken, comments").execute()
            items = results.get('comments', [])
            if not items: return
            for item in items: comments.append(item)
            next = results.get('nextPageToken')
            if not next: break
        return comments
    except HttpError as e:
        print(f'An error occurred: {e}')

def test_list():
    toyen = '1FgKHLwYvUxyVcy_GdMjyKR2sB48fQN3e7lS0CbC38ZA'
    comments = list_comments(toyen)
    spit(dumps(comments).encode('utf-8'), 'toyen.json')
    voksne = '1hGA9JLmdaVLUVrZp3Dcz3oS9TgsleQ1ZTU8QlAxza2Q'
    comments = list_comments(voksne)
    spit(dumps(comments).encode('utf-8'), 'voksne.json')

'''
<span class="c7">skyflet</span>
<sup><a href="#cmnt74" id="cmnt_ref74">[bv]</a></sup>
<span class="c0">&nbsp;de ferdigstekte pølsebitene rundt og rundt i panna – uten deg ville det ikke vært noen kafé og dermed heller ikke noe fellesskap. Kalle ville gått på en annen skole. Tøyen ville vært et annet Tøyen.</span>

<div class="c5">
    <p class="c1">
        <a href="#cmnt_ref74" id="cmnt74">[bv]</a>
        <span class="c6">skyfle, shovel, сгребать лопатой </span>
    </p>
    <p class="c1">
        <span class="c6">skrape med en skyffel</span>
    </p>
</div>
'''

class Comment:
    def __init__(self, ref: str, context: str, api_comment: ApiComment):
        self.ref = ref
        self.context = context
        self.api_comment = api_comment
    def __repr__(self):
        return f'Comment(ref="{self.ref}", context="{self.context}", api_comment={self.api_comment})'
    @staticmethod
    def from_html(html: str, api_comments: List[ApiComment]) -> List['Comment']:
        by_content = { c.content: c for c in api_comments }
        soup = BeautifulSoup(html, 'html.parser')
        comments = []
        for (ref, body) in Comment._tags(soup):
            if body not in by_content: raise ValueError(f'No comment for "{body}"')
            context = Comment._context(soup, ref)
            api_comment = by_content[body]
            comment = Comment(ref, context, api_comment)
            comments.append(comment)
            print(comment)
        return comments
    @staticmethod
    def _context(soup: BeautifulSoup, ref: str) -> str:
        context = []
        def left_dot(s: str) -> bool:
            found = False
            if '.' in s: s = s[s.find('.')+1:]; found = True
            context.insert(0, s)
            return found
        def right_dot(s: str) -> bool:
            found = False
            if '.' in s: s = s[:s.find('.')+1]; found = True
            context.append(s)
            return found
        tag = soup.find('a', attrs={'id': f'{ref}'}).parent
        while tag:
            if tag.name != 'sup':
                if left_dot(tag.text): break
            tag = tag.previous_sibling
        tag = soup.find('a', attrs={'id': f'{ref}'}).parent
        while tag:
            if tag.name != 'sup':
                if right_dot(tag.text): break
            tag = tag.next_sibling
        context = ''.join(context).strip()
        return context
    @staticmethod
    def _tags(soup: BeautifulSoup) -> List[Tuple[str, str]]:
        aTags = soup.find_all('a')
        tags = []
        for a in aTags:
            ref = ''
            if a.has_attr('href') and a['href'].startswith('#cmnt_ref'):
                ref = a['href'][1:]
                div = a.parent.parent
                a.extract()
                body = '\n'.join([p.text for p in div.find_all('p')]).strip()
                tags.append((ref, body))
        return tags

def parse_comments_from_html(filename: str) -> List[Comment]:
    return Comment.from_html(slurp(filename))

def test_parse():
    toyen = '1FgKHLwYvUxyVcy_GdMjyKR2sB48fQN3e7lS0CbC38ZA'
    data = download_html_with_comments(toyen)
    api_comments = ApiComment.from_json(list_comments(toyen))
    # comments = parse_comments_from_html('toyen.html')
    comments = Comment.from_html(data, api_comments)
    # print(comments)

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36'

def refresh_access_token():
    url = 'https://chat.openai.com/api/auth/session'
    cookies = chrome_cookies(url)
    headers = {'user-agent': USER_AGENT}
    resp = requests.get(url, cookies=cookies, headers=headers)
    print(resp)
    resp.raise_for_status()
    resp = resp.json()
    filename = '~/.config/revChatGPT/config.json'
    data = {'access_token': resp['accessToken']}
    spit(dumps(data).encode('utf-8'), filename)

def ask_gpt(prompt: str) -> str:
    # access_token = loads(slurp('~/.config/revChatGPT/config.json'))['access_token']
    access_token = loads(slurp('./session.json'))['accessToken']
    chatbot = Chatbot(config={ "access_token": access_token, })
    response = ""
    for data in chatbot.ask(prompt):
        response = data["message"]
    return response

def prompt_meaning_in_text(word: str, text: str) -> str:
    prompt = f'''
hva betyr "{word}" på norsk i teksten? når brukes det? i hvilke situasjoner? hvilken konnotasjon har det? hva er synonymer og antonymer? oversett ordet på english og russisk. gi flere eksempler med ord i en setning. her er opprinnelig teksten for kontekst:
{text}
    '''
    return prompt

def test_gpt():
    prompt = prompt_meaning_in_text('fortrengte', '''
Jeg kjente hvor lett skrytet fortrengte det i meg, som hadde villet reservere kvelden for Jostein: Jeg var verdens beste redaktør – da var det klart at jeg slapp det jeg hadde i hendene når forfatteren min trengte meg
''')
    print(ask_gpt(prompt))

if __name__ == '__main__':
    pass
    # main()
