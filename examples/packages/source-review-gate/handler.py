def run(value):
    known = set(value["source_ids"])
    unsupported = [
        index
        for index, claim in enumerate(value["claims"])
        if not claim["source_ids"] or not set(claim["source_ids"]).issubset(known)
    ]
    return {"passed": not unsupported, "unsupported_claims": unsupported}
