import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.sentiment import SentimentAnalyzer

import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import numpy as np

# Load manually labeled data
labeled_df = pd.read_csv('data/comments_manually_labeled.csv')

print("="*80)
print("SENTIMENT ANALYZER EVALUATION - MANUAL LABELS")
print("="*80)
print(f"\nTotal comments: {len(labeled_df)}")
print(f"Label distribution:")
print(labeled_df['manual_label'].value_counts())
print()

# Initialize analyzer
analyzer = SentimentAnalyzer()

# Get predictions
predictions = []
for text in labeled_df['text']:
    try:
        pred = analyzer.analyze_sentiment(text)
        predictions.append(pred.value)
    except Exception as e:
        print(f"Error analyzing: {text[:50]}... - {e}")
        predictions.append('neutral')  # Default to neutral on error

labeled_df['predicted'] = predictions

# Calculate overall accuracy
accuracy = accuracy_score(labeled_df['manual_label'], labeled_df['predicted'])

print("="*80)
print(f"OVERALL ACCURACY: {accuracy:.2%}")
print("="*80)

# Classification report
print("\nDetailed Classification Report:")
print(classification_report(labeled_df['manual_label'], labeled_df['predicted'], 
                          target_names=['positive', 'negative', 'neutral', 'mixed'],
                          zero_division=0))

# Confusion matrix
print("\nConfusion Matrix:")
print("(Rows = Actual, Columns = Predicted)")
cm = confusion_matrix(labeled_df['manual_label'], labeled_df['predicted'],
                     labels=['positive', 'negative', 'neutral', 'mixed'])
cm_df = pd.DataFrame(cm, 
                     index=['Actual: Pos', 'Actual: Neg', 'Actual: Neu', 'Actual: Mix'],
                     columns=['Pred: Pos', 'Pred: Neg', 'Pred: Neu', 'Pred: Mix'])
print(cm_df)

# Show some misclassified examples
print("\n" + "="*80)
print("SAMPLE MISCLASSIFICATIONS")
print("="*80)
misclassified = labeled_df[labeled_df['manual_label'] != labeled_df['predicted']]
if len(misclassified) > 0:
    sample = misclassified.sample(min(10, len(misclassified)))
    for idx, row in sample.iterrows():
        print(f"\nText: {row['text'][:80]}...")
        print(f"  Manual: {row['manual_label']}, Predicted: {row['predicted']}")
else:
    print("No misclassifications found!")

# Show some correctly classified examples
print("\n" + "="*80)
print("SAMPLE CORRECT CLASSIFICATIONS")
print("="*80)
correct = labeled_df[labeled_df['manual_label'] == labeled_df['predicted']]
if len(correct) > 0:
    sample = correct.sample(min(5, len(correct)))
    for idx, row in sample.iterrows():
        print(f"\nText: {row['text'][:80]}...")
        print(f"  Both labeled as: {row['manual_label']} ✓")

# Per-label accuracy breakdown
print("\n" + "="*80)
print("ACCURACY BY SENTIMENT LABEL")
print("="*80)
for label in ['positive', 'negative', 'neutral', 'mixed']:
    subset = labeled_df[labeled_df['manual_label'] == label]
    if len(subset) > 0:
        label_acc = (subset['manual_label'] == subset['predicted']).mean()
        print(f"{label.capitalize():10s}: {label_acc:6.2%} ({len(subset)} samples)")

# Save results
output_file = 'data/manual_evaluation_results.csv'
labeled_df.to_csv(output_file, index=False)
print(f"\n✓ Saved detailed results to {output_file}")
print("="*80)