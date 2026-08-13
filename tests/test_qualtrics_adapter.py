import os
import sys

import pandas as pd

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "src"))

from qualtrics_adapter import adapt_faculty_qualtrics, adapt_student_qualtrics

ROSTER = os.path.join(HERE, "IEOR_Faculty_Roster.xlsx")


def _grid():
    return pd.DataFrame([
        {"slot_id": "D1-S1", "day": 1, "start_time": "09:00", "end_time": "09:30"},
        {"slot_id": "D1-S2", "day": 1, "start_time": "11:30", "end_time": "12:00"},
        {"slot_id": "D1-S3", "day": 1, "start_time": "11:40", "end_time": "12:10"},
        {"slot_id": "D1-S4", "day": 1, "start_time": "14:20", "end_time": "14:50"},
        {"slot_id": "D2-S1", "day": 2, "start_time": "09:00", "end_time": "09:30"},
        {"slot_id": "D2-S2", "day": 2, "start_time": "14:20", "end_time": "14:50"},
    ])


def test_student_qualtrics_export_maps_rank_and_time_blocks():
    responses = pd.DataFrame([
        {
            "StartDate": "Start Date",
            "RecipientEmail": "Recipient Email",
            "Q1": "Student Name (First, Last)",
            "Q2": "How many faculty members do you want to meet with?",
            "Q3_1": "Rank faculty - Ilan Adler",
            "Q3_2": "Rank faculty - Anil Aswani",
            "Q3_4": "Rank faculty - Alper Atamturk",
            "Q4_1": "Please pick your time availability - Date 1",
            "Q4_2": "Please pick your time availability - Date 2",
        },
        {
            "StartDate": '{"ImportId":"startDate"}',
            "RecipientEmail": '{"ImportId":"recipientEmail"}',
            "Q1": '{"ImportId":"QID1_TEXT"}',
            "Q2": '{"ImportId":"QID2"}',
            "Q3_1": '{"ImportId":"QID3_1"}',
            "Q3_2": '{"ImportId":"QID3_2"}',
            "Q3_4": '{"ImportId":"QID3_4"}',
            "Q4_1": '{"ImportId":"QID4_1"}',
            "Q4_2": '{"ImportId":"QID4_2"}',
        },
        {
            "StartDate": "2026-08-13 09:00:00",
            "RecipientEmail": "student@example.edu",
            "Q1": "Student One",
            "Q2": "2",
            "Q3_1": "3",
            "Q3_2": "1",
            "Q3_4": "2",
            "Q4_1": "Time 1,Time 3",
            "Q4_2": "Time 2",
        },
    ])

    prefs, interests, requests, availability, students, faculty, warnings = adapt_student_qualtrics(
        responses, ROSTER, _grid()
    )

    assert prefs.to_dict("records") == [
        {"student_id": "S01", "faculty_id": "Q3_2", "rank": 1},
        {"student_id": "S01", "faculty_id": "Q3_4", "rank": 2},
    ]
    assert requests.to_dict("records") == [{"student_id": "S01", "max_meetings_requested": 2}]
    assert set(availability["slot_id"]) == {"D1-S1", "D1-S2", "D1-S4"}
    assert students.loc[0, "email"] == "student@example.edu"
    assert faculty["name"].tolist() == ["Ilan Adler", "Anil Aswani", "Alper Atamturk"]
    assert interests.empty
    assert warnings == []


def test_faculty_qualtrics_export_maps_name_and_time_blocks():
    responses = pd.DataFrame([
        {
            "StartDate": "Start Date",
            "Q1": "Please choose your name from the list",
            "Q2_1": "Please pick your time availability - Date 1",
            "Q2_2": "Please pick your time availability - Date 2",
        },
        {
            "StartDate": '{"ImportId":"startDate"}',
            "Q1": '{"ImportId":"QID1"}',
            "Q2_1": '{"ImportId":"QID2_1"}',
            "Q2_2": '{"ImportId":"QID2_2"}',
        },
        {
            "StartDate": "2026-08-13 09:00:00",
            "Q1": "Ilan Adler",
            "Q2_1": "Time 1",
            "Q2_2": "Time 3",
        },
    ])
    faculty = pd.DataFrame([{"faculty_id": "F01", "name": "Ilan Adler", "email": ""}])

    availability, warnings = adapt_faculty_qualtrics(responses, faculty, _grid())

    assert set(availability["slot_id"]) == {"D1-S1", "D1-S2", "D2-S2"}
    assert warnings == []


def test_faculty_duplicate_response_keeps_latest_row():
    responses = pd.DataFrame([
        {
            "StartDate": "Start Date",
            "Q1": "Please choose your name from the list",
            "Q2_1": "Please pick your time availability - Date 1",
            "Q2_2": "Please pick your time availability - Date 2",
        },
        {
            "StartDate": '{"ImportId":"startDate"}',
            "Q1": '{"ImportId":"QID1"}',
            "Q2_1": '{"ImportId":"QID2_1"}',
            "Q2_2": '{"ImportId":"QID2_2"}',
        },
        {"StartDate": "2026-08-13 09:00:00", "Q1": "Ilan Adler", "Q2_1": "Time 1", "Q2_2": ""},
        {"StartDate": "2026-08-13 09:10:00", "Q1": "Ilan Adler", "Q2_1": "", "Q2_2": "Time 3"},
    ])
    faculty = pd.DataFrame([{"faculty_id": "Q3_1", "name": "Ilan Adler", "email": ""}])

    availability, warnings = adapt_faculty_qualtrics(responses, faculty, _grid())

    assert set(availability["slot_id"]) == {"D2-S2"}
    assert any("Duplicate faculty responses" in w for w in warnings)


def test_student_duplicate_email_keeps_latest_row():
    base_question = {
        "StartDate": "Start Date",
        "RecipientEmail": "Recipient Email",
        "Q1": "Student Name (First, Last)",
        "Q2": "How many faculty members do you want to meet with?",
        "Q3_1": "Rank faculty - Ilan Adler",
        "Q3_2": "Rank faculty - Anil Aswani",
        "Q4_1": "Please pick your time availability - Date 1",
        "Q4_2": "Please pick your time availability - Date 2",
    }
    base_import = {
        "StartDate": '{"ImportId":"startDate"}',
        "RecipientEmail": '{"ImportId":"recipientEmail"}',
        "Q1": '{"ImportId":"QID1_TEXT"}',
        "Q2": '{"ImportId":"QID2"}',
        "Q3_1": '{"ImportId":"QID3_1"}',
        "Q3_2": '{"ImportId":"QID3_2"}',
        "Q4_1": '{"ImportId":"QID4_1"}',
        "Q4_2": '{"ImportId":"QID4_2"}',
    }
    responses = pd.DataFrame([
        base_question,
        base_import,
        {
            "StartDate": "2026-08-13 09:00:00",
            "RecipientEmail": "student@example.edu",
            "Q1": "Student One",
            "Q2": "1",
            "Q3_1": "1",
            "Q3_2": "2",
            "Q4_1": "Time 1",
            "Q4_2": "",
        },
        {
            "StartDate": "2026-08-13 09:10:00",
            "RecipientEmail": "student@example.edu",
            "Q1": "Student One",
            "Q2": "1",
            "Q3_1": "2",
            "Q3_2": "1",
            "Q4_1": "",
            "Q4_2": "Time 3",
        },
    ])

    prefs, _, _, availability, _, _, warnings = adapt_student_qualtrics(responses, ROSTER, _grid())

    assert prefs.to_dict("records") == [{"student_id": "S01", "faculty_id": "Q3_2", "rank": 1}]
    assert set(availability["slot_id"]) == {"D2-S2"}
    assert any("Duplicate student responses" in w for w in warnings)


def test_unfinished_qualtrics_rows_are_ignored():
    responses = pd.DataFrame([
        {
            "StartDate": "Start Date",
            "Finished": "Finished",
            "RecipientEmail": "Recipient Email",
            "Q1": "Student Name (First, Last)",
            "Q2": "How many faculty members do you want to meet with?",
            "Q3_1": "Rank faculty - Ilan Adler",
            "Q4_1": "Please pick your time availability - Date 1",
        },
        {
            "StartDate": '{"ImportId":"startDate"}',
            "Finished": '{"ImportId":"finished"}',
            "RecipientEmail": '{"ImportId":"recipientEmail"}',
            "Q1": '{"ImportId":"QID1_TEXT"}',
            "Q2": '{"ImportId":"QID2"}',
            "Q3_1": '{"ImportId":"QID3_1"}',
            "Q4_1": '{"ImportId":"QID4_1"}',
        },
        {
            "StartDate": "2026-08-13 09:00:00",
            "Finished": "False",
            "RecipientEmail": "unfinished@example.edu",
            "Q1": "Unfinished Student",
            "Q2": "1",
            "Q3_1": "1",
            "Q4_1": "Time 1",
        },
        {
            "StartDate": "2026-08-13 09:10:00",
            "Finished": "True",
            "RecipientEmail": "finished@example.edu",
            "Q1": "Finished Student",
            "Q2": "1",
            "Q3_1": "1",
            "Q4_1": "Time 1",
        },
    ])

    prefs, _, _, _, students, _, _ = adapt_student_qualtrics(responses, ROSTER, _grid())

    assert prefs["student_id"].tolist() == ["S01"]
    assert students["email"].tolist() == ["finished@example.edu"]
