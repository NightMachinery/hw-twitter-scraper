CREATE (a:User {username: 'a'})
CREATE (b:User {username: 'b'})
CREATE (c:User {username: 'c'})
CREATE (d:User {username: 'd'})
CREATE (e:User {username: 'e'})
CREATE (a)-[:FOLLOWS]->(c)
CREATE (e)-[:FOLLOWS]->(c)
CREATE (a)-[:FOLLOWS]->(b)
CREATE (b)-[:FOLLOWS]->(a)
CREATE (a)-[:FOLLOWS]->(d)
CREATE (d)-[:FOLLOWS]->(a)
CREATE (e)-[:FOLLOWS]->(d)
CREATE (d)-[:FOLLOWS]->(e)

CREATE (h1:Hashtag {hashtag: '#all'})
CREATE (h2:Hashtag {hashtag: '#jungle'})
CREATE (h3:Hashtag {hashtag: '#bad'})
CREATE (h4:Hashtag {hashtag: '#soup'})


;
// MATCH (u:User) WHERE u.username in ['a','b','c','d','e'] MATCH r=(u)--() return r
// MATCH (u:User) WHERE u.username in ['a','b','c','d','e'] detach delete u