CREATE CONSTRAINT ON (u:User)
       ASSERT u.username IS UNIQUE ;
CREATE CONSTRAINT ON (t:Tweet)
       ASSERT t.link IS UNIQUE ;
CREATE CONSTRAINT ON (p:Place)
       ASSERT p.location IS UNIQUE ;
CREATE CONSTRAINT ON (d:Date)
       ASSERT d.date IS UNIQUE ;
CREATE CONSTRAINT ON (url:URL)
       ASSERT url.address IS UNIQUE ;
CREATE CONSTRAINT ON (photo:Photo)
       ASSERT photo.photourl IS UNIQUE ;
CREATE CONSTRAINT ON (hashtag:Hashtag)
       ASSERT hashtag.hashtag IS UNIQUE ;
CREATE CONSTRAINT ON (cashtag:Cashtag)
       ASSERT cashtag.cashtag IS UNIQUE ;
CREATE INDEX ON :User(bucket) ;