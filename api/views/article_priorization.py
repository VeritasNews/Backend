# ============================================
# 🧠 Smart Feed Prioritization Training Script (User-Aware)
# ============================================

import pandas as pd
import joblib
from sqlalchemy import create_engine
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import os
import sys
import locale
from urllib.parse import quote_plus

print("System encoding:", sys.getdefaultencoding())
print("Locale encoding:", locale.getpreferredencoding())
locale.setlocale(locale.LC_ALL, '')

# --------------------------------------------
# 1. Connect to PostgreSQL DB
# --------------------------------------------
DB_NAME = 'veritas'
DB_USER = 'postgres'
DB_PASSWORD = quote_plus('Veritasnews123')
DB_HOST = 'localhost'
DB_PORT = '5432'

engine = create_engine(
    f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}',
    connect_args={"options": "-c client_encoding=utf8"}
)

# --------------------------------------------
# 2. Load interaction data
# --------------------------------------------
print("🔄 Loading interaction data...")
df = pd.read_sql("SELECT * FROM api_articleinteraction", engine)

for col in df.select_dtypes(include='object').columns:
    df[col] = df[col].apply(
        lambda x: x.encode('latin1').decode('utf-8', errors='ignore') if isinstance(x, str) else x
    )

df['timestamp'] = pd.to_datetime(df['timestamp'])
df.dropna(subset=['action'], inplace=True)

# --------------------------------------------
# 3. Feature engineering
# --------------------------------------------
print("🛠️ Processing features...")
df['is_like'] = df['action'].apply(lambda x: 1 if x == 'like' else 0)
df['is_view'] = df['action'].apply(lambda x: 1 if x == 'view' else 0)
df['is_click'] = df['action'].apply(lambda x: 1 if x == 'click' else 0)
df['is_share'] = df['action'].apply(lambda x: 1 if x == 'share' else 0)

engagement = df.groupby(['user_id', 'article_id']).agg({
    'time_spent': 'mean',
    'is_like': 'max',
    'is_click': 'max',
    'is_view': 'max',
    'is_share': 'max',
}).reset_index()

engagement['target'] = ((engagement['is_like'] + engagement['is_click']) > 0).astype(int)

# Sanity check
print("\n📊 Class distribution:")
print(engagement['target'].value_counts())

if engagement['target'].nunique() < 2:
    raise ValueError("❌ You need both positive and negative samples to train the model.")

# --------------------------------------------
# 4. Join with article metadata
# --------------------------------------------
print("🔗 Joining with article metadata...")
articles = pd.read_sql("SELECT id, category, priority, \"popularityScore\" FROM api_article", engine)

for col in articles.select_dtypes(include='object').columns:
    articles[col] = articles[col].astype(str)

merged = engagement.merge(articles, left_on='article_id', right_on='id')
merged['category'] = merged['category'].fillna('unknown')
merged['priority'] = merged['priority'].fillna('low')
merged['popularityScore'] = merged['popularityScore'].fillna(0)

# --------------------------------------------
# 5. Join with user preferences
# --------------------------------------------
print("🔗 Joining with user preferences...")
users = pd.read_sql("SELECT id, \"preferredCategories\" FROM api_user", engine)

# Convert preferredCategories to list
users['preferredCategories'] = users['preferredCategories'].apply(
    lambda x: x.split(',') if isinstance(x, str) else []
)

all_categories = [
    "Siyaset", "Entertainment", "Spor", "Teknoloji", "Saglik", "Cevre", "Bilim", "Egitim",
    "Ekonomi", "Seyahat", "Moda", "Kultur", "Suc", "Yemek", "YasamTarzi", "IsDunyasi",
    "DunyaHaberleri", "Oyun", "Otomotiv", "Sanat", "Tarih", "Uzay", "Iliskiler", "Din",
    "RuhSagligi", "Magazin"
]

for cat in all_categories:
    users[f'pref_{cat}'] = users['preferredCategories'].apply(lambda cats: int(cat in cats))

merged = merged.merge(users.drop(columns=['preferredCategories']), left_on='user_id', right_on='id', suffixes=('', '_user'))

# --------------------------------------------
# 6. One-hot encode article fields
# --------------------------------------------
merged = pd.get_dummies(merged, columns=['category', 'priority'])

# --------------------------------------------
# 7. Train model
# --------------------------------------------
X = merged.drop(columns=['user_id', 'article_id', 'id', 'id_user', 'target'])
y = merged['target']

print(f"\n🧮 Total samples: {len(X)} | Positive samples: {y.sum()}")
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

print("\n🧠 Training model...")
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# --------------------------------------------
# 8. Evaluate
# --------------------------------------------
y_pred = model.predict(X_test)
print("\n🌟 Model Evaluation:")
print(classification_report(y_test, y_pred))

# --------------------------------------------
# 9. Save
# --------------------------------------------
MODEL_DIR = os.path.dirname(__file__)
MODEL_PATH = os.path.join(MODEL_DIR, 'recommender_model.pkl')
FEATURE_PATH = os.path.join(MODEL_DIR, 'model_features.pkl')

joblib.dump(model, MODEL_PATH)
joblib.dump(X.columns.tolist(), FEATURE_PATH)

print(f"✅ Model saved to {MODEL_PATH}")
print(f"📜 Feature order saved to {FEATURE_PATH}")