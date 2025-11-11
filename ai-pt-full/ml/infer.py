import joblib
import torch
from transformers import DistilBertTokenizerFast, DistilBertForSequenceClassification
import numpy as np
import os

# --- Configuration ---
TFIDF_MODEL_PATH = "models/multilabel_tfidf.joblib"
TRANSFORMER_MODEL_DIR = "models/transformer"

class ModelInference:
    def __init__(self):
        self.tfidf_pipeline = None
        self.transformer_model = None
        self.transformer_tokenizer = None
        self.transformer_binarizer = None

        self._load_tfidf_model()
        self._load_transformer_model()

    def _load_tfidf_model(self):
        """Loads the TF-IDF model pipeline."""
        if not os.path.exists(TFIDF_MODEL_PATH):
            print(f"[!] TF-IDF model not found at {TFIDF_MODEL_PATH}. TF-IDF inference will be unavailable.")
            return
        print("[*] Loading TF-IDF model...")
        self.tfidf_pipeline = joblib.load(TFIDF_MODEL_PATH)
        print("[*] TF-IDF model loaded.")

    def _load_transformer_model(self):
        """Loads the fine-tuned Transformer model."""
        if not os.path.exists(TRANSFORMER_MODEL_DIR):
            print(f"[!] Transformer model not found at {TRANSFORMER_MODEL_DIR}. Transformer inference will be unavailable.")
            return
        print("[*] Loading Transformer model...")
        self.transformer_model = DistilBertForSequenceClassification.from_pretrained(TRANSFORMER_MODEL_DIR)
        self.transformer_tokenizer = DistilBertTokenizerFast.from_pretrained(TRANSFORMER_MODEL_DIR)
        self.transformer_binarizer = joblib.load(f"{TRANSFORMER_MODEL_DIR}/label_binarizer.joblib")
        print("[*] Transformer model loaded.")

    def predict_tfidf(self, text):
        """
        Predicts vulnerability probabilities using the TF-IDF model.
        """
        if not self.tfidf_pipeline:
            return {"error": "TF-IDF model is not loaded."}

        # Vectorize the input text
        text_vectorized = self.tfidf_pipeline['vectorizer'].transform([text])

        # Get probability estimates
        probabilities = self.tfidf_pipeline['classifier'].predict_proba(text_vectorized)

        # Map probabilities to labels
        results = {}
        for i, class_name in enumerate(self.tfidf_pipeline['binarizer'].classes_):
            results[class_name] = probabilities[0][i]

        return results

    def predict_transformer(self, text):
        """
        Predicts vulnerability probabilities using the Transformer model.
        """
        if not self.transformer_model or not self.transformer_tokenizer:
            return {"error": "Transformer model is not loaded."}

        # Tokenize the input text
        inputs = self.transformer_tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=512)

        # Get model outputs (logits)
        with torch.no_grad():
            outputs = self.transformer_model(**inputs)

        # Apply sigmoid to get probabilities
        sigmoid = torch.nn.Sigmoid()
        probs = sigmoid(outputs.logits.squeeze())

        # Map probabilities to labels
        results = {}
        for i, class_name in enumerate(self.transformer_binarizer.classes_):
            results[class_name] = probs[i].item()

        return results

if __name__ == '__main__':
    # --- Example Usage ---
    inference = ModelInference()

    sample_text_xss = "<script>alert('XSS')</script>"
    sample_text_sqli = "SELECT * FROM users WHERE id = '1' OR '1' = '1'"

    print("\n--- TF-IDF Model Predictions ---")
    if inference.tfidf_pipeline:
        print("Sample (XSS):", inference.predict_tfidf(sample_text_xss))
        print("Sample (SQLi):", inference.predict_tfidf(sample_text_sqli))
    else:
        print("TF-IDF model not available.")

    print("\n--- Transformer Model Predictions ---")
    if inference.transformer_model:
        print("Sample (XSS):", inference.predict_transformer(sample_text_xss))
        print("Sample (SQLi):", inference.predict_transformer(sample_text_sqli))
    else:
        print("Transformer model not available.")
