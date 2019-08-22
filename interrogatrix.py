#!/usr/bin/env python3
"""
interrogatrix.py

A highlevel API for our Twitter graph. Returns cypher queries.

Usage:
 interrogatrix.py usertweets <username> [--limit-likes=<likes>]
 interrogatrix.py show-node <id>
 interrogatrix.py -h | --help
 interrogatrix.py --version

Options:
  -h --help     Show this screen.
  --version     Show version.
  --limit-likes Limit like count. This will be injected directly into the query. You can,e.g., use `'> 150'`.
"""
import sys
from IPython import embed
from docopt import docopt
args = docopt(__doc__, version='interrogatrix v0.1')
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
            """
        )
    elif query == "limit_likes":
        cyph+= f""" WHERE tweet.likes_count {kwargs['count']} """
    elif query == 'show-node':
        cyph += f""" MATCH (n)
        WHERE ID(n) = {kwargs['id']}
        RETURN n
        """

if args['usertweets']:
    add_cypher('usertweets', username=args['<username>'])
    if args['--limit-likes']:
        add_cypher('limit_likes', count=args['--limit-likes'])
    cyph+=' RETURN tweet_rel '
elif args['show-node']:
    add_cypher('show-node', id=args['<id>'])
print(cyph)
