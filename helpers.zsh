## SOURCE ME
## Needs night.sh sourced first for some functions.

PATH="$(realpath "${0:h}"):$PATH"
alias cyph='cypher-shell -u neo4j -p changeme -a "bolt+routing://localhost:7687"'
alias cy='cyph  | color 255 140 10'
cyn() { interrogatrix.py show-node -e "$@" | cyph }
cyr() { interrogatrix.py show-rel -e "$@" | cyph }
cyrm-all() { cyph 'match (n) detach delete n;' }
cyavatar() {
    local res="$(cyph --format plain "match (user:User {username: TOLOWER('$1')})-[:HAS_AVATAR]->(photo:Photo)
return photo.photourl")"
    local url="${${${(@f)res}[2]}[2,-2]}"
    re dvar res url
    aa --dir ./$1/ "$url"
    image ./$1/*
}

cygetfollowees() {
    (($+aliases[mdocu])) && mdocu '<username>
Returns (to stdout) people who <username> follows.' MAGIC
    local query="
    MATCH (m:User)<-[:FOLLOWS]-(u:User {username: tolower('$1')})
    RETURN DISTINCT m.username
"
    local res="$(cyph --format plain $query)"
    local i
    for i in "${(@)${(@f)res}[2,-1]}"
    do
        print -r -- "${i[2,-2]}"
    done
}
cygetbucket() {
    local bs="$1" be="$2"
    local query=":param bstart => $bs ;
:param bend => $be ;
MATCH (u:User)
WHERE u.bucket > \$bstart AND u.bucket < \$bend
RETURN u.username;"
    # color red $query
    local res="$(<<<$query cyph --format plain)"
    # color blue $res
    local i
    for i in "${(@)${(@f)res}[2,-1]}"
    do
        print -r -- "${i[2,-2]}"
    done
}
cypara() {
    parallel --verbose --max-args 1 --jobs ${cypara_j:-10} "$(realpath $commands[python3])" "$@"
}
