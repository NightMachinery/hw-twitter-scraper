#!/usr/bin/env python3
"""
interrogatrix.py

A highlevel API for our Twitter graph. Returns cypher queries.

Usage:
 interrogatrix.py userinfo <username> ... [options]
 interrogatrix.py usertweets <username> ... [--limit-likes=<comparison>] [--limit-replies=<comparison>] [--limit-retweets=<comparison>] [--cypher-condition=<cypher> ...] [--return=<count>] [--sort=<by-what> --ascending] [options]
 interrogatrix.py show-node <id> [options]
 interrogatrix.py show-rel <id> [options]
 interrogatrix.py on-date <yyyy-mm-dd> [--limit-likes=<comparison>] [--limit-replies=<comparison>] [--limit-retweets=<comparison>] [--cypher-condition=<cypher> ...] [--return=<count>] [--sort=<by-what>] [options]
 interrogatrix.py -h | --help
 interrogatrix.py --version

Options:
  -h --help  Show this screen.
  --version  Show version.
  -l <a>, --limit-likes <a>  Limit like count. This will be injected directly into the query. You can,e.g., use `'> 150'`. If you use a number, interrogatrix will automagically change it to `'>= NUMBER'`.
  -r <a>, --limit-replies <a>  ↑
  -w <a>, --limit-retweets <a>  ↑
  -c <a>, --cypher-condition <a>  Allows you to add arbitrary cypher conditions.
  -n <a>, --return <a>  The number of results to return.
  -s <a>, --sort <a>  Sort by `date`, `like`, `retweet`, or `replies`.
  -a, --ascending  Change the sort order to ascending.
  -e, --cypher-shell  Output parameters suitable for cypher-shell's consumption (on stdout).

Examples:
  interrogatrix.py on-date 2019-08-29
  interrogatrix.py usertweets danieldennett --limit-retweets '> 10' --limit-likes '> 50' --limit-replies '> 10' -c 'tweet.created_at > datetime({year:2019,month:1})'

Warning:
 There is a bug in the neo4j browser that makes us unable to set the parameters automatically. So, we print the parameters in a json dump format in stderr, and in the standard way in stdout (see --cypher-shell). The standard way works in cypher-shell, but you'll have to manually use the json dump to set the params in the browser. (Just copy and paste it in the browser.)
 You can upvote these tickets to help solve the problem:
 https://github.com/neo4j/neo4j-browser/issues/961
 https://github.com/neo4j-contrib/neo4j-apoc-procedures/issues/500
 https://github.com/neo4j/neo4j-browser/issues/693

Todos:
Add Python API
Parametrize queries
Make queries FOREACHy
busiest-day
user-most-used-hashtag
user-followings-most-used-hashtag
get-mutuals
user-most-interactions (Uses mutual mentions)
"""
import sys, os, inspect, json
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
        cyph += (f"""
            MATCH (user:User)
            WHERE TOLOWER(user.username) in [un in $username | TOLOWER(un)]
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
    clean_cyph()
def clean_cyph():
    global cyph
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
    elif sort_by.startswith('date'):
        cyph += 'tweet.created_at'
    if not args['--ascending']:
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
    if not args['--cypher-shell']:
        print(":params " + json.dumps(kwargs), file=sys.stderr)
    else:
        for key, value in kwargs.items():
            if not value:
                continue
            cyph += f"""
            :param {key} => {json.dumps(value)} ;"""
        clean_cyph()

add_params_str(username=args['<username>'], date=args['<yyyy-mm-dd>'], id=args['<id>'])
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
    cyph += f"""
    MATCH (user:User)
    WHERE TOLOWER(user.username) in [un in $username | TOLOWER(un)]
    MATCH user_out=(user)-->()
    RETURN user, user_out"""
cyph += " ;"
print(cyph)
