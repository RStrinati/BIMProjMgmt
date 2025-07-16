import pyodbc
from tkinter import messagebox
from dateutil.relativedelta import relativedelta
from datetime import timedelta
import pandas as pd
from database import (
    connect_to_db,
    insert_review_cycle_details,
    upsert_project_review_progress,
    get_cycle_ids,
)





def update_review_date(review_id, new_date):
    """Update a specific review date."""
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE ReviewSchedule
        SET review_date = ?
        WHERE review_id = ?;
    """, (new_date, review_id))
    conn.commit()
    conn.close()

def adjust_future_tasks(review_id, new_date, project_id, cycle_id):
    """Auto-adjust all future reviews after moving a task."""
    conn = connect_to_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT review_id, review_date FROM ReviewSchedule
        WHERE project_id = ? AND cycle_id = ? AND review_id > ?
        ORDER BY review_date ASC;
    """, (project_id, cycle_id, review_id))

    future_reviews = cursor.fetchall()
    original_review_date = pd.to_datetime(new_date)

    for idx, (future_review_id, future_review_date) in enumerate(future_reviews):
        shift_days = (pd.to_datetime(future_review_date) - original_review_date).days
        new_future_date = original_review_date + pd.Timedelta(days=shift_days)

        cursor.execute("""
            UPDATE ReviewSchedule
            SET review_date = ?
            WHERE review_id = ?;
        """, (new_future_date.strftime('%Y-%m-%d'), future_review_id))

    conn.commit()
    conn.close()

def delete_review_task(review_id):
    """Delete a review task while keeping future tasks unchanged."""
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM ReviewSchedule WHERE review_id = ?;", (review_id,))
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
    planned_start_entry,
    planned_completion_entry,
    actual_start_entry,
    actual_completion_entry,
    hold_date_entry,
    resume_date_entry,
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
        planned_start = planned_start_entry.get_date()
        planned_completion = planned_completion_entry.get_date()
        actual_start = actual_start_entry.get_date()
        actual_completion = actual_completion_entry.get_date()
        hold_date = hold_date_entry.get_date()
        resume_date = resume_date_entry.get_date()
        new_contract = bool(new_contract_var.get())

        # ✅ Generate cycle ID properly
        cursor.execute("SELECT ISNULL(MAX(cycle_id), 0) + 1 FROM ReviewParameters WHERE ProjectID = ?", (project_id,))
        cycle_id = cursor.fetchone()[0]

        cursor.execute(
            """
            INSERT INTO ReviewParameters
            (ProjectID, ReviewStartDate, NumberOfReviews, ReviewFrequency, LicenseStartDate, LicenseEndDate, cycle_id)
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
            planned_start.strftime("%Y-%m-%d"),
            planned_completion.strftime("%Y-%m-%d"),
            actual_start.strftime("%Y-%m-%d"),
            actual_completion.strftime("%Y-%m-%d"),
            hold_date.strftime("%Y-%m-%d"),
            resume_date.strftime("%Y-%m-%d"),
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

        messagebox.showinfo("Success", f"Review schedule submitted successfully!")

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
        cursor.execute("""
                    WITH ReviewData AS (
                        SELECT 
                            rp.ProjectID, rp.cycle_id, rp.ReviewStartDate, rp.LicenseStartDate, rp.LicenseEndDate,
                            rp.NumberOfReviews, rp.ReviewFrequency,
                            MAX(rs.review_date) AS LastReviewDate,
                            DATEDIFF(DAY, rp.LicenseStartDate, rp.LicenseEndDate) AS LicenseDays,
                            DATEDIFF(MONTH, rp.LicenseStartDate, rp.LicenseEndDate) AS LicenseMonths,
                            (DATEDIFF(DAY, rp.LicenseStartDate, rp.LicenseEndDate) / rp.ReviewFrequency) AS PossibleReviewsWithinLicense
                        FROM ReviewParameters rp
                        LEFT JOIN ReviewSchedule rs ON rp.ProjectID = rs.project_id AND rp.cycle_id = rs.cycle_id
                        WHERE rp.ProjectID = ? AND rp.cycle_id = ?
                        GROUP BY rp.ProjectID, rp.cycle_id, rp.ReviewStartDate, rp.LicenseStartDate, rp.LicenseEndDate, rp.NumberOfReviews, rp.ReviewFrequency
                    )
                    SELECT *, 
                        CASE 
                            WHEN NumberOfReviews > PossibleReviewsWithinLicense THEN 'Yes' 
                            ELSE 'No' 
                        END AS ExceedsLicense
                    FROM ReviewData;
                """, (project_id, cycle_id))

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
            "SELECT ISNULL(MAX(cycle_id),0)+1 FROM ReviewParameters WHERE ProjectID = ?",
            (project_id,),
        )
        cycle_id = cursor.fetchone()[0]

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
                    "INSERT INTO ReviewSchedule (project_id, cycle_id, review_date) VALUES (?, ?, ?);",
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
