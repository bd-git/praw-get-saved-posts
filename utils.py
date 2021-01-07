from pprint import pprint
import praw

def database_setup(cursor):
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
    is_saved integer NOT NULL,
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
    subscribers integer,
    accounts_active_is_fuzzed integer
    );
    """
    #audience_target text,
    #advertiser_category text,
    
    cursor.execute(POSTS_TABLE)
    cursor.execute(SUBREDDIT_TABLE)

def database_insert_post(_post, cursor):
    ''' poplulate the columns of our post database row then insert to database '''

    # We need to handle saved comments and saved submissions a little bit differently, first set up the things they have in common

    # TODO? For some reason i'm accessing the post information with an 'items' dict (vars dict of the post's class) instead of directly... fix this

    # ...first, set up the things they have in common
    items = vars(_post)
    postinfo =( items['id'],
                post_get_type(_post),
                int(post_is_selfpost(_post)),
                items['name'],
                post_get_subreddit(_post), #string representation of "praw.reddit.subreddit" instance
                items['subreddit_id'],
                items['subreddit_name_prefixed'],
                int(items['created_utc']),
                int(items['over_18']),
                1, # "is_saved"
                items['permalink']
                )
    
    # ...then, default the submission specific and comment specific columns to blank
    submissioninfo = tuple(['']*4) 
    commentinfo = tuple(['']*6) 
    
    # ...handle fields that are submission specific
    if post_is_submission(_post):
        submissioninfo = ( int(items['is_self']),
                items['selftext'],
                items['selftext_html'],
                items['url']
                )
                
    # ...handle fields that are comment specific
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
        cursor.execute("INSERT OR REPLACE INTO post VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", insert_row)
    except:
        pprint(insert_row)
        [print(type(val)) for val in insert_row]
        raise

def database_insert_subreddit(_subreddit_instance, cursor):
    items = vars(_subreddit_instance)
    print(f"Inserting subreddit {items['display_name']}")
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
        #items['audience_target'],
        #items['advertiser_category'],
        int(items['subscribers']),
        int(items['accounts_active_is_fuzzed'])
        )
    try:
        cursor.execute("INSERT INTO subreddit VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", subinfo)
    except:
        pprint(subinfo)
        [print(type(val)) for val in subinfo]
        raise
       
def reddit_get_saved_posts_dict(_redditinstance,_username,_limit=None):
	return {x.id:x for x in _redditinstance.redditor(name=_username).saved(limit=_limit)}
   
def trim_id(_linkid):
    _linkid=_linkid.strip()
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
    
def get_saved_posts_subreddits(in_dictofposts):
    """ loop thru a given list or dict of posts, return a dict of those posts unique subreddits where key is subreddit name, value is subreddit object"""
    subreddits = dict()
    for post_id,post in in_dictofposts.items():
        # post.subreddit_id will look something like 't5_a230zs' so trim t5_ then use it as key
        sub_id = trim_id(post.subreddit_id)
        try:
            subreddits[sub_id] #if this line succeeds, do nothing
        except KeyError:
            #if KeyError, subreddit not yet in dict so add it: name as key , instance as value
            subreddits[sub_id] = vars(post)['subreddit']
    return subreddits 

def database_get_posts_id(cursor):
    # query IDs of saved posts from database
    # since only getting one column, convert tuple of tuples to list
    return [x[0] for x in cursor.execute("select p.id from post p").fetchall()]

def database_get_subreddits_id(cursor):
    # query IDs of saved posts from database
    # since only getting one column, convert tuple of tuples to list
    return [x[0] for x in cursor.execute("select s.id from subreddit s").fetchall()]

def database_get_posts_id_type_ifsaved(cursor):
    # query IDs, type of saved posts from database
    return cursor.execute("select p.id, p.calc_type from post p where p.is_saved=1").fetchall()

def database_unsave_post(_postid, cursor):
    return cursor.execute("UPDATE post SET is_saved = 0 WHERE id = ? ", (_postid,))

def database_get_posts_subreddits(cursor):
    return [x[0] for x in cursor.execute("select p.subreddit_id from post p").fetchall()]

def database_get_subreddit_subreddits(cursor):
    return [x[0] for x in cursor.execute("select s.name from subreddit s").fetchall()] 

def database_delete_post(_postid, cursor):
    return cursor.execute("DELETE FROM post WHERE id = ?",(_postid,))

def database_delete_subreddit(_subredditid, cursor):
    cursor.execute("DELETE FROM subreddit WHERE id = ?",(_subredditid,))

def database_cleanup_subreddit_table(cursor):
    orphan_subreddits = cursor.execute("""
    select
        s.id
    from subreddit s 
    where s.name not in (select p.subreddit_id from post p)
    """).fetchall()
    for orphan in orphan_subreddits:
        database_delete_subreddit(orphan[0],cursor)

def database_find_missing_subreddits(cursor):
    missing_subreddits = cursor.execute("""
    select distinct
        p.subreddit
    from post p
    where p.subreddit_id not in (select s.name from subreddit s)
    """).fetchall()
    return missing_subreddits

if __name__ == "__main__":
    print("Import Me!")