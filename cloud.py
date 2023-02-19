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

engine = Engine()
RSS = Object.extend('RSS')


def html_clean(html):
    html = str(html)
    html_tags = [r"<[^>]+>", "&nbsp;", " "]
    for html_tag in html_tags:
        html = re.sub(html_tag, "", html)
    return html


def tg(message):
    TG_BOT = os.environ['TG_BOT']
    chat_id = os.environ['CHAT_ID']
    url = f"https://api.telegram.org/bot{TG_BOT}/sendMessage?disable_web_page_preview=true&parse_mode=Markdown&chat_id={chat_id}&text={message}"
    requests.get(url=url)


def get_rss_content(rss_name: str, link: str, max_time: datetime):
    feed = feedparser.parse(link)
    for new in feed["entries"]:
        publish_time = time_parse(new["published"])
        if publish_time.timestamp() > max_time.timestamp():
            title = html_clean(new["title"]).strip()
            link = new.get("link")
            summary = html_clean(new.get("summary")).strip()
            msg = f"""*{rss_name}*\n[{title}]({link})\n{summary[:100]}\nTime:{publish_time.strftime("%Y-%m-%d %H:%M:%S")}"""
            tg(msg)

            rss = RSS()
            rss.set("rss_name", rss_name)
            rss.set("title", title)
            rss.set("publish_time", publish_time)
            rss.set("summary", summary)
            rss.set("link", link)
            rss.save()

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
def pull_rss(**params):
    rss_list = [
        ("电鸭", "https://rsshub.app/eleduck/jobs"),
        ("AI研习社-New", "https://rsshub.app/aiyanxishe/all/new"),
        ("远程.work", "https://rsshub.app/remote-work/all"),
    ]
    for rss_name, link in rss_list:
        max_time = get_max_time(rss_name)
        get_rss_content(rss_name, link, max_time)
