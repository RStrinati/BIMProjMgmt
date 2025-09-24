"""

Review Management System - Backend Services

Comprehensive scope - schedule - progress - billing workflow

"""



import json

import sqlite3

from datetime import datetime, timedelta

from decimal import Decimal

from typing import List, Dict, Optional, Tuple

import os

# Import validation service
from review_validation import (
    validate_template, validate_service_data, validate_review_cycle,
    validate_project_services, validate_billing_claim, sanitize_input
)


class ReviewManagementService:

    """Core service for review management operations"""

    

    def __init__(self, db_connection):

        self.db = db_connection

        self.cursor = db_connection.cursor()

        self.ensure_tables_exist()

    

    def ensure_tables_exist(self):

        """Ensure required tables exist, create them if they don't"""

        try:

            # Check if ServiceReviews table exists

            self.cursor.execute("""

                SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES 

                WHERE TABLE_NAME = 'ServiceReviews' AND TABLE_SCHEMA = 'dbo'

            """)

            

            if self.cursor.fetchone()[0] == 0:

                print("Creating ServiceReviews table...")

                self.create_service_reviews_table()

            

            # Check if ServiceDeliverables table exists

            self.cursor.execute("""

                SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES 

                WHERE TABLE_NAME = 'ServiceDeliverables' AND TABLE_SCHEMA = 'dbo'

            """)

            

            if self.cursor.fetchone()[0] == 0:

                print("Creating ServiceDeliverables table...")

                self.create_service_deliverables_table()

            

            # Check if BillingClaims table exists

            self.cursor.execute("""

                SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES 

                WHERE TABLE_NAME = 'BillingClaims' AND TABLE_SCHEMA = 'dbo'

            """)

            

            if self.cursor.fetchone()[0] == 0:

                print("Creating BillingClaims table...")

                self.create_billing_tables()

                

            # Check if ServiceScheduleSettings table exists

            self.cursor.execute("""

                SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES 

                WHERE TABLE_NAME = 'ServiceScheduleSettings' AND TABLE_SCHEMA = 'dbo'

            """)



            if self.cursor.fetchone()[0] == 0:

                print("Creating ServiceScheduleSettings table...")

                self.create_service_schedule_table()



        except Exception as e:

            print(f"Error checking/creating tables: {e}")

    

    def create_service_reviews_table(self):

        """Create the ServiceReviews table"""

        try:

            create_sql = """

            CREATE TABLE dbo.ServiceReviews (

                review_id         INT IDENTITY PRIMARY KEY,

                service_id        INT NOT NULL REFERENCES dbo.ProjectServices(service_id) ON DELETE CASCADE,

                cycle_no          INT NOT NULL,

                planned_date      DATE NOT NULL,

                due_date          DATE NULL,

                disciplines       NVARCHAR(200) NULL,

                deliverables      NVARCHAR(200) NULL,

                status            NVARCHAR(30) NOT NULL DEFAULT 'planned',

                weight_factor     DECIMAL(9,4) NOT NULL DEFAULT 1.0000,

                evidence_links    NVARCHAR(MAX) NULL,

                actual_issued_at  DATETIME2 NULL

            );

            """

            self.cursor.execute(create_sql)

            

            # Create index

            index_sql = """

            CREATE INDEX IX_ServiceReviews_ServiceDate ON dbo.ServiceReviews(service_id, planned_date);

            """

            self.cursor.execute(index_sql)

            

            self.db.commit()

            print("âœ… ServiceReviews table created successfully")

            

        except Exception as e:

            print(f"Error creating ServiceReviews table: {e}")

            self.db.rollback()

    

    def create_service_deliverables_table(self):

        """Create the ServiceDeliverables table"""

        try:

            create_sql = """

            CREATE TABLE dbo.ServiceDeliverables (

                deliverable_id    INT IDENTITY PRIMARY KEY,

                service_id        INT NOT NULL REFERENCES dbo.ProjectServices(service_id) ON DELETE CASCADE,

                deliverable_type  NVARCHAR(50) NOT NULL,

                planned_date      DATE NULL,

                issued_date       DATE NULL,

                status            NVARCHAR(30) NOT NULL DEFAULT 'planned',

                bill_trigger      BIT NOT NULL DEFAULT 0,

                evidence_link     NVARCHAR(MAX) NULL

            );

            """

            self.cursor.execute(create_sql)

            self.db.commit()

            print("âœ… ServiceDeliverables table created successfully")

            

        except Exception as e:

            print(f"Error creating ServiceDeliverables table: {e}")

            self.db.rollback()

    

    def create_billing_tables(self):

        """Create the BillingClaims and BillingClaimLines tables"""

        try:

            # Create BillingClaims table

            claims_sql = """

            CREATE TABLE dbo.BillingClaims (

                claim_id          INT IDENTITY PRIMARY KEY,

                project_id        INT NOT NULL REFERENCES dbo.Projects(project_id) ON DELETE CASCADE,

                period_start      DATE NOT NULL,

                period_end        DATE NOT NULL,

                po_ref            NVARCHAR(100) NULL,

                invoice_ref       NVARCHAR(100) NULL,

                status            NVARCHAR(30) NOT NULL DEFAULT 'draft',

                created_at        DATETIME2 DEFAULT SYSDATETIME()

            );

            """

            self.cursor.execute(claims_sql)

            

            # Create BillingClaimLines table

            lines_sql = """

            CREATE TABLE dbo.BillingClaimLines (

                line_id           INT IDENTITY PRIMARY KEY,

                claim_id          INT NOT NULL REFERENCES dbo.BillingClaims(claim_id) ON DELETE CASCADE,

                service_id        INT NOT NULL REFERENCES dbo.ProjectServices(service_id),

                stage_label       NVARCHAR(200) NOT NULL,

                prev_pct          DECIMAL(9,4) NOT NULL,

                curr_pct          DECIMAL(9,4) NOT NULL,

                delta_pct         AS (CASE WHEN curr_pct >= prev_pct THEN curr_pct - prev_pct ELSE 0 END) PERSISTED,

                amount_this_claim DECIMAL(18,2) NOT NULL,

                note              NVARCHAR(400) NULL

            );

            """

            self.cursor.execute(lines_sql)

            

            # Create index

            index_sql = """

            CREATE INDEX IX_BillingLines_ClaimService ON dbo.BillingClaimLines(claim_id, service_id);

            """

            self.cursor.execute(index_sql)

            

            self.db.commit()

            print("âœ… BillingClaims and BillingClaimLines tables created successfully")

            

        except Exception as e:

            print(f"Error creating billing tables: {e}")

            self.db.rollback()

    

    def create_service_schedule_table(self):

        """Create the ServiceScheduleSettings table"""

        try:

            create_sql = """

            CREATE TABLE dbo.ServiceScheduleSettings (

                service_id    INT PRIMARY KEY REFERENCES dbo.ProjectServices(service_id) ON DELETE CASCADE,

                start_date    DATE NULL,

                end_date      DATE NULL,

                frequency     NVARCHAR(20) NOT NULL DEFAULT 'weekly',

                auto_complete BIT NOT NULL DEFAULT 1,

                updated_at    DATETIME2 DEFAULT SYSDATETIME()

            );

            """

            self.cursor.execute(create_sql)

            self.db.commit()

            print("? ServiceScheduleSettings table created successfully")

        except Exception as e:

            print(f"Error creating ServiceScheduleSettings table: {e}")

            self.db.rollback()



    def load_template(self, template_name: str) -> Optional[Dict]:

        """Load a service template by name from templates/service_templates.json"""

        try:

            # Get the path to the templates directory

            template_file = os.path.join(os.path.dirname(__file__), 'templates', 'service_templates.json')

            if not os.path.exists(template_file):

                print(f"Template file not found: {template_file}")

                return None

            # Load and parse the template file

            with open(template_file, 'r', encoding='utf-8') as f:

                data = json.load(f)

            # Find the template by name

            for template in data.get('templates', []):

                if template.get('name') == template_name:

                    # Validate the template before returning

                    validation_errors = validate_template(template)

                    if validation_errors:

                        print(f"Template '{template_name}' has validation errors:")

                        for error in validation_errors:

                            print(f"  - {error}")

                        return None

                    return template

            print(f"Template '{template_name}' not found in templates")

            return None

        except Exception as e:

            print(f"Error loading template '{template_name}': {e}")

            return None

    def get_available_templates(self) -> List[Dict]:
        """Get list of available service templates from templates/service_templates.json"""
        try:
            import json
            import os

            # Get the path to the templates directory
            template_file = os.path.join(os.path.dirname(__file__), 'templates', 'service_templates.json')

            if not os.path.exists(template_file):
                print(f"Template file not found: {template_file}")
                return []

            # Load and parse the template file
            with open(template_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Return all templates with basic info
            templates = []
            for template in data.get('templates', []):
                templates.append({
                    'name': template.get('name', ''),
                    'sector': template.get('sector', ''),
                    'description': template.get('notes', '')
                })

            return templates

        except Exception as e:
            print(f"Error getting available templates: {e}")
            return []



    def apply_template(self, project_id: int, template_name: str, overrides: Dict = None) -> List[Dict]:

        """Apply service template to project, creating ProjectServices"""

        try:

            # Load template

            template = self.load_template(template_name)

            if not template:

                raise ValueError(f"Template '{template_name}' not found")

            

            services_created = []

            overrides = overrides or {}

            

            for item in template['items']:

                # Apply overrides if provided

                unit_qty = overrides.get(f"{item['service_code']}_units", item.get('default_units', 1))

                unit_rate = overrides.get(f"{item['service_code']}_rate", item.get('unit_rate', 0))

                lump_sum = overrides.get(f"{item['service_code']}_lump", item.get('lump_sum_fee', 0))

                

                # Calculate agreed fee

                if item['unit_type'] == 'lump_sum':

                    agreed_fee = lump_sum

                else:

                    agreed_fee = unit_qty * unit_rate

                

                # Create service record

                service_data = {

                    'project_id': project_id,

                    'phase': item['phase'],

                    'service_code': item['service_code'],

                    'service_name': item['service_name'],

                    'unit_type': item['unit_type'],

                    'unit_qty': unit_qty,

                    'unit_rate': unit_rate,

                    'lump_sum_fee': lump_sum,

                    'agreed_fee': agreed_fee,

                    'bill_rule': item['bill_rule'],

                    'notes': item.get('notes', '')

                }

                

                # Validate service data before creation

                validation_errors = validate_service_data(service_data)

                if validation_errors:

                    print(f"Service validation errors for {item['service_code']}: {validation_errors}")

                    continue  # Skip invalid services

                

                service_id = self.create_project_service(service_data)


                if service_id:


                    service_data['service_id'] = service_id


                    schedule_start = datetime.now().strftime('%Y-%m-%d')


                    schedule_end = (datetime.now() + timedelta(days=30 * max(1, int(unit_qty or 1)))).strftime('%Y-%m-%d')


                    self.upsert_service_schedule(service_id, schedule_start, schedule_end, item.get('frequency', 'weekly'))


                    if item['unit_type'] == 'review':


                        self.rebuild_service_reviews(service_id)


                    services_created.append(service_data)
            

            return services_created

            

        except Exception as e:

            print(f"Error applying template: {e}")

            return []

    

    def create_project_service(self, service_data: Dict) -> int:

        """Create a new project service"""

        # Validate service data

        validation_errors = validate_service_data(service_data)

        if validation_errors:

            error_msg = f"Service validation failed: {', '.join([str(e) for e in validation_errors])}"

            print(error_msg)

            raise ValueError(error_msg)

        

        # Sanitize input data

        service_data = sanitize_input(service_data)

        

        query = """

        INSERT INTO ProjectServices (

            project_id, phase, service_code, service_name, unit_type,

            unit_qty, unit_rate, lump_sum_fee, agreed_fee, bill_rule, notes

        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

        """

        

        params = (

            service_data['project_id'],

            service_data['phase'],

            service_data['service_code'],

            service_data['service_name'],

            service_data['unit_type'],

            service_data.get('unit_qty'),

            service_data.get('unit_rate'),

            service_data.get('lump_sum_fee'),

            service_data['agreed_fee'],

            service_data['bill_rule'],

            service_data.get('notes', '')

        )

        

        self.cursor.execute(query, params)

        

        # Get the last inserted ID for SQL Server

        self.cursor.execute("SELECT @@IDENTITY")

        service_id = self.cursor.fetchone()[0]

        

        self.db.commit()

        return int(service_id)

    

    def generate_review_cycles(self, service_id: int, unit_qty: int,

                             start_date: datetime, end_date: datetime,

                             cadence: str = 'weekly', disciplines: str = 'All') -> List[Dict]:

        """Generate review cycles for a service"""

        try:

            if unit_qty <= 0:

                return []



            freq_key = (cadence or 'weekly').lower().replace('_', '-')

            interval_lookup = {

                'weekly': 7,

                'bi-weekly': 14,

                'biweekly': 14,

                'fortnightly': 14,

                'monthly': 30

            }

            interval_days = interval_lookup.get(freq_key)



            dates: List[datetime] = []

            current_date = start_date



            if interval_days:
                # Generate exactly unit_qty cycles with proper interval spacing
                for i in range(unit_qty):
                    cycle_date = start_date + timedelta(days=i * interval_days)
                    dates.append(cycle_date)

                # Ensure final date does not exceed requested end window

                # FIXED: Don't cap dates to ensure exactly unit_qty cycles
                # dates = [min(date, end_date) for date in dates]

            else:

                total_days = max(1, (end_date - start_date).days)

                if unit_qty == 1:

                    dates = [start_date]

                else:

                    interval = total_days / (unit_qty - 1)

                    dates = [start_date + timedelta(days=int(round(i * interval))) for i in range(unit_qty)]



            cycles_created: List[Dict] = []

            for i, planned_date in enumerate(dates):

                # Keep dates within requested window

                if planned_date > end_date:

                    planned_date = end_date

                elif planned_date < start_date:

                    planned_date = start_date



                # For BIM coordination meetings, planned_date and due_date are the same (meeting date)
                # No separate preparation period - the review IS the meeting
                due_date = planned_date



                cycle_data = {

                    'service_id': service_id,

                    'cycle_no': i + 1,

                    'planned_date': planned_date.strftime('%Y-%m-%d'),

                    'due_date': due_date.strftime('%Y-%m-%d'),

                    'disciplines': disciplines,

                    'deliverables': 'progress_report,issues',

                    'status': 'planned',

                    'weight_factor': 1.0

                }



                review_id = self.create_service_review(cycle_data)

                cycle_data['review_id'] = review_id

                cycles_created.append(cycle_data)



            return cycles_created



        except Exception as e:

            print(f"Error generating cycles: {e}")

            return []

    

    def create_service_review(self, review_data: Dict) -> int:

        """Create a service review cycle"""

        try:

            query = """

            INSERT INTO ServiceReviews (

                service_id, cycle_no, planned_date, due_date, disciplines,

                deliverables, status, weight_factor

            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);

            """

            

            params = (

                review_data['service_id'],

                review_data['cycle_no'],

                review_data['planned_date'],

                review_data['due_date'],

                review_data['disciplines'],

                review_data['deliverables'],

                review_data['status'],

                review_data['weight_factor']

            )

            

            self.cursor.execute(query, params)

            

            # Get the last inserted ID

            self.cursor.execute("SELECT SCOPE_IDENTITY()")

            review_id = self.cursor.fetchone()[0]

            

            self.db.commit()

            return int(review_id) if review_id else 0

            

        except Exception as e:

            print(f"Error creating service review: {e}")

            self.db.rollback()

            return 0

    

    def mark_reviews_completed(self, review_ids: List[int]) -> int:

        """Mark a set of reviews as completed."""

        if not review_ids:

            return 0



        placeholders = ','.join(['?'] * len(review_ids))

        query = f"""

        UPDATE ServiceReviews

        SET status = 'completed',

            actual_issued_at = COALESCE(actual_issued_at, SYSDATETIME())

        WHERE review_id IN ({placeholders})

        """

        self.cursor.execute(query, review_ids)

        self.db.commit()

        return self.cursor.rowcount



    def mark_review_issued(self, review_id: int, evidence_link: str = None) -> bool:

        """Mark a review as report issued"""

        try:

            query = """

            UPDATE ServiceReviews 

            SET status = 'report_issued', 

                actual_issued_at = ?,

                evidence_links = ?

            WHERE review_id = ?

            """

            

            self.cursor.execute(query, (

                datetime.now().isoformat(),

                evidence_link,

                review_id

            ))

            self.db.commit()

            return True

            

        except Exception as e:

            print(f"Error marking review issued: {e}")

            return False

    

    def update_review_status_to(self, review_id: int, new_status: str, evidence_link: str = None) -> bool:
        """Update review status to any valid status with optional evidence link"""
        try:
            valid_statuses = ['planned', 'in_progress', 'completed', 'report_issued', 'closed', 'cancelled']
            
            if new_status not in valid_statuses:
                print(f"Invalid status: {new_status}. Must be one of {valid_statuses}")
                return False
            
            # Get current status for validation
            current_status = self.get_review_current_status(review_id)
            if not current_status:
                print(f"Could not find review with ID: {review_id}")
                return False
            
            # Validate status transition
            if not self.is_valid_status_transition(current_status, new_status):
                print(f"Invalid transition from '{current_status}' to '{new_status}'")
                return False
            
            # Build query based on status type
            if new_status in ['completed', 'report_issued', 'closed']:
                # These statuses should set actual_issued_at
                query = """
                UPDATE ServiceReviews 
                SET status = ?, 
                    actual_issued_at = COALESCE(actual_issued_at, SYSDATETIME()),
                    evidence_links = CASE WHEN ? IS NOT NULL THEN ? ELSE evidence_links END
                WHERE review_id = ?
                """
                self.cursor.execute(query, (new_status, evidence_link, evidence_link, review_id))
            else:
                # For planned, in_progress, cancelled - don't update actual_issued_at
                query = """
                UPDATE ServiceReviews 
                SET status = ?,
                    evidence_links = CASE WHEN ? IS NOT NULL THEN ? ELSE evidence_links END
                WHERE review_id = ?
                """
                self.cursor.execute(query, (new_status, evidence_link, evidence_link, review_id))
            
            self.db.commit()
            return self.cursor.rowcount > 0
            
        except Exception as e:
            print(f"Error updating review status: {e}")
            return False

    def get_review_current_status(self, review_id: int) -> str:
        """Get current status of a review"""
        try:
            query = "SELECT status FROM ServiceReviews WHERE review_id = ?"
            self.cursor.execute(query, (review_id,))
            result = self.cursor.fetchone()
            return result[0] if result else None
        except Exception as e:
            print(f"Error getting current status: {e}")
            return None

    def is_valid_status_transition(self, current_status: str, new_status: str) -> bool:
        """Validate if status transition is allowed"""
        # Allow any transition if current is same as new (no change)
        if current_status == new_status:
            return True
        
        # Define valid transitions
        valid_transitions = {
            'planned': ['in_progress', 'cancelled'],
            'in_progress': ['completed', 'cancelled', 'planned'],  # Allow back to planned
            'completed': ['report_issued', 'in_progress'],  # Allow rework
            'report_issued': ['closed', 'completed'],  # Allow rework after issue
            'closed': ['report_issued'],  # Allow reopening
            'cancelled': ['planned', 'in_progress']  # Allow reactivation
        }
        
        # Allow admin override - any status can go to any other status
        # This provides flexibility for project management
        return new_status in valid_transitions.get(current_status, []) or True  # Allow all transitions for flexibility

    def generate_claim(self, project_id: int, period_start: datetime, 

                      period_end: datetime, po_ref: str = None) -> Dict:

        """Generate billing claim for period"""

        try:

            # Validate claim data

            claim_data = {

                'project_id': project_id,

                'period_start': period_start.date() if hasattr(period_start, 'date') else period_start,

                'period_end': period_end.date() if hasattr(period_end, 'date') else period_end,

                'po_ref': po_ref

            }

            

            validation_errors = validate_billing_claim(claim_data)

            if validation_errors:

                error_msg = f"Billing claim validation failed: {', '.join([str(e) for e in validation_errors])}"

                print(error_msg)

                raise ValueError(error_msg)

            

            # Create claim header

            query = """

            INSERT INTO BillingClaims (project_id, period_start, period_end, po_ref)

            VALUES (?, ?, ?, ?)

            """

            

            self.cursor.execute(query, (

                project_id,

                period_start.strftime('%Y-%m-%d'),

                period_end.strftime('%Y-%m-%d'),

                po_ref

            ))

            claim_id = self.cursor.lastrowid

            

            # Get services and calculate deltas

            services = self.get_project_services(project_id)

            claim_lines = []

            total_amount = 0

            

            for service in services:

                # Get previous claimed percentage

                prev_pct = self.get_last_claimed_percentage(service['service_id'], claim_id)

                curr_pct = service['progress_pct']

                

                if curr_pct > prev_pct:

                    delta_pct = curr_pct - prev_pct

                    amount = service['agreed_fee'] * (delta_pct / 100.0)

                    

                    # Create claim line

                    line_data = {

                        'claim_id': claim_id,

                        'service_id': service['service_id'],

                        'stage_label': service['phase'],

                        'prev_pct': prev_pct,

                        'curr_pct': curr_pct,

                        'amount_this_claim': amount

                    }

                    

                    self.create_claim_line(line_data)

                    claim_lines.append(line_data)

                    total_amount += amount

            

            self.db.commit()

            

            return {

                'claim_id': claim_id,

                'total_amount': total_amount,

                'lines': claim_lines

            }

            

        except Exception as e:

            print(f"Error generating claim: {e}")

            return {}

    

    def create_claim_line(self, line_data: Dict) -> int:

        """Create a billing claim line"""

        query = """

        INSERT INTO BillingClaimLines (

            claim_id, service_id, stage_label, prev_pct, curr_pct, amount_this_claim

        ) VALUES (?, ?, ?, ?, ?, ?)

        """

        

        params = (

            line_data['claim_id'],

            line_data['service_id'],

            line_data['stage_label'],

            line_data['prev_pct'],

            line_data['curr_pct'],

            line_data['amount_this_claim']

        )

        

        self.cursor.execute(query, params)

        return self.cursor.lastrowid

    

    def get_project_services(self, project_id: int) -> List[Dict]:

        """Get all services for a project"""

        query = """

        SELECT ps.service_id, ps.project_id, ps.phase, ps.service_code, ps.service_name,

               ps.unit_type, ps.unit_qty, ps.unit_rate, ps.lump_sum_fee, ps.agreed_fee,

               ps.bill_rule, ps.status, ps.progress_pct, ps.claimed_to_date, ps.notes,

               sss.start_date AS schedule_start, sss.end_date AS schedule_end, sss.frequency AS schedule_frequency

        FROM ProjectServices ps

        LEFT JOIN ServiceScheduleSettings sss ON sss.service_id = ps.service_id

        WHERE ps.project_id = ?

        ORDER BY ps.phase, ps.service_code

        """



        self.cursor.execute(query, (project_id,))

        rows = self.cursor.fetchall()



        columns = [desc[0] for desc in self.cursor.description]

        return [dict(zip(columns, row)) for row in rows]

    

    def get_service_by_id(self, service_id: int) -> Optional[Dict]:

        """Fetch a single project service with schedule information."""

        query = """

        SELECT ps.service_id, ps.project_id, ps.phase, ps.service_code, ps.service_name,

               ps.unit_type, ps.unit_qty, ps.unit_rate, ps.lump_sum_fee, ps.agreed_fee,

               ps.bill_rule, ps.status, ps.progress_pct, ps.claimed_to_date, ps.notes,

               sss.start_date AS schedule_start, sss.end_date AS schedule_end, sss.frequency AS schedule_frequency

        FROM ProjectServices ps

        LEFT JOIN ServiceScheduleSettings sss ON sss.service_id = ps.service_id

        WHERE ps.service_id = ?

        """



        self.cursor.execute(query, (service_id,))

        row = self.cursor.fetchone()

        if not row:

            return None

        columns = [desc[0] for desc in self.cursor.description]

        return dict(zip(columns, row))



    def get_service_schedule(self, service_id: int) -> Optional[Dict]:

        """Return schedule metadata for a service if available."""

        self.cursor.execute(

            "SELECT service_id, start_date, end_date, frequency, auto_complete FROM ServiceScheduleSettings WHERE service_id = ?",

            (service_id,)

        )

        row = self.cursor.fetchone()

        if not row:

            return None

        columns = [desc[0] for desc in self.cursor.description]

        return dict(zip(columns, row))



    def upsert_service_schedule(

        self,

        service_id: int,

        start_date: Optional[str],

        end_date: Optional[str],

        frequency: str = 'weekly',

        auto_complete: Optional[bool] = None,

    ):

        """Insert or update schedule metadata for a service."""

        freq = (frequency or 'weekly').lower()

        query = """

        IF EXISTS (SELECT 1 FROM ServiceScheduleSettings WHERE service_id = ?)

            UPDATE ServiceScheduleSettings

            SET start_date = ?,

                end_date = ?,

                frequency = ?,

                auto_complete = CASE WHEN ? IS NULL THEN auto_complete ELSE ? END,

                updated_at = SYSDATETIME()

            WHERE service_id = ?;

        ELSE

            INSERT INTO ServiceScheduleSettings (service_id, start_date, end_date, frequency, auto_complete)

            VALUES (?, ?, ?, ?, COALESCE(?, 1));

        """

        params = (

            service_id,

            start_date,

            end_date,

            freq,

            auto_complete,

            auto_complete,

            service_id,

            service_id,

            start_date,

            end_date,

            freq,

            auto_complete,

        )

        self.cursor.execute(query, params)

        self.db.commit()



    def delete_service_reviews(self, service_id: int):

        """Remove all existing review cycles for a service."""

        self.cursor.execute("DELETE FROM ServiceReviews WHERE service_id = ?", (service_id,))

        self.db.commit()



    def delete_project_service(self, service_id: int) -> bool:

        """Delete a project service and all related data"""

        try:

            from database import delete_project_service

            return delete_project_service(service_id)

        except Exception as e:

            print(f"Error deleting project service: {e}")

            return False

    def clear_all_project_services(self, project_id: int) -> int:

        """Delete all services for a project and return the count of deleted services"""

        try:

            # Get all services for the project

            services = self.get_project_services(project_id)

            deleted_count = 0

            

            # Delete each service individually to ensure proper cleanup

            for service in services:

                service_id = service['service_id']

                if self.delete_project_service(service_id):

                    deleted_count += 1

                else:

                    print(f"Failed to delete service {service_id}")

            

            return deleted_count

            

        except Exception as e:

            print(f"Error clearing all project services: {e}")

            return 0

    def rebuild_service_reviews(self, service_id: int) -> bool:

        """Recreate review cycles according to stored schedule settings."""

        service = self.get_service_by_id(service_id)

        if not service:

            return False



        schedule_start = service.get('schedule_start')

        schedule_end = service.get('schedule_end')

        frequency = service.get('schedule_frequency') or 'weekly'



        if not schedule_start or not schedule_end:

            return False



        try:

            start_date = datetime.strptime(schedule_start, '%Y-%m-%d') if isinstance(schedule_start, str) else schedule_start

            end_date = datetime.strptime(schedule_end, '%Y-%m-%d') if isinstance(schedule_end, str) else schedule_end

        except Exception:

            return False



        if not start_date or not end_date or end_date < start_date:

            return False



        unit_qty = service.get('unit_qty') or 0

        if unit_qty is None or unit_qty <= 0:

            unit_qty = 1 if (service.get('unit_type') or '').lower() == 'review' else 0

        if unit_qty <= 0:

            return False



        self.delete_service_reviews(service_id)

        cycles = self.generate_review_cycles(

            service_id=service_id,

            unit_qty=int(unit_qty),

            start_date=start_date,

            end_date=end_date,

            cadence=frequency,

            disciplines=service.get('phase', 'All') or 'All',

        )

        return bool(cycles)



    def get_project_review_stats(self, project_id: int) -> Dict:

        """Get review statistics for a project"""

        try:

            # Get total services

            self.cursor.execute("SELECT COUNT(*) FROM ProjectServices WHERE project_id = ?", (project_id,))

            total_services = self.cursor.fetchone()[0]

            

            # Get total reviews

            total_reviews_query = """

            SELECT COUNT(*) FROM ServiceReviews sr

            JOIN ProjectServices ps ON ps.service_id = sr.service_id

            WHERE ps.project_id = ?

            """

            self.cursor.execute(total_reviews_query, (project_id,))

            total_reviews = self.cursor.fetchone()[0] or 0

            

            # Get completed reviews

            completed_reviews_query = """

            SELECT COUNT(*) FROM ServiceReviews sr

            JOIN ProjectServices ps ON ps.service_id = sr.service_id

            WHERE ps.project_id = ? AND sr.status = 'completed'

            """

            self.cursor.execute(completed_reviews_query, (project_id,))

            completed_reviews = self.cursor.fetchone()[0] or 0

            

            # Get active reviews

            active_reviews_query = """

            SELECT COUNT(*) FROM ServiceReviews sr

            JOIN ProjectServices ps ON ps.service_id = sr.service_id

            WHERE ps.project_id = ? AND sr.status IN ('planned', 'in_progress')

            """

            self.cursor.execute(active_reviews_query, (project_id,))

            active_reviews = self.cursor.fetchone()[0] or 0

            

            return {

                'total_services': total_services,

                'total_reviews': total_reviews,

                'completed_reviews': completed_reviews,

                'active_reviews': active_reviews

            }

            

        except Exception as e:

            print(f"Error getting project review stats: {e}")

            return {

                'total_services': 0,

                'total_reviews': 0,

                'completed_reviews': 0,

                'active_reviews': 0

            }

    

    def get_billing_claims(self, project_id: int) -> List[Dict]:

        """Get billing claims summary for a project."""

        try:

            query = """

                SELECT bc.claim_id, bc.period_start, bc.period_end,

                       bc.po_ref, bc.invoice_ref, bc.status,

                       COALESCE(SUM(bcl.amount_this_claim), 0) AS total_amount

                FROM BillingClaims bc

                LEFT JOIN BillingClaimLines bcl ON bc.claim_id = bcl.claim_id

                WHERE bc.project_id = ?

                GROUP BY bc.claim_id, bc.period_start, bc.period_end,

                         bc.po_ref, bc.invoice_ref, bc.status

                ORDER BY bc.period_start DESC

            """

            self.cursor.execute(query, (project_id,))

            columns = [desc[0] for desc in self.cursor.description]

            return [dict(zip(columns, row)) for row in self.cursor.fetchall()]

        except Exception as e:

            print(f"Error getting billing claims: {e}")

            return []



    def get_service_progress_summary(self, project_id: int) -> List[Dict]:

        """Return progress and billing summary for each service in a project."""

        try:

            query = """

                SELECT service_id, service_name, phase, agreed_fee,

                       progress_pct, claimed_to_date, bill_rule, status

                FROM ProjectServices

                WHERE project_id = ?

                ORDER BY phase, service_name

            """

            self.cursor.execute(query, (project_id,))

            rows = self.cursor.fetchall()

            summary = []

            bill_rule_labels = {

                'on_completion': 'On completion',

                'per_unit_complete': 'Per unit completed',

                'on_setup': 'On setup',

                'on_report_issue': 'On report issue',

                'monthly': 'Monthly billing',

                'milestone': 'Milestone driven'

            }

            for row in rows:

                (service_id, service_name, phase, agreed_fee,

                 progress_pct, claimed_to_date, bill_rule, status) = row

                agreed_fee = float(agreed_fee or 0.0)

                progress_pct = round(float(progress_pct or 0.0), 1)

                claimed_to_date = float(claimed_to_date or 0.0)

                billed_amount = claimed_to_date if claimed_to_date > 0 else agreed_fee * (progress_pct / 100.0)

                billed_amount = round(billed_amount, 2)

                remaining = round(max(0.0, agreed_fee - billed_amount), 2)

                bill_rule_key = (bill_rule or '').lower()

                next_milestone = bill_rule_labels.get(bill_rule_key, 'Manual review')

                summary.append({

                    'service_id': service_id,

                    'service_name': service_name,

                    'phase': phase,

                    'agreed_fee': round(agreed_fee, 2),

                    'progress_pct': progress_pct,

                    'billed_amount': billed_amount,

                    'remaining_amount': remaining,

                    'next_milestone': next_milestone,

                    'status': status

                })

            return summary

        except Exception as e:

            print(f"Error getting service progress summary: {e}")

            return []



    def generate_service_reviews(self, project_id: int) -> List[Dict]:

        """Generate review cycles from project services"""

        try:

            reviews_created = []

            services = self.get_project_services(project_id)



            for service in services:

                service_id = service['service_id']

                unit_type = (service.get('unit_type') or '').lower()

                unit_qty = int(service.get('unit_qty') or 0)



                if unit_type != 'review' or unit_qty <= 0:

                    continue



                schedule_start = service.get('schedule_start')

                schedule_end = service.get('schedule_end')

                frequency = service.get('schedule_frequency') or 'weekly'



                if schedule_start and isinstance(schedule_start, str):

                    try:

                        start_date = datetime.strptime(schedule_start, '%Y-%m-%d')

                    except ValueError:

                        start_date = datetime.now()

                elif schedule_start and hasattr(schedule_start, 'year'):  # datetime.date or datetime.datetime

                    start_date = datetime.combine(schedule_start, datetime.min.time())

                else:

                    start_date = datetime.now()



                if schedule_end and isinstance(schedule_end, str):

                    try:

                        end_date = datetime.strptime(schedule_end, '%Y-%m-%d')

                    except ValueError:

                        end_date = start_date + timedelta(days=30 * max(1, unit_qty))

                elif schedule_end and hasattr(schedule_end, 'year'):  # datetime.date or datetime.datetime

                    end_date = datetime.combine(schedule_end, datetime.min.time())

                else:

                    end_date = start_date + timedelta(days=30 * max(1, unit_qty))



                # Persist defaults if the service had no recorded schedule

                if not schedule_start or not schedule_end:

                    self.upsert_service_schedule(

                        service_id=service_id,

                        start_date=start_date.strftime('%Y-%m-%d'),

                        end_date=end_date.strftime('%Y-%m-%d'),

                        frequency=frequency

                    )



                self.delete_service_reviews(service_id)

                cycles = self.generate_review_cycles(

                    service_id=service_id,

                    unit_qty=unit_qty,

                    start_date=start_date,

                    end_date=end_date,

                    cadence=frequency,

                    disciplines=service.get('phase', 'All') or 'All'

                )

                reviews_created.extend(cycles)



            return reviews_created



        except Exception as e:

            print(f"Error generating service reviews: {e}")

            return []

    

    def generate_stage_schedule_new(self, project_id: int, stages: List[Dict]) -> bool:

        """Generate review schedule from stage definitions using modern schema"""

        try:

            reviews_created = 0

            

            for stage in stages:

                stage_name = stage.get('stage_name', 'Unknown Stage')

                start_date = stage.get('start_date')

                end_date = stage.get('end_date') 

                num_reviews = int(stage.get('num_reviews', 0))

                frequency = stage.get('frequency', 'weekly')

                

                # Convert dates if they're strings

                if isinstance(start_date, str):

                    start_date = datetime.strptime(start_date, '%Y-%m-%d')

                if isinstance(end_date, str):

                    end_date = datetime.strptime(end_date, '%Y-%m-%d')

                

                if num_reviews <= 0:

                    continue

                

                # Create a virtual service for this stage

                service_data = {

                    'project_id': project_id,

                    'phase': stage_name,

                    'service_code': 'STAGE_REVIEW',

                    'service_name': f'{stage_name} Reviews',

                    'unit_type': 'review',

                    'default_units': num_reviews,

                    'unit_qty': num_reviews,

                    'unit_rate': 100.0,

                    'lump_sum_fee': 0.0,

                    'agreed_fee': 0.0,

                    'bill_rule': 'per_unit_complete',

                    'notes': f'Auto-generated review service for {stage_name} stage'

                }

                

                service_id = self.create_project_service(service_data)

                

                if service_id:

                    self.upsert_service_schedule(service_id, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'), frequency)

                    # Generate review cycles for this service

                    cycles = self.generate_review_cycles(

                        service_id=service_id,

                        unit_qty=num_reviews,

                        start_date=start_date,

                        end_date=end_date,

                        cadence=frequency,

                        disciplines=stage_name

                    )

                    reviews_created += len(cycles)

            

            return reviews_created > 0

            

        except Exception as e:

            print(f"Error generating stage schedule: {e}")

            return False
    
    def get_project_reviews(self, project_id: int) -> List[Dict]:
        """Get all reviews for a project"""
        try:
            self.cursor.execute("""
                SELECT 
                    rs.schedule_id, rs.review_date, rs.assigned_to, rs.status,
                    rs.cycle_id, rs.is_within_license_period, rs.is_blocked,
                    u.name as assigned_name,
                    c.cycle_number
                FROM ReviewSchedule rs
                LEFT JOIN users u ON rs.assigned_to = u.user_id
                LEFT JOIN project_review_cycles c ON rs.cycle_id = c.cycle_id
                WHERE rs.project_id = ?
                ORDER BY rs.review_date
            """, (project_id,))
            
            reviews = self.cursor.fetchall()
            
            return [
                {
                    'schedule_id': review.schedule_id,
                    'review_date': review.review_date,
                    'assigned_to': review.assigned_to,
                    'assigned_name': review.assigned_name,
                    'status': review.status,
                    'cycle_id': review.cycle_id,
                    'cycle_number': review.cycle_number,
                    'is_within_license_period': review.is_within_license_period,
                    'is_blocked': review.is_blocked
                } for review in reviews
            ]
            
        except Exception as e:
            print(f"Error getting project reviews: {e}")
            return []
    
    def get_review_details(self, review_id: int) -> Optional[Dict]:
        """Get detailed information for a specific review"""
        try:
            self.cursor.execute("""
                SELECT 
                    rs.schedule_id, rs.project_id, rs.review_date, rs.assigned_to, 
                    rs.status, rs.cycle_id, rs.is_within_license_period, rs.is_blocked,
                    rs.manual_override,
                    u.name as assigned_name,
                    p.project_name,
                    c.cycle_number
                FROM ReviewSchedule rs
                LEFT JOIN users u ON rs.assigned_to = u.user_id
                LEFT JOIN projects p ON rs.project_id = p.project_id
                LEFT JOIN project_review_cycles c ON rs.cycle_id = c.cycle_id
                WHERE rs.schedule_id = ?
            """, (review_id,))
            
            review = self.cursor.fetchone()
            
            if review:
                return {
                    'schedule_id': review.schedule_id,
                    'project_id': review.project_id,
                    'project_name': review.project_name,
                    'review_date': review.review_date,
                    'assigned_to': review.assigned_to,
                    'assigned_name': review.assigned_name,
                    'status': review.status,
                    'cycle_id': review.cycle_id,
                    'cycle_number': review.cycle_number,
                    'is_within_license_period': review.is_within_license_period,
                    'is_blocked': review.is_blocked,
                    'manual_override': review.manual_override
                }
            return None
            
        except Exception as e:
            print(f"Error getting review details: {e}")
            return None
    
    def update_review_assignment(self, review_id: int, user_id: int) -> bool:
        """Update the assigned user for a review"""
        try:
            self.cursor.execute("""
                UPDATE ReviewSchedule 
                SET assigned_to = ?, manual_override = 1
                WHERE schedule_id = ?
            """, (user_id, review_id))
            
            self.db.commit()
            print(f"✅ Review {review_id} assigned to user {user_id}")
            return True
            
        except Exception as e:
            print(f"Error updating review assignment: {e}")
            self.db.rollback()
            return False
    
    def get_project_details(self, project_id: int) -> Optional[Dict]:
        """Get project details including manager and lead"""
        try:
            self.cursor.execute("""
                SELECT 
                    p.project_id, p.project_name, p.project_manager, p.internal_lead,
                    pm.name as project_manager_name, il.name as internal_lead_name
                FROM projects p
                LEFT JOIN users pm ON p.project_manager = pm.user_id
                LEFT JOIN users il ON p.internal_lead = il.user_id
                WHERE p.project_id = ?
            """, (project_id,))
            
            project = self.cursor.fetchone()
            
            if project:
                return {
                    'project_id': project.project_id,
                    'project_name': project.project_name,
                    'project_manager': project.project_manager,
                    'project_manager_name': project.project_manager_name,
                    'internal_lead': project.internal_lead,
                    'internal_lead_name': project.internal_lead_name
                }
            return None
            
        except Exception as e:
            print(f"Error getting project details: {e}")
            return None
        except Exception as e:

            print(f"Error generating stage schedule: {e}")

            return False

    def get_service_reviews(self, project_id: int, cycle_id: int = None) -> List[Dict]:
        """Get review cycles for a project, optionally filtered by cycle_id"""
        try:
            if cycle_id:
                # Get reviews for a specific cycle
                self.cursor.execute("""
                    SELECT DISTINCT c.cycle_id, c.cycle_number, c.planned_start_date, c.actual_start_date,
                           c.planned_end_date, c.actual_end_date, c.status
                    FROM project_review_cycles c
                    WHERE c.project_id = ? AND c.cycle_id = ?
                    ORDER BY c.cycle_number
                """, (project_id, cycle_id))
            else:
                # Get all review cycles for the project
                self.cursor.execute("""
                    SELECT c.cycle_id, c.cycle_number, c.planned_start_date, c.actual_start_date,
                           c.planned_end_date, c.actual_end_date, c.status
                    FROM project_review_cycles c
                    WHERE c.project_id = ?
                    ORDER BY c.cycle_number
                """, (project_id,))
            
            cycles = self.cursor.fetchall()
            return [
                {
                    'cycle_id': cycle.cycle_id,
                    'cycle_number': cycle.cycle_number,
                    'planned_start_date': cycle.planned_start_date,
                    'actual_start_date': cycle.actual_start_date,
                    'planned_end_date': cycle.planned_end_date,
                    'actual_end_date': cycle.actual_end_date,
                    'status': cycle.status
                }
                for cycle in cycles
            ]
        except Exception as e:
            print(f"Error getting service reviews: {e}")
            return []

    # ===== ENHANCED TRACKING METHODS =====

    def get_project_progress_summary(self, project_id: int) -> Dict:
        """Get comprehensive project progress summary for tracking UI"""
        try:
            # Get total reviews count
            self.cursor.execute("""
                SELECT COUNT(*) as total_reviews
                FROM project_review_cycles
                WHERE project_id = ?
            """, (project_id,))
            total_reviews = self.cursor.fetchone().total_reviews

            # Get completed reviews
            self.cursor.execute("""
                SELECT COUNT(*) as completed_reviews
                FROM project_review_cycles
                WHERE project_id = ? AND status = 'completed'
            """, (project_id,))
            completed_reviews = self.cursor.fetchone().completed_reviews

            # Get active reviews
            self.cursor.execute("""
                SELECT COUNT(*) as active_reviews
                FROM project_review_cycles
                WHERE project_id = ? AND status = 'in_progress'
            """, (project_id,))
            active_reviews = self.cursor.fetchone().active_reviews

            # Get overdue reviews
            self.cursor.execute("""
                SELECT COUNT(*) as overdue_reviews
                FROM project_review_cycles
                WHERE project_id = ? AND due_date < ? AND status != 'completed'
            """, (project_id, datetime.now().date()))
            overdue_reviews = self.cursor.fetchone().overdue_reviews

            # Get upcoming reviews (due within 7 days)
            self.cursor.execute("""
                SELECT COUNT(*) as upcoming_reviews
                FROM project_review_cycles
                WHERE project_id = ? AND due_date BETWEEN ? AND ? AND status != 'completed'
            """, (project_id, datetime.now().date(), (datetime.now() + timedelta(days=7)).date()))
            upcoming_reviews = self.cursor.fetchone().upcoming_reviews

            # Calculate overall progress
            overall_progress = (completed_reviews / total_reviews * 100) if total_reviews > 0 else 0

            return {
                'total_reviews': total_reviews,
                'completed_reviews': completed_reviews,
                'active_reviews': active_reviews,
                'overdue_reviews': overdue_reviews,
                'upcoming_reviews': upcoming_reviews,
                'overall_progress': round(overall_progress, 1)
            }

        except Exception as e:
            print(f"Error getting project progress summary: {e}")
            return {
                'total_reviews': 0,
                'completed_reviews': 0,
                'active_reviews': 0,
                'overdue_reviews': 0,
                'upcoming_reviews': 0,
                'overall_progress': 0
            }

    def generate_progress_report(self, project_id: int) -> Dict:
        """Generate detailed progress report for the project"""
        try:
            progress_summary = self.get_project_progress_summary(project_id)

            # Get service progress
            services = self.get_project_services(project_id)
            service_progress = []
            for service in services:
                service_progress.append({
                    'service_name': service['service_name'],
                    'phase': service['phase'],
                    'progress_percentage': service['progress_pct'],
                    'agreed_fee': service['agreed_fee'],
                    'completed_value': service['agreed_fee'] * (service['progress_pct'] / 100)
                })

            # Get recent reviews
            self.cursor.execute("""
                SELECT cycle_number, status, due_date, actual_end_date
                FROM project_review_cycles
                WHERE project_id = ?
                ORDER BY cycle_number DESC
                LIMIT 10
            """, (project_id,))
            recent_reviews = self.cursor.fetchall()

            review_status = []
            for review in recent_reviews:
                review_status.append({
                    'cycle': review.cycle_number,
                    'status': review.status,
                    'due_date': review.due_date,
                    'completed_date': review.actual_end_date
                })

            return {
                'progress_summary': progress_summary,
                'service_progress': service_progress,
                'recent_reviews': review_status,
                'generated_at': datetime.now().isoformat()
            }

        except Exception as e:
            print(f"Error generating progress report: {e}")
            return {'error': str(e)}

    def get_project_milestones(self, project_id: int) -> List[Dict]:
        """Get project milestones for timeline visualization"""
        try:
            milestones = []

            # Get review cycle milestones
            self.cursor.execute("""
                SELECT cycle_number, planned_start_date, due_date, status
                FROM project_review_cycles
                WHERE project_id = ?
                ORDER BY cycle_number
            """, (project_id,))
            cycles = self.cursor.fetchall()

            for cycle in cycles:
                # Calculate progress percentage based on status
                progress_pct = {
                    'planned': 0,
                    'in_progress': 50,
                    'completed': 100,
                    'on_hold': 25,
                    'cancelled': 0
                }.get(cycle.status, 0)

                milestones.append({
                    'name': f'Cycle {cycle.cycle_number}',
                    'due_date': cycle.due_date,
                    'status': cycle.status,
                    'progress_percentage': progress_pct,
                    'type': 'review_cycle'
                })

            # Get service completion milestones
            services = self.get_project_services(project_id)
            for service in services:
                if service['progress_pct'] >= 100:
                    milestones.append({
                        'name': f"{service['service_name']} Complete",
                        'due_date': service.get('end_date'),
                        'status': 'completed',
                        'progress_percentage': 100,
                        'type': 'service_completion'
                    })

            return sorted(milestones, key=lambda x: x.get('due_date') or datetime.max.date())

        except Exception as e:
            print(f"Error getting project milestones: {e}")
            return []

    def get_detailed_tasks(self, project_id: int, filters: Dict = None) -> List[Dict]:
        """Get detailed task information with filtering"""
        try:
            query = """
                SELECT
                    r.review_id,
                    r.cycle_id,
                    r.planned_date,
                    r.due_date,
                    r.actual_start_date,
                    r.actual_end_date,
                    r.status,
                    r.assigned_to,
                    r.reviewer,
                    r.notes,
                    s.service_name,
                    s.phase,
                    s.progress_pct,
                    s.priority,
                    r.last_updated
                FROM project_reviews r
                JOIN project_services s ON r.service_id = s.service_id
                WHERE s.project_id = ?
            """

            params = [project_id]

            # Apply filters
            if filters:
                if filters.get('status'):
                    query += " AND r.status = ?"
                    params.append(filters['status'])
                if filters.get('assignee'):
                    query += " AND r.assigned_to = ?"
                    params.append(filters['assignee'])
                if filters.get('priority'):
                    query += " AND s.priority = ?"
                    params.append(filters['priority'])

                # Due date filters
                due_filter = filters.get('due_filter')
                if due_filter == 'today':
                    query += " AND r.due_date = ?"
                    params.append(datetime.now().date())
                elif due_filter == '3days':
                    query += " AND r.due_date <= ?"
                    params.append((datetime.now() + timedelta(days=3)).date())
                elif due_filter == 'week':
                    query += " AND r.due_date <= ?"
                    params.append((datetime.now() + timedelta(days=7)).date())
                elif due_filter == 'overdue':
                    query += " AND r.due_date < ? AND r.status != 'completed'"
                    params.append(datetime.now().date())

            query += " ORDER BY r.due_date ASC"

            self.cursor.execute(query, params)
            tasks = self.cursor.fetchall()

            detailed_tasks = []
            for task in tasks:
                # Determine if overdue or due soon
                is_overdue = False
                due_soon = False
                if task.due_date:
                    days_until_due = (task.due_date - datetime.now().date()).days
                    is_overdue = days_until_due < 0 and task.status != 'completed'
                    due_soon = 0 <= days_until_due <= 3 and task.status != 'completed'

                detailed_tasks.append({
                    'id': task.review_id,
                    'service_name': task.service_name,
                    'cycle': task.cycle_id,
                    'due_date': task.due_date.strftime('%Y-%m-%d') if task.due_date else None,
                    'status': task.status,
                    'assignee': task.assigned_to,
                    'progress_percentage': task.progress_pct or 0,
                    'priority': task.priority or 'medium',
                    'last_update': task.last_updated.isoformat() if task.last_updated else None,
                    'is_overdue': is_overdue,
                    'due_soon': due_soon,
                    'phase': task.phase,
                    'notes': task.notes
                })

            return detailed_tasks

        except Exception as e:
            print(f"Error getting detailed tasks: {e}")
            return []

    def update_task_status(self, task_id: int, new_status: str, progress_percentage: int = None):
        """Update task status and progress"""
        try:
            # Validate status
            valid_statuses = ['planned', 'in_progress', 'completed', 'on_hold', 'cancelled']
            if new_status not in valid_statuses:
                raise ValueError(f"Invalid status: {new_status}")

            # Update task
            update_fields = ["status = ?", "last_updated = ?"]
            params = [new_status, datetime.now()]

            if progress_percentage is not None:
                update_fields.append("progress_pct = ?")
                params.append(progress_percentage)

            query = f"""
                UPDATE project_reviews
                SET {', '.join(update_fields)}
                WHERE review_id = ?
            """
            params.append(task_id)

            self.cursor.execute(query, params)

            # If completing task, set actual end date
            if new_status == 'completed':
                self.cursor.execute("""
                    UPDATE project_reviews
                    SET actual_end_date = ?
                    WHERE review_id = ? AND actual_end_date IS NULL
                """, (datetime.now().date(), task_id))

            self.db.commit()

        except Exception as e:
            print(f"Error updating task status: {e}")
            raise

    def reassign_task(self, task_id: int, new_assignee_id: int):
        """Reassign task to different user"""
        try:
            self.cursor.execute("""
                UPDATE project_reviews
                SET assigned_to = ?, last_updated = ?
                WHERE review_id = ?
            """, (new_assignee_id, datetime.now(), task_id))

            self.db.commit()

        except Exception as e:
            print(f"Error reassigning task: {e}")
            raise

    def add_task_evidence(self, task_id: int, file_path: str):
        """Add evidence file to task"""
        try:
            # Read file content (for small files) or store path
            if os.path.getsize(file_path) < 1024 * 1024:  # Less than 1MB
                with open(file_path, 'rb') as f:
                    file_content = f.read()
                file_name = os.path.basename(file_path)

                # Store in database (you might want to create an evidence table)
                # For now, just update notes with evidence reference
                self.cursor.execute("""
                    UPDATE project_reviews
                    SET evidence_links = COALESCE(evidence_links || ';', '') || ?,
                        last_updated = ?
                    WHERE review_id = ?
                """, (f"FILE:{file_name}", datetime.now(), task_id))
            else:
                # For large files, just store the path reference
                self.cursor.execute("""
                    UPDATE project_reviews
                    SET evidence_links = COALESCE(evidence_links || ';', '') || ?,
                        last_updated = ?
                    WHERE review_id = ?
                """, (f"PATH:{file_path}", datetime.now(), task_id))

            self.db.commit()

        except Exception as e:
            print(f"Error adding task evidence: {e}")
            raise

    def get_task_details(self, task_id: int) -> Dict:
        """Get detailed information about a specific task"""
        try:
            self.cursor.execute("""
                SELECT
                    r.*,
                    s.service_name,
                    s.phase,
                    s.agreed_fee,
                    s.progress_pct as service_progress,
                    p.project_name
                FROM project_reviews r
                JOIN project_services s ON r.service_id = s.service_id
                JOIN projects p ON s.project_id = p.project_id
                WHERE r.review_id = ?
            """, (task_id,))

            task = self.cursor.fetchone()
            if task:
                return {
                    'id': task.review_id,
                    'service_name': task.service_name,
                    'phase': task.phase,
                    'status': task.status,
                    'assignee': task.assigned_to,
                    'due_date': task.due_date.strftime('%Y-%m-%d') if task.due_date else None,
                    'progress_percentage': task.service_progress or 0,
                    'priority': getattr(task, 'priority', 'medium'),
                    'description': task.notes or '',
                    'evidence_links': task.evidence_links or '',
                    'project_name': task.project_name,
                    'agreed_fee': task.agreed_fee,
                    'planned_date': task.planned_date.strftime('%Y-%m-%d') if task.planned_date else None,
                    'actual_start_date': task.actual_start_date.strftime('%Y-%m-%d') if task.actual_start_date else None,
                    'actual_end_date': task.actual_end_date.strftime('%Y-%m-%d') if task.actual_end_date else None
                }
            return {}

        except Exception as e:
            print(f"Error getting task details: {e}")
            return {}

    def export_task_data(self, project_id: int) -> List[Dict]:
        """Export task data for external analysis"""
        try:
            tasks = self.get_detailed_tasks(project_id)

            # Convert to export format
            export_data = []
            for task in tasks:
                export_data.append({
                    'Task_ID': task['id'],
                    'Service_Name': task['service_name'],
                    'Phase': task['phase'],
                    'Cycle': task['cycle'],
                    'Due_Date': task['due_date'],
                    'Status': task['status'],
                    'Assignee': task['assignee'],
                    'Progress_Percentage': task['progress_percentage'],
                    'Priority': task['priority'],
                    'Is_Overdue': task['is_overdue'],
                    'Due_Soon': task['due_soon'],
                    'Last_Update': task['last_update'],
                    'Notes': task.get('notes', '')
                })

            return export_data

        except Exception as e:
            print(f"Error exporting task data: {e}")
            return []

