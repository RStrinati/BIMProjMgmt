from tkinter import messagebox
from dateutil.relativedelta import relativedelta
from datetime import timedelta
import datetime
import pandas as pd
from database import (
    connect_to_db,
    insert_review_cycle_details,
    upsert_project_review_progress,
    get_cycle_ids,
)
from constants import schema as S





def update_review_date(schedule_id, new_date):
    """Update a specific review date."""
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute(
        f"""
        UPDATE {S.ReviewSchedule.TABLE}
        SET {S.ReviewSchedule.REVIEW_DATE} = ?, {S.ReviewSchedule.MANUAL_OVERRIDE} = 1
        WHERE {S.ReviewSchedule.ID} = ?;
        """,
        (new_date, schedule_id),
    )
    conn.commit()
    conn.close()

def adjust_future_tasks(schedule_id, new_date, project_id, cycle_id):
    """Auto-adjust all future reviews after moving a task."""
    conn = connect_to_db()
    cursor = conn.cursor()

    cursor.execute(
        f"""
        SELECT {S.ReviewSchedule.ID}, {S.ReviewSchedule.REVIEW_DATE} FROM {S.ReviewSchedule.TABLE}
        WHERE {S.ReviewSchedule.PROJECT_ID} = ? AND {S.ReviewSchedule.CYCLE_ID} = ? AND {S.ReviewSchedule.ID} > ?
        ORDER BY {S.ReviewSchedule.REVIEW_DATE} ASC;
        """,
        (project_id, cycle_id, schedule_id),
    )

    future_reviews = cursor.fetchall()
    original_review_date = pd.to_datetime(new_date)

    for idx, (future_schedule_id, future_review_date) in enumerate(future_reviews):
        shift_days = (pd.to_datetime(future_review_date) - original_review_date).days
        new_future_date = original_review_date + pd.Timedelta(days=shift_days)

        cursor.execute(
            f"""
            UPDATE {S.ReviewSchedule.TABLE}
            SET {S.ReviewSchedule.REVIEW_DATE} = ?
            WHERE {S.ReviewSchedule.ID} = ?;
            """,
            (new_future_date.strftime("%Y-%m-%d"), future_schedule_id),
        )

    conn.commit()
    conn.close()

def delete_review_task(schedule_id):
    """Delete a review task while keeping future tasks unchanged."""
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute(
        f"DELETE FROM {S.ReviewSchedule.TABLE} WHERE {S.ReviewSchedule.ID} = ?;",
        (schedule_id,),
    )
    conn.commit()
    conn.close()

# ---------------------------------------------------

def submit_review_schedule(
    project_dropdown,
    cycle_dropdown,
    review_start_date_entry,
    number_of_reviews_entry,
    review_frequency_entry,
    license_start_date_entry,
    license_duration_entry,
    stage_entry,
    fee_entry,
    assigned_users_entry,
    reviews_per_phase_entry,
    cycle_rows,
    new_contract_var,
): 
    """Submit review schedule to the database."""
    try:
        conn = connect_to_db()
        cursor = conn.cursor()

        selected_project = project_dropdown.get()
        if " - " in selected_project:
            project_id = selected_project.split(" - ")[0]
        else:
            messagebox.showerror("Error", "Invalid project selection!")
            return

        review_start_date = review_start_date_entry.get_date()
        number_of_reviews = int(number_of_reviews_entry.get())
        review_frequency = int(review_frequency_entry.get())
        license_start_date = license_start_date_entry.get_date()
        license_duration_months = int(license_duration_entry.get())

        license_end_date = license_start_date + relativedelta(months=license_duration_months)

        review_start_date_str = review_start_date.strftime('%Y-%m-%d')
        license_start_date_str = license_start_date.strftime('%Y-%m-%d')
        license_end_date_str = license_end_date.strftime('%Y-%m-%d')

        stage = stage_entry.get()
        fee = float(fee_entry.get() or 0)
        assigned_users = assigned_users_entry.get()
        reviews_per_phase = reviews_per_phase_entry.get()

        if not cycle_rows:
            messagebox.showerror("Error", "Cycle table has no rows to submit")
            return

        row_vals = cycle_rows[0][1]

        def parse_date(val):
            try:
                return datetime.datetime.strptime(val, "%Y-%m-%d").date()
            except Exception:
                return None

        planned_start = parse_date(row_vals[1])
        planned_completion = parse_date(row_vals[2])
        actual_start = parse_date(row_vals[3])
        actual_completion = parse_date(row_vals[4])
        hold_date = parse_date(row_vals[5])
        resume_date = parse_date(row_vals[6])
        new_contract = bool(new_contract_var.get())

        # ✅ Generate cycle ID properly
        cursor.execute(
            f"SELECT ISNULL(MAX({S.ReviewParameters.CYCLE_ID}), 0) + 1 FROM {S.ReviewParameters.TABLE} WHERE {S.ReviewParameters.PROJECT_ID} = ?",
            (project_id,),
        )
        cycle_id = cursor.fetchone()[0]

        cursor.execute(
            f"""
            INSERT INTO {S.ReviewParameters.TABLE}
            ({S.ReviewParameters.PROJECT_ID}, {S.ReviewParameters.REVIEW_START_DATE}, {S.ReviewParameters.NUMBER_OF_REVIEWS}, {S.ReviewParameters.REVIEW_FREQUENCY}, {S.ReviewParameters.LICENSE_START}, {S.ReviewParameters.LICENSE_END}, {S.ReviewParameters.CYCLE_ID})
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                project_id,
                review_start_date_str,
                number_of_reviews,
                review_frequency,
                license_start_date_str,
                license_end_date_str,
                cycle_id,
            ),
        )

        insert_review_cycle_details(
            project_id,
            cycle_id,
            stage,
            fee,
            assigned_users,
            reviews_per_phase,
            planned_start.strftime("%Y-%m-%d") if planned_start else None,
            planned_completion.strftime("%Y-%m-%d") if planned_completion else None,
            actual_start.strftime("%Y-%m-%d") if actual_start else None,
            actual_completion.strftime("%Y-%m-%d") if actual_completion else None,
            hold_date.strftime("%Y-%m-%d") if hold_date else None,
            resume_date.strftime("%Y-%m-%d") if resume_date else None,
            new_contract,
        )

        # store scoped review count for progress tracking
        upsert_project_review_progress(project_id, cycle_id, number_of_reviews, 0)

        # ✅ Run stored procedure before closing connection
        print("✅ Running stored procedure: EXEC GenerateReviewSchedule;")
        cursor.execute("EXEC GenerateReviewSchedule;")
        print("✅ Stored procedure executed successfully!")

        conn.commit()
        conn.close()

        messagebox.showinfo("Success", "Review schedule submitted successfully!")

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {str(e)}")

def update_cycle_dropdown(project_id, cycle_dropdown):
    """Fetch latest cycle IDs and update the UI dropdown."""
    cycles = get_cycle_ids(project_id)
    cycle_dropdown['values'] = cycles
    if cycles and cycles[0] != "No Cycles Available":
        cycle_dropdown.current(0)
    else:
        cycle_dropdown.set("No Cycles Available")

def fetch_review_summary(project_dropdown, cycle_dropdown, summary_label):
    """Fetch and display review summary for the selected project and cycle."""
    project_id = project_dropdown.get().split(" - ")[0]
    cycle_id = cycle_dropdown.get()

    if project_id == "No Projects" or cycle_id == "No Cycles Available":
        messagebox.showerror("Error", "Please select a valid project and cycle ID!")
        return

    try:
        conn = connect_to_db()
        cursor = conn.cursor()
        cursor.execute(
            f"""
                    WITH ReviewData AS (
                        SELECT
                            rp.{S.ReviewParameters.PROJECT_ID}, rp.{S.ReviewParameters.CYCLE_ID}, rp.{S.ReviewParameters.REVIEW_START_DATE}, rp.{S.ReviewParameters.LICENSE_START}, rp.{S.ReviewParameters.LICENSE_END},
                            rp.{S.ReviewParameters.NUMBER_OF_REVIEWS}, rp.{S.ReviewParameters.REVIEW_FREQUENCY},
                            MAX(rs.{S.ReviewSchedule.REVIEW_DATE}) AS LastReviewDate,
                            DATEDIFF(DAY, rp.{S.ReviewParameters.LICENSE_START}, rp.{S.ReviewParameters.LICENSE_END}) AS LicenseDays,
                            DATEDIFF(MONTH, rp.{S.ReviewParameters.LICENSE_START}, rp.{S.ReviewParameters.LICENSE_END}) AS LicenseMonths,
                            (DATEDIFF(DAY, rp.{S.ReviewParameters.LICENSE_START}, rp.{S.ReviewParameters.LICENSE_END}) / rp.{S.ReviewParameters.REVIEW_FREQUENCY}) AS PossibleReviewsWithinLicense
                        FROM {S.ReviewParameters.TABLE} rp
                        LEFT JOIN {S.ReviewSchedule.TABLE} rs ON rp.{S.ReviewParameters.PROJECT_ID} = rs.{S.ReviewSchedule.PROJECT_ID} AND rp.{S.ReviewParameters.CYCLE_ID} = rs.{S.ReviewSchedule.CYCLE_ID}
                        WHERE rp.{S.ReviewParameters.PROJECT_ID} = ? AND rp.{S.ReviewParameters.CYCLE_ID} = ?
                        GROUP BY rp.{S.ReviewParameters.PROJECT_ID}, rp.{S.ReviewParameters.CYCLE_ID}, rp.{S.ReviewParameters.REVIEW_START_DATE}, rp.{S.ReviewParameters.LICENSE_START}, rp.{S.ReviewParameters.LICENSE_END}, rp.{S.ReviewParameters.NUMBER_OF_REVIEWS}, rp.{S.ReviewParameters.REVIEW_FREQUENCY}
                    )
                    SELECT *,
                        CASE
                            WHEN NumberOfReviews > PossibleReviewsWithinLicense THEN 'Yes'
                            ELSE 'No'
                        END AS ExceedsLicense
                    FROM ReviewData;
                """,
            (project_id, cycle_id),
        )

        data = cursor.fetchone()
        conn.close()

        if not data:
            summary_label.config(text="No review summary data found.", fg="red")
            return

        # ✅ Extract results
        (proj_id, cycle, start_date, license_start, license_end, num_reviews, review_freq, last_review, 
        license_days, license_months, possible_reviews, exceeds_license) = data

        # ✅ Update the Label with Correct Summary Data
        summary_text = (
            f"📌 Project ID: {proj_id}\n"
            f"📌 Cycle ID: {cycle}\n"
            f"📆 Review Start Date: {start_date}\n"
            f"📆 License Period: {license_start} ➝ {license_end} ({license_months} months, {license_days} days)\n"
            f"📅 Last Review Date: {last_review if last_review else 'None'}\n"
            f"🔢 Planned Reviews: {num_reviews}\n"
            f"🔁 Review Frequency: Every {review_freq} days\n"
            f"✅ Possible Reviews in License: {possible_reviews}\n"
            f"⚠️ Exceeds License Period? {exceeds_license}"
        )
        summary_label.config(text=summary_text, fg="black")

    except Exception as e:
        summary_label.config(text=f"Error: {str(e)}", fg="red")


def generate_stage_review_schedule(project_id, stages):
    """Create review schedule entries for provided project stages."""
    conn = connect_to_db()
    if conn is None:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT ISNULL(MAX({S.ReviewParameters.CYCLE_ID}),0)+1 FROM {S.ReviewParameters.TABLE} WHERE {S.ReviewParameters.PROJECT_ID} = ?",
            (project_id,),
        )
        cycle_id = cursor.fetchone()[0]

        # Insert placeholder row so new cycle is visible via get_cycle_ids
        if stages:
            start_dates = [s["start_date"] for s in stages]
            end_dates = [s["end_date"] for s in stages]
            review_start = min(start_dates).strftime("%Y-%m-%d")
            license_start = review_start
            license_end = max(end_dates).strftime("%Y-%m-%d")
        else:
            review_start = None
            license_start = None
            license_end = None

        cursor.execute(
            f"""
            INSERT INTO {S.ReviewParameters.TABLE} (
                {S.ReviewParameters.PROJECT_ID},
                {S.ReviewParameters.REVIEW_START_DATE},
                {S.ReviewParameters.NUMBER_OF_REVIEWS},
                {S.ReviewParameters.REVIEW_FREQUENCY},
                {S.ReviewParameters.LICENSE_START},
                {S.ReviewParameters.LICENSE_END},
                {S.ReviewParameters.CYCLE_ID}
            ) VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            (
                project_id,
                review_start,
                0,
                0,
                license_start,
                license_end,
                cycle_id,
            ),
        )

        for stage in stages:
            start = stage["start_date"]
            end = stage["end_date"]
            count = int(stage["num_reviews"])
            stage_name = stage["stage_name"]

            insert_review_cycle_details(
                project_id,
                cycle_id,
                stage_name,
                0,
                "",
                count,
                start.strftime("%Y-%m-%d"),
                end.strftime("%Y-%m-%d"),
                start.strftime("%Y-%m-%d"),
                end.strftime("%Y-%m-%d"),
                None,
                None,
                False,
            )

            if count <= 0:
                continue
            interval = (end - start).days / float(count)
            for i in range(count):
                r_date = start + timedelta(days=round(interval * i))
                cursor.execute(
                    f"INSERT INTO {S.ReviewSchedule.TABLE} ({S.ReviewSchedule.PROJECT_ID}, {S.ReviewSchedule.CYCLE_ID}, {S.ReviewSchedule.REVIEW_DATE}) VALUES (?, ?, ?);",
                    (project_id, cycle_id, r_date.strftime("%Y-%m-%d")),
                )

        upsert_project_review_progress(project_id, cycle_id, sum(int(s["num_reviews"]) for s in stages), 0)

        conn.commit()
        return True
    except Exception as e:
        print(f"❌ Error generating stage schedule: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()
