# ProjectManagement Database Schema

This file lists the tables and columns used by the application.

## ACCImportFolders

| Column | Data Type | Length |
| ------ | --------- | ------ |
| acc_folder_path | nvarchar | 1000 |
| last_import_date | datetime | 8 |
| project_id | int | 4 |

## ACCImportLogs

| Column | Data Type | Length |
| ------ | --------- | ------ |
| folder_name | nvarchar | 1000 |
| import_date | datetime | 8 |
| log_id | int | 4 |
| project_id | int | 4 |
| summary | nvarchar | -1 |

## BlockingPeriods

| Column | Data Type | Length |
| ------ | --------- | ------ |
| block_end_date | date | 3 |
| block_id | int | 4 |
| block_start_date | date | 3 |

## ReviewAssignments

| Column | Data Type | Length |
| ------ | --------- | ------ |
| assignment_id | int | 4 |
| review_id | int | 4 |
| schedule_id | int | 4 |
| user_id | int | 4 |

## ReviewCycleDetails

| Column | Data Type | Length |
| ------ | --------- | ------ |
| actual_completion_date | date | 3 |
| actual_start_date | date | 3 |
| construction_stage | nvarchar | 200 |
| cycle_detail_id | int | 4 |
| cycle_id | int | 4 |
| hold_date | date | 3 |
| is_new_contract | bit | 1 |
| last_updated | datetime | 8 |
| license_duration_months | int | 4 |
| license_start_date | date | 3 |
| planned_completion_date | date | 3 |
| planned_start_date | date | 3 |
| project_id | int | 4 |
| proposed_fee | decimal | 9 |
| resume_date | date | 3 |
| reviews_per_phase | int | 4 |

## ReviewParameters

| Column | Data Type | Length |
| ------ | --------- | ------ |
| cycle_id | int | 4 |
| LicenseEndDate | date | 3 |
| LicenseStartDate | date | 3 |
| NumberOfReviews | int | 4 |
| ParameterID | int | 4 |
| ProjectID | int | 4 |
| ReviewFrequency | int | 4 |
| ReviewStartDate | date | 3 |

## ReviewSchedule

| Column | Data Type | Length |
| ------ | --------- | ------ |
| assigned_to | int | 4 |
| cycle_id | int | 4 |
| is_blocked | bit | 1 |
| is_within_license_period | bit | 1 |
| project_id | int | 4 |
| review_date | date | 3 |
| schedule_id | int | 4 |
| status | nvarchar | 100 |

## ReviewStages

| Column | Data Type | Length |
| ------ | --------- | ------ |
| created_at | datetime | 8 |
| cycle_id | varchar | 50 |
| end_date | date | 3 |
| number_of_reviews | int | 4 |
| project_id | int | 4 |
| stage_id | int | 4 |
| stage_name | varchar | 100 |
| start_date | date | 3 |
| updated_at | datetime | 8 |

## ReviewTasks

| Column | Data Type | Length |
| ------ | --------- | ------ |
| assigned_to | nvarchar | 510 |
| review_task_id | int | 4 |
| schedule_id | int | 4 |
| status | nvarchar | 100 |
| task_id | int | 4 |

## project_holds

| Column | Data Type | Length |
| ------ | --------- | ------ |
| created_at | datetime | 8 |
| created_by | int | 4 |
| cycle_id | int | 4 |
| hold_date | date | 3 |
| hold_id | int | 4 |
| reason | nvarchar | -1 |
| resume_date | date | 3 |
| stage_id | int | 4 |

## project_review_cycles

| Column | Data Type | Length |
| ------ | --------- | ------ |
| created_at | datetime | 8 |
| cycle_id | int | 4 |
| cycle_number | int | 4 |
| project_id | int | 4 |

## project_reviews

| Column | Data Type | Length |
| ------ | --------- | ------ |
| completed_reviews | int | 4 |
| cycle_id | int | 4 |
| last_updated | datetime | 8 |
| project_id | int | 4 |
| review_id | int | 4 |
| scoped_reviews | int | 4 |

## projects

| Column | Data Type | Length |
| ------ | --------- | ------ |
| created_at | datetime | 8 |
| data_export_folder | nvarchar | 1000 |
| end_date | date | 3 |
| folder_path | nvarchar | 1000 |
| ifc_folder_path | nvarchar | 1000 |
| priority | nvarchar | 100 |
| project_id | int | 4 |
| project_name | nvarchar | 510 |
| start_date | date | 3 |
| status | nvarchar | 100 |
| updated_at | datetime | 8 |

## review_cycles

| Column | Data Type | Length |
| ------ | --------- | ------ |
| actual_end | date | 3 |
| actual_start | date | 3 |
| created_at | datetime | 8 |
| cycle_id | int | 4 |
| manual_override | bit | 1 |
| notes | nvarchar | -1 |
| planned_end | date | 3 |
| planned_start | date | 3 |
| review_id | int | 4 |
| review_number | int | 4 |
| reviewer_id | int | 4 |
| stage_id | int | 4 |
| status | nvarchar | 100 |
| updated_at | datetime | 8 |

## stage_review_plan

| Column | Data Type | Length |
| ------ | --------- | ------ |
| created_at | datetime | 8 |
| cycle_id | int | 4 |
| end_date | date | 3 |
| is_generated | bit | 1 |
| number_of_reviews | int | 4 |
| review_frequency_days | int | 4 |
| stage_id | int | 4 |
| stage_name | nvarchar | 510 |
| start_date | date | 3 |
| updated_at | datetime | 8 |

## tasks

| Column | Data Type | Length |
| ------ | --------- | ------ |
| assigned_to | int | 4 |
| created_at | datetime | 8 |
| dependencies | nvarchar | 510 |
| end_date | date | 3 |
| progress | decimal | 5 |
| project_id | int | 4 |
| start_date | date | 3 |
| task_id | int | 4 |
| task_name | nvarchar | 510 |
| updated_at | datetime | 8 |

## tblACCDocs

| Column | Data Type | Length |
| ------ | --------- | ------ |
| created_at | datetime | 8 |
| date_modified | datetime | 8 |
| deleted_at | datetime | 8 |
| file_name | nvarchar | 510 |
| file_path | nvarchar | -1 |
| file_size_kb | float | 8 |
| file_type | nvarchar | 100 |
| id | int | 4 |
| project_id | int | 4 |

## tblControlModels

| Column | Data Type | Length |
| ------ | --------- | ------ |
| control_file_name | nvarchar | 510 |
| created_at | datetime | 8 |
| id | int | 4 |
| is_active | bit | 1 |
| project_id | int | 4 |
| updated_at | datetime | 8 |

## users

| Column | Data Type | Length |
| ------ | --------- | ------ |
| created_at | datetime | 8 |
| email | nvarchar | 510 |
| name | nvarchar | 510 |
| role | nvarchar | 100 |
| user_id | int | 4 |