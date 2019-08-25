#!/usr/bin/env python3
"""
t2n; twint2neo4j; Scrapes Twitter and saves to neo4j.

Usage:
 t2n trackuser <username>
 t2n usertweets <username>
 t2n userinfo <username>
 t2n userfollowgraph <username>
 t2n -h | --help
 t2n --version

Options:
  -h --help     Show this screen.
  --version     Show version.
"""
import sys, os, datetime
import hashlib
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
    if isFollower:
        cyphercmd += f"""
        MERGE (orig:User {{username: $orig}})
        MERGE (user)-[:FOLLOWS]->(orig)
        """
    if isFollowing:
        cyphercmd += f"""
        MERGE (orig:User {{username: $orig}})
        MERGE (orig)-[:FOLLOWS]->(user)
        """

    # embed()
    tx.run(cyphercmd,
           orig=username,
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

def set_last_scraped_tx(tx, username, date):
    cyphercmd = (
        f"""
        MERGE (user:User {{username: $username}})
        SET user += {{last_scraped: $date}}
        """)
    tx.run(cyphercmd,
           date=date,
           username=username)


def set_last_scraped(s, username, date):
    s.write_transaction(set_last_scraped_tx, username, date)

def get_last_scraped_tx(tx, username):
    cyphercmd = (
        f"""
        MATCH (user:User {{username: $username}})
        RETURN user.last_scraped
        """)
    return tx.run(cyphercmd,
           username=username)


def get_last_scraped(s, username):
    res = s.read_transaction(get_last_scraped_tx, username)
    return res.value()[0]

def track_user_tx(tx):
    cyphercmd = (
        f"""
        MERGE (user:User {{username: $username}})
        SET user += {{is_tracked: $is_tracked,
        bucket: $bucket
        }}
        """)
    tx.run(cyphercmd,
           is_tracked=True,
           bucket=bucket,
           username=username)


def track_user():
    s.write_transaction(track_user_tx)

### twint


def resolve(address):
    host, port = address
    if port == 7687:
        yield "core1", 7687
    elif port == 7688:
        yield "core2", 7688
    elif port == 7689:
        yield "core3", 7689
    elif port == 7691:
        yield "core4", 7691
    elif port == 7690:
        yield "read1", 7690
    else:
        yield host, port

driver = GraphDatabase.driver("bolt+routing://db:7687",
                              auth=("neo4j", "changeme"), resolver=resolve)
module = sys.modules["twint.storage.write"]


def Json(obj, config):
    tweet = obj.__dict__
    # embed()
    if args['usertweets']:
        add_from_tweet(s, tweet)
    elif args['userinfo']:
        add_userinfo(s, tweet)
    elif args['userfollowgraph']:
        add_userinfo(s, tweet)


module.Json = Json


def twint2neo4j(iargs):
    global args, isFollowing, isFollower, s, username, bucket
    isFollower = False
    isFollowing = False
    args = iargs
    with driver.session() as ses:
        s = ses
        c = twint.Config()
        username = args['<username>'].lower()
        bucket = int(hashlib.md5(username.encode('utf-8')).hexdigest(), 16) % 100
        c.Username = username
        c.Store_json = True
        c.Output = "tweets.json"
        if os.getenv('TWINT_NO_PROXY', '') == '':
            c.Proxy_host = "127.0.0.1"
            c.Proxy_port = 1080
            c.Proxy_type = "socks5"
        since = None
        try:
            since = get_last_scraped(s, username)
        except:
            pass
        if since:
            c.Since = since
        if os.getenv('DEBUGME', '') != '':
            print("args:\n" + repr(args) + f"""
            since: {since}
            c.Since: {c.Since}
            bucket: {bucket}
            """, file=sys.stderr)
        # c.Hide_output = True
        if args['trackuser']:
            track_user()
        if args['usertweets']:
            twint.run.Search(c)
            today = datetime.datetime.today().strftime('%Y-%m-%d')
            set_last_scraped(s, username, today)
        if args['userinfo']:
            twint.run.Lookup(c)
        if args['userfollowgraph']:
            c.User_full = True
            isFollowing = True
            twint.run.Following(c)
            isFollowing = False
            isFollower = True
            twint.run.Followers(c)
            isFollower = False


if __name__ == '__main__':
    iargs = docopt(__doc__, version='t2n v0.1')
    twint2neo4j(iargs)
