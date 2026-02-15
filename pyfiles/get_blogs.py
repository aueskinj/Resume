import feedparser

# 1. Fetch the feed
url = "https://medium.com/feed/@austinkmhi"
feed = feedparser.parse(url)

# 2. Extract data for your UI
for entry in feed.entries:
    print(f"Title: {entry.title}")
    print(f"Link: {entry.link}")
    print(f"Date: {entry.published}")
    
    # Check if tags exist before accessing them
    if hasattr(entry, 'tags'):
        print(f"Tags: {[tag.term for tag in entry.tags]}")
    else:
        print("Tags: None")
    
    print("---")