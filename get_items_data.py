from notion_client import Client
import os
from typing import Dict, Any, Generator, List
from datetime import timezone, timedelta, datetime
from dotenv import load_dotenv

load_dotenv()

NOTION_API_KEY = os.environ["NOTION_API_KEY"]
NOTION_DATA_SOURCE_ID = os.environ["NOTION_DATA_SOURCE_ID"]

JST = timezone(timedelta(hours=9))
now_jst = datetime.now(JST)
tomorrow = (now_jst + timedelta(hours=12)).date().isoformat()

def fetch_datasource_page(client: Client, query_filter: Dict[str, Any]={}) -> Generator[Dict[str, Any], None, None]:
    start_cursor = None
    has_more = True
    while has_more:
        res:Dict[str, Any] = client.data_sources.query(data_source_id=NOTION_DATA_SOURCE_ID, start_cursor=start_cursor, filter=query_filter) #type: ignore
        has_more = res["has_more"]
        start_cursor = res["next_cursor"]
        for result in res["results"]:
            yield result
            
tomorrow_deadline_condition: Dict[str, Any] = {
    "property" : "期限",
    "date" : {
        "equals": tomorrow
    }
}

not_completed_condition: Dict[str, Any] = {
    "property" : "完了",
    "checkbox" : {
        "equals": False,
    }
}

is_needed_items: Dict[str, Any] = {
    "property" : "種類",
    "select" : {
        "equals": "持ち物",
    }
}

is_homework: Dict[str, Any] = {
    "property" : "種類",
    "select" : {
        "equals": "課題",
    }
}

not_updated_condition: Dict[str, Any] = {
    "property" : "終了",
    "checkbox" : {
        "equals": False,
    }
}

needed_items_condition = {
    "and" : [
        tomorrow_deadline_condition,
        not_completed_condition,
        is_needed_items,
        not_updated_condition
    ]
}

homework_condition = {
    "and" : [
        tomorrow_deadline_condition,
        not_completed_condition,
        is_homework,
        not_updated_condition
    ]
}

def fetch_needed_items(client: Client) -> List[str]:
    needed_items: List[str] = []
    for result in fetch_datasource_page(client=client, query_filter=needed_items_condition):
        name = result["properties"]["課題"]["title"][0]["text"]["content"]
        needed_items.append(name)
    return needed_items

def fetch_homework(client: Client) -> List[str]:
    homework: List[str] = []
    for result in fetch_datasource_page(client=client, query_filter=homework_condition):
        name = result["properties"]["課題"]["title"][0]["text"]["content"]
        homework.append(name)
    return homework