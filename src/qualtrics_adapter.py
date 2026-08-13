"""Convert finalized Qualtrics exports into scheduler-ready tables.

Qualtrics CSV exports include two metadata rows after the header. The first
metadata row stores the human-readable question text, which is also where the
rank-order question stores each faculty name.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta

import pandas as pd

from roster import load_roster
from student_metrics import MAX_COL

TIME_BLOCKS = {
    "time 1": (datetime.strptime("09:00", "%H:%M"), datetime.strptime("11:40", "%H:%M")),
    "time 2": (datetime.strptime("11:40", "%H:%M"), datetime.strptime("14:20", "%H:%M")),
    "time 3": (datetime.strptime("14:20", "%H:%M"), datetime.strptime("17:00", "%H:%M") + timedelta(minutes=1)),
}

FINALIZED_STUDENT_SURVEY_FACULTY = [
    "Ilan Adler",
    "Anil Aswani",
    "Alper Atamturk",
    "Ying Cui",
    "Lee Fleming",
    "Ken Goldberg",
    "Paul Grigas",
    "Xin Guo",
    "Dorit Hochbaum",
    "Huiwen Jia",
    "Philip M. Kaminsky",
    "Phillip Kerger",
    "Javad Lavaei",
    "Thibaut Mastrolia",
    "Daniel Pirutinsky",
    "Rhonda Righter",
    "Rajan Udwani",
    "Chiwei Yan",
    "Candace Yano",
    "Zeyu Zheng",
    "Chenyang Zhong",
    "Pieter Abbeel",
]


def adapt_student_qualtrics(responses: pd.DataFrame, roster_path: str, grid: pd.DataFrame):
    """Return preferences, interests, request limits, availability, students, faculty, warnings."""
    question_text = _question_text(responses)
    data = _response_rows(responses)
    roster = load_roster(roster_path)
    slot_map = _qualtrics_slot_map(grid)
    rank_cols = [c for c in responses.columns if str(c).startswith("Q3_")]
    day_cols = [c for c in responses.columns if re.match(r"^Q4_\d+$", str(c))]
    survey_faculty = _faculty_from_rank_columns(question_text, rank_cols, roster)
    name2id = _name_to_id(survey_faculty)

    warnings = []
    pref_rows = []
    request_rows = []
    availability_rows = []
    student_rows = []

    data, duplicate_warnings = _dedupe_responses(data, ["RecipientEmail", "Q1"], "student")
    warnings.extend(duplicate_warnings)

    for idx, (_, row) in enumerate(data.iterrows(), start=1):
        sid = str(row.get("student_id", "")).strip() or f"S{idx:02d}"
        name = _clean(row.get("Q1")) or sid
        email = _clean(row.get("RecipientEmail"))
        requested = _clean_positive_int(row.get("Q2"), default=1, low=1, high=8)
        if not email:
            warnings.append(f"{name}: no RecipientEmail value found; staff may need to look up the email manually.")

        student_rows.append({"student_id": sid, "name": name, "email": email, MAX_COL: requested})
        request_rows.append({"student_id": sid, MAX_COL: requested})

        ranked = []
        for col in rank_cols:
            rank = _number(row.get(col))
            if rank is None:
                continue
            faculty_name = _faculty_name_from_question(question_text.get(col, ""))
            fid = name2id.get(_normalize_name(faculty_name)) if faculty_name else None
            if fid is None:
                warnings.append(f"{name}: '{faculty_name or col}' from Qualtrics ranking could not match a faculty roster name.")
                continue
            ranked.append((rank, fid, faculty_name))

        seen = set()
        dense_rank = 0
        for _, fid, faculty_name in sorted(ranked, key=lambda x: x[0])[:requested]:
            if fid in seen:
                warnings.append(f"{name}: duplicate ranking for {faculty_name}; kept the earlier ranking.")
                continue
            seen.add(fid)
            dense_rank += 1
            pref_rows.append({"student_id": sid, "faculty_id": fid, "rank": dense_rank})
        if dense_rank == 0:
            warnings.append(f"{name}: no valid faculty preferences were parsed.")

        selected_slots = _selected_slots(row, day_cols, slot_map)
        if day_cols and not selected_slots:
            warnings.append(f"{name}: no valid time availability was selected; this student cannot be scheduled.")
        for slot_id in selected_slots:
            availability_rows.append({"student_id": sid, "slot_id": slot_id})

    preferences = pd.DataFrame(pref_rows, columns=["student_id", "faculty_id", "rank"])
    interests = pd.DataFrame(columns=["student_id", "interest_area"])
    students = pd.DataFrame(student_rows, columns=["student_id", "name", "email", MAX_COL])
    requests = pd.DataFrame(request_rows, columns=["student_id", MAX_COL])
    availability = pd.DataFrame(availability_rows, columns=["student_id", "slot_id"]).drop_duplicates()
    return preferences, interests, requests, availability, students, survey_faculty, warnings


def adapt_faculty_qualtrics(responses: pd.DataFrame, faculty: pd.DataFrame, grid: pd.DataFrame):
    """Return availability and staff-facing warnings from the faculty Qualtrics export."""
    data = _response_rows(responses)
    if "faculty_id" not in faculty.columns:
        return pd.DataFrame(columns=["faculty_id", "slot_id"]), [
            "Faculty list must include faculty_id before responses can be converted to availability.csv."
        ]

    faculty = faculty.copy()
    faculty["faculty_id"] = faculty["faculty_id"].astype(str).str.strip()
    by_name = {
        _normalize_name(r["name"]): str(r["faculty_id"]).strip()
        for _, r in faculty.iterrows()
        if _clean(r.get("name"))
    }
    slot_map = _qualtrics_slot_map(grid)
    day_cols = [c for c in responses.columns if re.match(r"^Q2_\d+$", str(c))]

    warnings = []
    data, duplicate_warnings = _dedupe_responses(data, ["Q1"], "faculty")
    warnings.extend(duplicate_warnings)

    rows = []
    for _, row in data.iterrows():
        name = _clean(row.get("Q1"))
        fid = by_name.get(_normalize_name(name))
        if fid is None:
            warnings.append(f"{name or 'Unnamed faculty response'}: could not match this response to a faculty name.")
            continue
        selected_slots = _selected_slots(row, day_cols, slot_map)
        if not selected_slots:
            warnings.append(f"{name}: no valid available time windows were selected.")
        for slot_id in selected_slots:
            rows.append({"faculty_id": fid, "slot_id": slot_id})

    availability = pd.DataFrame(rows, columns=["faculty_id", "slot_id"]).drop_duplicates()
    return availability, warnings


def _question_text(df: pd.DataFrame) -> dict:
    if df is None or df.empty:
        return {}
    first = df.iloc[0]
    return {col: _clean(first.get(col)) for col in df.columns}


def _response_rows(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    out = df.copy()
    if "StartDate" in out.columns:
        start = out["StartDate"].fillna("").astype(str).str.strip()
        meta = start.eq("Start Date") | start.str.startswith("{")
        out = out[~meta].copy()
    if "Finished" in out.columns:
        finished = out["Finished"].fillna("").astype(str).str.strip().str.lower()
        out = out[finished.isin(["true", "1", "yes"])].copy()
    return out.reset_index(drop=True)


def _dedupe_responses(df: pd.DataFrame, key_cols: list[str], label: str):
    if df.empty:
        return df, []
    warnings = []
    out = df.copy()
    available_cols = [col for col in key_cols if col in out.columns]
    if available_cols:
        key = out.apply(lambda row: _first_nonblank_key(row, available_cols), axis=1)
    else:
        key = None
    if key is None:
        return out, warnings
    dupes = key[key.duplicated(keep=False) & key.ne("")]
    if not dupes.empty:
        warnings.append(
            f"Duplicate {label} responses found for {dupes.nunique()} respondent(s); "
            "the app kept the latest row in the Qualtrics export."
        )
        out = out.assign(_dedupe_key=key)
        out = out[out["_dedupe_key"].eq("") | ~out["_dedupe_key"].duplicated(keep="last")]
        out = out.drop(columns=["_dedupe_key"])
    return out.reset_index(drop=True), warnings


def _first_nonblank_key(row, cols):
    for col in cols:
        val = _normalize_name(row.get(col))
        if val:
            return val
    return ""


def _selected_slots(row, day_cols, slot_map):
    slots = []
    for col in day_cols:
        day = _day_number(col)
        for label in _split_multi(row.get(col)):
            key = (day, label.strip().lower())
            slots.extend(slot_map.get(key, []))
    return sorted(set(slots))


def _qualtrics_slot_map(grid: pd.DataFrame) -> dict:
    slot_map = {}
    if grid is None or grid.empty:
        return slot_map
    for r in grid.itertuples():
        start = datetime.strptime(str(r.start_time), "%H:%M")
        for label, (lo, hi) in TIME_BLOCKS.items():
            if lo <= start < hi:
                slot_map.setdefault((int(r.day), label), []).append(r.slot_id)
    return slot_map


def _faculty_name_from_question(text: str) -> str:
    if " - " in text:
        return text.rsplit(" - ", 1)[1].strip()
    return text.strip()


def _faculty_from_rank_columns(question_text: dict, rank_cols: list, roster: pd.DataFrame) -> pd.DataFrame:
    area_by_name = {
        _normalize_name(r["name"]): _clean(r.get("area"))
        for _, r in roster.iterrows()
        if _clean(r.get("name"))
    }
    rows = []
    for col in rank_cols:
        name = _faculty_name_from_question(question_text.get(col, ""))
        if not name:
            continue
        rows.append({
            "faculty_id": str(col),
            "name": name,
            "area": area_by_name.get(_normalize_name(name), ""),
            "email": "",
        })
    return pd.DataFrame(rows, columns=["faculty_id", "name", "area", "email"])


def _day_number(col: str) -> int:
    match = re.search(r"_(\d+)$", str(col))
    return int(match.group(1)) if match else 1


def _name_to_id(roster: pd.DataFrame) -> dict:
    return {_normalize_name(n): fid for n, fid in zip(roster["name"], roster["faculty_id"])}


def _normalize_name(value) -> str:
    return re.sub(r"\s+", " ", _clean(value)).lower()


def _split_multi(value) -> list[str]:
    raw = _clean(value)
    if not raw:
        return []
    return [p.strip() for p in raw.replace(";", ",").split(",") if p.strip()]


def _clean(value) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def _number(value):
    try:
        if pd.isna(value) or str(value).strip() == "":
            return None
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _clean_positive_int(value, default, low, high):
    parsed = _number(value)
    if parsed is None:
        return default
    return min(max(parsed, low), high)
