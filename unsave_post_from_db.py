import praw
import sqlite3
import argparse
import credentials
from pprint import pprint
from pathlib import Path
from tqdm import tqdm
import logging
import utils

def unsave_post_by_id(_postidstring,_posttype,_reddit):
    if _posttype == "t1":
        p = praw.models.Comment(_reddit, id=_postidstring)
    elif _posttype == "t3":
        p = praw.models.Submission(_reddit, id=_postidstring)
    p.unsave()
    return True

def save_post_by_id(_postidstring,_posttype,_reddit):
    if _posttype == "t1":
        p = praw.models.Comment(_reddit, id=_postidstring)
    elif _posttype == "t3":
        p = praw.models.Submission(_reddit, id=_postidstring)
    p.save()
    return True

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
    
    # Start populating / modifying our database
    with sqlite3.connect(args.database) as con:
        # Create a db cursor object to send into our utility functions
        cursor = con.cursor()

        # Lets first run a query on our post table 
        existing_db_saved_posts_id_type = utils.database_get_posts_id_type_ifsaved(cursor)
        num_saved_posts = len(existing_db_saved_posts_id_type)
        logging.info(f"Found {num_saved_posts=} in db")

        if num_saved_posts>0:
            # Set up the Reddit API
            logging.info("Setting up the reddit connection")
            reddit = praw.Reddit(client_id=credentials.login['clientID'],
                            client_secret=credentials.login['clientSecret'],
                            password=credentials.login['PASS'],
                            user_agent='RedditBot by /u/{}'.format(credentials.login['USER']),
                            username=credentials.login['USER'])
            pbar = tqdm(total=num_saved_posts)
            for post_id, post_type in existing_db_saved_posts_id_type:
                success = unsave_post_by_id(post_id,post_type,reddit)
                if success:
                    result = utils.database_unsave_post(post_id,cursor)
                    con.commit()
                pbar.update()
            pbar.close()

        
# Run the main program if called directly
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(funcName)s - %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', handlers=[ logging.StreamHandler() ] ) # logging.FileHandler("debug.log.txt",mode="w"),
    main()