import praw
import pandas as pd
import numpy as np
import re
import json
from datetime import datetime
import matplotlib.pyplot as plt
from dotenv import load_dotenv
import os

load_dotenv()

# Set up absolute paths so it works from anywhere
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')

# DATA COLLECTION WITH PRAW

def authenticate_reddit():
    reddit = praw.Reddit(
        client_id=os.getenv('REDDIT_CLIENT_ID'),
        client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
        user_agent=os.getenv('REDDIT_USER_AGENT')
    )
    return reddit

def collect_reddit_data(reddit, subreddits, posts_per_sub=10, comments_per_post=50):
    # Collect posts and comments from specified subreddits. Returns list of dicts containing post and comment data
    data = []
    
    for subreddit_name in subreddits:
        print(f"Collecting from r/{subreddit_name}...")
        subreddit = reddit.subreddit(subreddit_name)
        
        # Get top posts from the week
        for post in subreddit.top(time_filter='week', limit=posts_per_sub):
            post_entry = {
                'post_id': post.id,
                'subreddit': subreddit_name,
                'title': post.title,
                'selftext': post.selftext,
                'score': post.score,
                'num_comments': post.num_comments,
                'created_utc': post.created_utc,
                'comments': []
            }
            
            # Collect comments
            post.comments.replace_more(limit=0)  # Remove "MoreComments" objects
            for i, comment in enumerate(post.comments.list()):
                if i >= comments_per_post:
                    break
                
                comment_entry = {
                    'comment_id': comment.id,
                    'body': comment.body,
                    'score': comment.score,
                    'created_utc': comment.created_utc
                }
                post_entry['comments'].append(comment_entry)
            
            data.append(post_entry)
            print(f"  Collected post '{post.title[:50]}...' with {len(post_entry['comments'])} comments")
    
    return data

def save_raw_data(data, filename='raw_reddit_data.json'):
    # Save collected data to JSON file in root data/ folder.
    filepath = os.path.join(DATA_DIR, filename)
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(data)} posts to {filepath}")


def fetch_post_and_comments(url: str, max_comments: int = 500) -> dict:
    # Fetches a post by URL and returns dict with post and comments
    
    reddit = authenticate_reddit()
    subm = reddit.submission(url=url)
    subm.comments.replace_more(limit=0)

    post = {
        "post_id": subm.id,
        "subreddit": str(subm.subreddit),
        "title": clean_text(subm.title),
        "selftext": clean_text(subm.selftext or ""),
        "score": int(subm.score),
        "num_comments": int(subm.num_comments),
        "created_utc": float(subm.created_utc),
    }

    comments = []
    for index, comment in enumerate(subm.comments.list()):
        if index >= max_comments:
            break
        body = clean_text(comment.body or "")
        comments.append({
            "id": comment.id,
            "body": body,
            "score": int(getattr(comment, "score", 0) or 0),
            "created_utc": float(getattr(comment, "created_utc", 0.0) or 0.0),
        })

    return {"post": post, "comments": comments}


# DATA PREPROCESSING

def clean_text(text):
    # Clean text by removing URLs, special characters, extra whitespace.

    if not isinstance(text, str):
        return ""
    
    # Remove URLs
    text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
    
    # Remove emails
    text = re.sub(r'\S+@\S+', '', text)
    
    # Remove special characters (but keep basic punctuation)
    text = re.sub(r'[^a-zA-Z0-9\s\.\!\?\,\-\']', '', text)
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def validate_data_completeness(data):
    # Validate that collected data has all required fields and handle edge cases.
    # Returns cleaned data with invalid entries removed.
    valid_posts = []
    removed_count = 0
    
    for post in data:
        # Check if post has all required fields
        required_post_fields = ['post_id', 'subreddit', 'title', 'comments']
        if not all(field in post for field in required_post_fields):
            removed_count += 1
            continue
        
        # Skip deleted or removed posts
        if post['title'] == '[deleted]' or post['title'] == '[removed]':
            removed_count += 1
            continue
        
        # Validate comments
        valid_comments = []
        for comment in post['comments']:
            required_comment_fields = ['comment_id', 'body', 'score']
            if not all(field in comment for field in required_comment_fields):
                continue
            
            # Skip deleted/removed comments
            if comment['body'] in ['[deleted]', '[removed]', '']:
                continue
            
            valid_comments.append(comment)
        
        # Only keep posts with at least 1 valid comment
        if valid_comments:
            post['comments'] = valid_comments
            valid_posts.append(post)
        else:
            removed_count += 1
    
    print(f"\nData Validation: Removed {removed_count} invalid posts")
    print(f"Kept {len(valid_posts)} valid posts with valid comments")
    
    return valid_posts

def preprocess_reddit_data(data):
    # Convert raw Reddit data into clean dataframes with posts and comments.
    # Includes controversy metrics. 
    # Returns tuple of (posts_df, comments_df)

    posts_list = []
    comments_list = []
    
    for post in data:
        # Calculate controversy metrics for comments
        comment_scores = [c['score'] for c in post['comments']]
        
        if comment_scores:
            # Controversy: how much disagreement in voting
            # High std dev = mixed opinions
            comment_score_std = np.std(comment_scores)
            avg_comment_score = np.mean(comment_scores)
            
            # Controversy ratio: mix of positive and negative
            positive_comments = sum(1 for s in comment_scores if s > 0)
            negative_comments = sum(1 for s in comment_scores if s < 0)
            total_comments = len(comment_scores)
            
            # Higher when both positive and negative exist
            controversy_ratio = (positive_comments * negative_comments) / (total_comments ** 2) if total_comments > 0 else 0
        else:
            comment_score_std = 0
            avg_comment_score = 0
            positive_comments = 0
            negative_comments = 0
            controversy_ratio = 0
        
        # Add post to posts list
        posts_list.append({
            'post_id': post['post_id'],
            'subreddit': post['subreddit'],
            'title': clean_text(post['title']),
            'selftext': clean_text(post['selftext']),
            'score': post['score'],
            'num_comments': post['num_comments'],
            'created_utc': post['created_utc'],
            'total_comments_collected': len(post['comments']),
            'avg_comment_score': avg_comment_score,
            'comment_score_std': comment_score_std,
            'positive_comments_count': positive_comments,
            'negative_comments_count': negative_comments,
            'controversy_ratio': controversy_ratio
        })
        
        # Add comments
        for comment in post['comments']:
            comments_list.append({
                'post_id': post['post_id'],
                'comment_id': comment['comment_id'],
                'text': clean_text(comment['body']),
                'score': comment['score'],
                'created_utc': comment['created_utc']
            })
    
    posts_df = pd.DataFrame(posts_list)
    comments_df = pd.DataFrame(comments_list)
    
    # Remove duplicates
    posts_df = posts_df.drop_duplicates(subset=['post_id'])
    comments_df = comments_df.drop_duplicates(subset=['comment_id'])
    
    print(f"\nDuplicate Removal: {len(posts_df)} unique posts, {len(comments_df)} unique comments")
    
    return posts_df, comments_df

def save_preprocessed_data(posts_df, comments_df):
    # Save preprocessed data to CSV in root data/ folder.
    os.makedirs(DATA_DIR, exist_ok=True)
    posts_df.to_csv(os.path.join(DATA_DIR, 'posts_preprocessed.csv'), index=False)
    comments_df.to_csv(os.path.join(DATA_DIR, 'comments_preprocessed.csv'), index=False)
    print("Saved preprocessed data to data/ folder")

# EXPLORATORY DATA ANALYSIS (EDA)

def generate_eda_report(posts_df, comments_df):
    # Generate exploratory data analysis with statistics and visualizations
    report = {
        'total_posts': len(posts_df),
        'total_comments': len(comments_df),
        'avg_comments_per_post': comments_df.groupby('post_id').size().mean(),
        'total_subreddits': posts_df['subreddit'].nunique(),
        'subreddit_distribution': posts_df['subreddit'].value_counts().to_dict(),
        'avg_post_score': posts_df['score'].mean(),
        'avg_comment_score': comments_df['score'].mean(),
        'avg_comment_length': comments_df['text'].str.len().mean(),
        'median_comment_length': comments_df['text'].str.len().median(),
        'comments_with_negative_score': (comments_df['score'] < 0).sum(),
        'comments_with_positive_score': (comments_df['score'] > 0).sum(),
        'avg_controversy_ratio': posts_df['controversy_ratio'].mean(),
        'avg_comment_score_std': posts_df['comment_score_std'].mean(),
    }
    
    print("\n" + "="*60)
    print("EXPLORATORY DATA ANALYSIS REPORT")
    print("="*60)
    print(f"Total Posts Collected: {report['total_posts']}")
    print(f"Total Comments Collected: {report['total_comments']}")
    print(f"Average Comments per Post: {report['avg_comments_per_post']:.2f}")
    print(f"Subreddits Represented: {report['total_subreddits']}")
    print(f"\nSubreddit Distribution:")
    for sub, count in report['subreddit_distribution'].items():
        print(f"  r/{sub}: {count} posts")
    print(f"\nScore Statistics:")
    print(f"  Average Post Score: {report['avg_post_score']:.2f}")
    print(f"  Average Comment Score: {report['avg_comment_score']:.2f}")
    print(f"\nComment Text Length (characters):")
    print(f"  Average: {report['avg_comment_length']:.2f}")
    print(f"  Median: {report['median_comment_length']:.2f}")
    print(f"\nComment Sentiment (by score):")
    print(f"  Positive (score > 0): {report['comments_with_positive_score']} ({report['comments_with_positive_score']/len(comments_df)*100:.1f}%)")
    print(f"  Negative (score < 0): {report['comments_with_negative_score']} ({report['comments_with_negative_score']/len(comments_df)*100:.1f}%)")
    print(f"\nControversy Metrics:")
    print(f"  Average Controversy Ratio: {report['avg_controversy_ratio']:.3f} (0=consensus, 1=max divisive)")
    print(f"  Average Comment Score Std Dev: {report['avg_comment_score_std']:.2f} (higher=more mixed opinions)")
    print("="*60 + "\n")
    
    return report

def visualize_eda(posts_df, comments_df, save_path='eda_visualizations.png'):
    # Create visualizations for EDA and save to root data/ folder
    filepath = os.path.join(DATA_DIR, save_path)
    os.makedirs(DATA_DIR, exist_ok=True)
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Reddit Data Exploratory Analysis', fontsize=16)
    
    # Plot 1: Comment length distribution
    axes[0, 0].hist(comments_df['text'].str.len(), bins=50, edgecolor='black')
    axes[0, 0].set_title('Comment Length Distribution')
    axes[0, 0].set_xlabel('Character Count')
    axes[0, 0].set_ylabel('Frequency')
    
    # Plot 2: Comment score distribution
    axes[0, 1].hist(comments_df['score'], bins=50, edgecolor='black', range=(-50, 100))
    axes[0, 1].set_title('Comment Score Distribution')
    axes[0, 1].set_xlabel('Score')
    axes[0, 1].set_ylabel('Frequency')
    
    # Plot 3: Subreddit distribution
    subreddit_controversy = posts_df.groupby('subreddit')['controversy_ratio'].mean()
    subreddit_controversy.plot(kind='bar', ax=axes[1, 0], color='coral')
    axes[1, 0].set_title('Average Controversy Ratio by Subreddit')
    axes[1, 0].set_ylabel('Controversy Ratio')
    axes[1, 0].set_xlabel('Subreddit')
    axes[1, 0].tick_params(axis='x', rotation=45)
    
    # Plot 4: Comments per post
    comments_per_post = comments_df.groupby('post_id').size()
    axes[1, 1].hist(comments_per_post, bins=20, edgecolor='black')
    axes[1, 1].set_title('Comments per Post Distribution')
    axes[1, 1].set_xlabel('Number of Comments')
    axes[1, 1].set_ylabel('Frequency')
    
    plt.tight_layout()
    plt.savefig(filepath, dpi=300, bbox_inches='tight')
    print(f"Saved visualizations to {filepath}")

# MAIN EXECUTION

if __name__ == "__main__":
    # Authenticate and collect data
    print("Step 1: Authenticating with Reddit API...")
    reddit = authenticate_reddit()
    
    print("Step 2: Collecting Reddit data...")
    # Mix of subreddits: tech, general discussion, and controversial for sentiment variety
    subreddits = [
        'python', 'learnprogramming', 'webdev',
        'AskReddit', 'unpopularopinion', 'ChangeMyView',
        'movies', 'gaming',
        'politics', 'news', 'AmItheAsshole'
    ]
    # Collecting 8 posts per subreddit = 88 posts, ~40 comments each
    raw_data = collect_reddit_data(reddit, subreddits, posts_per_sub=8, comments_per_post=40)
    save_raw_data(raw_data)
    
    # Validate data
    print("\nStep 3: Validating data completeness...")
    validated_data = validate_data_completeness(raw_data)
    
    # Preprocess data
    print("\nStep 4: Preprocessing data...")
    posts_df, comments_df = preprocess_reddit_data(validated_data)
    save_preprocessed_data(posts_df, comments_df)
    
    # Generate EDA
    print("\nStep 5: Generating EDA report...")
    eda_report = generate_eda_report(posts_df, comments_df)
    visualize_eda(posts_df, comments_df)
    
    print("\nPipeline complete! Check data/ folder for outputs.")