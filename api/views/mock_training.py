import pandas as pd
import numpy as np
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import os

# -----------------------------
# 1. Generate Fake Interaction Data
# -----------------------------
np.random.seed(42)
num_samples = 100

user_ids = np.random.randint(1, 20, num_samples)
article_ids = np.random.randint(1, 10, num_samples)

data = {
    'user_id': user_ids,
    'article_id': article_ids,
    'time_spent': np.random.normal(30, 10, num_samples),
    'is_like': np.random.randint(0, 2, num_samples),
    'is_click': np.random.randint(0, 2, num_samples),
    'is_view': np.random.randint(0, 2, num_samples),
    'is_share': np.random.randint(0, 2, num_samples),
}
df = pd.DataFrame(data)

df['target'] = ((df['is_like'] + df['is_click']) > 0).astype(int)

# ✅ Balance the classes (optional but helpful for small mock data)
positive = df[df['target'] == 1]
negative = df[df['target'] == 0]

min_len = min(len(positive), len(negative))
if min_len > 0:
    df = pd.concat([positive.sample(min_len, random_state=42), negative.sample(min_len, random_state=42)])
else:
    raise ValueError("❌ Not enough data to balance classes. Regenerate or increase sample size.")


# -----------------------------
# 2. Fake Article Metadata
# -----------------------------
article_meta = pd.DataFrame({
    'id': range(1, 11),
    'category': np.random.choice(['sports', 'politics', 'unknown'], size=10),
    'priority': np.random.choice(['low', 'medium', 'high'], size=10),
    'popularity_score': np.random.randint(0, 100, size=10)
})

# -----------------------------
# 3. Join + Preprocess
# -----------------------------
merged = df.merge(article_meta, left_on='article_id', right_on='id')

merged['category'] = merged['category'].fillna('unknown')
merged['priority'] = merged['priority'].fillna('low')

merged = pd.get_dummies(merged, columns=['category', 'priority'])

X = merged.drop(columns=['user_id', 'article_id', 'id', 'target'])
y = merged['target']

# -----------------------------
# 4. Train Model
# -----------------------------
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

print("✅ Model trained on mock data!")
print(classification_report(y_test, model.predict(X_test)))

import os
import joblib

# 🔥 Load model & features from the correct directory
CURRENT_DIR = os.path.dirname(__file__)
MODEL_PATH = os.path.join(CURRENT_DIR, 'recommender_model.pkl')
FEATURE_PATH = os.path.join(CURRENT_DIR, 'model_features.pkl')

model = joblib.load(MODEL_PATH)
model_features = joblib.load(FEATURE_PATH)
