# SOURCE ME
addToPATH "$(realpath "${0:h}")"
alias cyph='cypher-shell -u neo4j -p changeme -a "bolt+routing://localhost:7687"'
alias cy='cyph  | color 255 140 10'
cyn() { interrogatrix.py show-node -e "$@" | cyph }
cyr() { interrogatrix.py show-rel -e "$@" | cyph }
cyrm-all() { cyph 'match (n) detach delete n;' }
