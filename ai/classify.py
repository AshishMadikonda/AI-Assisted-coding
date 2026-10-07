# Simple placeholder for AI issue classification
# Later this will call a real AI vision API

def classify_issue(image_path):
    # Placeholder logic - will be replaced with real AI API call
    category = "road_damage"
    urgency = "medium"
    return {"category": category, "urgency": urgency}

if __name__ == "__main__":
    result = classify_issue("sample.jpg")
    print(result)