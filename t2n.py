#!/usr/bin/env python3
"""
t2n; twint2neo4j; Scrapes Twitter and saves to neo4j.

Usage:
 t2n usertweets <username>
 t2n userinfo <username>
 t2n -h | --help
 t2n --version

Options:
  -h --help     Show this screen.
  --version     Show version.
"""
import sys, os
from docopt import docopt
import urllib.parse
import pytz
import neotime
from IPython import embed
import twint
import json
from neo4j import GraphDatabase


def merge_userinfo(tx, info):
    cyphercmd = (f"""
        MERGE (user:User {{username: $username}})
        SET user += {{name: $name,
        bio: $bio,
        tweets: $tweets,
        following: $following,
        followers: $followers,
        likes: $likes,
        media_count: $media_count,
        is_private: $is_private,
        is_verified: $is_verified,
        join_date: $join_date,
        join_time: $join_time
        }}
        """)
    if info['background_image']:
        cyphercmd += f"""
        MERGE (background_image:Photo {{photourl: $background_image}})
        MERGE (user)-[:HAS_BACKGROUND_IMAGE]->(background_image)
        """
    if info['avatar']:
        cyphercmd += f"""
        MERGE (avatar:Photo {{photourl: $avatar}})
        MERGE (user)-[:HAS_AVATAR]->(avatar)
        """
    if info['url']:
        cyphercmd += f"""
        MERGE (url:URL {{address: $url}})
        MERGE (user)-[:HAS_URL]->(url)
        """
    if info['location']:
        cyphercmd += f"""
        MERGE (loc:Place {{location: $location}})
        MERGE (user)-[:IN_PLACE]->(loc)
        """
    from dateutil.parser import parse
    join_date_py = parse(info['join_date'])
    join_date = neotime.Date(join_date_py.year, join_date_py.month,
                             join_date_py.day)
    join_time_py = parse(info['join_time'])
    join_time = neotime.Time(join_time_py.hour, join_time_py.minute,
                             join_time_py.second)
    # embed()
    tx.run(cyphercmd,
           username=str(info['username']).lower(),
           name=info['name'],
           bio=info['bio'],
           tweets=info['tweets'],
           following=info['following'],
           followers=info['followers'],
           likes=info['likes'],
           media_count=info['media_count'],
           is_private=info['is_private'],
           is_verified=info['is_verified'],
           join_date=join_date,
           join_time=join_time,
           background_image=info['background_image'],
           avatar=info['avatar'],
           url=info['url'],
           location=info['location'])


def add_userinfo(s, info):
    s.write_transaction(merge_userinfo, info)


def create_from_tweet(tx, tweet):
    cyphercmd = (
        f"""
        MERGE (user:User {{username: $username}})
        SET user += {{is_tracked: $is_tracked}}
        MERGE (tweet:Tweet {{link: $link}})
        {'SET tweet :Reply' if len(tweet['reply_to']) > 1 else ''}
        SET tweet += {{
        created_at: $created_at,
        replies_count: $replies_count,
        retweets_count: $retweets_count,
        likes_count: $likes_count,
        is_retweet: $is_retweet,
        is_video: $is_video,
        content: $content}} """
        "MERGE (date:Date {date: $date}) "
        "MERGE (tweet)-[:ON_DATE]->(date) "
        # "MERGE (tz:Timezone {zone: $zone}) " # This timezone is the scraper's tz, it seems :D
        # "MERGE (tweet)-[:In_TZ]->(tz) "
        "MERGE (tweet)-[:TWEET_OF]->(user) ")

    if tweet['place'] != '':
        cyphercmd += ("MERGE (place:Place {location: $place}) "
                      "MERGE (tweet)-[:IN_PLACE]->(place) ")

    if tweet['quote_url'] != '':
        cyphercmd += ("MERGE (quoted_tweet:Tweet {link: $quote_url}) "
                      "MERGE (tweet)-[:QUOTES]->(quoted_tweet) ")
    cyphercmd += ("""
        FOREACH (mention in $mentions |
        MERGE (muser:User {username: TOLOWER(mention)})
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
        MERGE (cuser:User {username: TOLOWER(ruser.username)})
        MERGE (tweet)-[:REPLIED_TO]->(cuser)
        )
        """)

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

driver = GraphDatabase.driver("bolt+routing://db:7687",
                              auth=("neo4j", "changeme"))
module = sys.modules["twint.storage.write"]


def Json(obj, config):
    tweet = obj.__dict__
    if args['usertweets']:
        add_from_tweet(s, tweet)
    elif args['userinfo']:
        add_userinfo(s, tweet)


module.Json = Json

def twint2neo4j(iargs):
    global args
    args = iargs
    if os.getenv('DEBUGME', '') != '':
        print(args, file=sys.stderr)
    with driver.session() as ses:
        global s
        s = ses
        c = twint.Config()
        username = args['<username>']
        c.Username = username
        c.Store_json = True
        c.Output = "tweets.json"
        c.Since = "2011-05-20"
        c.Hide_output = True
        if args['usertweets']:
            twint.run.Search(c)
        if args['userinfo']:
            twint.run.Lookup(c)

if __name__ == '__main__':
    iargs = docopt(__doc__, version='t2n v0.1')
    twint2neo4j(iargs)

