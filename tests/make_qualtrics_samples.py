"""Generate synthetic Qualtrics-style CSV exports for staff testing.

These files mimic the finalized Qualtrics structure: one header row, two
Qualtrics metadata rows, then response rows. The data is fake and safe to commit.
"""

import os
import random
import sys

import pandas as pd

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "src"))

from roster import load_roster

OUT = os.path.join(HERE, "sample_data")
ROSTER = os.path.join(HERE, "IEOR_Faculty_Roster.xlsx")

STUDENTS = [
    "Maya Patel", "Liam Nguyen", "Sofia Garcia", "Noah Kim", "Aisha Hassan", "Ethan Chen",
    "Isabella Martinez", "Lucas Johnson", "Amara Okafor", "Daniel Lee", "Nina Singh", "Mateo Rivera",
]
BASE_COLUMNS = [
    "StartDate", "EndDate", "Status", "IPAddress", "Progress", "Duration (in seconds)", "Finished",
    "RecordedDate", "ResponseId", "RecipientLastName", "RecipientFirstName", "RecipientEmail",
    "ExternalReference", "LocationLatitude", "LocationLongitude", "DistributionChannel", "UserLanguage",
]


def main():
    os.makedirs(OUT, exist_ok=True)
    faculty = load_roster(ROSTER).head(10)[["faculty_id", "name", "area"]].reset_index(drop=True)
    write_student_sample(faculty, "qualtrics_student_responses_balanced_12.csv", limited=False)
    write_student_sample(faculty, "qualtrics_student_responses_limited_12.csv", limited=True)
    write_student_edge_sample(faculty)
    write_faculty_sample(faculty, "qualtrics_faculty_responses_balanced_10.csv", sparse=False)
    write_faculty_sample(faculty, "qualtrics_faculty_responses_sparse_10.csv", sparse=True)
    write_faculty_unmatched_sample(faculty)
    print("wrote Qualtrics sample CSVs to sample_data/")


def write_student_sample(faculty, filename, limited):
    rows = [_student_question_row(faculty), _student_import_row(faculty)]
    rng = random.Random(23 if limited else 19)
    for i, name in enumerate(STUDENTS, start=1):
        request = 2 + (i % 4)
        ranking = faculty["name"].tolist()
        rng.shuffle(ranking)
        if i <= 5:
            ranking = faculty["name"].tolist()[i % 3:] + faculty["name"].tolist()[:i % 3]
        day1 = "Time 1,Time 2,Time 3"
        day2 = "Time 1,Time 2,Time 3"
        if limited:
            day1 = ["Time 1", "Time 2", "Time 3", "Time 1,Time 2"][i % 4]
            day2 = ["Time 2", "Time 3", "Time 1", ""][i % 4]
        rows.append(_student_response_row(i, name, request, faculty, ranking, day1, day2))
    _write(rows, _student_columns(faculty), filename)


def write_student_edge_sample(faculty):
    rows = [_student_question_row(faculty), _student_import_row(faculty)]
    ranking = faculty["name"].tolist()
    rows.append(_student_response_row(1, "Student Missing Time", 3, faculty, ranking, "", ""))
    rows.append(_student_response_row(2, "Student No Email", 2, faculty, ranking[1:] + ranking[:1], "Time 1", "Time 3", email=""))
    rows.append(_student_response_row(3, "Student One Choice", 1, faculty, ranking[2:] + ranking[:2], "Time 2", "Time 2"))
    _write(rows, _student_columns(faculty), "qualtrics_student_responses_edge_cases.csv")


def write_faculty_sample(faculty, filename, sparse):
    rows = [_faculty_question_row(), _faculty_import_row()]
    names = faculty["name"].tolist()
    if sparse:
        names = names[:6]
    for i, name in enumerate(names, start=1):
        if sparse:
            day1 = ["Time 1", "Time 2", "", "Time 3", "Time 1,Time 2", ""][i - 1]
            day2 = ["Time 2", "", "Time 3", "Time 1", "", "Time 2,Time 3"][i - 1]
        else:
            day1 = "Time 1,Time 2,Time 3"
            day2 = "Time 1,Time 2,Time 3"
        rows.append(_faculty_response_row(i, name, day1, day2))
    _write(rows, BASE_COLUMNS + ["Q1", "Q2_1", "Q2_2"], filename)


def write_faculty_unmatched_sample(faculty):
    rows = [_faculty_question_row(), _faculty_import_row()]
    rows.append(_faculty_response_row(1, faculty.loc[0, "name"], "Time 1", "Time 2"))
    rows.append(_faculty_response_row(2, "Professor Not In Survey", "Time 1", "Time 3"))
    _write(rows, BASE_COLUMNS + ["Q1", "Q2_1", "Q2_2"], "qualtrics_faculty_responses_edge_cases.csv")


def _student_columns(faculty):
    rank_cols = [f"Q3_{i + 1}" for i in range(len(faculty))]
    return BASE_COLUMNS + ["Q1", "Q2"] + rank_cols + ["Q4_1", "Q4_2"]


def _base_question_row():
    return {
        "StartDate": "Start Date",
        "EndDate": "End Date",
        "Status": "Response Type",
        "IPAddress": "IP Address",
        "Progress": "Progress",
        "Duration (in seconds)": "Duration (in seconds)",
        "Finished": "Finished",
        "RecordedDate": "Recorded Date",
        "ResponseId": "Response ID",
        "RecipientLastName": "Recipient Last Name",
        "RecipientFirstName": "Recipient First Name",
        "RecipientEmail": "Recipient Email",
        "ExternalReference": "External Data Reference",
        "LocationLatitude": "Location Latitude",
        "LocationLongitude": "Location Longitude",
        "DistributionChannel": "Distribution Channel",
        "UserLanguage": "User Language",
    }


def _base_import_row():
    return {
        "StartDate": '{"ImportId":"startDate","timeZone":"America/Los_Angeles"}',
        "EndDate": '{"ImportId":"endDate","timeZone":"America/Los_Angeles"}',
        "Status": '{"ImportId":"status"}',
        "IPAddress": '{"ImportId":"ipAddress"}',
        "Progress": '{"ImportId":"progress"}',
        "Duration (in seconds)": '{"ImportId":"duration"}',
        "Finished": '{"ImportId":"finished"}',
        "RecordedDate": '{"ImportId":"recordedDate","timeZone":"America/Los_Angeles"}',
        "ResponseId": '{"ImportId":"_recordId"}',
        "RecipientLastName": '{"ImportId":"recipientLastName"}',
        "RecipientFirstName": '{"ImportId":"recipientFirstName"}',
        "RecipientEmail": '{"ImportId":"recipientEmail"}',
        "ExternalReference": '{"ImportId":"externalDataReference"}',
        "LocationLatitude": '{"ImportId":"locationLatitude"}',
        "LocationLongitude": '{"ImportId":"locationLongitude"}',
        "DistributionChannel": '{"ImportId":"distributionChannel"}',
        "UserLanguage": '{"ImportId":"userLanguage"}',
    }


def _student_question_row(faculty):
    row = _base_question_row()
    row.update({
        "Q1": "Student Name (First, Last)",
        "Q2": "How many faculty members do you want to meet with?",
        "Q4_1": "Please pick your time availability - Date 1",
        "Q4_2": "Please pick your time availability - Date 2",
    })
    for i, name in enumerate(faculty["name"], start=1):
        row[f"Q3_{i}"] = (
            "Based on your previous answer: Please rank the desired professor engagements "
            f"from most favorite to least. - {name}"
        )
    return row


def _student_import_row(faculty):
    row = _base_import_row()
    row.update({"Q1": '{"ImportId":"QID1_TEXT"}', "Q2": '{"ImportId":"QID2"}'})
    for i in range(1, len(faculty) + 1):
        row[f"Q3_{i}"] = f'{{"ImportId":"QID3_{i}"}}'
    row["Q4_1"] = '{"ImportId":"QID4_1"}'
    row["Q4_2"] = '{"ImportId":"QID4_2"}'
    return row


def _student_response_row(i, name, request, faculty, ranking, day1, day2, email=None):
    if email is None:
        email = f"student{i:02d}@example.edu"
    row = _response_base(i, name, email)
    row["Q1"] = name
    row["Q2"] = request
    rank_lookup = {faculty_name: rank for rank, faculty_name in enumerate(ranking, start=1)}
    for j, faculty_name in enumerate(faculty["name"], start=1):
        row[f"Q3_{j}"] = rank_lookup[faculty_name]
    row["Q4_1"] = day1
    row["Q4_2"] = day2
    return row


def _faculty_question_row():
    row = _base_question_row()
    row.update({
        "Q1": "Please choose your name from the list",
        "Q2_1": "Please pick your time availability - Date 1",
        "Q2_2": "Please pick your time availability - Date 2",
    })
    return row


def _faculty_import_row():
    row = _base_import_row()
    row.update({
        "Q1": '{"ImportId":"QID1"}',
        "Q2_1": '{"ImportId":"QID2_1"}',
        "Q2_2": '{"ImportId":"QID2_2"}',
    })
    return row


def _faculty_response_row(i, name, day1, day2):
    row = _response_base(i, name, f"faculty{i:02d}@example.edu")
    row["Q1"] = name
    row["Q2_1"] = day1
    row["Q2_2"] = day2
    return row


def _response_base(i, name, email):
    first, *last = name.split()
    return {
        "StartDate": f"2026-08-13 09:{i:02d}:00",
        "EndDate": f"2026-08-13 09:{i + 1:02d}:00",
        "Status": "IP Address",
        "IPAddress": "",
        "Progress": "100",
        "Duration (in seconds)": str(45 + i),
        "Finished": "True",
        "RecordedDate": f"2026-08-13 09:{i + 1:02d}:10",
        "ResponseId": f"R_SAMPLE_{i:03d}",
        "RecipientLastName": " ".join(last),
        "RecipientFirstName": first,
        "RecipientEmail": email,
        "ExternalReference": "",
        "LocationLatitude": "",
        "LocationLongitude": "",
        "DistributionChannel": "email",
        "UserLanguage": "EN",
    }


def _write(rows, columns, filename):
    pd.DataFrame(rows, columns=columns).to_csv(os.path.join(OUT, filename), index=False)


if __name__ == "__main__":
    main()
