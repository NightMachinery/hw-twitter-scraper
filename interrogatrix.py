#!/usr/bin/env python3
"""
interrogatrix.py

A highlevel API for our Twitter graph. Returns cypher queries.

Usage:
 interrogatrix.py userinfo <username>
 interrogatrix.py usertweets <username> [--limit-likes=<comparison>] [--limit-replies=<comparison>] [--limit-retweets=<comparison>] [--cypher-condition=<cypher> ...] [--return=<count>] [--sort=<by-what>]
 interrogatrix.py show-node <id>
 interrogatrix.py show-rel <id>
 interrogatrix.py on-date <yyyy-mm-dd> [--limit-likes=<comparison>] [--limit-replies=<comparison>] [--limit-retweets=<comparison>] [--cypher-condition=<cypher> ...] [--return=<count>] [--sort=<by-what>]
 interrogatrix.py -h | --help
 interrogatrix.py --version

Options:
  -h --help     Show this screen.
  --version     Show version.
  -l, --limit-likes Limit like count. This will be injected directly into the query. You can,e.g., use `'> 150'`. If you use a number, interrogatrix will automagically change it to `'>= NUMBER'`.
  -r, --limit-replies ↑
  -w, --limit-retweets ↑
  -c, --cypher-condition Allows you to add arbitrary cypher conditions.
  -n, --return The number of results to return.
  -s, --sort Sort by `like`, `retweet`, or `replies`.

Examples:
  interrogatrix.py on-date 2019-08-29
  interrogatrix.py usertweets danieldennett --limit-retweets '> 10' --limit-likes '> 50' --limit-replies '> 10' -c 'tweet.created_at > datetime({year:2019,month:1})'

Todos:
Parametrize queries
Make queries FOREACHy
busiest-day
user-most-used-hashtag
user-followings-most-used-hashtag
get-mutuals
user-most-interactions (Uses mutual mentions)
"""
import sys, os, inspect
from IPython import embed
from docopt import docopt
args = docopt(__doc__, version='interrogatrix v0.1')
if os.getenv('DEBUGME', '') != '':
    print(args, file=sys.stderr)
cyph = ''


def add_cypher(query, **kwargs):
    global cyph
    if query == None or query == '':
        return
    if kwargs.get('count') != None and kwargs['count'].isdigit():
        kwargs['count'] = f">= {kwargs['count']}"
    if query == "usertweets":
        username = kwargs['username']
        cyph += (f"""
            MATCH (user:User {{username: $username}})
            MATCH tweet_rel=(tweet:Tweet)-[:TWEET_OF]->(user)
            """)
    elif query == 'on-date':
        cyph += f"""
        MATCH (date:Date {{date: $date}})
        MATCH tweet_rel=(tweet:Tweet)-[:ON_DATE]->(date)
        """
    elif query == "limit_likes":
        cyph += f""" AND tweet.likes_count {kwargs['count']} """
    elif query == "limit_replies":
        cyph += f""" AND tweet.replies_count {kwargs['count']} """
    elif query == "limit_retweets":
        cyph += f""" AND tweet.retweets_count {kwargs['count']} """
    elif query == 'conditions':
        for condition in kwargs['conditions']:
            cyph += f""" AND ({condition}) """
    elif query == 'show-node':
        cyph += f"""
        MATCH (n)
        WHERE ID(n) = $id
        RETURN n
        """
    elif query == 'show-rel':
        cyph += f"""
        MATCH r=()-[n]->()
        WHERE ID(n) = $id
        RETURN r
        """
    cyph = inspect.cleandoc(cyph)


def add_tweet_constraints():
    global cyph
    cyph += "\nWHERE TRUE "
    if args['--limit-likes']:
        add_cypher('limit_likes', count=args['--limit-likes'])
    if args['--limit-retweets']:
        add_cypher('limit_retweets', count=args['--limit-retweets'])
    if args['--limit-replies']:
        add_cypher('limit_replies', count=args['--limit-replies'])
    if args['--cypher-condition']:
        add_cypher('conditions', conditions=args['--cypher-condition'])


def add_sort():
    sort_by = args['--sort']
    if not sort_by:
        return 
    global cyph
    cyph += "\nORDER BY "
    if sort_by.startswith('like'):
        cyph += 'tweet.likes_count'
    elif sort_by.startswith('retweet'):
        cyph += 'tweet.retweets_count'
    elif sort_by.startswith('reply') or sort_by.startswith('replies'):
        cyph += 'tweet.replies_count'
    cyph += ' DESC'


def add_limit():
    global cyph
    if args['--return']:
        cyph += f"\nLIMIT {args['--return']}"


def add_extra_tweet():
    global cyph
    add_tweet_constraints()
    cyph += '\nWITH tweet_rel , tweet'
    add_sort()
    add_limit()
    cyph += '\nMATCH tweet_out=(tweet)-->()'
    cyph += '\nRETURN tweet_rel, tweet_out '

def add_params_str(**kwargs):
    global cyph
    for key, value in kwargs.iteritems():
        if not value:
            continue
        cyph += f"""
        :param {key} => "{value}" ;"""

if args['usertweets']:
    add_cypher('usertweets')
    add_extra_tweet()
elif args['show-rel']:
    add_cypher('show-rel')
elif args['show-node']:
    add_cypher('show-node')
elif args['on-date']:
    add_cypher('on-date')
    add_extra_tweet()
elif args['userinfo']:
    cyph += f"""MATCH (user:User {{username: $username}}
    MATCH user_out=(user)-->()
    return user_out"""
cyph += " ;"
add_params_str(username=args['<username>'], date=args['<yyyy-mm-dd>'], id=args['<id>'])
print(cyph + " ;")
