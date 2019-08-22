# Source me in my directory
addToPATH "$(realpath .)"
alias cyph='cypher-shell -u neo4j -p changeme -a "bolt+routing://localhost:7687"'
alias cy='cyph  | color 255 140 10'
cyn() { interrogatrix.py show-node "$@" | cyph }
cyr() { interrogatrix.py show-rel "$@" | cyph }
