def run(value):
    labels = {item.lower() for item in value["labels"]}
    category = "bug" if "bug" in labels else "question" if "question" in labels else "request"
    return {
        "source_id": f"issue:{value['number']}",
        "title": value["title"].strip(),
        "description": value["body"].strip(),
        "category": category,
    }
