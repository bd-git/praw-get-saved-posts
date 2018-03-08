import praw
import sqlite3
import argparse
import credentials
from pprint import pprint

def database_setup(database_file):
    POSTS_TABLE = """
CREATE TABLE IF NOT EXISTS post (
    id text PRIMARY KEY,
    calc_type text NOT NULL,
    calc_is_self integer NOT NULL,
    name text NOT NULL,
    subreddit text NOT NULL,
    subreddit_id text NOT NULL,
    subreddit_name_prefixed text NOT NULL,
    created_utc integer NOT NULL,
    over_18 integer NOT NULL,
    s_permalink text,
    s_is_self integer,
    s_selftext text,
    s_selftext_html text,
    s_url text,
    c_link_title text,
    c_parent_id text,
    c_body text,
    c_body_html text,
    c_link_url text,
    c_link_id text
);
    """
    
    SUBREDDIT_TABLE = """
CREATE TABLE IF NOT EXISTS subreddit (
    id text PRIMARY KEY,
    name text NOT NULL,
    created integer NOT NULL,
    url text NOT NULL,
    display_name text NOT NULL,
    display_name_prefixed text NOT NULL,
    title text,
    header_title text,
    over18 integer,
    user_is_subscriber integer, 
    user_has_favorited  integer,
    user_is_banned integer,
    user_is_contributor integer,
    user_is_moderator integer,
    user_is_muted integer,
    allow_discovery integer,
    allow_images integer,
    allow_videogifs integer,
    allow_videos integer,
    audience_target text,
    advertiser_category text,
    subscribers integer,
    accounts_active_is_fuzzed integer
);
    """
    
    with sqlite3.connect(database_file) as con:
        c = con.cursor()
        c.execute(POSTS_TABLE)
        c.execute(SUBREDDIT_TABLE)
        con.commit()
        #con.close()

def database_insert_post(_post, cursor):
    items = vars(_post)
    postinfo =( items['id'],
                post_get_type(_post),
                int(post_is_selfpost(_post)),
                items['name'],
                post_get_subreddit(_post), #string representation of "praw.reddit.subreddit" instance
                items['subreddit_id'],
                items['subreddit_name_prefixed'],
                int(items['created_utc']),
                int(items['over_18'])
                )
    
    submissioninfo = tuple(['']*5) 
    commentinfo = tuple(['']*6) 
    
    if post_is_submission(_post):
        submissioninfo = ( items['permalink'],
                int(items['is_self']),
                items['selftext'],
                items['selftext_html'],
                items['url']
                )
                
    elif post_is_comment(_post):
        commentinfo = ( items['link_title'],
                items['parent_id'],
                items['body'],
                items['body_html'],
                items['link_url'],
                items['link_id']
                )
    
    insert_row = postinfo + submissioninfo + commentinfo
    try:
        cursor.execute("INSERT INTO post VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", insert_row)
    except:
        pprint(insert_row)
        [print(type(val)) for val in insert_row]
        raise

def database_insert_subreddit(_subreddit_instance, cursor):
    items = vars(_subreddit_instance)
    subinfo =(
        items['id'],
        items['name'],
        int(items['created']),
        items['url'],
        items['display_name'],
        items['display_name_prefixed'],
        items['title'],
        items['header_title'],
        int(items['over18']),
        int(items['user_is_subscriber']), 
        int(items['user_has_favorited']),
        int(items['user_is_banned']),
        int(items['user_is_contributor']),
        int(items['user_is_moderator']),
        int(items['user_is_muted']),
        int(items['allow_discovery']),
        int(items['allow_images']),
        int(items['allow_videogifs']),
        int(items['allow_videos']),
        items['audience_target'],
        items['advertiser_category'],
        int(items['subscribers']),
        int(items['accounts_active_is_fuzzed'])
        )
    try:
        cursor.execute("INSERT INTO subreddit VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", subinfo)
    except:
        pprint(subinfo)
        [print(type(val)) for val in subinfo]
        raise
    
    
def reddit_getsavedposts(_redditinstance,_username,_limit=None):
	return [x for x in _redditinstance.redditor(name=_username).saved(limit=_limit)]
   
def trim_id(_linkid):
    _linkid=strip(linkid)
    # strip first 2 characters of name variable (t1_ t3_ t5_) if needed
    if _linkid [0] == 't' and _linkid [2] == '_':
        return _linkid[3:] # return id starting from char 3
    return _linkid
    
def post_get_type(_post):
    items = vars(_post)
    # return first 2 characters of name variable (t1 or t3)
    type = items['name'][0]+ items['name'][1]
    if type in ['t1','t3']: return type
    return None
    
def post_get_subreddit(_post):
    return str(vars(_post)['subreddit']) #string representation of "praw.reddit.subreddit" instance
    
def post_is_submission(_post):
    return post_get_type(_post) == 't3'

def post_is_comment(_post):
    return post_get_type(_post) == 't1'

def post_is_selfpost(_post):
    items = vars(_post)
    if post_is_submission(_post):
        # if submission is selfpost, permalink = /r/path_to_submission (need to add reddit.com)
        #                            url = https://reddit.com/r/path_to_submission
        #               is not_self, permalink = /r/path_to_submission (need to add reddit.com)
        #                            url = submitted link
        return items['is_self']
    elif post_is_comment(_post):
        # if comment is selfpost, link_url = direct link to selfpost submission
        #                         link_url+id = direct link to saved comment
        # if comment is not_self, link_url = submitted link (ie streamable.com)
        #                         link_id = link_id of submission (t3_uLINKID)
        #                         parent_id = link_id of comment parent (t3_uLINKID if parent is submission (ie toplevel comment), else t1_)
        #                         link_title = submitted title for submitted link
        #                         id = id of comment
        #                         name = link_id of comment (ie t1_ID)
        #         link to submission = https://www.reddit.com/ subreddit_prefixed /comments/ trim(link_id) / link_title /
        #         link to comment    = https://www.reddit.com/ subreddit_prefixed /comments/ trim(link_id) / link_title / id
        return 'reddit.com' in items['link_url']
    return False
    
def get_saved_posts_subreddits(in_listofposts):
        subreddits = dict()
        for post in in_listofposts:
                try:
                    subreddits[post_get_subreddit(post)] #if this line succeeds, do nothing
                except KeyError:
                    #if KeyError, subreddit not yet in dict so add it: name as key , instance as value
                    subreddits[post_get_subreddit(post)] = vars(post)['subreddit']
        return subreddits 
    
def main():
    
    # We only need to parse command line flags if running as the main script
    argparser = argparse.ArgumentParser(
        description="Grab Saved Posts"
    )
    # The list of input files
    argparser.add_argument(
        "-d",
        "--database",
        type=str,
        help="the database to write to, which will be created if it does not exist",
        default="~/savedposts.sqlite3"
    )
    
    args = argparser.parse_args()
    
    # Set up the Reddit API
    reddit = praw.Reddit(client_id=credentials.login['clientID'],
                     client_secret=credentials.login['clientSecret'],
                     password=credentials.login['PASS'],
                     user_agent='RedditBot by /u/{}'.format(credentials.login['USER']),
                     username=credentials.login['USER'])

    # Set up the database
    database_setup(args.database)
    
    # Get saved reddit posts for your userid
    listofposts = reddit_getsavedposts(reddit,credentials.login['USER'])
    
    # Put saved posts into a database
    with sqlite3.connect(args.database) as con:
        cursor = con.cursor()
        for post in listofposts:
            database_insert_post(post, cursor)
        con.commit()
    
    # Get all the unique subreddits of the saved posts (e.g. 'r/nba','r/nba','r/nhl','r/nba','r/nfl' = nba,nhl,nfl )
    subreddits = get_saved_posts_subreddits(listofposts)
    
    # For each subreddit, get the subreddit info (this takes time) then add it to database
    # 
    # This takes significantly longer than getting the posts (1 call for all saved posts vs N calls for N subreddits)
    # Comment this out if you do not need this info 
    
    count = 0
    subs = str(len(subreddits))
    with sqlite3.connect(args.database) as con:
        print("Fetching subreddit information")
        cursor = con.cursor()
        for subreddit_name, subreddit_instance in subreddits.items():
            count+=1
            print(str(count)+" of "+subs+" subreddits. Current: "+subreddit_name)
            subreddit_instance.created #doing this will cause praw to grab subreddit info
            database_insert_subreddit(subreddit_instance, cursor)
        con.commit()

# Run the main program if called directly
if __name__ == "__main__":
    main()