# Staff User Guide

This guide is for IEOR staff using the Visit-Day Matching app in a browser.

## What the app does

The app builds student-faculty meeting schedules for Visit Day. It uses student
ranked faculty preferences, faculty availability, and the visit-day time grid to
produce a schedule that prioritizes student satisfaction while keeping outcomes
fair.

## Recommended workflow

### 1. Build visit days

Open the **Build visit days** tab.

Set:

- meeting length
- buffer time between meetings
- start and end time for each day
- blocked events such as lunch, welcome sessions, tours, or breaks

The app shows how many meeting slots are available. If there are no slots, widen
the day hours or remove blocks.

### 2. Load prospective students

Open **Prospective students**.

Enter student names, emails, and max meetings requested directly in the table.
Add rows as needed. This is the recommended workflow for a typical cohort of
roughly 40 students. Max meetings requested defaults to 4.

If you already have a file, use the optional CSV import section. The CSV can use:

- `name,email`
- or `first name,last name,email`

Use **Download sample student CSV** if you want to test the upload flow without
using real student data.

Use the finalized Qualtrics student survey. In the survey invitation or survey
instructions, tell students that selecting at least 3 genuine faculty preferences
improves schedule flexibility, even though the app can accept as few as 1
requested meeting.

After students respond, export the Qualtrics responses as CSV and upload it
under **Import student Qualtrics responses**. The app will create downloadable
`preferences.csv`, `students.csv`, and `student_availability.csv` files.

The student survey does not need a separate email question. For real Qualtrics
mailings, the exported `RecipientEmail` column carries the email address staff
can use later when sending individual schedules.

### 3. Load faculty availability

Open **Faculty availability**.

Enter faculty names and emails directly in the table. Area is optional. The app
assigns simple faculty IDs such as `F01` and `F02` for the availability workflow.
This is the recommended workflow for a small faculty group.

If you already have a file, use the optional CSV import section. Use **Download
sample faculty CSV** if you want to test the upload flow without using real
faculty data. The app previews the availability form based on the visit-day slots
configured in step 1.

For scheduling, the availability file must eventually be converted to:

```csv
faculty_id,slot_id
F01,D1-S1
F01,D1-S2
```

Use the finalized Qualtrics faculty survey. If possible, upload the student
Qualtrics CSV before the faculty CSV so the app can reuse the exact faculty list
from the student ranking question. After faculty respond, export the Qualtrics
responses as CSV and upload it under **Import faculty Qualtrics responses**. The
app will create downloadable `availability.csv`.

Faculty response parsing requires faculty IDs. When you use the direct-entry
table, the app creates those IDs automatically.

### 4. Build schedules

Open **Build schedules**.

For a quick test, choose **Use Demo Data**.

For real data, choose **Use Collected Data** and upload:

- `faculty.csv`
- `availability.csv`
- `preferences.csv`

The app provides sample scheduler CSVs in this section. Download those files if
you want to test the collected-data workflow exactly as staff will use it.

If you already parsed student and faculty responses in the current app session,
leave **Use parsed Qualtrics response data from this session** checked instead
of downloading and re-uploading the solver-ready files.

For direct CSV scheduling, upload:

- `faculty.csv`
- `availability.csv`
- `preferences.csv`
- optional `students.csv`
- optional `student_availability.csv`

The app checks the files before solving. Red errors must be fixed before the
schedule can run. Yellow warnings are allowed, but staff should review them
because they may explain sparse or uneven schedules.

### 5. Review diagnostics

After solving, start with the simplified review panel:

- total meetings
- capacity utilization
- average meetings per student
- number of items needing review
- plain-language review notes

The review notes highlight practical issues such as faculty with no meetings,
faculty nobody selected, students who may need manual attention, and popular
faculty bottlenecks. Detailed diagnostic tables are available only in the
optional troubleshooting expander.

### 6. Make manual adjustments

Open **Manual review** after a schedule is produced.

Staff can:

- lock a meeting so it is marked as intentionally kept
- unlock a meeting
- remove an unlocked meeting
- manually add a meeting if the student and faculty do not already have a
  conflict in that time slot and both marked the slot as available

Manual additions are locked by default. This version does not rerun the optimizer
around locked meetings; it is intended for small final corrections.

### 7. Download outputs

Open the **Exports** tab and download:

- `master_schedule.csv`
- `student_schedules.csv`
- `faculty_schedules.csv`
- `student_email_text.csv`
- `faculty_email_text.csv`

Save these files somewhere durable after each final run. The app session is not
a permanent archive.

## Common data issues

### Unknown faculty IDs

The same `faculty_id` values must be used in `faculty.csv`,
`availability.csv`, and `preferences.csv`.

### Unknown slot IDs

Availability must refer to slot IDs generated by the current visit-day setup,
such as `D1-S1`.

### Too few preferences

Students with very short preference lists may receive fewer meetings. Ask them
for more ranked faculty if possible.

### Faculty with no availability

Faculty without available slots cannot be scheduled, even if many students rank
them highly.

### Students with no usable availability

Students without any parsed time slots cannot be scheduled. Check the Qualtrics
time availability answers first.

## Safety expectations

The launch workflow does not send emails automatically. Staff should use the
downloaded recipient list and email text, then send through Gmail or Outlook.

Do not enter credentials or passwords into code files. Use Streamlit secrets or
environment variables when the deployment owner enables integrations.

For deployed use, the app should ask for an internal password before showing any
workflow screens. If it does not, ask the deployment owner to set `APP_PASSWORD`
in Streamlit Secrets before using real data.
