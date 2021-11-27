import datetime
import json
import os
import time
from multiprocessing import cpu_count
from threading import Thread

from collector import Collector, WebDriverException
from tweetDB import TweetDB

class Args:

    def __init__(self, searchKey, start_date,end_date):
        self.searchKey = searchKey
        self.search_as = "stock"
        self.start_date = start_date
        self.end_date = end_date
        self.lang = 'en'
        self.settings_file = True
args = []
container_pool = ""
db_conn = ""
THREAD_COUNT = ""
DATE_START = ""
DATE_END = ""
USERNAME =""
PASSWORD=""
CHROMEDRIVER_PATH=""
DAY =""
STEP=""
SEARCH_AS=""
KEY=""
LANG=""

def  setArgs(searchKey):
    global args, run

    start_date=datetime.date.today()
    end_date= datetime.date.today()
    args= Args(searchKey,start_date,end_date)



def get_missing_dates(reverse_sorted: bool = False) -> list:
    """Returns missing dates between DATE_START and DATE_END 
    that are fetched from database"""
    c = db_conn.conn.cursor()
    c.execute("SELECT DISTINCT post_date FROM Tweet")
    collected_dates = set([datetime.date.fromtimestamp(i[0])
                           for i in c.fetchall()])
    c.close()

    all_dates = set([DATE_START + datetime.timedelta(days=i)
                     for i in range((DATE_END-DATE_START).days)])

    return sorted(all_dates - collected_dates, reverse=reverse_sorted)


def search_tweets_by_date_to_container(date: datetime.date, container: list):
    """Main searching function that runs on thread"""
    collector = Collector(USERNAME, PASSWORD, chromePath=CHROMEDRIVER_PATH)

    from_ = date
    to_ = date + DAY*STEP

    print(f"Collecting {KEY}: {from_} - {to_}")

    try:
        collector.search(SEARCH_AS + KEY, tabName='live',
                         from_=from_, to_=to_, lang=LANG)
        collector.retrieve_tweets_to_container(KEY, container, lang=LANG)
    except WebDriverException as e:
        print(f"An error occured in browser:\n{str(e)}\nClosing browser...")
        collector.closeAll()
    finally:
        container_pool.append(container)


def container_collection(container: list):
    """pushes content of container to database and empties the container"""
    while len(container) > 0:
        db_conn.insert_tweet(container.pop())
    db_conn.conn.commit()


def collection_process(dates_list: list):
    """Searching process controller funtion. 
    Opens threads and manages containers"""
    while len(dates_list) > 0:
        if len(container_pool) > 0:
            process_container = container_pool.pop()
            container_collection(process_container)

            process_date = dates_list.pop()

            def target_func():
                search_tweets_by_date_to_container(process_date,
                                                   process_container)

            Thread(target=target_func).start()

        else:
            time.sleep(3)

    while len(container_pool) != THREAD_COUNT:
        time.sleep(3)

    for container in container_pool:
        container_collection(container)


def run():
    global container_pool, db_conn, THREAD_COUNT, DATE_START,DATE_END, USERNAME, PASSWORD, CHROMEDRIVER_PATH, DAY, STEP, SEARCH_AS, KEY, LANG

    if args.settings_file:
        with open("settings.json", 'r') as settings_file:
            settings = json.load(settings_file)

        USERNAME = settings["username"]
        PASSWORD = settings["password"]

        CHROMEDRIVER_PATH = settings["chromedriver_path"]
        THREAD_COUNT = (settings["thread_count"]
                        if settings["thread_count"] else cpu_count() * 2 - 1)

        MISSING_DATES_TRIAL_COUNT = settings["missing_run_count"]

    if not os.path.isfile(CHROMEDRIVER_PATH):
        raise ValueError(f"missing chromedriver file: {CHROMEDRIVER_PATH}")

    if args.search_as == 'tag':
        if args.searchKey.startswith('$'):
            print("WARNING: key starts with '$' but search_as selected as 'tag'. Consider using '-a stock'")
        SEARCH_AS = '%23'
    elif args.search_as == 'stock':
        if args.searchKey.startswith('#'):
            print("WARNING: key starts with '#' but search_as selected as 'stock'. Consider using '-a tag'")
        SEARCH_AS = '%24'
    elif args.search_as == 'word':
        if args.searchKey.startswith('$'):
            print("WARNING: key starts with '$' but search_as selected as 'word'. Consider using '-a word'")
        elif args.searchKey.startswith('#'):
            print("WARNING: key starts with '#' but search_as selected as 'word'. Consider using '-a word'")
        SEARCH_AS = ''

    KEY = args.searchKey.replace('$', '').replace('#', '')

    LANG = args.lang

    DATE_START = datetime.datetime.strptime("2021-11-24", "%Y-%m-%d").date()
    DATE_END = datetime.datetime.strptime("2021-11-25", "%Y-%m-%d").date()
    DAY = datetime.timedelta(days=1)
    STEP = 1

    print(f"Collector is starting with {THREAD_COUNT} threads.")

    db_conn = TweetDB(f"{KEY}_{DATE_START}-{DATE_END}")
    db_conn.create_tables()

    container_pool = [list() for _ in range(THREAD_COUNT)]

    t0 = time.time()

    # extract dates
    target_dates = sorted([DATE_START + datetime.timedelta(days=i)
                        for i in range((DATE_END-DATE_START).days)],
                        reverse=True)
    # start collection
    collection_process(target_dates)

    # start collection for missing dates
    for _ in range(MISSING_DATES_TRIAL_COUNT):
        missing_dates = get_missing_dates(reverse_sorted=True)
        print(f"Number of missing days: {len(missing_dates)}")

        if len(missing_dates) > 0:
            break

        collection_process(missing_dates)

    print(f"Collector finished in {datetime.timedelta(seconds=time.time() - t0)}")
