# coding: utf-8

from leancloud import Engine
from leancloud import Object
import os
import requests
import feedparser
from datetime import datetime, timedelta
import re
from dateutil.parser import parse as time_parse
from time import sleep as time_sleep
import logging
from tenacity import retry, stop_after_attempt, wait_exponential

engine = Engine()
RSS = Object.extend('RSS')


def html_clean(html):
    html = str(html)
    html_tags = [r"<[^>]+>", "&nbsp;", " "]
    for html_tag in html_tags:
        html = re.sub(html_tag, "", html)
    return html


@retry(stop=stop_after_attempt(7), wait=wait_exponential(multiplier=1, min=4, max=20))
def tg(message, preview=False):
    TG_BOT = os.environ['TG_BOT']
    chat_id = os.environ['CHAT_ID']
    url = f"https://api.telegram.org/bot{TG_BOT}/sendMessage"
    payload = {
        "parse_mode": "html",
        "chat_id": chat_id,
        "text": message
    }
    if not preview:
        payload["disable_web_page_preview"] = True

    response = requests.post(url=url, json=payload)
    if response.ok:
        return True
    else:
        logging.error(response.status_code)
        logging.error(response.text)
        return False


def get_rss_content(rss_name: str, link: str, max_time: datetime, preview: bool = False):
    feed = feedparser.parse(link)
    for new in sorted(feed["entries"], key=lambda x: time_parse(x["published"])):
        publish_time = time_parse(new["published"])
        if publish_time.timestamp() > max_time.timestamp():
            title = html_clean(new["title"]).strip()
            link = new.get("link")
            summary = html_clean(new.get("summary")).strip()
            msg = f"""<b>{rss_name}</b>\n<a href="{link}">{title}</a>\n<a>{summary[:100]}</a>\n<a>Time: {publish_time.strftime("%Y-%m-%d %H:%M:%S")}</a>"""
            if tg(msg, preview):
                logging.info(f"{rss_name}{title}{link}")
                rss = RSS()
                rss.set("rss_name", rss_name)
                rss.set("title", title)
                rss.set("publish_time", publish_time)
                rss.set("summary", summary)
                rss.set("link", link)
                rss.save()
            else:
                break
            time_sleep(2)


def get_max_time(rss_name):
    try:
        query = RSS.query
        query.equal_to('rss_name', rss_name)
        query.descending('publish_time')
        max_time = query.first()
        return max_time.get('publish_time')
    except:
        return datetime.now() - timedelta(days=10)


@engine.define
def send_tg(**params):
    return tg(params.get("message"))


@engine.define
def pull_rss(**params):
    rss_list = [
        ("??????", "https://rsshub.app/eleduck/jobs", False),
        ("AI?????????-New", "https://rsshub.app/aiyanxishe/all/new", False),
        ("??????.work", "https://rsshub.app/remote-work/all", False),
        ("500px-????????????", "https://rsshub.app/500px/tribe/set/f5de0b8aa6d54ec486f5e79616418001", False),
        ("DailyArt ????????????", "https://rsshub.app/dailyart/zh", True),
    ]
    for rss_name, link, preview in rss_list:
        max_time = get_max_time(rss_name)
        get_rss_content(rss_name, link, max_time, preview)
