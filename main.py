import asyncio
import threading
import requests
import operator
import time
import os
import sys

subreddit = 'dotnet'

BASE_URL = 'https://www.reddit.com/'
API_URL= 'https://oauth.reddit.com/'
HEADERS = {'User-Agent': 'PyRedditTracker by Certain_Albatross'}

POSTS = {}

# async I/O stuff
post_lock = threading.Lock()
stop_threads = threading.Event()

def update_post_statistics():
    while not stop_threads.is_set():
        time.sleep(10)  # Poll once every 10 seconds'
        author_counts = {}
        with post_lock:
            for post in POSTS.values():
                author = post['author']
                author_counts[author] = author_counts.get(author, 0) + post['ups']
        ordered_posts = sorted(author_counts.items(), key = lambda i: i[1], reverse=True)
        print("\nAuthor Statistics:")
        for author, value in ordered_posts[:5]:
            print(f"{author} - {value}")

        with post_lock:
            ordered_posts = sorted(POSTS.values(), key=operator.itemgetter('ups'), reverse=True)

        print("\nPost Statistics:")
        for post in ordered_posts[:5]:
            print(f"{post['title']} - {post['ups']} ({post['ups'] - post['downs']})")


def _make_throttled_request( url):
    while True:
        response = requests.get(API_URL+url, headers=HEADERS)
        if response.status_code == 429:  # Too Many Requests
            print("Rate limit exceeded. Retrying after a short delay...")
            time.sleep(1)  # Wait before retrying
            continue

        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            print(err)
            raise
        data = response.json()
        return data

def get_acess_token():
    data = {'grant_type': 'password', 'username': 'Certain_Albatross', 'password': 'iby5SC%X^Azq73%b'}
    auth = requests.auth.HTTPBasicAuth('7rYi6JTlp1Cno_3IwIPhGg', 'npQCEFf4xnHLxlZ2SfiXf6RsmaLlIA')
    response = requests.post(BASE_URL + 'api/v1/access_token', data=data, headers=HEADERS, auth=auth)
    response.raise_for_status()
    data = response.json()
    return data['access_token']

def poll_for_new_posts(subreddit):
    print(f"Polling for new posts in r/{subreddit}...")
    while not stop_threads.is_set():
        # Example endpoint to get hot posts from a subreddit
        data = _make_throttled_request(f"r/{subreddit}/new")
        for post in data['data']['children']:
            post_id = post['data']['id']
            with post_lock:
                POSTS[post_id] = post['data']
    print("Stopped polling for new posts.")


async def main():
    access_token = get_acess_token()
    # Use the access token in the Authorization header
    HEADERS['Authorization'] = f'Bearer {access_token}'
    t1 = threading.Thread(target=poll_for_new_posts, args=(subreddit,), daemon=True)
    t2 = threading.Thread(target=update_post_statistics, daemon=True)
    t1.start()
    t2.start()

    # We use to_thread for input() because input() is also blocking
    await asyncio.to_thread(sys.stdin.read, 1)

    # 4. Clean up
    stop_threads.set()
    print("Done!")

if __name__=="__main__":
    asyncio.run(main())

