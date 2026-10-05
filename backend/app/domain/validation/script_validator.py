"""Script semantics. Call only after successful structural validation.

The input is not mutated. Character offsets count Unicode code points, with an
exclusive end. Active instances may remain on screen at the end of the script.
"""
from .report import ValidationReport, empty_report, pointer


def validate_script(script: dict) -> ValidationReport:
    report = empty_report()

    def issue(code, parts, message):
        report["errors"].append({"code": code, "path": pointer(parts), "message": message})

    for collection in ("sentences", "entityDefinitions", "entityInstances"):
        seen = set()
        for index, item in enumerate(script[collection]):
            if item["id"] in seen:
                issue("script.duplicate_id", (collection, index, "id"), "ID must be unique in its collection.")
            seen.add(item["id"])

    definitions = {item["id"] for item in script["entityDefinitions"]}
    instances = {item["id"] for item in script["entityInstances"]}
    for index, item in enumerate(script["entityInstances"]):
        if item["entityId"] not in definitions:
            issue("script.unknown_entity", ("entityInstances", index, "entityId"), "Entity definition does not exist.")

    active = set()
    for index, sentence in enumerate(script["sentences"]):
        base = ("sentences", index)
        if sentence["order"] != index:
            issue("script.order", (*base, "order"), "Sentence order must be contiguous from zero in array order.")
        ranges = []
        for offset, emphasis in enumerate(sentence["emphasisRanges"]):
            location = (*base, "emphasisRanges", offset)
            start, end = emphasis["startChar"], emphasis["endChar"]
            if not 0 <= start < end <= len(sentence["narrationText"]):
                issue("script.range_bounds", location, "Range must be nonempty and within narration text.")
                continue
            if sentence["narrationText"][start:end] != emphasis["text"]:
                issue("script.range_text", location, "Range text must match narration exactly.")
            if any(start < other_end and other_start < end for other_start, other_end in ranges):
                issue("script.range_overlap", location, "Emphasis ranges must not overlap.")
            ranges.append((start, end))

        for offset, instruction in enumerate(sentence["entityInstructions"]):
            location = (*base, "entityInstructions", offset)
            instance, action = instruction["instanceId"], instruction["action"]
            target = instruction.get("targetInstanceId")
            if target is not None and target not in instances:
                issue("script.unknown_target", (*location, "targetInstanceId"), "Target instance does not exist.")
            if instance not in instances:
                issue("script.unknown_instance", (*location, "instanceId"), "Instance does not exist.")
                continue
            if action == "enter":
                if instance in active:
                    issue("script.duplicate_enter", location, "Instance is already active.")
                else:
                    active.add(instance)
            elif instance not in active:
                issue("script.inactive_instance", location, "Instance must enter before this action; re-enter after exit.")
            elif action == "exit":
                active.remove(instance)

    expected = sum(item["estimatedDurationMs"] for item in script["sentences"])
    expected += script["interSentencePauseMs"] * (len(script["sentences"]) - 1)
    if script["estimatedTotalDurationMs"] != expected:
        issue("script.duration_total", ("estimatedTotalDurationMs",), f"Expected {expected} ms including pauses only between sentences.")
    # Integer arithmetic avoids boundary drift at exactly +/-20%.
    if abs(expected - script["targetDurationMs"]) * 5 > script["targetDurationMs"]:
        issue("script.duration_target", ("targetDurationMs",), "Computed duration must be within 20% of target.")
    return report
