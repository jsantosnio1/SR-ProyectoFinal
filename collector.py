import time

from selenium import webdriver
from selenium.common.exceptions import (NoSuchElementException,
                                        StaleElementReferenceException,
                                        WebDriverException)
from selenium.webdriver.common.keys import Keys 
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from bufferedQue import BufferedQue
from tweet import Tweet
from writer import Writer
from tweetDB import TweetDB

BASE_URL = "https://www.twitter.com/"


class Collector:

    _driver = None
    _Lsleep_seconds = 3.0
    _Msleep_seconds = 2.25
    _Ssleep_seconds = 1.5
    _process = False

    def __init__(self, username: str, password: str, chromePath=None, firefoxPath=None):
        """
            Collect tweets by using selenium.

                Args:
                    username (str): Twitter account's username
                    password (str): Twitter account's password
                    chromePath (str): File path of executable chromedriver
                    firefoxPath (str): File path of executable firefox webdriver (geckodriver)
        """
        count = 0
        while count < 5:
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-features=NetworkService") ##this did it for me
            chrome_options.add_argument("--window-size=1920x1080")
            chrome_options.add_argument("--disable-features=VizDisplayCompositor")
            try:
                if chromePath is None:
                    if firefoxPath is None:
                        self._driver = webdriver.Chrome(
                           executable_path="chromedriver",
                           chrome_options=chrome_options)
                    else:
                        self._driver = webdriver.Firefox(
                            executable_path="geckodriver")
                else:
                    self._driver = webdriver.Chrome(executable_path=chromePath,
                                                    chrome_options=chrome_options)

                time.sleep(self._Msleep_seconds)
                count = 6
            except Exception as e:
                print(e)
                if self._driver:
                    self._driver.quit()
                time.sleep(5)
            count += 1

        if count == 5:
            print("Failed to start and login.")

    def search(self, searchKey: str, tabName="top", from_=None, to_=None, lang=None) -> None:
        """
            Method that makes searchs on twitter search engine on specified tab
            and/or specific time intervals.

                Args:
                    `searchKey` (str): Key word(s) to searh on twitter
                    `tabname` (str): section name to filter results
                        there are 4 options:
                            top (default): default twitter listing
                            live (Latest): list result according to dates in
                                           ascending order
                            user (People): list related users
                            image (Photos): list related photos
                            video (Videos): list realted videos
                    `from_` (datetime.date): starting date of filtering
                    `to_` (datetime.date): end date of filtering
        """
        tab_str = f"&f={tabName}" if tabName != "top" else ""
        from_str = f"%20since%3A{str(from_)}" if from_ is not None else ""
        to_str = f"%20until%3A{str(to_)}" if to_ is not None else ""
        lang_str = f"%20lang%3A{str(lang)}" if lang is not None else ""
        searchKey = searchKey.replace(' ', '%20')

        search_str = BASE_URL + "search?q=" + searchKey + \
            to_str + from_str + lang_str + "&src=typed_query" + tab_str

        print(search_str)
        self._driver.get(search_str)
        time.sleep(self._Msleep_seconds)

    def retrieve_tweets_to_database(self, searchKey, database: TweetDB, lang='en'):
        """
            Method to obtain tweets from driver.

                Args:
                    `searchKey` (str): search key
                    `database` (TweetDB): database instance to insert tweets in
        """
        retrieved_count = 0
        scroll_height = 0
        try_count = 0
        bufque = BufferedQue(50)
        self._process = True

        # Collect tweets until enough different tweet is collected
        while try_count < 5 and self._process:
            # Control if reached the end
            new_scroll_height = self._driver.execute_script(
                "return document.documentElement.scrollHeight")
            if abs(scroll_height - new_scroll_height) < 5:
                try_count += 1
            else:
                try_count = 0
                scroll_height = new_scroll_height

            # Obtain raw tweet elements
            #tweet_webElements = WebDriverWait(self._driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, "css-1dbjc4n r-1loqt21 r-18u37iz r-1ny4l3l r-1udh08x r-1qhn6m8 r-i023vh r-o7ynqc r-6416eg")))
            tweet_webElements = self._driver.find_elements_by_xpath(
                "//div[@data-testid='tweet']")
            print('HOLADB')
            #print(tweet_webElements)

            # Iterate over raw tweets to extract detailed indormation and insert to database
            for elem in tweet_webElements:
                try:
                    #tweet_id = WebDriverWait(self._driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, "css-4rbku5 css-18t94o4 css-901oao r-14j79pv r-1loqt21 r-1q142lx r-37j5jr r-a023e6 r-16dba41 r-rjixqe r-bcqeeo r-3s2u2q r-qvutc0")).get_attribute('href').split('/')[-1])
                    tweet_id = int(elem.find_element_by_xpath(
                        ".//a[contains(@href, '/status/')]").get_attribute('href').split('/')[-1])
                    # Check if tweet exist in bufque, if so continue to next one
                    if bufque.contains(tweet_id):
                        continue

                    #writer = WebDriverWait(self._driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, "css-901oao css-16my406 r-poiln3 r-bcqeeo r-qvutc0"))).text.replace('@', '')
                    writer = elem.find_element_by_xpath(
                        ".//div[@dir='ltr']").text.replace('@', '')
                    post_date = time.strptime(elem.find_element_by_xpath(
                        ".//time").get_attribute("datetime"), "%Y-%m-%dT%H:%M:%S.000Z")
                    try:
                        body = elem.find_element_by_xpath(
                            f".//div[@lang='{lang}' and @dir='auto']").text.replace('\n', '')
                    except NoSuchElementException:
                        continue
                    try:
                        comment_num = int(elem.find_element_by_xpath(
                            ".//div[@data-testid='reply']").text)
                    except ValueError:
                        comment_num = 0
                    try:
                        retweet_num = int(elem.find_element_by_xpath(
                            ".//div[@data-testid='retweet']").text)
                    except ValueError:
                        retweet_num = 0
                    try:
                        like_num = int(elem.find_element_by_xpath(
                            ".//div[@data-testid='like']").text)
                    except ValueError:
                        like_num = 0
                except (StaleElementReferenceException, NoSuchElementException):
                    try:
                        print("Exception during collection of tweet:", writer)
                    except NameError:
                        pass
                    continue

                # Add tweet to bufferedque
                tweet = Tweet(tweet_id=tweet_id, writer=writer, post_date=post_date,
                              body=body, searchKey=searchKey, comment_num=comment_num,
                              retweet_num=retweet_num, like_num=like_num)
                overhead_tweet = bufque.add(tweet_id, tweet)

                # Insert tweet to database
                if overhead_tweet is not None:
                    database.insert_tweet(overhead_tweet)
                retrieved_count += 1

            # Scroll page down
            self._driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(self._Ssleep_seconds)

            # Process information
            try:
                last_date = time.strftime("%Y-%m-%d", tweet.post_date)
                print(
                    f"Last retrieved date: {last_date}({retrieved_count})-try count: {try_count}")
            except UnboundLocalError:
                print(f"No tweets - try count: {try_count}")

        database.insert_tweets(bufque.toList())
        print("Cannot retrieve new tweets. Finisihing...")

    def retrieve_tweets_to_container(self, searchKey, container: list, lang='en'):
        """
            Method to obtain tweets from driver.

                Args:
                    `searchKey` (str): search key of tweets
                    `container` (list)   : container instance to append tweets
        """
        retrieved_count = 0
        scroll_height = 0
        try_count = 0
        bufque = BufferedQue(50)
        self._process = True

        # Collect tweets until enough different tweet is collected
        while try_count < 5 and self._process:
            # Control if reached the end
            new_scroll_height = self._driver.execute_script(
                "return document.documentElement.scrollHeight")
            if abs(scroll_height - new_scroll_height) < 5:
                try_count += 1
            else:
                try_count = 0
                scroll_height = new_scroll_height

            # Obtain raw tweet elements
            #tweet_webElements = WebDriverWait(self._driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, "css-1dbjc4n r-1loqt21 r-18u37iz r-1ny4l3l r-1udh08x r-1qhn6m8 r-i023vh r-o7ynqc r-6416eg")))
            tweet_webElements = self._driver.find_elements(By.XPATH, '/html/body/div/div/div/div[2]/main/div/div/div/div/div/div[2]/div/div/section/div/div/div/div/div/article')
            #tweet_webElements = self._driver.find_elements_by_xpath(
             #   "//div[@data-testid='tweet']")
            print('holaCON')
            #print(len(tweet_webElements))
            # Iterate over raw tweets to extract detailed indormation and append to container
            for elem in tweet_webElements:
                try:
                    #tweet_id = WebDriverWait(self._driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, "css-4rbku5 css-18t94o4 css-901oao r-14j79pv r-1loqt21 r-1q142lx r-37j5jr r-a023e6 r-16dba41 r-rjixqe r-bcqeeo r-3s2u2q r-qvutc0")).get_attribute('href').split('/')[-1])
                    tweet_id = int(elem.find_element_by_xpath(
                        ".//a[contains(@href, '/status/')]").get_attribute('href').split('/')[-1])
                    # Check if tweet exist in bufque, if so continue to next one
                    if bufque.contains(tweet_id):
                        continue

                    #writer = WebDriverWait(self._driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, "css-901oao css-16my406 r-poiln3 r-bcqeeo r-qvutc0"))).text.replace('@', '')
                    writer = elem.find_element_by_xpath(
                        ".//div[@dir='ltr']").text.replace('@', '')
                    post_date = time.strptime(elem.find_element_by_xpath(
                        ".//time").get_attribute("datetime"), "%Y-%m-%dT%H:%M:%S.000Z")
                    try:
                        body = elem.find_element_by_xpath(
                            f".//div[@lang='{lang}' and @dir='auto']").text.replace('\n', '')
                    except NoSuchElementException:
                        continue
                    try:
                        comment_num = int(elem.find_element_by_xpath(
                            ".//div[@data-testid='reply']").text)
                    except ValueError:
                        comment_num = 0
                    try:
                        retweet_num = int(elem.find_element_by_xpath(
                            ".//div[@data-testid='retweet']").text)
                    except ValueError:
                        retweet_num = 0
                    try:
                        like_num = int(elem.find_element_by_xpath(
                            ".//div[@data-testid='like']").text)
                    except ValueError:
                        like_num = 0
                except (StaleElementReferenceException, NoSuchElementException):
                    try:
                        print("Exception during collection of tweet:", writer)
                    except NameError:
                        pass
                    continue

                # Add tweet to bufferedque
                tweet = Tweet(tweet_id=tweet_id, writer=writer,
                              post_date=post_date, body=body,
                              searchKey=searchKey,
                              comment_num=comment_num, retweet_num=retweet_num,
                              like_num=like_num)
                overhead_tweet = bufque.add(tweet_id, tweet)

                # Insert tweet to container
                if overhead_tweet is not None:
                    container.append(overhead_tweet)
                retrieved_count += 1

            # Scroll page down
            self._driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(self._Ssleep_seconds)

            # Process information
            try:
                last_date = time.strftime("%Y-%m-%d", tweet.post_date)
                print(
                    f"Last retrieved date: {last_date}({retrieved_count})-try count: {try_count}")
            except UnboundLocalError:
                print(f"No tweets - try count: {try_count}")

        container.extend(bufque.toList())
        print("Cannot retrieve new tweets. Finisihing...")

    def insert_unreachable_writer(self, database: TweetDB, user_id: str, status: str):
        database.c.execute("INSERT INTO UnreachableWriter VALUES (:user_id, :status)",
                           {'user_id': user_id, 'status': status})

    def fetch_unreachable_writer(self, database: TweetDB):
        database.c.execute("SELECT * FROM UnreachableWriter")
        return database.c.fetchall()

    def classify_unreachable_writer(self):
        try:
            self._driver.find_element_by_xpath(
                "//*[contains(text(), 'This account doesn')]")
            return "existance"
        except NoSuchElementException:
            try:
                self._driver.find_element_by_xpath(
                    "//*[contains(text(), 'Account suspended')]")
                return "suspended"
            except NoSuchElementException:
                return None

    def retrieve_writers_to_db(self, database: TweetDB, passed_writers=[]):
        user_ids = [i[0] for i in database.get_companies_by_query(
            """ SELECT DISTINCT writer 
                FROM Tweet
                EXCEPT
                SELECT user_id
                FROM Writer
            """)]
        writers = list()

        for passed_writer in self.fetch_unreachable_writer(database):
            if not passed_writer[0] in passed_writers:
                passed_writers.append(passed_writer[0])

        try:
            for idx, user_id in enumerate(user_ids):
                if user_id in passed_writers:
                    print("instant passed writer:", user_id)
                    continue

                self._driver.get(f"https://www.twitter.com/{user_id}")
                time.sleep(self._Msleep_seconds)

                username = self._driver.find_element_by_xpath(
                    "//h2[@aria-level='2' and @role='heading' and @dir='ltr']").text
                    #"/html/body/div/div/div/div[2]/main/div/div/div/div/div/div[2]/div/div/div[1]/div/div[2]/div/div/div[2]/div/span").text

                # try-catch to handle restricted accounts
                try:
                    following = int(self._driver.find_element_by_xpath(
                        f"//a[contains(@href, '{user_id}/following')]").get_attribute('title').replace(',', ''))
                except NoSuchElementException:
                    try:
                        try:
                            following = int(self._driver.find_element_by_xpath(
                                "//div[@dir='auto' and @role='button']").get_attribute('title').replace(',', ''))
                        except NoSuchElementException:
                            self._driver.find_element_by_xpath(
                                "//span[contains(text(), 'Yes, view profile')]").click()
                            time.sleep(self._Ssleep_seconds)
                            following = int(self._driver.find_element_by_xpath(
                                f"//a[contains(@href, '{user_id}/following')]").get_attribute('title').replace(',', ''))
                    except NoSuchElementException:
                        passed_writers.append(user_id)
                        status = self.classify_unreachable_writer()
                        if status:
                            self.insert_unreachable_writer(database,
                                                           user_id, status)
                        print(f"passed writer:{user_id} - {status}")
                        continue

                # Follower count data
                try:
                    follower = int(self._driver.find_element_by_xpath(
                        f"//a[contains(@href, '{user_id}/follower')]").get_attribute('title').replace(',', ''))
                except NoSuchElementException:
                    try:
                        follower = following = int(self._driver.find_elements_by_xpath(
                            "//div[@dir='auto' and @role='button']")[1].get_attribute('title').replace(',', ''))
                    except NoSuchElementException:
                        print("passed writer:", user_id)
                        passed_writers.append(user_id)
                        continue

                # Tweet count data
                try:
                    tweet_count = self.number_converter(self._driver.find_element_by_xpath(
                        "//div[@dir='auto' and contains(text(), ' Tweets')]").text.split(' ')[0])
                except NoSuchElementException:
                    tweet_count = 0

                # Bio text data
                try:
                    bio_text = self._driver.find_element_by_xpath(
                        "//div[@data-testid='UserDescription']").text.replace('\n', '')
                except NoSuchElementException:
                    bio_text = None
                user_profile_items = self._driver.find_element_by_xpath(
                    "//div[@data-testid='UserProfileHeader_Items']")

                # Website link data
                try:
                    website = user_profile_items.find_element_by_xpath(
                        "//a[@target='_blank']").text
                except NoSuchElementException:
                    website = None

                # Born date data
                try:
                    born_text = user_profile_items.find_element_by_xpath(
                        "//span[contains(text(), 'Born')]").text
                    if born_text.find(',') > -1:
                        born = time.strptime(born_text, "Born %B %d, %Y")
                    else:
                        born = time.strptime(born_text, "Born %B %d")
                except NoSuchElementException:
                    born_text = ""
                    born = None
                except ValueError:
                    born = None

                # Joined date data
                try:
                    joined_text = user_profile_items.find_element_by_xpath(
                        "//span[contains(text(), 'Joined') and not(contains(text(), 'Twitter'))]").text
                    joined = time.strptime(joined_text, "Joined %B %Y")
                except:
                    continue

                # Location text data
                location = user_profile_items.text.replace(born_text, '').replace(
                    joined_text, '').replace(website if website else "", '')
                if len(location) <= 0:
                    location = None

                writers.append(Writer(user_id=user_id, username=username,
                                      following=following, follower=follower,
                                      tweet_count=tweet_count, bio_text=bio_text,
                                      location=location, website=website, born=born,
                                      joined=joined))

                # insertion operation
                if len(writers) > 10:
                    print("Inserting writers to database")
                    database.insert_writers(writers)
                    writers = list()
                print(f"{idx}/{len(user_ids)}, {user_id}")
            print("writer collecting is finished")
            database.insert_writers(writers)
        except Exception as e:
            print(e)
            return False, passed_writers
        return True, passed_writers

    @staticmethod
    def number_converter(number_string: str, return_type=int):
        number_string = number_string.replace(',', '')
        if number_string.find('K') > -1:
            return return_type(float(number_string.replace('K', ''))*10e3)
        if number_string.find('M') > -1:
            return return_type(float(number_string.replace('M', ''))*10e6)
        return return_type(number_string)

    def closeAll(self):
        self._driver.quit()