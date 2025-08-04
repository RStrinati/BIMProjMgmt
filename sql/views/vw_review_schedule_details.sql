CREATE VIEW vw_ReviewScheduleDetails AS
SELECT
    rs.schedule_id,
    rs.review_date,
    rs.cycle_id,
    rs.project_id,
    p.project_name,
    d.construction_stage,
    d.proposed_fee,
    d.assigned_users,
    d.reviews_per_phase,
    d.planned_start_date,
    d.planned_completion_date,
    d.actual_start_date,
    d.actual_completion_date,
    d.hold_date,
    d.resume_date,
    d.new_contract,
    rs.assigned_to,
    rs.status
FROM ReviewSchedule rs
JOIN Projects p ON rs.project_id = p.project_id
LEFT JOIN ReviewCycleDetails d ON rs.project_id = d.project_id AND rs.cycle_id = d.cycle_id;
GO
