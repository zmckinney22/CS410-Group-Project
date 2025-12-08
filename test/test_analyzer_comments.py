import json
import csv
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent.parent))
from backend.sentiment import SentimentAnalyzer

def load_reddit_data(comments_file, posts_file):
    """
    Load Reddit comments with subreddit context for sentiment evaluation.
    
    Args:
        comments_file: CSV with columns: comment_id, text, manual_label, post_id
        posts_file: CSV with columns: post_id, subreddit
    
    Returns:
        list[dict]: Examples with text, label (positive/negative/neutral/mixed), 
        and subreddit info. Invalid entries are filtered out.
    """
    post_to_subreddit = {}
    with open(posts_file, 'r', encoding='utf-8') as f:
        # Auto-detect delimiter (tab or comma)
        first_line = f.readline()
        f.seek(0)
        delimiter = '\t' if '\t' in first_line else ','
        reader = csv.DictReader(f, delimiter=delimiter)
        for row in reader:
            post_to_subreddit[row['post_id']] = row['subreddit']
    
    examples = []
    with open(comments_file, 'r', encoding='utf-8') as f:
        # Auto-detect delimiter
        first_line = f.readline()
        f.seek(0)
        delimiter = '\t' if '\t' in first_line else ','
        reader = csv.DictReader(f, delimiter=delimiter)
        
        for row in reader:
            text = row.get('text', '').strip()
            label = row.get('manual_label', '').strip().lower()
            
            # Filter out invalid entries: empty text or invalid labels
            if not text or label not in ['positive', 'negative', 'neutral', 'mixed']:
                continue
            
            examples.append({
                'comment_id': row.get('comment_id', ''),
                'text': text,
                'label': label,
                'subreddit': post_to_subreddit.get(row.get('post_id', ''), None),
                'post_id': row.get('post_id', '')
            })
    
    return examples


def evaluate_dataset(examples, params, use_subreddit=False):
    """
    Evaluate sentiment analyzer on labeled data.
    
    Args:
        examples: List of dicts with 'text' and 'label' keys
        params: SentimentAnalyzer configuration parameters
        use_subreddit: If True, cache subreddit-specific analyzers for context-aware analysis
    
    Returns:
        dict: accuracy, per-class metrics (precision/recall/F1), and pos_neg_f1
    """
    analyzer_cache = {}
    default_analyzer = SentimentAnalyzer(**params)
    
    confusion = {
        'positive': {'positive': 0, 'negative': 0, 'neutral': 0, 'mixed': 0},
        'negative': {'positive': 0, 'negative': 0, 'neutral': 0, 'mixed': 0},
        'neutral': {'positive': 0, 'negative': 0, 'neutral': 0, 'mixed': 0},
        'mixed': {'positive': 0, 'negative': 0, 'neutral': 0, 'mixed': 0} 
    }
    
    for item in examples:
        subreddit = item.get('subreddit')
        
        # Use subreddit-specific analyzer if enabled and available
        if use_subreddit and subreddit:
            if subreddit not in analyzer_cache:
                analyzer_cache[subreddit] = SentimentAnalyzer(subreddit=subreddit, **params)
            predicted = analyzer_cache[subreddit].analyze_sentiment(item['text']).value
        else:
            predicted = default_analyzer.analyze_sentiment(item['text']).value
        
        # Update confusion matrix: confusion[true_label][predicted_label]
        confusion[item['label']][predicted] += 1
    
    # Overall accuracy
    total = len(examples)
    correct = sum(confusion[label][label] for label in confusion)
    accuracy = correct / total
    
    metrics = {'accuracy': accuracy, 'classes': {}}
    
    for label in ['positive', 'negative', 'neutral', 'mixed']:
        # True Positives
        tp = confusion[label][label]
        # False Positives
        fp = sum(confusion[other][label] for other in confusion if other != label)
        # False Negatives
        fn = sum(confusion[label][other] for other in confusion[label] if other != label)
        
        # Precision
        p = tp / (tp + fp) if (tp + fp) > 0 else 0
        # Recall
        r = tp / (tp + fn) if (tp + fn) > 0 else 0
        # F1
        f1 = 2 * (p * r) / (p + r) if (p + r) > 0 else 0
        
        metrics['classes'][label] = {'precision': p, 'recall': r, 'f1': f1}
    
    # Metric for binary sentiment tasks
    metrics['pos_neg_f1'] = (metrics['classes']['positive']['f1'] + metrics['classes']['negative']['f1']) / 2
    return metrics


def evaluate_sst2(sst2_file, params):
    """
    Evaluate on SST-2 (Stanford Sentiment Treebank) benchmark.
    
    Args:
        sst2_file: Path to TSV file (format: text\tlabel, where label is 0/1)
        params: SentimentAnalyzer configuration
    
    Returns:
        dict: Evaluation metrics (same format as evaluate_dataset)
    """
    examples = []
    with open(sst2_file, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.strip().split('\t')
            if len(parts) == 2:
                # Convert binary labels (0/1) to sentiment labels
                examples.append({
                    'text': parts[0],
                    'label': 'positive' if parts[1] == '1' else 'negative'
                })
    
    return evaluate_dataset(examples, params)


def evaluate_sentiment140(sent140_file, params, sample_size=10000):
    """
    Evaluate on Sentiment140 Twitter dataset (1.6M tweets, randomly sampled).
    
    Args:
        sent140_file: Path to Sentiment140 CSV file
        params: SentimentAnalyzer configuration
        sample_size: Number of examples to sample (default: 10000, None for all)
    
    Returns:
        dict: Evaluation metrics (same format as evaluate_dataset)
    
    Note: Polarity encoding: 0=negative, 4=positive. Uses latin-1 encoding.
    """
    examples = []
    with open(sent140_file, 'r', encoding='latin-1', errors='ignore') as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) >= 6:
                polarity = row[0]
                # Filter for labeled tweets (0=negative, 4=positive)
                if polarity in ['0', '4']:
                    examples.append({
                        'text': row[5],
                        'label': 'negative' if polarity == '0' else 'positive'
                    })
    
    if sample_size and sample_size < len(examples):
        import random
        random.seed(42)
        examples = random.sample(examples, sample_size)
    
    return evaluate_dataset(examples, params)


def main():
    data_dir = Path(__file__).parent.parent / 'data'
    
    params = {
        'use_socialsent': True,
        'socialsent_weight': 0.3,
        'pos_threshold': 0.01,
        'neg_threshold': -0.01,
        'negation_window': 2,
        'negation_flip_weight': 1.0
    }
    
    results = {}
    
    # Reddit Manual
    comments_file = data_dir / 'comments_manually_labeled.csv'
    posts_file = data_dir / 'posts_preprocessed.csv'
    if comments_file.exists() and posts_file.exists():
        examples = load_reddit_data(str(comments_file), str(posts_file))
        results['reddit_manual'] = evaluate_dataset(examples, params, use_subreddit=True)
    
    # SST-2
    sst2_file = data_dir / 'sst2' / 'dev.tsv'
    if sst2_file.exists():
        results['sst2'] = evaluate_sst2(str(sst2_file), params)
    
    # Sentiment140
    sent140_file = data_dir / 'sentiment140' / 'training.1600000.processed.noemoticon.csv'
    if sent140_file.exists():
        results['sentiment140'] = evaluate_sentiment140(str(sent140_file), params)
    
    print("\nEVALUATION RESULTS with SocialSent weight = 0.3")
    print(f"{'Dataset':<25} {'Accuracy':>12} {'Pos/Neg F1':>12} {'Pos F1':>12} {'Neg F1':>12} {'Neu F1':>12} {'Mixed F1':>12}")
    print("-" * 100)
    
    dataset_names = {
        'reddit_manual': 'Reddit Manual',
        'sst2': 'SST-2',
        'sentiment140': 'Sentiment140'
    }
    
    for dataset, metrics in results.items():
        name = dataset_names.get(dataset, dataset)
        pos_f1 = metrics['classes'].get('positive', {}).get('f1', 0.0)
        neg_f1 = metrics['classes'].get('negative', {}).get('f1', 0.0)
        neu_f1 = metrics['classes'].get('neutral', {}).get('f1', 0.0)

        mixed_f1 = metrics['classes'].get('mixed', {}).get('f1', 0.0)
        
        print(f"{name:<25} {metrics['accuracy']:>12.4f} {metrics['pos_neg_f1']:>12.4f} "
              f"{pos_f1:>12.4f} {neg_f1:>12.4f} {neu_f1:>12.4f} {mixed_f1:>12.4f}")
        
    with open(data_dir / 'evaluation_results.json', 'w') as f:
        json.dump({'configuration': params, 'results': results}, f, indent=2)
    
    print(f"\nResults saved to: {data_dir / 'evaluation_results.json'}")

if __name__ == "__main__":
    main()