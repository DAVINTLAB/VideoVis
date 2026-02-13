from collections import Counter

def get_author_comments(author, data, interval=30):
    author_comments = []
    for item in data:
        if item['author'] == author:
            author_comments.append(item)
    
    author_filtered_comments = [comment for comment in author_comments if comment['message'].strip()]
    return None, author_filtered_comments

def get_top_authors(data, n=5):
    filter_data = [item for item in data if item['message'].strip()]

    authors = [item['author'] for item in filter_data]
    author_freq = Counter(authors)

    top_authors = author_freq.most_common(n)
    return top_authors

