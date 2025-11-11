import pandas as pd
import numpy as np
import json
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.multiclass import OneVsRestClassifier
from sklearn.metrics import classification_report
from sklearn.preprocessing import MultiLabelBinarizer
import os

# --- Configuration ---
DATASET_PATH = "data/unified_dataset.csv"
MODEL_OUTPUT_PATH = "models/multilabel_tfidf.joblib"
MAX_FEATURES = 50000
NGRAM_RANGE = (1, 2)

def train_tfidf_multilabel_model():
    """
    Trains a TF-IDF + One-vs-Rest Logistic Regression model for multi-label text classification.
    """
    # --- 1. Load and Prepare Data ---
    print("[*] Loading and preparing data...")
    if not os.path.exists(DATASET_PATH):
        print(f"[!] Dataset not found at {DATASET_PATH}. Please run labeling.py first.")
        return

    df = pd.read_csv(DATASET_PATH)

    # Fill NaNs and ensure 'text' is string
    df['text'] = df['text'].fillna('').astype(str)

    # Safely parse the JSON string in 'labels'
    def parse_labels(labels_str):
        try:
            return json.loads(labels_str.replace("'", '"'))
        except (json.JSONDecodeError, AttributeError):
            return {}

    df['parsed_labels'] = df['labels'].apply(parse_labels)

    # Use MultiLabelBinarizer to convert label dictionaries to a binary matrix
    mlb = MultiLabelBinarizer()
    y = mlb.fit_transform(df['parsed_labels'].apply(lambda x: list(x.keys())))

    # Check if we have any labels to train on
    if y.shape[1] == 0:
        print("[!] No valid labels found after parsing. Cannot train the model.")
        return

    print(f"[*] Found {y.shape[1]} unique labels: {', '.join(mlb.classes_)}")

    X = df['text']

    # --- 2. Train-Test Split ---
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    print(f"[*] Data split into {len(X_train)} training samples and {len(X_test)} testing samples.")

    # --- 3. TF-IDF Vectorization ---
    print("[*] Performing TF-IDF vectorization...")
    tfidf_vectorizer = TfidfVectorizer(max_features=MAX_FEATURES, ngram_range=NGRAM_RANGE, stop_words='english')

    X_train_tfidf = tfidf_vectorizer.fit_transform(X_train)
    X_test_tfidf = tfidf_vectorizer.transform(X_test)

    # --- 4. Model Training ---
    print("[*] Training the multi-label classifier...")
    # Using a simple logistic regression model wrapped in OneVsRestClassifier for multi-label scenario
    logreg = LogisticRegression(solver='saga', penalty='l1', C=1.0, random_state=42, max_iter=200)
    ovr_classifier = OneVsRestClassifier(logreg, n_jobs=-1)

    ovr_classifier.fit(X_train_tfidf, y_train)
    print("[*] Training complete.")

    # --- 5. Evaluation ---
    print("[*] Evaluating the model...")
    y_pred = ovr_classifier.predict(X_test_tfidf)

    # Print classification report
    report = classification_report(y_test, y_pred, target_names=mlb.classes_, zero_division=0)
    print("\n--- Classification Report ---\n")
    print(report)
    print("-----------------------------\n")

    # --- 6. Save the Model Pipeline ---
    print(f"[*] Saving the trained model pipeline to {MODEL_OUTPUT_PATH}...")

    # Create the model directory if it doesn't exist
    if not os.path.exists('models'):
        os.makedirs('models')

    # We save the vectorizer, the binarizer, and the classifier together
    model_pipeline = {
        'vectorizer': tfidf_vectorizer,
        'binarizer': mlb,
        'classifier': ovr_classifier
    }

    joblib.dump(model_pipeline, MODEL_OUTPUT_PATH)
    print("[*] Model saved successfully!")

if __name__ == "__main__":
    train_tfidf_multilabel_model()
