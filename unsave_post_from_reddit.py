import praw
import sqlite3
import argparse
import credentials
from pprint import pprint
from pathlib import Path
from tqdm import tqdm

def unsavepost_by_id(_postidstring,_posttype,_reddit):
    if _posttype == "t1":
        e = praw.models.Comment(_reddit, id=_postidstring)
    elif _posttype == "t3":
        e = praw.models.Submission(_reddit, id=_postidstring)
    e.unsave()
    #e.save()
    #e._fetch()

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
        default=Path(".") / "savedposts.sqlite3" #~/savedposts.sqlite3"
    )
    
    args = argparser.parse_args()
    
    # Set up the Reddit API
    reddit = praw.Reddit(client_id=credentials.login['clientID'],
                     client_secret=credentials.login['clientSecret'],
                     password=credentials.login['PASS'],
                     user_agent='RedditBot by /u/{}'.format(credentials.login['USER']),
                     username=credentials.login['USER'])

    # query IDs of saved posts from database
    with sqlite3.connect(args.database) as con:
        cursor = con.cursor()
        # the fetchall will return items as a list of tuple
        dbsavedposts = cursor.execute("select p.id, p.calc_type from post p").fetchall()

    print(f"About to unsave {len(dbsavedposts)} posts")
    pbar = tqdm(total=len(dbsavedposts))
    for post_id,post_type in dbsavedposts:
        unsavepost_by_id(post_id,post_type,reddit)
        pbar.update()
    pbar.close()

# Run the main program if called directly
if __name__ == "__main__":
    main()