"""Download tables and email-ready text for schedules."""

import pandas as pd


def build_export_tables(schedule, student_metrics=None, students=None):
    schedule = schedule.drop(columns=["assignment_index"], errors="ignore")
    schedule = _merge_student_contact(schedule, students)
    if student_metrics is not None and not student_metrics.empty:
        metric_cols = [
            "student_id", "max_meetings_requested", "effective_max_meetings",
            "assigned_meetings", "raw_satisfaction", "max_possible_satisfaction",
            "normalized_satisfaction", "meeting_fulfillment_rate",
            "got_rank_1", "got_rank_2",
        ]
        available = [c for c in metric_cols if c in student_metrics.columns]
        schedule = schedule.merge(student_metrics[available], on="student_id", how="left")
    master = schedule.sort_values(["day", "start", "faculty", "student_id"]).copy()
    student = schedule.sort_values(["student_id", "day", "start"]).copy()
    faculty = schedule.sort_values(["faculty", "day", "start", "student_id"]).copy()
    return {
        "master_schedule": master,
        "student_schedules": student,
        "faculty_schedules": faculty,
        "student_diagnostics": student_metrics if student_metrics is not None else pd.DataFrame(),
        "student_email_text": _student_text(student),
        "faculty_email_text": _person_text(faculty, "faculty", "student_id"),
    }


def to_csv_bytes(df):
    return df.to_csv(index=False).encode("utf-8")


def _person_text(schedule, person_col, counterpart_col):
    rows = []
    for person, group in schedule.groupby(person_col, sort=True):
        lines = [f"Schedule for {person}", ""]
        for r in group.sort_values(["day", "start"]).itertuples():
            lines.append(
                f"Day {r.day}, {r.start}-{r.end}: meet with {getattr(r, counterpart_col)}"
            )
        rows.append({"recipient": person, "schedule_text": "\n".join(lines)})
    return pd.DataFrame(rows)


def _merge_student_contact(schedule, students):
    if students is None or getattr(students, "empty", True) or "student_id" not in students.columns:
        return schedule
    contact_cols = [c for c in ["student_id", "name", "email"] if c in students.columns]
    if len(contact_cols) == 1:
        return schedule
    contact = students[contact_cols].copy()
    contact["student_id"] = contact["student_id"].astype(str)
    contact = contact.drop_duplicates("student_id", keep="last")
    out = schedule.copy()
    out["student_id"] = out["student_id"].astype(str)
    return out.merge(contact, on="student_id", how="left")


def _student_text(schedule):
    rows = []
    for student_id, group in schedule.groupby("student_id", sort=True):
        name = _first_present(group, "name") or student_id
        email = _first_present(group, "email")
        lines = [f"Schedule for {name}", ""]
        for r in group.sort_values(["day", "start"]).itertuples():
            lines.append(f"Day {r.day}, {r.start}-{r.end}: meet with {r.faculty}")
        rows.append({
            "student_id": student_id,
            "recipient": email or student_id,
            "recipient_name": name,
            "recipient_email": email,
            "schedule_text": "\n".join(lines),
        })
    return pd.DataFrame(rows)


def _first_present(group, col):
    if col not in group.columns:
        return ""
    values = group[col].dropna().astype(str).str.strip()
    values = values[values != ""]
    return values.iloc[0] if not values.empty else ""
