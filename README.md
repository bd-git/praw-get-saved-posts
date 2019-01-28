# praw-get-saved-posts
Use PRAW to get your saved posts into an sqlite3 db

1) Go to Reddit, create an app to get a `client_id` and `client_secret` https://www.reddit.com/prefs/apps/

2) `git clone https://github.com/bd-git/praw-get-saved-posts.git`

3) `pip install praw` or `pip install -r requirements.txt`

4) Modify `credentials.py` to contain your Username, Password, ClientID, and ClientSecret

5) Run with `python3 grabdata.py -d ~/posts.sqlite3`  (`.\posts.sqlite3` on Windows)

6) Open `posts.sqlite3` in a sqlite3 browser to explore data or run queries
 
 
 
See http://praw.readthedocs.io/en/latest/getting_started/configuration/prawini.html
 
Remember, `t1 = comments` and `t3 = submissions` 
 
 
 
Example SQL - Select a max of 15 saved posts where  
  * the post is a submission and  
  * the submission is a link (to the www) and  
  * the user is subscribed to the subreddit that the post was posted to  
 
 
```SQL
select * 
  from post p 
  inner join subreddit s on p.subreddit_id = s.name

where
  p.calc_type = 't3' 
and 
  p.calc_is_self = 0
and
  s.user_is_subscriber = 1

limit 15
```
