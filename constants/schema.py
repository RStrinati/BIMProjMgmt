# ===================== Project Management Tables =====================

class ACCImportFolders:
    TABLE = "ACCImportFolders"
    PROJECT_ID = "project_id"
    ACC_FOLDER_PATH = "acc_folder_path"
    LAST_IMPORT_DATE = "last_import_date"


class ACCImportLogs:
    TABLE = "ACCImportLogs"
    LOG_ID = "log_id"
    PROJECT_ID = "project_id"
    FOLDER_NAME = "folder_name"
    IMPORT_DATE = "import_date"
    SUMMARY = "summary"
    STATUS = "status"
    MESSAGE = "message"
    IMPORT_ID = "import_id"
    FILE_NAME = "file_name"
    TIMESTAMP = "timestamp"


class BEPApprovals:
    TABLE = "bep_approvals"
    ID = "id"
    BEP_SECTION_ID = "bep_section_id"
    USER_ID = "user_id"
    APPROVED = "approved"
    COMMENT = "comment"
    TIMESTAMP = "timestamp"
    APPROVED_AT = "approved_at"
    APPROVAL_ID = "approval_id"
    PROJECT_ID = "project_id"
    APPROVED_BY = "approved_by"
    SECTION_ID = "section_id"
    VERSION_ID = "version_id"


class BEPSectionVersions:
    TABLE = "bep_section_versions"
    ID = "id"
    BEP_SECTION_ID = "bep_section_id"
    VERSION = "version"
    CONTENT = "content"
    UPDATED_BY = "updated_by"
    UPDATED_AT = "updated_at"
    VERSION_ID = "version_id"
    SECTION_ID = "section_id"
    CREATED_AT = "created_at"


class BEPSections:
    TABLE = "bep_sections"
    ID = "id"
    TITLE = "title"
    DEFAULT_CONTENT = "default_content"
    SORT_ORDER = "sort_order"
    CREATED_AT = "created_at"
    SECTION_NAME = "section_name"
    SECTION_ID = "section_id"


class BlockingPeriods:
    TABLE = "BlockingPeriods"
    BLOCK_ID = "block_id"
    BLOCK_START_DATE = "block_start_date"
    BLOCK_END_DATE = "block_end_date"
    BLOCKING_NAME = "blocking_name"
    BLOCKING_ID = "blocking_id"
    END_DATE = "end_date"
    START_DATE = "start_date"


class Clients:
    TABLE = "clients"
    CLIENT_ID = "client_id"
    CLIENT_NAME = "client_name"
    CONTACT_NAME = "contact_name"
    CONTACT_EMAIL = "contact_email"
    CONTACT_PHONE = "contact_phone"
    ADDRESS = "address"
    CITY = "city"
    STATE = "state"
    POSTCODE = "postcode"
    COUNTRY = "country"


class ConstructionStages:
    TABLE = "construction_stages"
    CONSTRUCTION_STAGE_ID = "construction_stage_id"
    CONSTRUCTION_STAGE_NAME = "construction_stage_name"


class DeliveryMethods:
    TABLE = "delivery_methods"
    DELIVERY_METHOD_ID = "delivery_method_id"
    DELIVERY_METHOD_NAME = "delivery_method_name"


class ProjectBEPSections:
    TABLE = "project_bep_sections"
    ID = "id"
    PROJECT_ID = "project_id"
    SECTION_ID = "section_id"
    TITLE = "title"
    CONTENT = "content"
    STATUS = "status"
    LAST_UPDATED_BY = "last_updated_by"
    LAST_UPDATED_AT = "last_updated_at"
    VERSION_ID = "version_id"


class ProjectHolds:
    TABLE = "project_holds"
    HOLD_ID = "hold_id"
    CYCLE_ID = "cycle_id"
    STAGE_ID = "stage_id"
    HOLD_DATE = "hold_date"
    RESUME_DATE = "resume_date"
    REASON = "reason"
    CREATED_BY = "created_by"
    CREATED_AT = "created_at"
    PROJECT_ID = "project_id"
    DESCRIPTION = "description"
    END_DATE = "end_date"
    START_DATE = "start_date"


class ProjectPhases:
    TABLE = "project_phases"
    PROJECT_PHASE_ID = "project_phase_id"
    PROJECT_PHASE_NAME = "project_phase_name"


class ProjectReviewCycles:
    TABLE = "project_review_cycles"
    CYCLE_ID = "cycle_id"
    PROJECT_ID = "project_id"
    CYCLE_NUMBER = "cycle_number"
    CREATED_AT = "created_at"


class ProjectReviews:
    TABLE = "project_reviews"
    REVIEW_ID = "review_id"
    PROJECT_ID = "project_id"
    CYCLE_ID = "cycle_id"
    SCOPED_REVIEWS = "scoped_reviews"
    COMPLETED_REVIEWS = "completed_reviews"
    LAST_UPDATED = "last_updated"


class ProjectTypes:
    TABLE = "project_types"
    TYPE_ID = "type_id"
    TYPE_NAME = "type_name"
    PROJECT_TYPE_ID = "project_type_id"
    PROJECT_TYPE_NAME = "project_type_name"


class Projects:
    TABLE = "projects"
    ID = "project_id"
    NAME = "project_name"
    CLIENT_ID = "client_id"
    TYPE_ID = "type_id"
    SECTOR_ID = "sector_id"
    METHOD_ID = "method_id"
    PHASE_ID = "phase_id"
    STAGE_ID = "stage_id"
    PROJECT_MANAGER = "project_manager"
    INTERNAL_LEAD = "internal_lead"
    CONTRACT_NUMBER = "contract_number"
    CONTRACT_VALUE = "contract_value"
    AGREED_FEE = "agreed_fee"
    PAYMENT_TERMS = "payment_terms"
    FOLDER_PATH = "folder_path"
    IFC_FOLDER_PATH = "ifc_folder_path"
    DATA_EXPORT_FOLDER = "data_export_folder"
    START_DATE = "start_date"
    END_DATE = "end_date"
    STATUS = "status"
    PRIORITY = "priority"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    # New fields added for enhanced project creation
    AREA_HECTARES = "area_hectares"
    MW_CAPACITY = "mw_capacity"
    ADDRESS = "address"
    CITY = "city"
    STATE = "state"
    POSTCODE = "postcode"


class ReviewCycles:
    TABLE = "review_cycles"
    REVIEW_ID = "review_id"
    STAGE_ID = "stage_id"
    CYCLE_ID = "cycle_id"
    REVIEW_NUMBER = "review_number"
    PLANNED_START = "planned_start"
    PLANNED_END = "planned_end"
    ACTUAL_START = "actual_start"
    ACTUAL_END = "actual_end"
    REVIEWER_ID = "reviewer_id"
    STATUS = "status"
    NOTES = "notes"
    MANUAL_OVERRIDE = "manual_override"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    REVIEW_CYCLE_ID = "review_cycle_id"
    PROJECT_ID = "project_id"
    START_DATE = "start_date"
    END_DATE = "end_date"
    NUM_REVIEWS = "num_reviews"
    CREATED_BY = "created_by"


class ProjectBookmarks:
    TABLE = "project_bookmarks"
    BOOKMARK_ID = "bookmark_id"
    PROJECT_ID = "project_id"
    TITLE = "title"
    URL = "url"
    DESCRIPTION = "description"
    CREATED_AT = "created_at"

class ReviewStages:
    TABLE = "ReviewStages"
    STAGE_ID = "stage_id"
    PROJECT_ID = "project_id"
    CYCLE_ID = "cycle_id"
    STAGE_NAME = "stage_name"
    START_DATE = "start_date"
    END_DATE = "end_date"
    NUMBER_OF_REVIEWS = "number_of_reviews"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"

class ReviewTasks:
    TABLE = "ReviewTasks"
    REVIEW_TASK_ID = "review_task_id"
    SCHEDULE_ID = "schedule_id"
    TASK_ID = "task_id"
    ASSIGNED_TO = "assigned_to"
    STATUS = "status"

class Tasks:
    TABLE = "tasks"
    TASK_ID = "task_id"
    TASK_NAME = "task_name"
    PROJECT_ID = "project_id"
    START_DATE = "start_date"
    END_DATE = "end_date"
    ASSIGNED_TO = "assigned_to"
    PROGRESS = "progress"
    DEPENDENCIES = "dependencies"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    CYCLE_ID = "cycle_id"


    PRIORITY = "priority"
    ESTIMATED_HOURS = "estimated_hours"
    ACTUAL_HOURS = "actual_hours"
    PREDECESSOR_TASK_ID = "predecessor_task_id"
    PROGRESS_PERCENTAGE = "progress_percentage"
    STATUS = "status"
    DESCRIPTION = "description"
    TASK_TYPE = "task_type"
    REVIEW_ID = "review_id"
class Users:
    TABLE = "users"
    ID = "user_id"
    NAME = "name"
    ROLE = "role"
    EMAIL = "email"
    CREATED_AT = "created_at"

# ===================== Revit Health Check =====================

class TblRvtProjHealth:
    TABLE = "tblRvtProjHealth"
    NID = "nId"
    NRVTUSERID = "nRvtUserId"
    NSYSNAMEID = "nSysNameId"
    STR_RVT_VERSION = "strRvtVersion"
    STR_RVT_BUILD_VERSION = "strRvtBuildVersion"
    STR_RVT_FILENAME = "strRvtFileName"
    STR_PROJECT_NAME = "strProjectName"
    STR_PROJECT_NUMBER = "strProjectNumber"
    STR_CLIENT_NAME = "strClientName"
    NRVTLINKCOUNT = "nRvtLinkCount"
    NDWGLINKCOUNT = "nDwgLinkCount"
    NDWGIMPORTCOUNT = "nDwgImportCount"
    NTOTALVIEWCOUNT = "nTotalViewCount"
    NCOPIEDVIEWCOUNT = "nCopiedViewCount"
    NDEPENDENTVIEWCOUNT = "nDependentViewCount"
    NVIEWSNOTONSHEETSCOUNT = "nViewsNotOnSheetsCount"
    NVIEWTEMPLATECOUNT = "nViewTemplateCount"
    NWARNINGSCOUNT = "nWarningsCount"
    NCRITICALWARNINGSCOUNT = "nCriticalWarningsCount"
    NFAMILYCOUNT = "nFamilyCount"
    NGROUPCOUNT = "nGroupCount"
    NDETAILGROUPTYPECOUNT = "nDetailGroupTypeCount"
    NMODELGROUPTYPECOUNT = "nModelGroupTypeCount"
    NTOTALELEMENTSCOUNT = "nTotalElementsCount"
    JSON_TYPE_OF_ELEMENTS = "jsonTypeOfElements"
    NINPLACEFAMILIESCOUNT = "nInPlaceFamiliesCount"
    NSKETCHUPIMPORTSCOUNT = "nSketchupImportsCount"
    NSHEETSCOUNT = "nSheetsCount"
    NDESIGNOPTIONSETCOUNT = "nDesignOptionSetCount"
    NDESIGNOPTIONCOUNT = "nDesignOptionCount"
    JSON_DESIGN_OPTIONS = "jsonDesignOptions"
    JSON_DWG_IMPORTS = "jsonDwgImports"
    JSON_FAMILIES = "jsonFamilies"
    JSON_LEVELS = "jsonLevels"
    JSON_LINES = "jsonLines"
    JSON_ROOMS = "jsonRooms"
    JSON_VIEWS = "jsonViews"
    JSON_WARNINGS = "jsonWarnings"
    JSON_WORKSETS = "jsonWorksets"
    NEXPORTEDON = "nExportedOn"
    NDELETEDON = "nDeletedOn"
    CONVERTED_EXPORTED_DATE = "ConvertedExportedDate"
    CONVERTED_DELETED_DATE = "ConvertedDeletedDate"
    VALIDATION_STATUS = "validation_status"
    VALIDATION_REASON = "validation_reason"
    STR_EXTRACTED_PROJECT_NAME = "strExtractedProjectName"
    COMPILED_REGEX = "compiled_regex"
    JSON_GRIDS = "jsonGrids"
    JSON_PROJECT_BASE_POINT = "jsonProjectBasePoint"
    JSON_SURVEY_POINT = "jsonSurveyPoint"
    VALIDATED_DATE = "validated_date"
    FAILED_FIELD_NAME = "failed_field_name"
    FAILED_FIELD_VALUE = "failed_field_value"
    FAILED_FIELD_REASON = "failed_field_reason"
    DISCIPLINE_CODE = "discipline_code"
    DISCIPLINE_FULL_NAME = "discipline_full_name"
    NMODEL_FILE_SIZE_MB = "nModelFileSizeMB"
    JSON_TITLEBLOCKS_SUMMARY = "jsonTitleBlocksSummary"
    JSON_FAMILY_SIZES = "jsonFamily_sizes"
    JSON_SCHEDULES = "jsonSchedules"
    JSON_PLACED_FAMILIES = "jsonPlaced_families"
    JSON_PHASES = "jsonPhases"


class TblRvtUser:
    TABLE = "tblRvtUser"
    NID = "nId"
    RVT_USERNAME = "rvtUserName"


class TblSysName:
    TABLE = "tblSysName"
    NID = "nId"
    SYS_USERNAME = "sysUserName"

# ===================== Revizto Data =====================

class TblReviztoProjects:
    TABLE = "tblReviztoProjects"
    PROJECT_ID = "projectId"
    LICENSE_UUID = "licenseUuid"
    PROJECT_UUID = "projectUuid"
    TITLE = "title"
    CREATED = "created"
    UPDATED = "updated"
    REGION = "region"
    ARCHIVED = "archived"
    FROZEN = "frozen"
    OWNER_EMAIL = "ownerEmail"
    PROJECT_JSON = "projectJson"


class TblReviztoProjectIssues:
    TABLE = "tblReviztoProjectIssues"
    ISSUE_ID = "issueId"
    PROJECT_UUID = "projectUuid"
    ISSUE_JSON = "issueJson"
    RETRIEVED_AT = "retrievedAt"


class TblReviztoIssueComments:
    TABLE = "tblReviztoIssueComments"
    COMMENT_ID = "commentId"
    ISSUE_UUID = "issueUuid"
    PROJECT_ID = "projectId"
    PAGE = "page"
    RETRIEVAL_DATE = "retrievalDate"
    RETRIEVED_AT = "retrievedAt"
    COMMENT_JSON = "commentJson"


class TblLicenseMembers:
    TABLE = "tblLicenseMembers"
    LICENSE_UUID = "licenseUuid"
    MEMBER_UUID = "memberUuid"
    EMAIL = "email"
    INVITED_AT = "invitedAt"
    ACTIVATED = "activated"
    DEACTIVATED = "deactivated"
    LAST_ACTIVE = "lastActive"
    MEMBER_JSON = "memberJson"


class TblUserLicenses:
    TABLE = "tblUserLicenses"
    ID = "id"
    UUID = "uuid"
    NAME = "name"
    EXPIRES = "expires"
    TYPE = "type"
    CREATED = "created"
    REGION = "region"
    OWNER_ID = "ownerId"
    OWNER_UUID = "ownerUuid"
    OWNER_EMAIL = "ownerEmail"
    PLAN_USERS = "planUsers"
    PLAN_PROJECTS = "planProjects"
    SLOTS_PROJECTS = "slotsProjects"
    SLOTS_USERS = "slotsUsers"
    CLASH_AUTOMATION = "clashAutomation"
    ALLOW_BE_EXTERNAL_GUEST = "allowBeExternalGuest"
    ALLOW_GUESTS_HERE = "allowGuestsHere"
    ALLOW_BCF_EXPORT = "allowBCFExport"
    ALLOW_API_ACCESS = "allowApiAccess"
    INSERTED_AT = "insertedAt"

class ControlModels:
    TABLE = "tblControlModels"
    ID = "id"
    PROJECT_ID = "project_id"
    CONTROL_FILE_NAME = "control_file_name"
    IS_ACTIVE = "is_active"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"

class Sectors:
    TABLE = "sectors"
    SECTOR_ID = "sector_id"
    SECTOR_NAME = "sector_name"

class ACCDocs:
    TABLE = "tblACCDocs"
    ID = "id"
    FILE_NAME = "file_name"
    FILE_PATH = "file_path"
    DATE_MODIFIED = "date_modified"
    FILE_TYPE = "file_type"
    FILE_SIZE_KB = "file_size_kb"
    CREATED_AT = "created_at"
    DELETED_AT = "deleted_at"
    PROJECT_ID = "project_id"

class ReviewSchedules:
    TABLE = "review_schedules"
    REVIEW_ID = "review_id"
    PROJECT_ID = "project_id"
    REVIEW_NUMBER = "review_number"
    REVIEW_NAME = "review_name"
    REVIEW_DATE = "review_date"
    NOTES = "notes"

class ReviewCycleDetails:
    TABLE = "ReviewCycleDetails"
    CYCLE_DETAIL_ID = "cycle_detail_id"
    PROJECT_ID = "project_id"
    CYCLE_ID = "cycle_id"
    CONSTRUCTION_STAGE = "construction_stage"
    PLANNED_START_DATE = "planned_start_date"
    PLANNED_COMPLETION_DATE = "planned_completion_date"
    ACTUAL_START_DATE = "actual_start_date"
    ACTUAL_COMPLETION_DATE = "actual_completion_date"
    HOLD_DATE = "hold_date"
    RESUME_DATE = "resume_date"
    LICENSE_START_DATE = "license_start_date"
    LICENSE_DURATION_MONTHS = "license_duration_months"
    PROPOSED_FEE = "proposed_fee"
    IS_NEW_CONTRACT = "is_new_contract"
    REVIEWS_PER_PHASE = "reviews_per_phase"
    LAST_UPDATED = "last_updated"
    ASSIGNED_USERS = "assigned_users"
    NEW_CONTRACT = "new_contract"

class ReviewSchedule:
    TABLE = "ReviewSchedule"
    SCHEDULE_ID = "schedule_id"
    PROJECT_ID = "project_id"
    REVIEW_DATE = "review_date"
    IS_WITHIN_LICENSE_PERIOD = "is_within_license_period"
    IS_BLOCKED = "is_blocked"
    CYCLE_ID = "cycle_id"
    ASSIGNED_TO = "assigned_to"
    STATUS = "status"
    MANUAL_OVERRIDE = "manual_override"

class ReviewAssignments:
    TABLE = "ReviewAssignments"
    ASSIGNMENT_ID = "assignment_id"
    SCHEDULE_ID = "schedule_id"
    USER_ID = "user_id"
    REVIEW_ID = "review_id"

class ContractualLinks:
    TABLE = "ContractualLinks"
    ID = "id"
    PROJECT_ID = "project_id"
    REVIEW_CYCLE_ID = "review_cycle_id"
    BEP_CLAUSE = "bep_clause"
    BILLING_EVENT = "billing_event"
    AMOUNT_DUE = "amount_due"
    STATUS = "status"

class ReviewParameters:
    TABLE = "ReviewParameters"
    PARAMETER_ID = "ParameterID"
    PROJECT_ID = "ProjectID"
    REVIEW_START_DATE = "ReviewStartDate"
    NUMBER_OF_REVIEWS = "NumberOfReviews"
    REVIEW_FREQUENCY = "ReviewFrequency"
    LICENSE_START = "LicenseStartDate"
    LICENSE_END = "LicenseEndDate"
    CYCLE_ID = "cycle_id"

class StageReviewPlan:
    TABLE = "stage_review_plan"
    STAGE_ID = "stage_id"
    CYCLE_ID = "cycle_id"
    STAGE_NAME = "stage_name"
    START_DATE = "start_date"
    END_DATE = "end_date"
    REVIEW_FREQUENCY_DAYS = "review_frequency_days"
    NUMBER_OF_REVIEWS = "number_of_reviews"
    IS_GENERATED = "is_generated"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"

class ProjectAliases:
    TABLE = "project_aliases"
    ALIAS_NAME = "alias_name"
    PM_PROJECT_ID = "pm_project_id"

class ServiceDeliverables:
    TABLE = "ServiceDeliverables"
    DELIVERABLE_ID = "deliverable_id"
    SERVICE_ID = "service_id"
    DELIVERABLE_TYPE = "deliverable_type"
    PLANNED_DATE = "planned_date"
    ISSUED_DATE = "issued_date"
    STATUS = "status"
    BILL_TRIGGER = "bill_trigger"
    EVIDENCE_LINK = "evidence_link"

class BillingClaims:
    TABLE = "BillingClaims"
    CLAIM_ID = "claim_id"
    PROJECT_ID = "project_id"
    PERIOD_START = "period_start"
    PERIOD_END = "period_end"
    PO_REF = "po_ref"
    INVOICE_REF = "invoice_ref"
    STATUS = "status"
    CREATED_AT = "created_at"

class BillingClaimLines:
    TABLE = "BillingClaimLines"
    LINE_ID = "line_id"
    CLAIM_ID = "claim_id"
    SERVICE_ID = "service_id"
    STAGE_LABEL = "stage_label"
    PREV_PCT = "prev_pct"
    CURR_PCT = "curr_pct"
    DELTA_PCT = "delta_pct"
    AMOUNT_THIS_CLAIM = "amount_this_claim"
    NOTE = "note"

class DocLibrary:
    TABLE = "DocLibrary"
    LIBRARY_ID = "library_id"
    DOCUMENT_TYPE = "document_type"
    JURISDICTION = "jurisdiction"
    TEMPLATE_NAME = "template_name"
    VERSION = "version"
    CREATED_AT = "created_at"

class DocLibrarySections:
    TABLE = "DocLibrarySections"
    SECTION_ID = "section_id"
    LIBRARY_ID = "library_id"
    CODE = "code"
    TITLE = "title"
    BODY_MD = "body_md"
    PARENT_CODE = "parent_code"
    ORD = "ord"

class DocLibraryClauses:
    TABLE = "DocLibraryClauses"
    CLAUSE_ID = "clause_id"
    SECTION_ID = "section_id"
    CODE = "code"
    TITLE = "title"
    BODY_MD = "body_md"
    OPTIONAL = "optional"
    ORD = "ord"

class ProjectDocuments:
    TABLE = "ProjectDocuments"
    PROJECT_DOCUMENT_ID = "project_document_id"
    PROJECT_ID = "project_id"
    LIBRARY_ID = "library_id"
    TITLE = "title"
    VERSION = "version"
    DOCUMENT_TYPE = "document_type"
    STATUS = "status"
    CREATED_AT = "created_at"

class ProjectSections:
    TABLE = "ProjectSections"
    PROJECT_SECTION_ID = "project_section_id"
    PROJECT_DOCUMENT_ID = "project_document_id"
    ORIGINAL_SECTION_ID = "original_section_id"
    CODE = "code"
    TITLE = "title"
    BODY_MD = "body_md"
    ORD = "ord"

class ProjectClauses:
    TABLE = "ProjectClauses"
    PROJECT_CLAUSE_ID = "project_clause_id"
    PROJECT_SECTION_ID = "project_section_id"
    ORIGINAL_CLAUSE_ID = "original_clause_id"
    CODE = "code"
    TITLE = "title"
    BODY_MD = "body_md"
    OPTIONAL = "optional"
    SELECTED = "selected"
    ORD = "ord"

class ClauseAssignments:
    TABLE = "ClauseAssignments"
    ASSIGNMENT_ID = "assignment_id"
    PROJECT_CLAUSE_ID = "project_clause_id"
    DISCIPLINE = "discipline"
    OWNER = "owner"
    OWNER_EMAIL = "owner_email"
    DUE_DATE = "due_date"
    EVIDENCE_TYPE = "evidence_type"
    CHECK_TYPE = "check_type"
    CHECK_REF = "check_ref"
    PARAMS_JSON = "params_json"
    STATUS = "status"
    LAST_RUN = "last_run"
    LAST_RESULT = "last_result"

class DocumentRevisions:
    TABLE = "DocumentRevisions"
    REVISION_ID = "revision_id"
    PROJECT_DOCUMENT_ID = "project_document_id"
    REVISION_NO = "revision_no"
    CHANGE_NOTE = "change_note"
    CREATED_AT = "created_at"
    CREATED_BY = "created_by"
    STATUS = "status"

class PublishedFiles:
    TABLE = "PublishedFiles"
    FILE_ID = "file_id"
    REVISION_ID = "revision_id"
    PATH = "path"
    FORMAT = "format"
    CREATED_AT = "created_at"

class ProjectServices:
    TABLE = "ProjectServices"
    SERVICE_ID = "service_id"
    PROJECT_ID = "project_id"
    PHASE = "phase"
    SERVICE_CODE = "service_code"
    SERVICE_NAME = "service_name"
    UNIT_TYPE = "unit_type"
    UNIT_QTY = "unit_qty"
    UNIT_RATE = "unit_rate"
    LUMP_SUM_FEE = "lump_sum_fee"
    AGREED_FEE = "agreed_fee"
    BILL_RULE = "bill_rule"
    NOTES = "notes"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    STATUS = "status"
    PROGRESS_PCT = "progress_pct"
    CLAIMED_TO_DATE = "claimed_to_date"

class ServiceReviews:
    TABLE = "ServiceReviews"
    REVIEW_ID = "review_id"
    SERVICE_ID = "service_id"
    CYCLE_NO = "cycle_no"
    PLANNED_DATE = "planned_date"
    DUE_DATE = "due_date"
    DISCIPLINES = "disciplines"
    DELIVERABLES = "deliverables"
    STATUS = "status"
    WEIGHT_FACTOR = "weight_factor"
    EVIDENCE_LINKS = "evidence_links"
    ACTUAL_ISSUED_AT = "actual_issued_at"

class ServiceScheduleSettings:
    TABLE = "ServiceScheduleSettings"
    SERVICE_ID = "service_id"
    START_DATE = "start_date"
    END_DATE = "end_date"
    FREQUENCY = "frequency"
    AUTO_COMPLETE = "auto_complete"
    UPDATED_AT = "updated_at"


# ===================== Service Templates =====================
class ServiceTemplates:
    TABLE = "ServiceTemplates"
    ID = "id"
    TEMPLATE_NAME = "template_name"
    DESCRIPTION = "description"
    SERVICE_TYPE = "service_type"
    PARAMETERS = "parameters"
    CREATED_BY = "created_by"
    CREATED_AT = "created_at"
    IS_ACTIVE = "is_active"

class ProjectBookmarks:
    TABLE = "ProjectBookmarks"
    ID = "bookmark_id"
    PROJECT_ID = "project_id"
    NAME = "name"
    URL = "url"
    DESCRIPTION = "description"
    CATEGORY = "category"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
