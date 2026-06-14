import joblib

obj = joblib.load("models/train_delay_model.pkl")

print(type(obj))

if isinstance(obj, dict):
    print(obj.keys())