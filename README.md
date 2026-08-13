# IEOR Visit-Day Matching Tool

Streamlit app for helping Berkeley IEOR staff schedule prospective graduate
student meetings with faculty during Visit Day.

The app is meant to be a practical internal operations tool: staff configure the
visit-day structure, collect or upload student preferences and faculty
availability, run an OR-Tools CP-SAT scheduler, review diagnostics, and download
the final schedules.

## Current workflow

1. Build visit days: set meeting length, buffer time, day hours, and blocked
   events such as lunch or tours.
2. Enter prospective student names/emails directly, or import an optional CSV,
   set each student's max meetings requested, then preview the student
   preference form.
3. Use the finalized Qualtrics student survey, then upload the exported student
   response CSV. The app parses requested meeting counts, ranked faculty, and
   daily time availability.
4. Enter faculty names/emails directly, use the finalized Qualtrics faculty
   survey, and upload the exported faculty response CSV.
5. Build schedules from demo data, parsed session data, or uploaded CSVs.
6. Review validation messages before solving.
7. Review schedule diagnostics after solving.
8. Download master, student, faculty, and email-ready exports.

The intake workflow is semi-automated and staff-controlled. The app prepares
Qualtrics surveys, recipient lists, and email text, but staff send emails
manually through Gmail/Outlook and upload exported response CSVs after surveys
are collected. This avoids API setup and keeps handoff simpler.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

CLI smoke test:

```bash
python src/run.py
```

Pipeline test:

```bash
pytest
```

## Input schemas

For the scheduler, the collected-data path expects three required CSV files and
one optional student availability file.
For small groups, the intake tabs use editable tables so staff can type names
and emails directly. Sample files are still available in `sample_data/` and
through optional in-app download buttons.

`faculty.csv`

```csv
faculty_id,name,area
F01,Faculty Name,Optimization
```

Required columns: `faculty_id`, `name`. `area` is useful for display and future
filtering, but the Stage 1 scheduler validation only requires the first two.

`availability.csv`

```csv
faculty_id,slot_id
F01,D1-S1
F01,D1-S2
```

Required columns: `faculty_id`, `slot_id`. Slot IDs must come from the visit-day
setup shown in the app.

`preferences.csv`

```csv
student_id,faculty_id,rank
S01,F01,1
S01,F03,2
```

Required columns: `student_id`, `faculty_id`, `rank`. Ranks must be positive
whole numbers.

`students.csv` (optional)

```csv
student_id,max_meetings_requested
S01,4
S02,3
```

If omitted, `max_meetings_requested` defaults to 4. The effective maximum used by
the optimizer is the smaller of the requested maximum, the number of ranked
faculty for that student, and the number of slots where the student can attend.

`student_availability.csv` (optional)

```csv
student_id,slot_id
S01,D1-S1
S01,D1-S2
```

When Qualtrics student responses are uploaded, the app creates this table from
the daily Time 1/Time 2/Time 3 availability questions. Time blocks are interpreted
as 9:00-11:40, 11:40-14:20, and 14:20-17:00 for each day. If omitted in the
direct CSV path, the app assumes students are available for all visit-day slots.

## Validation

Before solving, the app checks:

- missing required columns
- duplicate faculty IDs
- duplicate student/faculty preference pairs
- duplicate faculty/slot availability rows
- unknown faculty IDs in preferences or availability
- unknown slot IDs in availability
- unknown student IDs or slot IDs in student availability
- invalid rank values
- empty preference or availability files
- faculty with zero availability
- students with too few preferences
- students with no usable time availability
- unreasonable max meeting requests

Errors block scheduling. Warnings allow scheduling but should be reviewed.

## Diagnostics and exports

After a successful solve, the app shows a simplified review dashboard:

- total meetings
- capacity utilization
- average meetings per student
- number of issues that need review
- plain-language review notes, such as faculty with no meetings, faculty nobody
  selected, students with weak outcomes, and popular faculty bottlenecks

Detailed diagnostic tables are still available in an optional troubleshooting
section, but the default view is designed for staff review rather than model
debugging.

Downloadable files:

- `master_schedule.csv`
- `student_schedules.csv`
- `faculty_schedules.csv`
- `student_email_text.csv`
- `faculty_email_text.csv`
- `send_log.csv`
- `student_diagnostics.csv`

Staff should download these files after each final run because Streamlit session
state is not a permanent system of record.

## Project layout

- `app.py`: Streamlit staff app
- `sample_data/`: small CSV files for trying the upload workflow
- `src/config.py`: tunable scheduling settings
- `src/visit_days.py`: visit-day and slot-grid construction
- `src/model.py`: OR-Tools CP-SAT optimizer
- `src/validation.py`: staff-facing input validation
- `src/diagnostics.py`: schedule diagnostics tables
- `src/exports.py`: downloadable schedule export tables
- `src/google_intake.py`: recipient validation and staff-send package boundary
- `src/qualtrics_adapter.py`: finalized Qualtrics student/faculty response parser
- `src/form_spec.py`: student preference form template
- `src/faculty_form_spec.py`: faculty availability form template
- `src/adapter.py`: student response CSV adapter
- `tests/`: pipeline checks and sample response generation

## Safety notes

- Do not hardcode credentials, API keys, passwords, Gmail accounts, OAuth
  secrets, or personal data.
- Use Streamlit secrets or environment variables for credentials.
- Set `APP_PASSWORD` in Streamlit Secrets before sharing a deployed app link.
- The app should not send live email in the launch workflow.
- Staff should send emails manually through Gmail/Outlook using the generated
  recipients and email text.
- Preserve CSV upload/download workflows as the primary handoff path.
