import praw
import sqlite3
import argparse
import credentials
from pprint import pprint
from pathlib import Path
from tqdm import tqdm
import logging
import utils

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
    logging.info("Setting up the reddit connection")
    reddit = praw.Reddit(client_id=credentials.login['clientID'],
                     client_secret=credentials.login['clientSecret'],
                     password=credentials.login['PASS'],
                     user_agent='RedditBot by /u/{}'.format(credentials.login['USER']),
                     username=credentials.login['USER'])

    # Set up the database
    logging.info(f"Setting up the sqlite database file with post and subreddit tables if they don't already exist: {args.database=}")
    with sqlite3.connect(args.database) as con:
        cursor = con.cursor()
        utils.database_setup(cursor)
        con.commit()
    
    # Get saved reddit posts for your userid
    logging.info(f"Using PRAW to get saved posts for user: {credentials.login['USER']=}")
    dictofposts = utils.reddit_get_saved_posts_dict(reddit,credentials.login['USER'])
    logging.info(f"Collected {len(dictofposts)} saved posts ")
    # Get all the unique subreddits of the saved posts (e.g. 'r/nba','r/nba','r/nhl','r/nba','r/nfl' = nba,nhl,nfl )
    dictofsubreddits = utils.get_saved_posts_subreddits(dictofposts)   
    logging.info(f"Saved posts belong to {len(dictofsubreddits)} unique subreddits ")
    
    # Start populating / modifying our database
    with sqlite3.connect(args.database) as con:
        # Create a db cursor object to send into our utility functions
        cursor = con.cursor()

        # Lets first run a query on our tables to see what is there. 
        # The ids that these functions return will be unique because id is a PK
        # However, we want to save these ids as sets because set is hashable for O(1) lookups
        existing_db_post_ids = set(utils.database_get_posts_id(cursor))
        existing_db_subreddit_ids = set(utils.database_get_subreddits_id(cursor))

        # Put saved posts into a database
        logging.info(f"Inserting posts into database file if not already exist")
        pbar = tqdm(total=len(dictofposts))
        inserts = 0
        for post_id, post in dictofposts.items():
            if post_id not in existing_db_post_ids:
                utils.database_insert_post(post, cursor)
                inserts+=1
            pbar.update()
        pbar.close()
        logging.info(f"Post insert complete, inserted {inserts} posts, committing to database")
        con.commit()

        # For each subreddit, get the subreddit info (this takes time) then add it to database
        # This takes significantly longer than getting the posts (1 call for all saved posts vs N calls for N subreddits)
        logging.info("About to fetch information about the individual subreddits, will insert into database if not already exist")
        pbar = tqdm(total=len(dictofsubreddits))
        inserts = 0
        for subreddit_id, subreddit_instance in dictofsubreddits.items():
            # The subreddit_instance is just a PRAW 'subreddit class' shell taken from the saved post's 'post class' 
            # Calling the subreddit class's "created" method below causes the class to grab this info (and the rest of the subreddit's info too...)
            if subreddit_id not in existing_db_subreddit_ids:
                # calling .created below causes PRAW to do a fetch
                subreddit_instance.created
                # our subreddit_instance now looks much different, data fields are now populated, now ready to insert into database
                utils.database_insert_subreddit(subreddit_instance, cursor)
                # lets commit after each subreddit is queried and inserted
                con.commit() 
                inserts+=1
            pbar.update()
        
        pbar.close()
        logging.info(f"Subreddit insert complete, inserted {inserts} subreddits, committing to database")

        logging.info(f"Check for missing subreddit table rows, then commit to database")
        missing_subreddits = [x[0] for x in utils.database_find_missing_subreddits(cursor)]

        if len(missing_subreddits)>0:
            for sub in missing_subreddits:
                subreddit_instance = reddit.subreddit(sub)
                subreddit_instance._fetch()
                utils.database_insert_subreddit(subreddit_instance, cursor)
            con.commit()

        logging.info(f"Clean-up orphan subreddit table rows, then commit to database")
        utils.database_cleanup_subreddit_table(cursor)
        con.commit()
        
# Run the main program if called directly
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(funcName)s - %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', handlers=[ logging.StreamHandler() ] ) # logging.FileHandler("debug.log.txt",mode="w"),
    main()