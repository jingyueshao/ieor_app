# Sample data

App download-button samples:

- `test_students.csv`: 40-student recipient list.
- `test_faculty.csv`: 10-faculty scheduler roster.
- `test_preferences.csv`: preferences for the same 40 students and 10 faculty.
- `test_availability.csv`: availability for the same 10 faculty.
- `test_student_requests.csv`: max-meeting requests for the same 40 students.
- `test_student_availability.csv`: time availability for the same 40 students.

These files use the same people as the full staff workflow test files below, so
the in-app sample downloads and direct GitHub samples stay consistent.

Full staff workflow test samples:

- `staff_test_students_40.csv`: 40-student recipient list for the Prospective Students tab.
- `staff_test_student_google_responses_40.csv`: older simulated Google Sheets CSV export from the student preference form.
- `staff_test_faculty_google_responses_10.csv`: older simulated Google Sheets CSV export from the faculty availability form.

Qualtrics workflow test samples:

- `qualtrics_student_responses_balanced_12.csv`: clean 12-student Qualtrics export with broad student availability.
- `qualtrics_faculty_responses_balanced_10.csv`: clean 10-faculty Qualtrics export with broad faculty availability.
- `qualtrics_student_responses_limited_12.csv`: student export with tighter time availability to test time constraints.
- `qualtrics_faculty_responses_sparse_10.csv`: faculty export with fewer available windows to test bottleneck diagnostics.
- `qualtrics_student_responses_edge_cases.csv`: student export with missing email and missing availability examples.
- `qualtrics_faculty_responses_edge_cases.csv`: faculty export with an unmatched faculty name example.

Scheduler-ready test samples:

- `staff_test_scheduler_faculty_10.csv`
- `staff_test_scheduler_availability_10.csv`
- `staff_test_scheduler_preferences_40.csv`
- `staff_test_scheduler_students_40.csv`
- `staff_test_student_interests_40.csv`

Recommended testing paths:

1. Semi-automated response upload path:
   - Upload `staff_test_students_40.csv` in tab 3.
   - Upload `qualtrics_student_responses_balanced_12.csv` as the student response CSV.
   - Upload `qualtrics_faculty_responses_balanced_10.csv` as the faculty response CSV.
   - Use parsed response data in tab 5.

2. Stress-test Qualtrics constraints:
   - Upload `qualtrics_student_responses_limited_12.csv`.
   - Upload `qualtrics_faculty_responses_sparse_10.csv`.
   - Build schedules and review warnings/diagnostics.

3. Direct scheduler CSV path:
   - In tab 5, upload `test_faculty.csv`, `test_availability.csv`, `test_preferences.csv`, and optionally `test_student_requests.csv` and `test_student_availability.csv`.
   - The `staff_test_scheduler_*.csv` files are equivalent, more descriptive copies for reviewers browsing the repo.
