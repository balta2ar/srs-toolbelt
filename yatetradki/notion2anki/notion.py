"""
A helper that imports your data from Notion into a zipped file
(archived by Notion). You can import that file further into 2anki.net,
and then to Anki.

Put your credentials into ~/.netrc as follows:

    machine notion login <your-email> password <your-password>

Usage:

    python3 ./notion.py <block_id>
"""
import argparse
import netrc
import re
import time
from typing import List, Optional, Tuple

import requests

from yatetradki.tools.io import Blob
from yatetradki.tools.log import get_logger

_logger = get_logger('anki_import_notion')

"""
{
  "task": {
    "eventName": "exportBlock",
    "request": {
      "blockId": "994e653d-c9ef-423b-bc5f-c9d2ddc7b4b3",
      "recursive": true,
      "exportOptions": {
        "exportType": "html",
        "timeZone": "Europe/Oslo",
        "locale": "en"
      }
    }
  }
}

994e653dc9ef423bbc5fc9d2ddc7b4b3
994e653d-c9ef-423b-bc5f-c9d2ddc7b4b3
8        4    4    4    12

anki-994e653dc9ef423bbc5fc9d2ddc7b4b3

{"taskId":"bb42e59a-d046-4246-b203-d11df5047848"}

{"taskIds":["bb42e59a-d046-4246-b203-d11df5047848"]}

{
  "results": [
    {
      "id": "bb42e59a-d046-4246-b203-d11df5047848",
      "eventName": "exportBlock",
      "request": {
        "blockId": "994e653d-c9ef-423b-bc5f-c9d2ddc7b4b3",
        "recursive": true,
        "exportOptions": {
          "exportType": "html",
          "timeZone": "Europe/Oslo",
          "locale": "en"
        }
      },
      "actor": {
        "table": "notion_user",
        "id": "5e10fd0f-e64c-433c-a871-bb54094e0db0"
      },
      "state": "success",
      "status": {
        "type": "complete",
        "pagesExported": 4,
        "exportURL": "https://s3.us-west-2.amazonaws.com/temporary.notion-static.com/Export-b456fbbf-8d8c-49e6-9ffe-787231cbf16d.zip?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAT73L2G45O3KS52Y5%2F20201018%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20201018T191036Z&X-Amz-Expires=604800&X-Amz-Signature=6930bebe22c254505c26fb82f8390f0eb653827fefb62b8dfdeafc151fafb6f6&X-Amz-SignedHeaders=host&response-content-disposition=attachment%3B%20filename%20%3D%22Export-b456fbbf-8d8c-49e6-9ffe-787231cbf16d.zip%22"
      }
    }
  ]
}
"""


def parse_args():
    parser = argparse.ArgumentParser(description='Export Notion page with subpages')
    parser.add_argument('block_id', type=str, help='URL to export')
    return parser.parse_args()


class NotionTask:
    def __init__(self, id_, block_id, export_url):
        self.id = id_
        self.block_id = block_id
        self.export_url = export_url


class Notion:
    LOGIN_URL = 'https://www.notion.so/api/v3/loginWithEmail'
    ENQUEUE_URL = 'https://www.notion.so/api/v3/enqueueTask'
    GET_TASKS_URL = 'https://www.notion.so/api/v3/getTasks'
    TASK_STATUS_RETRY = 5.0
    TASK_TIMEOUT = 30.0

    def __init__(self):
        self._session = requests.Session()

    def login(self, username: Optional[str], password: Optional[str]) -> None:
        if username is None or password is None:
            username, password = get_notion_username_password()

        response = self._session.post(self.LOGIN_URL, json={
            'email': username,
            'password': password,
        })
        response.raise_for_status()
        _logger.info('login result: %s', response.content)

    def enqueue_task(self, block_id: str):
        payload = {
            "task": {
                "eventName": "exportBlock",
                "request": {
                    "blockId": block_id,
                    "recursive": True,
                    "exportOptions": {
                        "exportType": "html",
                        "timeZone": "Europe/Oslo",
                        "locale": "en"
                    }
                }
            }
        }
        response = self._session.post(self.ENQUEUE_URL, json=payload)
        response.raise_for_status()
        _logger.info("enqueue_task response: %s", response.text)
        return response.json()['taskId']

    def get_tasks(self, task_ids: List[str]) -> List[NotionTask]:
        response = self._session.post(self.GET_TASKS_URL, json={
            'taskIds': task_ids
        })
        response.raise_for_status()
        tasks = []
        _logger.info('get_tasks: %s', response.json())

        for task in response.json()['results']:
            if task['state'] == 'success' and task['status']['type'] == 'complete':
                tasks.append(NotionTask(
                    task['id'],
                    task['request']['blockId'],
                    task['status']['exportURL']),
                )
        return tasks

    def wait_for_task_completion(self, task_id: str, timeout: float) -> NotionTask:
        deadline = time.time() + timeout
        while time.time() < deadline:
            for task in self.get_tasks([task_id]):
                if task.id == task_id:
                    return task
            time.sleep(self.TASK_STATUS_RETRY)
        else:
            raise TimeoutError(f'task "{task_id}" waiting timeout: {timeout}')

    def download(self, url: str) -> bytes:
        response = self._session.get(url)
        response.raise_for_status()
        return response.content

    def export(self, block_id: str) -> Blob:
        block_id = maybe_add_dashes_to_block_id(block_id)
        task_id = self.enqueue_task(block_id)
        task = self.wait_for_task_completion(task_id, self.TASK_TIMEOUT)
        _logger.info('task is ready: %s', task)
        return Blob(self.download(task.export_url))


def get_notion_username_password() -> Tuple[str, str]:
    login, _, password = netrc.netrc().hosts['notion']
    return login, password


def maybe_add_dashes_to_block_id(block_id: str) -> str:
    if '-' in block_id:
        return block_id

    parts = re.split(r'(\w{8})(\w{4})(\w{4})(\w{4})(\w{12})', block_id)
    assert len(parts) == 7
    return '-'.join(parts[1:-1])


def main():
    args = parse_args()
    notion = Notion()
    username, password = get_notion_username_password()
    notion.login(username, password)
    notion.export(args.block_id).save('notion.export.zip')


if __name__ == '__main__':
    main()
