import pandas as pd
import numpy as np
import json
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import DistilBertTokenizerFast, DistilBertForSequenceClassification, Trainer, TrainingArguments
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.metrics import f1_score, roc_auc_score, accuracy_score
import os

# --- Configuration ---
DATASET_PATH = "data/unified_dataset.csv"
MODEL_NAME = 'distilbert-base-uncased'
MODEL_OUTPUT_DIR = "models/transformer"

def train_transformer_model():
    """
    Fine-tunes a DistilBERT model for multi-label text classification.
    """
    # --- 1. Load and Prepare Data ---
    print("[*] Loading and preparing data for Transformer training...")
    if not os.path.exists(DATASET_PATH):
        print(f"[!] Dataset not found at {DATASET_PATH}. Please run labeling.py first.")
        return

    df = pd.read_csv(DATASET_PATH)
    df['text'] = df['text'].fillna('').astype(str)

    def parse_labels(labels_str):
        try:
            return list(json.loads(labels_str.replace("'", '"')).keys())
        except:
            return []

    df['labels_list'] = df['labels'].apply(parse_labels)

    # Use MultiLabelBinarizer to create multi-hot encoded labels
    mlb = MultiLabelBinarizer()
    labels = mlb.fit_transform(df['labels_list'])
    num_labels = len(mlb.classes_)

    if num_labels == 0:
        print("[!] No labels found. Cannot train model.")
        return

    print(f"[*] Found {num_labels} unique labels: {', '.join(mlb.classes_)}")

    # --- 2. Train-Validation Split ---
    train_texts, val_texts, train_labels, val_labels = train_test_split(
        df['text'].tolist(), labels, test_size=0.2, random_state=42
    )

    # --- 3. Tokenization ---
    print("[*] Tokenizing data...")
    tokenizer = DistilBertTokenizerFast.from_pretrained(MODEL_NAME)
    train_encodings = tokenizer(train_texts, truncation=True, padding=True, max_length=512)
    val_encodings = tokenizer(val_texts, truncation=True, padding=True, max_length=512)

    # --- 4. Create PyTorch Dataset ---
    class VulnerabilityDataset(Dataset):
        def __init__(self, encodings, labels):
            self.encodings = encodings
            self.labels = labels

        def __getitem__(self, idx):
            item = {key: torch.tensor(val[idx]) for key, val in self.encodings.items()}
            item['labels'] = torch.tensor(self.labels[idx], dtype=torch.float)
            return item

        def __len__(self):
            return len(self.labels)

    train_dataset = VulnerabilityDataset(train_encodings, train_labels)
    val_dataset = VulnerabilityDataset(val_encodings, val_labels)

    # --- 5. Load Model ---
    print("[*] Loading pre-trained DistilBERT model...")
    model = DistilBertForSequenceClassification.from_pretrained(MODEL_NAME, num_labels=num_labels, problem_type="multi_label_classification")

    # --- 6. Define Training Arguments ---
    training_args = TrainingArguments(
        output_dir=f'{MODEL_OUTPUT_DIR}/results',
        num_train_epochs=3,
        per_device_train_batch_size=8,
        per_device_eval_batch_size=8,
        warmup_steps=500,
        weight_decay=0.01,
        logging_dir=f'{MODEL_OUTPUT_DIR}/logs',
        logging_steps=10,
        eval_strategy="steps",
        eval_steps=50,
        save_strategy="steps", # Must be the same as evaluation_strategy
        save_steps=50,
        load_best_model_at_end=True,
    )

    # --- 7. Define Metrics ---
    def compute_metrics(p):
        preds = p.predictions[0] if isinstance(p.predictions, tuple) else p.predictions
        # Apply sigmoid to get probabilities and then threshold
        sigmoid = torch.nn.Sigmoid()
        probs = sigmoid(torch.Tensor(preds))
        y_pred = np.zeros(probs.shape)
        y_pred[np.where(probs >= 0.5)] = 1
        y_true = p.label_ids

        f1_micro_avg = f1_score(y_true=y_true, y_pred=y_pred, average='micro')
        accuracy = accuracy_score(y_true, y_pred)

        return {'f1': f1_micro_avg, 'accuracy': accuracy}


    # --- 8. Initialize Trainer ---
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        compute_metrics=compute_metrics
    )

    # --- 9. Train the Model ---
    print("[*] Starting model training...")
    trainer.train()
    print("[*] Training complete.")

    # --- 10. Save the Model ---
    print(f"[*] Saving the fine-tuned model to {MODEL_OUTPUT_DIR}...")
    model.save_pretrained(MODEL_OUTPUT_DIR)
    tokenizer.save_pretrained(MODEL_OUTPUT_DIR)

    # Save the label binarizer as well
    joblib.dump(mlb, f"{MODEL_OUTPUT_DIR}/label_binarizer.joblib")

    print("[*] Transformer model training and saving process completed.")


if __name__ == "__main__":
    train_transformer_model()
