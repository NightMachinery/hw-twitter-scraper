#!/usr/bin/env python3
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
        """{created_at: $created_at, content: $content}) """
        "MERGE (tweet)-[:TWEET_OF]->(user) ")
    # print(cyphercmd)
    tx.run(cyphercmd,
           created_at=str(tweet['datetime']),
           dbg=str(tweet['datetime']),
           content=str(tweet['tweet']),
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
    c.Username = 'danieldennett'
    add_user(s, c.Username)
    c.Store_json = True
    # c.Custom["user"] = ["tweet", "username", "hashtags", "mentions"]
    c.Output = "tweets.json"
    c.Since = "2011-05-20"
    c.Hide_output = True

    twint.run.Search(c)
