# Download SST-2 and Sentiment140 datasets for sentiment analysis evaluation
import os
import urllib.request
import sys
from pathlib import Path

# Set up project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / 'data'

def download_file(url, destination, description):
    """
    Download a file from URL with progress bar
    """
    print(f"\nDownloading {description}...")
    print(f"URL: {url}")
    
    try:
        def report_progress(block_num, block_size, total_size):
            """Display download progress as a percentage bar"""
            downloaded = block_num * block_size
            if total_size > 0:
                percent = min(100, downloaded * 100 / total_size)
                bar_length = 50
                filled = int(bar_length * downloaded / total_size)
                bar = '=' * filled + '-' * (bar_length - filled)
                sys.stdout.write(f'\r[{bar}] {percent:.1f}%')
                sys.stdout.flush()
        
        urllib.request.urlretrieve(url, destination, reporthook=report_progress)
        print(f"\nDownloaded to {destination}")
        return True
    except Exception as e:
        print(f"\nError downloading: {e}")
        return False

def download_sst2():
    """
    Download SST-2 (Stanford Sentiment Treebank) dataset
    Binary sentiment classification dataset with movie reviews
    Downloads both training and dev sets
    """
    print("\n" + "="*70)
    print("DOWNLOADING SST-2 DATASET")
    print("="*70)
    
    # Create directory if it doesn't exist
    sst2_dir = DATA_DIR / 'sst2'
    sst2_dir.mkdir(parents=True, exist_ok=True)
    
    # Define files to download (dev and train splits)
    files = [
        ('dev.tsv', 'https://raw.githubusercontent.com/clairett/pytorch-sentiment-classification/master/data/SST2/dev.tsv'),
        ('train.tsv', 'https://raw.githubusercontent.com/clairett/pytorch-sentiment-classification/master/data/SST2/train.tsv')
    ]
    
    success_count = 0
    for filename, url in files:
        destination = sst2_dir / filename
        # Skip if file already exists
        if destination.exists():
            print(f"\n{filename} already exists, skipping...")
            success_count += 1
        else:
            if download_file(url, destination, f"SST-2 {filename}"):
                success_count += 1
    
    # Validate downloaded files
    if success_count == len(files):
        print("\nSST-2 dataset downloaded successfully!")
        
        # Show dataset sizes
        dev_file = sst2_dir / 'dev.tsv'
        if dev_file.exists():
            with open(dev_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                print(f"  - dev.tsv: {len(lines)} examples")
        
        train_file = sst2_dir / 'train.tsv'
        if train_file.exists():
            with open(train_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                print(f"  - train.tsv: {len(lines)} examples")
        
        return True
    else:
        print("\nWARNING: Some files failed to download")
        return False

def download_sentiment140(confirmation_required=True):
    """
    Download Sentiment140 dataset (1.6M tweets with sentiment labels)
    Large dataset used for Twitter/social media sentiment analysis

    Args:
        confirmation_required: Whether to ask for user confirmation before download
    """
    print("\n" + "="*70)
    print("DOWNLOADING SENTIMENT140 DATASET")
    print("="*70)
    print("WARNING: This is a large file (~80MB, 1.6M tweets)")

    # Confirm download due to large file size (if required)
    if confirmation_required:
        response = input("Do you want to download it? (y/n): ")
        if response.lower() != 'y':
            print("Skipped Sentiment140 download")
            return False
    
    # Create directory if it doesn't exist
    sent140_dir = DATA_DIR / 'sentiment140'
    sent140_dir.mkdir(parents=True, exist_ok=True)
    
    # Download zip file
    url = 'http://cs.stanford.edu/people/alecmgo/trainingandtestdata.zip'
    zip_file = sent140_dir / 'trainingandtestdata.zip'
    
    # Skip download if zip already exists
    if zip_file.exists():
        print(f"\nZip file already exists at {zip_file}")
    else:
        if not download_file(url, zip_file, "Sentiment140 dataset"):
            return False
    
    # Extract zip file
    print("\nExtracting files...")
    try:
        import zipfile
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            zip_ref.extractall(sent140_dir)
        print("Extracted successfully!")
        
        # Verify main dataset file exists
        main_file = sent140_dir / 'training.1600000.processed.noemoticon.csv'
        if main_file.exists():
            print(f"Found main dataset: {main_file}")
            return True
        else:
            print("ERROR: Main dataset file not found after extraction")
            return False
    except Exception as e:
        print(f"Error extracting: {e}")
        return False

def main():
    """
    Main function to download all evaluation datasets
    Downloads SST-2 and Sentiment140 for sentiment analyzer evaluation
    """
    print("="*70)
    print("DATASET DOWNLOADER")
    print("="*70)
    print(f"Data will be saved to: {DATA_DIR}")
    
    # Download both datasets
    results = {}
    results['sst2'] = download_sst2()
    results['sentiment140'] = download_sentiment140()
    
    # Print summary of download results
    print("\n" + "="*70)
    print("DOWNLOAD SUMMARY")
    print("="*70)
    for dataset, success in results.items():
        status = "SUCCESS" if success else "FAILED"
        print(f"{dataset.upper()}: {status}")
    
    if all(results.values()):
        print("\nAll datasets downloaded successfully!")
    else:
        print("\nWARNING: Some datasets failed to download")
    
    print("="*70)

if __name__ == "__main__":
    main()