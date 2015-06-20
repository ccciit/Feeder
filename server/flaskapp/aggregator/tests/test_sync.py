# -*- coding: utf-8 -*-
from ..sync import parse_feed
from ..database import GraphDB

from .feeds import testfeed, testfeed_link, testfeed_updated
from ..util import (parse_timestamp, timestamp, format_timestamp,
                   feed_to_dict, feeditem_to_dict)

import feedparser as fp
import json


def test_cache_feed(graph):
    # Local rss file
    db = GraphDB(graph=graph)
    # Make sure user exists
    email = 'bob@bob.com'
    db.merge_user(email)
    # First subscribe
    db.subscribe(email, testfeed_link)

    rss = fp.parse(testfeed)
    print(rss)

    parse_feed(db, rss)


    res = graph.cypher.execute("MATCH (:Feed {{link: {} }})<-[:IN]-(item:Item)\nRETURN COUNT(item) as count".format(json.dumps(testfeed_link)))
    print(res)
    assert len(res) == 1
    assert res[0]['count'] == 2

    # Make sure feed stuff are correct
    res = graph.cypher.execute("MATCH (feed:Feed {{link: {} }})\nRETURN feed".format(json.dumps(testfeed_link)))

    print(res)
    f = res[0]['feed']
    print(rss.feed)
    print(f)
    assert f['title'] == "Cowboy Programmer"
    assert f['description'] == "Ramblings about stuff."

    # Sync again should make no difference, as the guids are the same
    parse_feed(db, rss)

    res = graph.cypher.execute("MATCH (:Feed {{link: {} }})<-[:IN]-(item:Item)\nRETURN COUNT(item) as count".format(json.dumps(testfeed_link)))
    print(res)
    assert len(res) == 1
    assert res[0]['count'] == 2


def test_cache_updated(graph):
    db = GraphDB(graph=graph)

    rss = fp.parse(testfeed_updated)

    parse_feed(db, rss)
    res = graph.cypher.execute("MATCH (:Feed {{link: {} }})<-[:IN]-(item:Item)\nRETURN COUNT(item) as count".format(json.dumps(testfeed_link)))
    print(res)
    assert len(res) == 1
    # There is one new item, and one item was updated
    assert res[0]['count'] == 3


def test_get_items(graph):
    # Local rss file
    db = GraphDB(graph=graph)
    # Make sure user exists
    email = 'bob@bob.com'
    db.merge_user(email)
    # First subscribe
    db.subscribe(email, testfeed_link)


def test_rest_get(graph):
    ts = None
    db = GraphDB(graph=graph)

    res = db.get_users_new_feeditems("bob@bob.com", ts)

    feeds = []
    for r in res:
        feed = feed_to_dict(r['feed'])
        # If feed has no title, it has not synced.
        # Result must have a valid title, move on
        if feed['title'] is None:
            continue

        sub = r['subscription']

        # Set user title if it exists
        if sub['usertitle'] is not None:
            feed['title'] = sub['usertitle']

        feed['tag'] = sub['usertag']
        # Set items on feed for json conversion
        feed['items'] = []
        for i, r in zip(r['items'], r['reads']):
            feed['items'].append(feeditem_to_dict(i, r))
            print(feed['items'][-1])
        # Add to list
        feeds.append(feed)

    # Fetch unsubscriptions if we have a timestamp
    deletes = []
    if ts is not None:
        for r in db.get_users_new_unsubscribes(userid, ts):
            deletes.append(feed_to_dict(r['feed']))
