#!/usr/bin/env python3
import urllib.parse
import pytz
import neotime
from IPython import embed
import twint
import json
from neo4j import GraphDatabase

driver = GraphDatabase.driver("bolt://localhost:7687",
                              auth=("neo4j", "dyeurHEART"))


def cn_user(tx, username):
    tx.run("MERGE (:User {username: $username})", username=username)


def add_user(s, username):
    s.write_transaction(cn_user, username)


def create_from_tweet(tx, tweet):
    cyphercmd = (
        "MERGE (user:User {username: $username}) "
        f"MERGE (tweet:Tweet{':Reply' if len(tweet['reply_to']) > 1 else ''} "
        """{created_at: $created_at,
        is_video: $is_video,
        content: $content}) """
        "MERGE (date:Date {date: $date}) "
        "MERGE (tweet)-[:On_DATE]->(date) "
        "MERGE (tz:Timezone {zone: $zone}) "
        "MERGE (tweet)-[:In_TZ]->(tz) "
        "MERGE (tweet)-[:TWEET_OF]->(user) ")

    i = 0
    for mention in tweet['mentions']:
        cyphercmd += (f"MERGE (mentioned{i}:User "
                      "{username: '" + mention + "'}) "
                      f"MERGE (tweet)-[:MENTIONS]->(mentioned{i}) ")
        i += 1
    i = 0
    for url in tweet['urls']:
        cyphercmd += (f"MERGE (url{i}:URL "
                      "{address: '" + urllib.parse.quote(url.rstrip(), safe='/:?=&') + "'}) "
                      f"MERGE (tweet)-[:HAS_URL]->(url{i}) ")
        i += 1
    i = 0
    for photo in tweet['photos']:
        cyphercmd += (f"MERGE (photo{i}:PHOTO "
                      "{address: '" + urllib.parse.quote(photo.rstrip(), safe='/:?=&') + "'}) "
                      f"MERGE (tweet)-[:HAS_PHOTO]->(photo{i}) ")
        i += 1
    i = 0
    for hashtag in tweet['hashtags']:
        cyphercmd += (f"MERGE (hashtag{i}:HASHTAG "
                      "{tag: '" + hashtag + "'}) "
                      f"MERGE (tweet)-[:HAS_HASHTAG]->(hashtag{i}) ")
        i += 1
    i = 0
    for cashtag in tweet['cashtags']:
        cyphercmd += (f"MERGE (cashtag{i}:CASHTAG "
                      "{ctag: '" + cashtag + "'}) "
                      f"MERGE (tweet)-[:HAS_CASHTAG]->(cashtag{i}) ")
        i += 1
         


    time = neotime.gmtime(tweet['datetime']/1000)
    ntime = neotime.DateTime(time.tm_year, time.tm_mon, time.tm_mday,
                             time.tm_hour, time.tm_min, time.tm_sec,
                             pytz.utc)
    # embed()
    tx.run(cyphercmd,
           is_video=(tweet['video']==1)
           created_at=ntime,
           zone=tweet['timezone'],
           content=str(tweet['tweet']),
           date=tweet['datestamp'],
           username=str(tweet['username']))


def add_from_tweet(s, tweet):
    s.write_transaction(create_from_tweet, tweet)


### twint

import sys
module = sys.modules["twint.storage.write"]

i = 0


def Json(obj, config):
    global i
    i += 1
    tweet = obj.__dict__
    if not tweet['tweet']:
        embed()
    add_from_tweet(s, tweet)
    # print(str(tweet))


module.Json = Json

with driver.session() as s:
    # ses=s
    c = twint.Config()
    c.Username = sys.argv[1]
    add_user(s, c.Username)
    c.Store_json = True
    # c.Custom["user"] = ["tweet", "username", "hashtags", "mentions"]
    c.Output = "tweets.json"
    c.Since = "2011-05-20"
    c.Hide_output = True

    twint.run.Search(c)
