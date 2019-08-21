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

def create_from_tweet(tx, tweet):
    cyphercmd = (
        "MERGE (user:User {username: $username, is_tracked: $is_tracked}) "
        f"MERGE (tweet:Tweet{':Reply' if len(tweet['reply_to']) > 1 else ''} "
        """{
        created_at: $created_at,
        replies_count: $replies_count,
        retweets_count: $retweets_count,
        likes_count: $likes_count,
        link: $link,
        is_retweet: $is_retweet,
        is_video: $is_video,
        content: $content}) """
        "MERGE (date:Date {date: $date}) "
        "MERGE (tweet)-[:On_DATE]->(date) "
        # "MERGE (tz:Timezone {zone: $zone}) " # This timezone is the scraper's tz, it seems :D
        # "MERGE (tweet)-[:In_TZ]->(tz) "
        "MERGE (tweet)-[:TWEET_OF]->(user) ")

    if tweet['place'] != '':
        cyphercmd += ("MERGE (place:Place {location: $place}) "
                      "MERGE (tweet)-[:IN_PLACE]->(place) ")

    if tweet['quote_url'] != '':
        cyphercmd += ("MERGE (quoted_tweet:Tweet {link: $quote_url}) "
                      "MERGE (tweet)-[:QUOTES]->(quoted_tweet) ")
    cyphercmd += (
        """
        FOREACH (mention in $mentions |
        MERGE (muser:User {username: LOWER(mention)})
        MERGE (tweet)-[:MENTIONS]->(muser)
        )
        """
        """
        FOREACH (url in $urls |
        MERGE (curl:URL {address: url})
        MERGE (tweet)-[:HAS_URL]->(curl)
        )
        """
        """
        FOREACH (photo in $photos |
        MERGE (cphoto:Photo {photourl: photo})
        MERGE (tweet)-[:HAS_PHOTO]->(cphoto)
        )
        """
        """
        FOREACH (hashtag in $hashtags |
        MERGE (chtag:Hashtag {hashtag: hashtag})
        MERGE (tweet)-[:HAS_HASHTAG]->(chtag)
        )
        """
        """
        FOREACH (cashtag in $cashtags |
        MERGE (cctag:Cashtag {cashtag: cashtag})
        MERGE (tweet)-[:HAS_CASHTAG]->(cctag)
        )
        """
        """
        FOREACH (ruser in $reply_to |
        MERGE (cuser:User {username: LOWER(ruser.username)})
        MERGE (tweet)-[:REPLIED_TO]->(cuser)
        )
        """


    )

    time = neotime.gmtime(tweet['datetime'] / 1000)
    ntime = neotime.DateTime(time.tm_year, time.tm_mon, time.tm_mday,
                             time.tm_hour, time.tm_min, time.tm_sec, pytz.utc)
    # embed()
    tx.run(cyphercmd,
           is_tracked=True,
           mentions=tweet['mentions'],
           reply_to=tweet['reply_to'][1:],
           photos=tweet['photos'],
           urls=tweet['urls'],
           hashtags=tweet['hashtags'],
           cashtags=tweet['cashtags'],
           is_video=(tweet['video'] == 1),
           replies_count=int(tweet['replies_count']),
           retweets_count=int(tweet['retweets_count']),
           likes_count=int(tweet['likes_count']),
           link=tweet['link'],
           is_retweet=tweet['retweet'],
           quote_url=tweet['quote_url'],
           place=tweet['place'],
           created_at=ntime,
           zone=tweet['timezone'],
           content=str(tweet['tweet']),
           date=tweet['datestamp'],
           username=str(tweet['username']).lower())


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
    username = sys.argv[1].lower()
    c.Username = username
    # add_user(s, c.Username)
    c.Store_json = True
    # c.Custom["user"] = ["tweet", "username", "hashtags", "mentions"]
    c.Output = "tweets.json"
    c.Since = "2011-05-20"
    c.Hide_output = True

    twint.run.Search(c)
