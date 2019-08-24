# Requirements
You need docker, docker-compose, and a neo4j cluster connection at "bolt+routing://localhost:7687". Your neo4j should have APOC installed and configured properly. You can use our neo4j-compose.yml to set this up, but you still need to download APOC to the plugins folder yourself.

You need to have a socks5 proxy active at localhost:1080, or you need to disable proxying via suitable environment variables.

# Usage
You can use the dockerfile `hworkerDF2` to create a Docker image capable of scraping to neo4j and querying it. Or you can just install `cypher-shell`, `zsh`, and the Pythonic requirements.txt and use the scripts directly.

If you want to use this via docker, build `hworkerDF2`:

`docker build --tag hworker -f hworkerDF2 . # Run this in our directory`

Then you can prefix all the following commands with `docker run --rm -it --net=host hworker zsh -c 'COMMAND HERE'`.

First source `helpers.zsh` in your `zsh` session.

Use `interrogatrix.py --help` to see its documentation. It is a highlevel API for creating cypher queries you can run against cypher-shell or the neo4j browser (Which is accessible on `http://localhost:7474/browser/` in our config).

You can run all `interrogatrix` queries like this in the command line:

`interrogatrix.py usertweets jack -s like -n 2 -e | cyph`

In which `cyph` is an alias that authenticates cypher-shell with our config.

See `t2n.py --help` for our twint-to-neo4j tool.

Of note is `t2n.pt trackuser <username>` which marks that user to be tracked by us.

Read the source of `helpers.zsh`, we provide some neat helpers there. E.g., you can use this oneliner to track all your followees:

`cygetfollowees your_username | cypara t2n.py trackuser`

`cypara`, in particular, is a very helpful function that runs jobs in parallel. It uses `GNU parallel` under the hoods.

To start the machinary that automatically tracks users, use `docker-compose` with one of our `hworkers.yml` configs:

`docker-compose --file hworkers_lightweight.yml up`

Feel free to create your own `hworkers.yml` config. We hash each tracked username and assign it a bucket between 0 and 100, and these config files specify which buckets each worker updates.
