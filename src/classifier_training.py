# classifier_training.py

import pandas as pd
import numpy as np
import joblib
from sentence_transformers import SentenceTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
from iterstrat.ml_stratifiers import MultilabelStratifiedShuffleSplit

# ── CONFIG (updated) ─────────────────────────────────────────────────────────
DATASET_PATH      = "dataset.csv"
PROMPT_COLUMN     = "prompt"
LABEL_COLUMN      = "label"
EMBEDDING_MODEL   = "all-MiniLM-L6-v2"
RANDOM_STATE      = 42
TEST_SIZE         = 0.2

MODEL_SAVE_PATH     = "ccs_classifier.joblib"
EMBEDDER_SAVE_PATH  = "ccs_embedder.joblib"

LABEL_MAP = {
    0: "benign",
    1: "ccs1",
    2: "ccs2",
    3: "ccs3",
    4: "ccs4",
    5: "ccs5",
    6: "ccs6",
    7: "ccs7"
}
LABEL_NAMES = {
    "benign" : "Benign",
    "ccs1"   : "Authority",
    "ccs2"   : "Context_Poisoning",
    "ccs3"   : "Goal_Conflict",
    "ccs4"   : "Role_Confusion",
    "ccs5"   : "False_Premise",
    "ccs6"   : "Cognitive_Overload",
    "ccs7"   : "Emotional_Manipulation"
}
CLASSES = list(LABEL_MAP.values())  # ["benign", "ccs1", ..., "ccs7"]



# ── LOAD & VALIDATE (updated) ────────────────────────────────────────────────
df = pd.read_csv(DATASET_PATH)

# Map integer labels to class name strings
df[LABEL_COLUMN] = df[LABEL_COLUMN].astype(int).map(LABEL_MAP)

# Sanity check for any unmapped values
if df[LABEL_COLUMN].isna().any():
    bad = df[df[LABEL_COLUMN].isna()].index.tolist()
    print(f"⚠ Unmapped label integers found at rows: {bad}")

print("── Label Distribution ──")
for cls in CLASSES:
    count = (df[LABEL_COLUMN] == cls).sum()
    ratio = count / len(df)
    bar   = "█" * int(ratio * 30)
    print(f"  {cls:<8} ({LABEL_NAMES[cls]:<24}): {count:>4} ({ratio*100:>5.1f}%)  [{bar:<30}]")
print(f"\n  Total: {len(df)}\n")



# ── EMBED ────────────────────────────────────────────────────────────────────
print("Embedding prompts...")
embedder = SentenceTransformer(EMBEDDING_MODEL)
X = embedder.encode(df[PROMPT_COLUMN].tolist(), show_progress_bar=True)
y = df[LABEL_COLUMN].values



# ── STRATIFIED SPLIT ─────────────────────────────────────────────────────────
# Standard stratified split works fine now — single label per row
from sklearn.model_selection import StratifiedShuffleSplit

sss = StratifiedShuffleSplit(n_splits=1, test_size=TEST_SIZE, random_state=RANDOM_STATE)
for train_idx, test_idx in sss.split(X, y):
    X_train, X_test = X[train_idx], X[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]

print(f"Train: {len(X_train)} | Test: {len(X_test)}\n")

# Verify each class survived the split
for cls in CLASSES:
    print(f"  {cls}: train={(y_train==cls).sum():>4}  test={(y_test==cls).sum():>3}")
print()



# ── TRAIN ────────────────────────────────────────────────────────────────────
# MultiOutputClassifier is no longer needed — single LogisticRegression handles
# multi-class natively via softmax (multi_class='multinomial' is default in lbfgs)

print("Training classifier...")
clf = LogisticRegression(
    max_iter    = 2000,
    class_weight= "balanced",   # accounts for benign being ~27% of data
    random_state= RANDOM_STATE,
    C           = 1.0,
    solver      = "lbfgs",
)
clf.fit(X_train, y_train)
print("Training complete.\n")



# ── EVALUATE ─────────────────────────────────────────────────────────────────
from sklearn.metrics import classification_report

y_pred = clf.predict(X_test)

print("── Classification Report ──\n")
print(classification_report(
    y_test, y_pred,
    labels   = CLASSES,
    target_names = [LABEL_NAMES[c] for c in CLASSES],
    zero_division= 0
))



# ── SAVE ─────────────────────────────────────────────────────────────────────
joblib.dump(clf, MODEL_SAVE_PATH)
joblib.dump(embedder, EMBEDDER_SAVE_PATH)
print(f"Saved: {MODEL_SAVE_PATH}, {EMBEDDER_SAVE_PATH}")