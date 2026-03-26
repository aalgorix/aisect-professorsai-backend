import json
import os

from config import OUTPUT_JSON_PATH, BASE_DIR


def generate_courses_week_topics():
    """Generate courses_week_topics.json from data/courses/course_output.json.

    Mapping:
      - course_output.course_id       -> courses_week_topics.course_id
      - course_output.course_title    -> courses_week_topics.course_title
      - course_output.modules         -> courses_week_topics.weeks
      - module.week                   -> week_number
      - module.title                  -> week_title
      - module.sub_topics[*].title    -> topic_title
      - topic_id                      -> running integer counter
    """
    source_path = OUTPUT_JSON_PATH
    target_path = os.path.join(BASE_DIR, "courses_week_topics.generated.json")

    if not os.path.exists(source_path):
        print(f"Source course_output.json not found at: {source_path}")
        return

    with open(source_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Normalize to list of courses
    if isinstance(data, dict) and "course_title" in data:
        courses = [data]
    elif isinstance(data, list):
        courses = [c for c in data if isinstance(c, dict)]
    else:
        print("Invalid course_output.json format; expected dict or list of dicts.")
        return

    result = []
    next_topic_id = 1

    for course in courses:
        course_id = course.get("course_id")
        course_title = course.get("course_title", "Untitled Course")
        modules = course.get("modules", [])

        weeks = []
        for module in modules:
            week_number = module.get("week")
            week_title = module.get("title", f"Week {week_number or ''}".strip())
            sub_topics = module.get("sub_topics", [])

            topics = []
            for sub in sub_topics:
                title = sub.get("title")
                if not title:
                    continue
                topics.append({
                    "topic_id": next_topic_id,
                    "topic_title": title,
                })
                next_topic_id += 1

            if topics:
                weeks.append({
                    "week_number": week_number,
                    "week_title": week_title,
                    "topics": topics,
                })

        if weeks:
            result.append({
                "course_id": course_id,
                "course_title": course_title,
                "weeks": weeks,
            })

    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"Generated {len(result)} courses into {target_path}")


if __name__ == "__main__":
    generate_courses_week_topics()
