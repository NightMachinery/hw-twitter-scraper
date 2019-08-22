#!/usr/bin/env python3
import sys
query=sys.argv[1]
cyph=''
if not sys.stdin.isatty():
    cyph=sys.stdin.read()
if query == "usertweets":
    username = sys.argv[2]
    cyph += (
        f"""
        MATCH (user:User {{username: "{username.lower()}"}})
        MATCH tweet_rel=(tweet:Tweet)-[:TWEET_OF]->(user)
        """
    )
elif query == "limit_likes_count":
    cyph+= f""" WHERE tweet.likes_count {" ".join(sys.argv[2:])} """
elif query == "ret":
    cyph+=' RETURN tweet_rel '
print(cyph)
