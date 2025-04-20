import joblib
import pandas as pd
import os

# Define model directory
MODEL_DIR = os.path.dirname(__file__)
model_path = os.path.join(MODEL_DIR, 'recommender_model.pkl')
features_path = os.path.join(MODEL_DIR, 'model_features.pkl')

# ✅ Load model and features list correctly
model = joblib.load(model_path)
features = joblib.load(features_path)  # Now this is a list, not a string!

# Example test input
test_input = pd.DataFrame([{
    'time_spent': 45,
    'is_like': 1,
    'is_click': 1,
    'is_view': 1,
    'is_share': 0,
    'popularityScore': 0.65,
    'category_Teknoloji': 1,
    'priority_high': 1,
    'pref_Teknoloji': 1,
    'pref_Ekonomi': 0,
    # Add all other possible features with 0
}])

# Ensure all columns from training are present
for col in features:
    if col not in test_input.columns:
        test_input[col] = 0

# Reorder columns
test_input = test_input[features]

# Make prediction
prediction = model.predict(test_input)
probability = model.predict_proba(test_input)

print("Predicted Label:", prediction[0])
print("Probability [not interested, interested]:", probability[0])
