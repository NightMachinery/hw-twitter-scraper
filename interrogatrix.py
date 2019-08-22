#!/usr/bin/env python3
"""
interrogatrix.py

A highlevel API for our Twitter graph. Returns cypher queries.

Usage:
 interrogatrix.py usertweets <username> [--limit-likes=<comparison>] [--limit-replies=<comparison>] [--limit-retweets=<comparison>] [--cypher-condition=<cypher> ...]
 interrogatrix.py show-node <id>
 interrogatrix.py show-rel <id>
 interrogatrix.py -h | --help
 interrogatrix.py --version

Options:
  -h --help     Show this screen.
  --version     Show version.
  --limit-likes Limit like count. This will be injected directly into the query. You can,e.g., use `'> 150'`.
  -r, --limit-replies ↑
  -w, --limit-retweets ↑
  -c, --cypher-condition Allows you to add arbitrary cypher conditions.

Examples:
  interrogatrix.py usertweets danieldennett --limit-retweets '> 10' --limit-likes '> 50' --limit-replies '> 10' -c 'tweet.created_at > datetime({year:2019,month:1})'
"""
import sys, os
from IPython import embed
from docopt import docopt
args = docopt(__doc__, version='interrogatrix v0.1')
if os.getenv('DEBUGME','') != '':
    print(args, file=sys.stderr)
cyph=''

def add_cypher(query, **kwargs):
    global cyph
    if query == None or query == '':
        return
    if query == "usertweets":
        username = kwargs['username']
        cyph += (
            f"""
            MATCH (user:User {{username: "{username.lower()}"}})
            MATCH tweet_rel=(tweet:Tweet)-[:TWEET_OF]->(user)
            MATCH tweet_out=(tweet)-->()
            """
        )
    elif query == "limit_likes":
        cyph+= f""" AND tweet.likes_count {kwargs['count']} """
    elif query == "limit_replies":
        cyph+= f""" AND tweet.replies_count {kwargs['count']} """
    elif query == "limit_retweets":
        cyph+= f""" AND tweet.retweets_count {kwargs['count']} """
    elif query == 'conditions':
        for condition in kwargs['conditions']:
            cyph += f""" AND ({condition}) """
    elif query == 'show-node':
        cyph += f""" MATCH (n)
        WHERE ID(n) = {kwargs['id']}
        RETURN n
        """
    elif query == 'show-rel':
        cyph += f""" MATCH r=()-[n]->()
        WHERE ID(n) = {kwargs['id']}
        RETURN r
        """


if args['usertweets']:
    add_cypher('usertweets', username=args['<username>'])
    cyph += " WHERE TRUE "
    if args['--limit-likes']:
        add_cypher('limit_likes', count=args['--limit-likes'])
    if args['--limit-retweets']:
        add_cypher('limit_retweets', count=args['--limit-retweets'])
    if args['--limit-replies']:
        add_cypher('limit_replies', count=args['--limit-replies'])
    if args['--cypher-condition']:
        add_cypher('conditions', conditions=args['--cypher-condition'])
    cyph+=' RETURN tweet_rel, tweet_out '
elif args['show-rel']:
    add_cypher('show-rel', id=args['<id>'])
elif args['show-node']:
    add_cypher('show-node', id=args['<id>'])
print(cyph + " ;")
