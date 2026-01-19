"""

Review Management System - Backend Services

Comprehensive scope - schedule - progress - billing workflow

"""



import json

import math
import sqlite3
import pyodbc

from collections import Counter
from datetime import datetime, timedelta, date

from decimal import Decimal, InvalidOperation

from typing import List, Dict, Optional, Tuple, Any

import os

from constants import schema as S

# Import fuzzy matching for enhanced template search
try:
    from difflib import SequenceMatcher
    FUZZY_MATCHING_AVAILABLE = True
except ImportError:
    FUZZY_MATCHING_AVAILABLE = False

# Import validation service
from review_validation import (
    validate_template, validate_service_data, validate_review_cycle,
    validate_project_services, validate_billing_claim, sanitize_input
)


class ReviewManagementService:

    """Core service for review management operations"""

    # Statuses that remain flexible enough to be rescheduled automatically
    ADJUSTABLE_STATUSES = {'planned', 'in_progress', 'overdue'}

    

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

            # Ensure billing metadata columns exist for legacy deployments
            self.ensure_service_review_billing_columns()

            

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



            # Check if ServiceItems table exists

            self.cursor.execute("""

                SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES 

                WHERE TABLE_NAME = 'ServiceItems' AND TABLE_SCHEMA = 'dbo'

            """)



            if self.cursor.fetchone()[0] == 0:

                print("Creating ServiceItems table...")

                self.create_service_items_table()



        except Exception as e:

            print(f"Error checking/creating tables: {e}")

        

    def _column_exists(self, table_name: str, column_name: str) -> bool:
        """Check if a column exists on a given table."""
        try:
            self.cursor.execute("""
                SELECT COUNT(*)
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = ? AND COLUMN_NAME = ?
            """, (table_name, column_name))
            row = self.cursor.fetchone()
            return bool(row and row[0])
        except Exception as exc:
            print(f"Error checking column {table_name}.{column_name}: {exc}")
            return False

    def ensure_service_review_billing_columns(self):
        """Ensure billing metadata columns exist on ServiceReviews."""
        try:
            columns = [
                (S.ServiceReviews.SOURCE_PHASE, 'NVARCHAR(200) NULL'),
                (S.ServiceReviews.BILLING_PHASE, 'NVARCHAR(200) NULL'),
                (S.ServiceReviews.BILLING_RATE, 'DECIMAL(18,2) NULL'),
                (S.ServiceReviews.BILLING_AMOUNT, 'DECIMAL(18,2) NULL'),
            ]

            altered = False
            for column_name, definition in columns:
                if not self._column_exists(S.ServiceReviews.TABLE, column_name):
                    try:
                        self.cursor.execute(f"ALTER TABLE dbo.{S.ServiceReviews.TABLE} ADD {column_name} {definition}")
                        altered = True
                    except Exception as exc:
                        print(f"Error adding column {column_name} to {S.ServiceReviews.TABLE}: {exc}")
                        self.db.rollback()
                        return

            if altered:
                self.db.commit()

            self.initialize_review_billing_defaults()
        except Exception as exc:
            print(f"Error ensuring ServiceReviews billing columns: {exc}")

    def initialize_review_billing_defaults(self):
        """Seed billing metadata for existing review rows based on their project service."""
        try:
            default_rate_sql = """
                CASE
                    WHEN LOWER(ISNULL(ps.unit_type, '')) = 'review' AND ps.unit_rate IS NOT NULL THEN ps.unit_rate
                    WHEN LOWER(ISNULL(ps.unit_type, '')) = 'review' AND ps.unit_qty IS NOT NULL AND ps.unit_qty <> 0 AND ps.agreed_fee IS NOT NULL
                        THEN CAST(ps.agreed_fee AS DECIMAL(18,4)) / NULLIF(CAST(ps.unit_qty AS DECIMAL(18,4)), 0)
                    WHEN LOWER(ISNULL(ps.unit_type, '')) = 'lump_sum' AND ps.unit_qty IS NOT NULL AND ps.unit_qty <> 0 AND ps.lump_sum_fee IS NOT NULL
                        THEN CAST(ps.lump_sum_fee AS DECIMAL(18,4)) / NULLIF(CAST(ps.unit_qty AS DECIMAL(18,4)), 0)
                    WHEN ps.unit_rate IS NOT NULL THEN ps.unit_rate
                    WHEN ps.unit_qty IS NOT NULL AND ps.unit_qty <> 0 AND ps.agreed_fee IS NOT NULL
                        THEN CAST(ps.agreed_fee AS DECIMAL(18,4)) / NULLIF(CAST(ps.unit_qty AS DECIMAL(18,4)), 0)
                    WHEN ps.lump_sum_fee IS NOT NULL THEN ps.lump_sum_fee
                    WHEN ps.agreed_fee IS NOT NULL THEN ps.agreed_fee
                    ELSE NULL
                END
            """.strip()

            update_sql = f"""
                UPDATE sr
                SET 
                    {S.ServiceReviews.SOURCE_PHASE} = COALESCE(sr.{S.ServiceReviews.SOURCE_PHASE}, ps.{S.ProjectServices.PHASE}),
                    {S.ServiceReviews.BILLING_PHASE} = COALESCE(sr.{S.ServiceReviews.BILLING_PHASE}, ps.{S.ProjectServices.PHASE}),
                    {S.ServiceReviews.BILLING_RATE} = COALESCE(sr.{S.ServiceReviews.BILLING_RATE}, ({default_rate_sql})),
                    {S.ServiceReviews.BILLING_AMOUNT} = COALESCE(
                        sr.{S.ServiceReviews.BILLING_AMOUNT},
                        COALESCE(({default_rate_sql}), 0) * COALESCE(NULLIF(sr.{S.ServiceReviews.WEIGHT_FACTOR}, 0), 1)
                    )
                FROM dbo.{S.ServiceReviews.TABLE} sr
                INNER JOIN dbo.{S.ProjectServices.TABLE} ps ON sr.{S.ServiceReviews.SERVICE_ID} = ps.{S.ProjectServices.SERVICE_ID}
                WHERE 
                    sr.{S.ServiceReviews.SOURCE_PHASE} IS NULL
                    OR sr.{S.ServiceReviews.BILLING_PHASE} IS NULL
                    OR sr.{S.ServiceReviews.BILLING_RATE} IS NULL
                    OR sr.{S.ServiceReviews.BILLING_AMOUNT} IS NULL
            """

            self.cursor.execute(update_sql)
            self.db.commit()
        except Exception as exc:
            print(f"Error initializing review billing defaults: {exc}")
            self.db.rollback()

    def _derive_default_billing_rate(self, service: Optional[Dict]) -> Optional[float]:
        """Compute a sensible default per-review billing rate from the project service."""
        if not service:
            return None

        def _to_decimal(value):
            if value is None or value == '':
                return None
            try:
                return Decimal(str(value))
            except (InvalidOperation, ValueError, TypeError):
                return None

        unit_type = (service.get('unit_type') or '').lower()
        unit_rate_dec = _to_decimal(service.get('unit_rate'))
        unit_qty_dec = _to_decimal(service.get('unit_qty'))
        lump_sum_dec = _to_decimal(service.get('lump_sum_fee'))
        agreed_fee_dec = _to_decimal(service.get('agreed_fee'))

        try:
            if unit_type == 'review':
                if unit_rate_dec is not None:
                    return float(unit_rate_dec)
                if unit_qty_dec and unit_qty_dec != 0 and agreed_fee_dec is not None:
                    return float(agreed_fee_dec / unit_qty_dec)

            if unit_type == 'lump_sum':
                if unit_qty_dec and unit_qty_dec != 0 and lump_sum_dec is not None:
                    return float(lump_sum_dec / unit_qty_dec)
                if lump_sum_dec is not None:
                    return float(lump_sum_dec)

            if unit_rate_dec is not None:
                return float(unit_rate_dec)

            if unit_qty_dec and unit_qty_dec != 0 and agreed_fee_dec is not None:
                return float(agreed_fee_dec / unit_qty_dec)

            if lump_sum_dec is not None:
                return float(lump_sum_dec)

            if agreed_fee_dec is not None:
                return float(agreed_fee_dec)
        except (InvalidOperation, ZeroDivisionError):
            return None

        return None


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

                actual_issued_at  DATETIME2 NULL,

                source_phase      NVARCHAR(200) NULL,

                billing_phase     NVARCHAR(200) NULL,

                billing_rate      DECIMAL(18,2) NULL,

                billing_amount    DECIMAL(18,2) NULL,

                regeneration_signature NVARCHAR(500) NULL

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


    def create_service_items_table(self):
        """Create the ServiceItems table for comprehensive service item tracking."""
        try:
            create_sql = """

            CREATE TABLE dbo.ServiceItems (

                item_id       INT IDENTITY(1,1) PRIMARY KEY,

                service_id    INT NOT NULL REFERENCES dbo.ProjectServices(service_id) ON DELETE CASCADE,

                item_type     NVARCHAR(50) NOT NULL,  -- 'review', 'audit', 'deliverable', 'milestone', etc.

                title         NVARCHAR(200) NOT NULL,

                description   NVARCHAR(MAX) NULL,

                planned_date  DATE NULL,

                due_date      DATE NULL,

                actual_date   DATE NULL,

                status        NVARCHAR(20) NOT NULL DEFAULT 'planned',  -- 'planned', 'in_progress', 'completed', 'overdue', 'cancelled'

                priority      NVARCHAR(20) NOT NULL DEFAULT 'medium',   -- 'low', 'medium', 'high', 'critical'

                assigned_to   NVARCHAR(100) NULL,

                invoice_reference NVARCHAR(200) NULL,  -- invoice number or shared folder link

                evidence_links NVARCHAR(MAX) NULL,  -- JSON array of links

                notes         NVARCHAR(MAX) NULL,

                created_at    DATETIME2 DEFAULT SYSDATETIME(),

                updated_at    DATETIME2 DEFAULT SYSDATETIME()

            );

            CREATE INDEX idx_service_items_service_id ON dbo.ServiceItems(service_id);

            CREATE INDEX idx_service_items_type ON dbo.ServiceItems(item_type);

            CREATE INDEX idx_service_items_status ON dbo.ServiceItems(status);

            CREATE INDEX idx_service_items_planned_date ON dbo.ServiceItems(planned_date);

            """

            self.cursor.execute(create_sql)

            self.db.commit()

            print("? ServiceItems table created successfully")

        except Exception as e:

            print(f"Error creating ServiceItems table: {e}")

            self.db.rollback()


    def load_template(self, template_name: str) -> Optional[Dict]:
        """Load a service template by name with enhanced fuzzy matching and error handling"""
        try:
            # Get the path to the templates directory
            template_file = os.path.join(os.path.dirname(__file__), 'templates', 'service_templates.json')
            if not os.path.exists(template_file):
                error_msg = f"Template file not found: {template_file}"
                print(f"❌ {error_msg}")
                return None

            # Load and parse the template file with better error handling
            try:
                with open(template_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except json.JSONDecodeError as e:
                print(f"❌ Invalid JSON in template file: {e}")
                return None
            except UnicodeDecodeError as e:
                print(f"❌ Encoding error in template file: {e}")
                return None

            templates = data.get('templates', [])
            if not templates:
                print(f"⚠️  No templates found in {template_file}")
                return None

            # Enhanced name normalization function
            def normalize_name(name: str) -> str:
                if not name:
                    return ""
                # Handle various dash types and clean whitespace
                normalized = name.replace('–', '-').replace('—', '-').replace('−', '-')
                # Remove extra whitespace and convert to lowercase for comparison
                return ' '.join(normalized.strip().lower().split())

            # Function to calculate similarity score
            def similarity_score(s1: str, s2: str) -> float:
                if not FUZZY_MATCHING_AVAILABLE:
                    return 1.0 if s1 == s2 else 0.0
                return SequenceMatcher(None, s1, s2).ratio()

            normalized_search = normalize_name(template_name)
            best_match = None
            best_score = 0.0
            match_info = []

            print(f"🔍 Searching for template: '{template_name}'")
            print(f"    Normalized search: '{normalized_search}'")

            # Search through all templates
            for template in templates:
                template_name_full = template.get('name', '')
                if not template_name_full:
                    continue

                # Try multiple matching strategies
                template_norm = normalize_name(template_name_full)
                template_base = template_norm.split(' (')[0].strip()  # Base name without parentheses
                template_sector = template.get('sector', '').lower()

                # Calculate scores for different matching approaches
                scores = {
                    'exact': 1.0 if template_name_full == template_name else 0.0,
                    'normalized': 1.0 if template_norm == normalized_search else 0.0,
                    'base': 1.0 if template_base == normalized_search else 0.0,
                    'fuzzy_full': similarity_score(normalized_search, template_norm),
                    'fuzzy_base': similarity_score(normalized_search, template_base),
                    'contains': 1.0 if normalized_search in template_norm or template_norm in normalized_search else 0.0
                }

                # Find the best score for this template
                max_score = max(scores.values())
                best_method = max(scores.keys(), key=lambda k: scores[k])

                match_info.append({
                    'template': template,
                    'name': template_name_full,
                    'score': max_score,
                    'method': best_method,
                    'sector': template_sector
                })

                # Update best match if this is better
                if max_score > best_score:
                    best_score = max_score
                    best_match = template

                print(f"    '{template_name_full}' -> score: {max_score:.3f} ({best_method})")

            # Sort matches by score for better reporting
            match_info.sort(key=lambda x: x['score'], reverse=True)

            # Determine if we found a good enough match
            threshold = 0.8  # Require 80% similarity for fuzzy matches
            exact_threshold = 1.0  # Require exact match for exact/normalized searches

            if best_score >= exact_threshold:
                # Exact or normalized match found
                print(f"✅ Found exact match: '{best_match['name']}' (score: {best_score:.3f})")
            elif best_score >= threshold and FUZZY_MATCHING_AVAILABLE:
                # Good fuzzy match found
                print(f"✅ Found fuzzy match: '{best_match['name']}' (score: {best_score:.3f})")
                print(f"    Did you mean '{best_match['name']}' instead of '{template_name}'?")
            else:
                # No good match found
                print(f"❌ No suitable match found for '{template_name}'")
                print(f"    Available templates:")
                for info in match_info[:5]:  # Show top 5 matches
                    print(f"      - {info['name']} ({info['sector']}) - similarity: {info['score']:.3f}")
                return None

            # Validate the template before returning
            if best_match:
                validation_errors = validate_template(best_match)
                if validation_errors:
                    print(f"❌ Template '{best_match['name']}' has validation errors:")
                    for error in validation_errors:
                        print(f"      - {error}")
                    return None

                print(f"✅ Template loaded and validated successfully")
                return best_match

            return None

        except Exception as e:
            print(f"❌ Unexpected error loading template '{template_name}': {e}")
            import traceback
            print(f"    Traceback: {traceback.format_exc()}")
            return None

    def get_available_templates(self) -> List[Dict]:
        """Get list of available service templates with comprehensive validation and error recovery"""
        try:
            # Get the path to the templates directory
            template_file = os.path.join(os.path.dirname(__file__), 'templates', 'service_templates.json')

            # Check if template file exists
            if not os.path.exists(template_file):
                print(f"❌ Template file not found: {template_file}")
                print(f"   📁 Creating template directory and default template file...")
                return self._create_default_template_file(template_file)

            # Validate file is not empty
            if os.path.getsize(template_file) == 0:
                print(f"❌ Template file is empty: {template_file}")
                print(f"   📁 Creating default template content...")
                return self._create_default_template_file(template_file)

            # Load and parse the template file with comprehensive error handling
            try:
                with open(template_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if not content:
                        print(f"❌ Template file contains no content")
                        return self._create_default_template_file(template_file)
                    
                    data = json.loads(content)
            except json.JSONDecodeError as e:
                print(f"❌ Invalid JSON in template file: {e}")
                print(f"   📍 Error at line {getattr(e, 'lineno', 'unknown')}, column {getattr(e, 'colno', 'unknown')}")
                print(f"   🔧 Attempting to backup corrupted file and create new one...")
                return self._handle_corrupted_template_file(template_file)
            except UnicodeDecodeError as e:
                print(f"❌ Encoding error in template file: {e}")
                print(f"   🔧 Attempting to fix encoding issue...")
                return self._handle_encoding_error(template_file)

            # Process template data using helper method
            return self._process_template_data(data)

        except Exception as e:
            print(f"❌ Unexpected error getting available templates: {e}")
            import traceback
            print(f"    Traceback: {traceback.format_exc()}")
            return []
    
    def _create_default_template_file(self, template_file: str) -> List[Dict]:
        """Create a default template file with basic templates"""
        try:
            # Ensure templates directory exists
            template_dir = os.path.dirname(template_file)
            os.makedirs(template_dir, exist_ok=True)
            
            # Create default template structure
            default_templates = {
                "templates": [
                    {
                        "name": "Standard Education Template",
                        "sector": "Education",
                        "notes": "Default template for education sector projects",
                        "items": [
                            {
                                "phase": "Phase 1 - Design Development",
                                "service_code": "DD_REV",
                                "service_name": "Design Development Reviews",
                                "unit_type": "review",
                                "default_units": 4,
                                "unit_rate": 2500,
                                "bill_rule": "per_unit_complete",
                                "notes": "Weekly design development review cycles"
                            },
                            {
                                "phase": "Phase 2 - Construction Documentation",
                                "service_code": "CD_REV",
                                "service_name": "Construction Documentation Reviews",
                                "unit_type": "review",
                                "default_units": 6,
                                "unit_rate": 3000,
                                "bill_rule": "per_unit_complete",
                                "notes": "Bi-weekly construction documentation reviews"
                            },
                            {
                                "phase": "Phase 3 - Project Completion",
                                "service_code": "PC_REP",
                                "service_name": "Project Completion Report",
                                "unit_type": "lump_sum",
                                "default_units": 1,
                                "lump_sum_fee": 5000,
                                "bill_rule": "on_completion",
                                "notes": "Final project completion documentation"
                            }
                        ]
                    }
                ]
            }
            
            # Write default template file
            with open(template_file, 'w', encoding='utf-8') as f:
                json.dump(default_templates, f, indent=2)
            
            print(f"✅ Created default template file: {template_file}")
            print(f"   📋 Added 1 default template with 3 service items")
            
            # Return the processed templates
            return self._process_template_data(default_templates)
            
        except Exception as e:
            print(f"❌ Failed to create default template file: {e}")
            return []
    
    def _handle_corrupted_template_file(self, template_file: str) -> List[Dict]:
        """Handle corrupted template file by backing up and creating new one"""
        try:
            import datetime
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = f"{template_file}.corrupt_{timestamp}.bak"
            
            # Backup corrupted file
            import shutil
            shutil.copy2(template_file, backup_file)
            print(f"✅ Backed up corrupted file to: {backup_file}")
            
            # Create new default template file
            return self._create_default_template_file(template_file)
            
        except Exception as e:
            print(f"❌ Failed to handle corrupted template file: {e}")
            return []
    
    def _handle_encoding_error(self, template_file: str) -> List[Dict]:
        """Handle encoding errors by trying different encodings"""
        encodings = ['utf-8', 'latin-1', 'cp1252', 'ascii']
        
        for encoding in encodings:
            try:
                print(f"   🔄 Trying encoding: {encoding}")
                with open(template_file, 'r', encoding=encoding) as f:
                    content = f.read()
                    data = json.loads(content)
                    
                print(f"✅ Successfully read file with {encoding} encoding")
                # Re-save with UTF-8 encoding
                with open(template_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                print(f"✅ Re-saved file with UTF-8 encoding")
                
                return self._process_template_data(data)
                
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue
        
        print(f"❌ Failed to read file with any encoding, creating new default file")
        return self._create_default_template_file(template_file)
    
    def _process_template_data(self, data: Dict) -> List[Dict]:
        """Process template data and return formatted template list"""
        # Validate the file structure
        if not isinstance(data, dict) or 'templates' not in data:
            print(f"❌ Invalid template file structure - missing 'templates' key")
            return []

        templates_data = data.get('templates', [])
        if not isinstance(templates_data, list):
            print(f"❌ Invalid template file structure - 'templates' must be a list")
            return []

        # Return enhanced template info with validation status
        templates = []
        for i, template in enumerate(templates_data):
            try:
                # Basic template validation
                if not isinstance(template, dict):
                    print(f"⚠️  Skipping invalid template at index {i} - not a dictionary")
                    continue

                name = template.get('name', f'Unnamed Template {i+1}')
                sector = template.get('sector', 'Unknown')
                description = template.get('notes', '')
                items = template.get('items', [])

                # Calculate template summary
                total_items = len(items)
                lump_sum_items = sum(1 for item in items if item.get('unit_type') == 'lump_sum')
                review_items = sum(1 for item in items if item.get('unit_type') == 'review')
                total_reviews = sum(item.get('default_units', 0) for item in items if item.get('unit_type') == 'review')
                
                # Calculate estimated value
                estimated_value = 0
                for item in items:
                    if item.get('unit_type') == 'lump_sum':
                        estimated_value += item.get('lump_sum_fee', 0)
                    else:
                        estimated_value += (item.get('default_units', 0) * item.get('unit_rate', 0))

                # Validate template data
                validation_errors = validate_template(template)
                is_valid = len(validation_errors) == 0

                template_info = {
                    'name': name,
                    'sector': sector,
                    'description': description,
                    'total_items': total_items,
                    'lump_sum_items': lump_sum_items,
                    'review_items': review_items,
                    'total_reviews': total_reviews,
                    'estimated_value': estimated_value,
                    'is_valid': is_valid,
                    'validation_errors': validation_errors
                }
                
                templates.append(template_info)

            except Exception as e:
                print(f"⚠️  Error processing template at index {i}: {e}")
                continue

        print(f"✅ Loaded {len(templates)} templates successfully")
        
        # Log summary
        valid_count = sum(1 for t in templates if t['is_valid'])
        invalid_count = len(templates) - valid_count
        if invalid_count > 0:
            print(f"⚠️  Warning: {invalid_count} templates have validation errors")
        
        # Additional validation check
        if len(templates) == 0:
            print(f"⚠️  No valid templates found - this may affect template functionality")
            print(f"   📝 Consider adding templates to the template file or using 'Save As Template' feature")

        return templates

    def get_available_phases(self) -> List[str]:
        """Get list of available phases from service templates"""
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

            # Extract unique phases
            phases = set()
            for template in data.get('templates', []):
                for item in template.get('items', []):
                    phase = item.get('phase', '').strip()
                    if phase:
                        phases.add(phase)

            return sorted(list(phases))

        except Exception as e:
            print(f"Error getting available phases: {e}")
            return []

    def get_available_service_codes(self) -> List[str]:
        """Get list of available service codes from service templates"""
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

            # Extract unique service codes
            service_codes = set()
            for template in data.get('templates', []):
                for item in template.get('items', []):
                    code = item.get('service_code', '').strip()
                    if code:
                        service_codes.add(code)

            return sorted(list(service_codes))

        except Exception as e:
            print(f"Error getting available service codes: {e}")
            return []

    def save_template(self, template_name: str, sector: str, notes: str, items: List[Dict], overwrite: bool = False) -> bool:
        """Save a new template or overwrite existing template"""
        try:
            import json
            import os

            # Get the path to the templates directory
            template_file = os.path.join(os.path.dirname(__file__), 'templates', 'service_templates.json')

            # Load existing templates
            if os.path.exists(template_file):
                with open(template_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                data = {"templates": []}

            # Create new template
            new_template = {
                "name": template_name,
                "sector": sector,
                "notes": notes,
                "items": items
            }

            # Check if template already exists
            existing_index = None
            for i, template in enumerate(data.get('templates', [])):
                if template.get('name') == template_name:
                    existing_index = i
                    break

            if existing_index is not None:
                if overwrite:
                    # Overwrite existing template
                    data['templates'][existing_index] = new_template
                    print(f"✅ Overwrote existing template: {template_name}")
                else:
                    print(f"❌ Template '{template_name}' already exists. Use overwrite=True to replace it.")
                    return False
            else:
                # Add new template
                data['templates'].append(new_template)
                print(f"✅ Created new template: {template_name}")

            # Save back to file
            with open(template_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            return True

        except Exception as e:
            print(f"Error saving template: {e}")
            return False



    def apply_template(
        self,
        project_id: int,
        template_name: str,
        overrides: Dict = None,
        replace_existing: bool = False,
        skip_existing_duplicates: bool = False,
    ) -> Dict[str, Any]:
        """Apply service template to a project with duplicate handling and transactional safety."""
        overrides = overrides or {}

        template = self.load_template(template_name)
        if not template:
            raise ValueError(f"Template '{template_name}' not found")

        items = template.get('items') or []
        if not isinstance(items, list):
            raise ValueError(f"Template '{template_name}' is missing service items")

        result: Dict[str, Any] = {
            'template_name': template_name,
            'created': [],
            'skipped': [],
            'duplicates': [],
            'existing_services': 0,
            'replaced_services': 0,
        }

        existing_services = self.get_project_services(project_id)
        result['existing_services'] = len(existing_services)
        existing_lookup = {}
        for svc in existing_services:
            code = (svc.get('service_code') or '').strip().upper()
            phase = (svc.get('phase') or '').strip().lower()
            if code:
                existing_lookup[(code, phase)] = svc

        duplicate_keys = set()

        if existing_services and replace_existing:
            try:
                self.delete_all_project_reviews(project_id)
            except Exception:
                pass
            removed = self.clear_all_project_services(project_id)
            result['replaced_services'] = removed
            existing_lookup = {}
        else:
            for item in items:
                key = (
                    (item.get('service_code') or '').strip().upper(),
                    (item.get('phase') or '').strip().lower(),
                )
                if key[0] and key in existing_lookup and key not in duplicate_keys:
                    duplicate_info = {
                        'service_code': item.get('service_code'),
                        'service_name': item.get('service_name'),
                        'phase': item.get('phase'),
                    }
                    result['duplicates'].append(duplicate_info)
                    duplicate_keys.add(key)

            if result['duplicates'] and not skip_existing_duplicates:
                duplicate_labels = [
                    f"{dup.get('service_code')} ({dup.get('phase') or 'no phase'})"
                    for dup in result['duplicates']
                ]
                raise ValueError(
                    "Template contains services that already exist on this project: "
                    + ", ".join(duplicate_labels)
                    + ". Select 'replace existing services' or enable duplicate skipping to continue."
                )

        created_services: List[Dict] = []
        skipped_items: List[Dict] = []
        existing_keys = set(existing_lookup.keys())
        now = datetime.now()

        def _as_decimal(raw_value, fallback, label: str) -> Decimal:
            candidate = raw_value if raw_value is not None else fallback
            try:
                return Decimal(str(candidate))
            except (InvalidOperation, TypeError):
                raise ValueError(
                    f"Invalid {label} value '{candidate}' for service {item.get('service_code') or ''}"
                )

        try:
            for item in items:
                service_code = (item.get('service_code') or '').strip()
                phase = (item.get('phase') or '').strip()

                if not service_code:
                    skipped_items.append({
                        'service_code': service_code,
                        'service_name': item.get('service_name'),
                        'phase': phase,
                        'reason': 'missing_service_code',
                    })
                    continue

                key = (service_code.upper(), phase.lower())

                if key in existing_keys:
                    duplicate_detail = {
                        'service_code': service_code,
                        'service_name': item.get('service_name'),
                        'phase': phase,
                    }
                    if key not in duplicate_keys:
                        result['duplicates'].append(duplicate_detail)
                        duplicate_keys.add(key)

                    skipped_items.append({**duplicate_detail, 'reason': 'duplicate'})
                    if not skip_existing_duplicates:
                        raise ValueError(
                            f"Service '{service_code}' in phase '{phase or 'unspecified'}' already exists on project {project_id}"
                        )
                    continue

                unit_qty_dec = _as_decimal(
                    overrides.get(f"{service_code}_units"), item.get('default_units', 1), 'unit quantity'
                )
                unit_rate_dec = _as_decimal(
                    overrides.get(f"{service_code}_rate"), item.get('unit_rate', 0), 'unit rate'
                )
                lump_sum_dec = _as_decimal(
                    overrides.get(f"{service_code}_lump"), item.get('lump_sum_fee', 0), 'lump sum fee'
                )

                if (item.get('unit_type') or '').lower() == 'lump_sum':
                    agreed_fee_dec = lump_sum_dec
                else:
                    agreed_fee_dec = unit_qty_dec * unit_rate_dec

                service_data = {
                    'project_id': project_id,
                    'phase': phase,
                    'service_code': service_code,
                    'service_name': item.get('service_name'),
                    'unit_type': item.get('unit_type'),
                    'unit_qty': float(unit_qty_dec),
                    'unit_rate': float(unit_rate_dec),
                    'lump_sum_fee': float(lump_sum_dec),
                    'agreed_fee': float(agreed_fee_dec),
                    'bill_rule': item.get('bill_rule'),
                    'notes': item.get('notes', ''),
                }

                validation_errors = validate_service_data(service_data)
                if validation_errors:
                    skipped_items.append({
                        'service_code': service_code,
                        'service_name': item.get('service_name'),
                        'phase': phase,
                        'reason': 'validation_error',
                        'details': [str(err) for err in validation_errors],
                    })
                    continue

                service_id = self.create_project_service(service_data, commit=False)
                if not service_id:
                    raise ValueError(
                        f"Failed to create service '{service_code}' for project {project_id}"
                    )

                service_data['service_id'] = service_id

                schedule_start = now.strftime('%Y-%m-%d')
                qty_for_schedule = float(unit_qty_dec) if unit_qty_dec > 0 else 1.0
                duration_multiplier = max(1, math.ceil(qty_for_schedule))

                schedule_end = (now + timedelta(days=30 * duration_multiplier)).strftime('%Y-%m-%d')

                self.upsert_service_schedule(
                    service_id,
                    schedule_start,
                    schedule_end,
                    item.get('frequency', 'weekly'),
                    commit=False,
                )

                if (item.get('unit_type') or '').lower() == 'review':
                    self.rebuild_service_reviews(service_id, commit=False)

                blueprint_items = item.get('service_items') or []
                if blueprint_items:
                    self._create_service_items_from_blueprint(
                        service_id,
                        blueprint_items,
                        schedule_start,
                        commit=False,
                    )

                created_services.append(service_data)
                existing_keys.add(key)

            self.db.commit()
        except Exception:
            try:
                self.db.rollback()
            except Exception:
                pass
            raise

        result['created'] = created_services
        result['skipped'] = skipped_items
        return result


    def build_template_from_project(
        self,
        project_id: int,
        include_reviews: bool = True,
        include_items: bool = True,
    ) -> List[Dict]:
        """Build template items from an existing project configuration."""
        services = self.get_project_services(project_id)
        return self._build_template_items(services, include_reviews, include_items)

    def _build_template_items(
        self,
        services: List[Dict],
        include_reviews: bool = True,
        include_items: bool = True,
    ) -> List[Dict]:
        template_items: List[Dict] = []

        for service in services:
            service_id = service.get('service_id')
            if not service_id:
                continue

            unit_type = (service.get('unit_type') or 'lump_sum').lower()
            unit_qty = service.get('unit_qty') if service.get('unit_qty') is not None else 0
            default_units = float(unit_qty or 0)
            if unit_type == 'lump_sum' and default_units <= 0:
                default_units = 1.0

            template_item: Dict[str, Any] = {
                'phase': service.get('phase') or '',
                'service_code': service.get('service_code') or '',
                'service_name': service.get('service_name') or '',
                'unit_type': unit_type,
                'default_units': default_units,
                'unit_rate': float(service.get('unit_rate') or 0),
                'lump_sum_fee': float(service.get('lump_sum_fee') or 0),
                'bill_rule': service.get('bill_rule') or 'on_completion',
                'notes': service.get('notes') or '',
            }

            schedule_info = self.get_service_by_id(service_id) or {}
            schedule_start_raw = schedule_info.get('schedule_start')
            schedule_freq = schedule_info.get('schedule_frequency')

            if schedule_freq:
                template_item['frequency'] = schedule_freq

            schedule_start_dt: Optional[datetime] = None
            if schedule_start_raw:
                if isinstance(schedule_start_raw, datetime):
                    schedule_start_dt = schedule_start_raw
                elif isinstance(schedule_start_raw, str):
                    try:
                        schedule_start_dt = datetime.fromisoformat(schedule_start_raw)
                    except ValueError:
                        schedule_start_dt = None

            if include_reviews:
                review_blueprint = self._build_review_blueprint(service_id)
                if review_blueprint:
                    template_item['review_blueprint'] = review_blueprint

            if include_items:
                service_items = self._build_service_item_blueprint(service_id, schedule_start_dt)
                if service_items:
                    template_item['service_items'] = service_items

            template_items.append(template_item)

        return template_items

    def _build_review_blueprint(self, service_id: int) -> Optional[Dict]:
        """Capture representative review blueprint data for a service."""
        try:
            query = f"""
                SELECT {S.ServiceReviews.CYCLE_NO},
                       {S.ServiceReviews.DISCIPLINES},
                       {S.ServiceReviews.DELIVERABLES},
                       {S.ServiceReviews.WEIGHT_FACTOR}
                FROM {S.ServiceReviews.TABLE}
                WHERE {S.ServiceReviews.SERVICE_ID} = ?
                ORDER BY {S.ServiceReviews.CYCLE_NO}
            """
            self.cursor.execute(query, (service_id,))
            rows = self.cursor.fetchall()
            if not rows:
                return None

            first_cycle = rows[0]
            total_cycles = len(rows)
            weight_factor = first_cycle[3] if len(first_cycle) > 3 else 1.0

            return {
                'total_cycles': total_cycles,
                'disciplines': first_cycle[1] or '',
                'deliverables': first_cycle[2] or '',
                'weight_factor': float(weight_factor or 1.0),
            }
        except Exception as exc:
            print(f"⚠️  Unable to capture review blueprint for service {service_id}: {exc}")
            return None

    def _build_service_item_blueprint(
        self,
        service_id: int,
        schedule_start: Optional[datetime],
    ) -> List[Dict]:
        """Capture service item blueprint data for reuse."""
        blueprint: List[Dict] = []
        try:
            query = f"""
                SELECT {S.ServiceItems.ITEM_TYPE},
                       {S.ServiceItems.TITLE},
                       {S.ServiceItems.DESCRIPTION},
                       {S.ServiceItems.PRIORITY},
                       {S.ServiceItems.STATUS},
                       {S.ServiceItems.PLANNED_DATE},
                       {S.ServiceItems.DUE_DATE},
                       {S.ServiceItems.NOTES}
                FROM {S.ServiceItems.TABLE}
                WHERE {S.ServiceItems.SERVICE_ID} = ?
                ORDER BY {S.ServiceItems.PLANNED_DATE}
            """
            self.cursor.execute(query, (service_id,))
            rows = self.cursor.fetchall()

            for row in rows:
                planned_dt = row[5]
                due_dt = row[6]

                planned_offset = None
                due_offset = None

                if isinstance(planned_dt, str):
                    try:
                        planned_dt = datetime.fromisoformat(planned_dt)
                    except ValueError:
                        planned_dt = None
                if isinstance(due_dt, str):
                    try:
                        due_dt = datetime.fromisoformat(due_dt)
                    except ValueError:
                        due_dt = None

                if schedule_start and isinstance(planned_dt, datetime):
                    planned_offset = (planned_dt.date() - schedule_start.date()).days
                if schedule_start and isinstance(due_dt, datetime):
                    due_offset = (due_dt.date() - schedule_start.date()).days

                blueprint.append({
                    'item_type': row[0] or 'other',
                    'title': row[1] or 'Untitled Item',
                    'description': row[2] or '',
                    'priority': row[3] or 'medium',
                    'status': row[4] or 'planned',
                    'planned_offset_days': planned_offset,
                    'due_offset_days': due_offset,
                    'notes': row[7] or '',
                })

        except Exception as exc:
            print(f"⚠️  Unable to capture service item blueprint for service {service_id}: {exc}")

        return blueprint

    def _create_service_items_from_blueprint(
        self,
        service_id: int,
        blueprint_items: List[Dict],
        schedule_start: Optional[str],
        commit: bool = False,
    ) -> None:
        """Create service items based on a saved blueprint."""
        if not blueprint_items:
            return

        try:
            base_dt: Optional[datetime] = None
            if schedule_start:
                try:
                    base_dt = datetime.fromisoformat(schedule_start)
                except ValueError:
                    base_dt = None
            if base_dt is None:
                base_dt = datetime.now()

            for item in blueprint_items:
                planned_offset = item.get('planned_offset_days')
                due_offset = item.get('due_offset_days')

                planned_dt = base_dt + timedelta(days=int(planned_offset)) if planned_offset is not None else base_dt
                due_dt = (
                    base_dt + timedelta(days=int(due_offset))
                    if due_offset is not None
                    else None
                )

                columns = [
                    S.ServiceItems.SERVICE_ID,
                    S.ServiceItems.ITEM_TYPE,
                    S.ServiceItems.TITLE,
                    S.ServiceItems.PLANNED_DATE,
                    S.ServiceItems.STATUS,
                    S.ServiceItems.PRIORITY,
                    S.ServiceItems.CREATED_AT,
                    S.ServiceItems.UPDATED_AT,
                ]
                values = [
                    service_id,
                    item.get('item_type') or 'other',
                    item.get('title') or 'Untitled Item',
                    planned_dt.strftime('%Y-%m-%d'),
                    (item.get('status') or 'planned'),
                    (item.get('priority') or 'medium'),
                    datetime.now(),
                    datetime.now(),
                ]
                placeholders = ['?'] * len(values)

                optional_pairs = [
                    (S.ServiceItems.DESCRIPTION, item.get('description')),
                    (S.ServiceItems.NOTES, item.get('notes')),
                    (S.ServiceItems.DUE_DATE, due_dt.strftime('%Y-%m-%d') if due_dt else None),
                ]

                for column, value in optional_pairs:
                    if value:
                        columns.append(column)
                        values.append(value)
                        placeholders.append('?')

                query = f"""
                    INSERT INTO {S.ServiceItems.TABLE} ({', '.join(columns)})
                    VALUES ({', '.join(placeholders)})
                """
                self.cursor.execute(query, values)

            if commit:
                self.db.commit()

        except Exception as exc:
            print(f"⚠️  Unable to create service items for service {service_id}: {exc}")

    def create_project_service(self, service_data: Dict, commit: bool = True) -> int:

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

        

        try:
            self.cursor.execute(query, params)
        except pyodbc.Error as exc:
            print(f"⚠️  Database error creating service '{service_data.get('service_code')}' for project {service_data.get('project_id')}: {exc}")
            raise

        self.cursor.execute("SELECT SCOPE_IDENTITY()")
        row = self.cursor.fetchone()

        service_id = 0
        if row and row[0] is not None:
            try:
                service_id = int(Decimal(str(row[0])))
            except (InvalidOperation, ValueError, TypeError):
                try:
                    service_id = int(row[0])
                except (ValueError, TypeError):
                    service_id = 0

        if not service_id:
            self.cursor.execute(
                """
                SELECT TOP 1 service_id
                FROM ProjectServices
                WHERE project_id = ? AND service_code = ?
                ORDER BY service_id DESC
                """,
                (service_data['project_id'], service_data['service_code']),
            )
            fallback_row = self.cursor.fetchone()
            if fallback_row and fallback_row[0] is not None:
                try:
                    service_id = int(fallback_row[0])
                except (ValueError, TypeError):
                    service_id = 0

        if not service_id:
            raise ValueError(f"Failed to retrieve service ID for project {service_data.get('project_id')} and service {service_data.get('service_code')}")

        if commit:
            self.db.commit()
        return service_id

    

    def generate_review_cycles(self, service_id: int, unit_qty: int,
                             start_date: datetime, end_date: datetime,
                             cadence: str = 'weekly', disciplines: str = 'All',
                             commit: bool = True) -> List[Dict]:
        """Fixed review cycle generation with consistent date handling"""
        try:
            if unit_qty <= 0:
                print(f"⚠️  Invalid unit quantity: {unit_qty}")
                return []

            freq_key = (cadence or 'weekly').lower().replace('_', '-')
            interval_lookup = {
                'one-off': 0,
                'weekly': 7,
                'bi-weekly': 14,
                'biweekly': 14,
                'fortnightly': 14,
                'monthly': 30
            }
            
            interval_days = interval_lookup.get(freq_key)
            dates: List[datetime] = []
            
            print(f"🗓️  Generating {unit_qty} {freq_key} reviews from {start_date} to {end_date}")
            
            if freq_key == 'one-off':
                # One-off: single review at start date
                dates = [start_date]
                print(f"   → One-off review scheduled for {start_date}")
                
            elif interval_days and interval_days > 0:
                # Fixed: Generate exactly unit_qty reviews with proper spacing
                for i in range(unit_qty):
                    review_date = start_date + timedelta(days=i * interval_days)
                    
                    # Only cap if review would be significantly beyond end date
                    if review_date > end_date + timedelta(days=7):  # 1 week grace period
                        print(f"   ⚠️  Review {i+1} would be {review_date} (beyond {end_date}), capping")
                        review_date = end_date
                    
                    dates.append(review_date)
                    
            else:
                # Custom frequency: distribute evenly across date range
                total_days = max(1, (end_date - start_date).days)
                if unit_qty == 1:
                    dates = [start_date]
                else:
                    interval = total_days / (unit_qty - 1)
                    dates = [start_date + timedelta(days=int(round(i * interval))) 
                            for i in range(unit_qty)]

            
            # Create cycle records
            cycles_created: List[Dict] = []
            for i, planned_date in enumerate(dates):
                # Keep dates within requested window with grace period
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

                review_id = self.create_service_review(cycle_data, commit=commit)
                cycle_data['review_id'] = review_id
                cycles_created.append(cycle_data)
                print(f"   ✅ Cycle {i+1}: {planned_date}")
            
            print(f"✅ Generated {len(cycles_created)} review cycles")
            return cycles_created

        except Exception as e:
            print(f"❌ Error generating review cycles: {e}")
            return []

    

    def create_service_review(self, review_data: Dict, commit: bool = True) -> int:

        """Create a service review cycle with billing metadata defaults"""

        try:

            service_id = review_data['service_id']
            weight_factor = review_data.get('weight_factor', 1.0) or 1.0

            service_defaults = self.get_service_by_id(service_id)
            default_phase = service_defaults.get('phase') if service_defaults else None
            default_rate = self._derive_default_billing_rate(service_defaults) if service_defaults else None

            source_phase = review_data.get('source_phase') or default_phase
            billing_phase = review_data.get('billing_phase') or source_phase or default_phase

            billing_rate = review_data.get('billing_rate')
            if billing_rate is None:
                billing_rate = default_rate
            if billing_rate is None:
                billing_rate = 0.0

            billing_amount = review_data.get('billing_amount')
            if billing_amount is None:
                try:
                    billing_amount = float(Decimal(str(billing_rate or 0)) * Decimal(str(weight_factor or 1)))
                except (InvalidOperation, ValueError, TypeError):
                    billing_amount = float(billing_rate or 0) * float(weight_factor or 1)

            # Get the regeneration signature for this service
            regeneration_signature = self.get_service_regeneration_signature(service_id)

            query = """

            INSERT INTO ServiceReviews (

                service_id, cycle_no, planned_date, due_date, disciplines,

                deliverables, status, weight_factor, evidence_links,

                invoice_reference, source_phase, billing_phase, billing_rate, billing_amount,

                regeneration_signature

            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);

            """

            status = review_data.get('status') or 'planned'

            params = (

                service_id,

                review_data['cycle_no'],

                review_data['planned_date'],

                review_data.get('due_date'),

                review_data.get('disciplines'),

                review_data.get('deliverables'),

                status,

                weight_factor,

                review_data.get('evidence_links'),

                review_data.get('invoice_reference'),

                source_phase,

                billing_phase,

                billing_rate,

                billing_amount,

                regeneration_signature

            )

            self.cursor.execute(query, params)

            # Get the last inserted ID
            self.cursor.execute("SELECT SCOPE_IDENTITY()")

            review_row = self.cursor.fetchone()
            review_id = int(review_row[0]) if review_row and review_row[0] is not None else 0

            if commit:
                self.db.commit()

            return review_id

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

    def reschedule_adjacent_reviews(
        self,
        review_id: int,
        anchor_date: Optional[date] = None,
        include_previous: bool = True,
        include_following: bool = True,
        auto_commit: bool = True,
    ) -> Dict[str, Any]:
        """
        Realign neighbouring reviews to maintain cadence when one review date changes.

        Args:
            review_id: The review that was manually adjusted.
            anchor_date: New planned date to anchor the series (defaults to stored value).
            include_previous: Whether to adjust earlier pending reviews.
            include_following: Whether to adjust later reviews.
            auto_commit: Commit changes automatically if True.

        Returns:
            Dict with counts of updated records and the cadence that was applied.
        """
        results = {
            'updated_forward': 0,
            'updated_previous': 0,
            'interval_days': None,
        }

        if not include_previous and not include_following:
            return results

        try:
            # Fetch anchor review details
            self.cursor.execute(
                f"""
                SELECT
                    {S.ServiceReviews.SERVICE_ID},
                    {S.ServiceReviews.CYCLE_NO},
                    {S.ServiceReviews.PLANNED_DATE},
                    {S.ServiceReviews.STATUS}
                FROM {S.ServiceReviews.TABLE}
                WHERE {S.ServiceReviews.REVIEW_ID} = ?
                """,
                (review_id,),
            )
            row = self.cursor.fetchone()
            if not row:
                print(f"[reviews] Review {review_id} not found for rescheduling")
                return results

            service_id, cycle_no, stored_planned, _ = row
            base_date = self._coerce_to_date(anchor_date or stored_planned)
            if not base_date:
                print(f"[reviews] Unable to determine anchor date for review {review_id}")
                return results

            # Resolve cadence
            self.cursor.execute(
                f"""
                SELECT {S.ServiceScheduleSettings.FREQUENCY}
                FROM {S.ServiceScheduleSettings.TABLE}
                WHERE {S.ServiceScheduleSettings.SERVICE_ID} = ?
                """,
                (service_id,),
            )
            freq_row = self.cursor.fetchone()
            interval_days = self._map_frequency_to_days(freq_row[0] if freq_row else None)
            if not interval_days:
                interval_days = self._infer_interval_days_from_reviews(service_id, exclude_review_id=review_id)
            if not interval_days:
                # Default to weekly if cadence cannot be determined
                interval_days = 7

            results['interval_days'] = interval_days
            cadence_delta = timedelta(days=interval_days)

            # Adjust later reviews
            if include_following:
                self.cursor.execute(
                    f"""
                    SELECT
                        {S.ServiceReviews.REVIEW_ID},
                        {S.ServiceReviews.CYCLE_NO},
                        {S.ServiceReviews.PLANNED_DATE},
                        {S.ServiceReviews.STATUS}
                    FROM {S.ServiceReviews.TABLE}
                    WHERE {S.ServiceReviews.SERVICE_ID} = ?
                      AND {S.ServiceReviews.CYCLE_NO} > ?
                    ORDER BY {S.ServiceReviews.CYCLE_NO}
                    """,
                    (service_id, cycle_no),
                )
                reference_date = base_date
                for next_review_id, _, planned_value, status_value in self.cursor.fetchall():
                    planned_date = self._coerce_to_date(planned_value)
                    status_key = (status_value or 'planned').lower()
                    if status_key not in self.ADJUSTABLE_STATUSES:
                        reference_date = planned_date or reference_date
                        continue

                    expected_date = reference_date + cadence_delta
                    if planned_date == expected_date:
                        reference_date = planned_date
                        continue

                    date_str = expected_date.strftime('%Y-%m-%d')
                    self.cursor.execute(
                        f"""
                        UPDATE {S.ServiceReviews.TABLE}
                        SET {S.ServiceReviews.PLANNED_DATE} = ?,
                            {S.ServiceReviews.DUE_DATE} = ?
                        WHERE {S.ServiceReviews.REVIEW_ID} = ?
                        """,
                        (date_str, date_str, next_review_id),
                    )
                    if self.cursor.rowcount:
                        results['updated_forward'] += 1
                    reference_date = expected_date

            # Adjust earlier reviews
            if include_previous:
                self.cursor.execute(
                    f"""
                    SELECT
                        {S.ServiceReviews.REVIEW_ID},
                        {S.ServiceReviews.CYCLE_NO},
                        {S.ServiceReviews.PLANNED_DATE},
                        {S.ServiceReviews.STATUS}
                    FROM {S.ServiceReviews.TABLE}
                    WHERE {S.ServiceReviews.SERVICE_ID} = ?
                      AND {S.ServiceReviews.CYCLE_NO} < ?
                    ORDER BY {S.ServiceReviews.CYCLE_NO} DESC
                    """,
                    (service_id, cycle_no),
                )
                reference_date = base_date
                for prev_review_id, _, planned_value, status_value in self.cursor.fetchall():
                    planned_date = self._coerce_to_date(planned_value)
                    status_key = (status_value or 'planned').lower()
                    if status_key not in self.ADJUSTABLE_STATUSES:
                        reference_date = planned_date or reference_date
                        continue

                    expected_date = reference_date - cadence_delta
                    if planned_date == expected_date:
                        reference_date = planned_date
                        continue

                    date_str = expected_date.strftime('%Y-%m-%d')
                    self.cursor.execute(
                        f"""
                        UPDATE {S.ServiceReviews.TABLE}
                        SET {S.ServiceReviews.PLANNED_DATE} = ?,
                            {S.ServiceReviews.DUE_DATE} = ?
                        WHERE {S.ServiceReviews.REVIEW_ID} = ?
                        """,
                        (date_str, date_str, prev_review_id),
                    )
                    if self.cursor.rowcount:
                        results['updated_previous'] += 1
                    reference_date = expected_date

            if auto_commit:
                self.db.commit()

            print(
                f"[reviews] Rescheduled service {service_id}: "
                f"{results['updated_previous']} previous, {results['updated_forward']} upcoming "
                f"(interval {interval_days} days)"
            )
            return results

        except Exception as exc:
            if auto_commit:
                try:
                    self.db.rollback()
                except Exception:
                    pass
            results['error'] = str(exc)
            print(f"[reviews] Error rescheduling reviews for {review_id}: {exc}")
            return results

    def _coerce_to_date(self, value: Any) -> Optional[date]:
        """Convert supported date representations to a date instance."""
        if value is None:
            return None
        if isinstance(value, date) and not isinstance(value, datetime):
            return value
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, str):
            text = value.strip()
            if not text:
                return None
            try:
                return datetime.fromisoformat(text).date()
            except ValueError:
                try:
                    return datetime.strptime(text[:10], '%Y-%m-%d').date()
                except ValueError:
                    return None
        return None

    def _map_frequency_to_days(self, frequency_value: Optional[Any]) -> Optional[int]:
        """Map stored frequency values to a number of days."""
        if frequency_value is None:
            return None

        if isinstance(frequency_value, (int, float)):
            return int(frequency_value)

        frequency_str = str(frequency_value).strip()
        if not frequency_str:
            return None

        # Support direct numeric strings like "14"
        try:
            numeric = int(float(frequency_str))
            if numeric > 0:
                return numeric
        except ValueError:
            pass

        normalized = frequency_str.lower().replace('_', '-')
        lookup = {
            'one-off': 0,
            'weekly': 7,
            'week': 7,
            'bi-weekly': 14,
            'biweekly': 14,
            'fortnightly': 14,
            'fortnight': 14,
            'two-weekly': 14,
            'monthly': 30,
            'quarterly': 90,
        }
        return lookup.get(normalized)

    def _infer_interval_days_from_reviews(
        self,
        service_id: int,
        exclude_review_id: Optional[int] = None,
    ) -> Optional[int]:
        """Infer cadence from existing review spacing when frequency metadata is missing."""
        try:
            params: List[Any] = [service_id]
            query = f"""
                SELECT {S.ServiceReviews.PLANNED_DATE}
                FROM {S.ServiceReviews.TABLE}
                WHERE {S.ServiceReviews.SERVICE_ID} = ?
            """
            if exclude_review_id:
                query += f" AND {S.ServiceReviews.REVIEW_ID} <> ?"
                params.append(exclude_review_id)
            query += f" ORDER BY {S.ServiceReviews.PLANNED_DATE}"

            self.cursor.execute(query, tuple(params))
            dates = [
                self._coerce_to_date(row[0])
                for row in self.cursor.fetchall()
                if row and row[0]
            ]

            diffs = []
            previous_date = None
            for current_date in dates:
                if not current_date:
                    continue
                if previous_date:
                    gap = (current_date - previous_date).days
                    if gap > 0:
                        diffs.append(gap)
                previous_date = current_date

            if diffs:
                return Counter(diffs).most_common(1)[0][0]

        except Exception as exc:
            print(f"[reviews] Unable to infer cadence for service {service_id}: {exc}")

        return None

    

    def update_review_status_to(self, review_id: int, new_status: str, evidence_link: str = None, is_manual_override: bool = True) -> bool:
        """Update review status to any valid status with optional evidence link
        
        Args:
            review_id: Review to update
            new_status: New status value
            evidence_link: Optional evidence URL
            is_manual_override: If True, marks this as a manual status change that won't be auto-updated
        """
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
            
            # Build query based on status type WITH OVERRIDE TRACKING
            override_flag = 1 if is_manual_override else 0
            
            if new_status in ['completed', 'report_issued', 'closed']:
                # These statuses should set actual_issued_at
                query = """
                UPDATE ServiceReviews 
                SET status = ?, 
                    actual_issued_at = COALESCE(actual_issued_at, SYSDATETIME()),
                    evidence_links = CASE WHEN ? IS NOT NULL THEN ? ELSE evidence_links END,
                    status_override = ?,
                    status_override_by = CASE WHEN ? = 1 THEN SYSTEM_USER ELSE NULL END,
                    status_override_at = CASE WHEN ? = 1 THEN SYSDATETIME() ELSE NULL END
                WHERE review_id = ?
                """
                self.cursor.execute(query, (
                    new_status, 
                    evidence_link, evidence_link,
                    override_flag,
                    override_flag,
                    override_flag,
                    review_id
                ))
            else:
                # For planned, in_progress, cancelled - don't update actual_issued_at
                query = """
                UPDATE ServiceReviews 
                SET status = ?,
                    evidence_links = CASE WHEN ? IS NOT NULL THEN ? ELSE evidence_links END,
                    status_override = ?,
                    status_override_by = CASE WHEN ? = 1 THEN SYSTEM_USER ELSE NULL END,
                    status_override_at = CASE WHEN ? = 1 THEN SYSDATETIME() ELSE NULL END
                WHERE review_id = ?
                """
                self.cursor.execute(query, (
                    new_status,
                    evidence_link, evidence_link,
                    override_flag,
                    override_flag,
                    override_flag,
                    review_id
                ))
            
            self.db.commit()
            print(f"✅ Review {review_id} status updated to '{new_status}' (manual_override={is_manual_override})")
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

        """
        Generate billing claim for period.
        
        This function now captures client snapshot data to preserve historical
        billing information even if the project changes ownership.
        
        Args:
            project_id: Project ID
            period_start: Claim period start date
            period_end: Claim period end date
            po_ref: Optional purchase order reference
            
        Returns:
            Dict with claim_id, total_amount, and claim lines
        """

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

            

            # Fetch client snapshot data from current project state

            client_query = """

            SELECT 

                p.project_id,

                c.client_id,

                c.name AS client_name,

                p.contract_number,

                p.contract_value

            FROM Projects p

            INNER JOIN Clients c ON p.client_id = c.client_id

            WHERE p.project_id = ?

            """

            

            self.cursor.execute(client_query, (project_id,))

            client_data = self.cursor.fetchone()

            

            if not client_data:

                error_msg = f"Project {project_id} or client not found"

                print(error_msg)

                raise ValueError(error_msg)

            

            # Unpack client snapshot

            _, client_id_snapshot, client_name_snapshot, contract_number_snapshot, contract_value_snapshot = client_data

            

            # Create claim header WITH client snapshot

            query = """

            INSERT INTO BillingClaims (

                project_id, 

                period_start, 

                period_end, 

                po_ref,

                client_id_snapshot,

                client_name_snapshot,

                contract_number_snapshot,

                contract_value_snapshot

            )

            VALUES (?, ?, ?, ?, ?, ?, ?, ?)

            """

            

            self.cursor.execute(query, (

                project_id,

                period_start.strftime('%Y-%m-%d'),

                period_end.strftime('%Y-%m-%d'),

                po_ref,

                client_id_snapshot,

                client_name_snapshot,

                contract_number_snapshot,

                contract_value_snapshot

            ))

            claim_id = self.cursor.lastrowid

            

            print(f"📋 Billing claim created with client snapshot: {client_name_snapshot} (ID: {client_id_snapshot})")

            

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

        commit: bool = True,

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

        if commit:

            self.db.commit()



    def delete_service_reviews(self, service_id: int, preserve_data: bool = True, commit: bool = True):
        """Remove all existing review cycles for a service."""
        try:
            if preserve_data:
                # Get existing review data to preserve important information
                self.cursor.execute("""
                    SELECT review_id, status, actual_issued_at, deliverables, 
                           planned_date, weight_factor
                    FROM ServiceReviews 
                    WHERE service_id = ? AND (
                        status IN ('completed', 'in_progress') OR 
                        actual_issued_at IS NOT NULL OR 
                        deliverables IS NOT NULL
                    )
                """, (service_id,))
                
                important_reviews = self.cursor.fetchall()
                
                if important_reviews:
                    print(f"⚠️  WARNING: Deleting {len(important_reviews)} reviews with important data for service {service_id}")
                    for review in important_reviews:
                        review_id, status, actual_issued_at, deliverables, planned_date, weight_factor = review
                        has_deliverables = 'Yes' if deliverables else 'No'
                        has_actual_date = 'Yes' if actual_issued_at else 'No'
                        print(f"   📋 Review {review_id} ({planned_date}): {status}, deliverables: {has_deliverables}, actual date: {has_actual_date}")
                else:
                    print(f"✅ Safe to delete {service_id} reviews - no important data found")
            
            # Proceed with deletion
            self.cursor.execute("DELETE FROM ServiceReviews WHERE service_id = ?", (service_id,))
            deleted_count = self.cursor.rowcount
            if commit:
                self.db.commit()
            print(f"🗑️  Deleted {deleted_count} review cycles for service {service_id}")
            
        except Exception as e:
            print(f"❌ Error deleting service reviews for {service_id}: {e}")
            raise



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

    def delete_all_project_reviews(self, project_id: int) -> dict:
        """Delete all review cycles for a project and optionally the associated services"""
        try:
            print(f"🗑️ Starting deletion for project {project_id}")
            
            reviews_deleted = 0
            services_deleted = 0
            
            # Use simple direct SQL approach like the fallback method
            # First count reviews to delete
            count_sql = """
                SELECT COUNT(*) FROM ServiceReviews sr
                INNER JOIN ProjectServices ps ON sr.service_id = ps.service_id
                WHERE ps.project_id = ?
            """
            self.cursor.execute(count_sql, (project_id,))
            reviews_deleted = self.cursor.fetchone()[0]
            print(f"📊 Found {reviews_deleted} reviews to delete")
            
            if reviews_deleted > 0:
                # Delete reviews first
                delete_reviews_sql = """
                    DELETE sr FROM ServiceReviews sr
                    INNER JOIN ProjectServices ps ON sr.service_id = ps.service_id
                    WHERE ps.project_id = ?
                """
                self.cursor.execute(delete_reviews_sql, (project_id,))
                print(f"🗑️ Deleted {reviews_deleted} review cycles")
                
                # Now delete only auto-generated review services
                delete_services_sql = """
                    DELETE FROM ProjectServices 
                    WHERE project_id = ? AND unit_type = 'review'
                """
                self.cursor.execute(delete_services_sql, (project_id,))
                services_deleted = self.cursor.rowcount
                print(f"🗑️ Deleted {services_deleted} auto-generated services")
            
            # Commit the transaction
            self.db.commit()
            print(f"✅ Successfully committed deletion")
            
            return {
                'reviews_deleted': reviews_deleted,
                'services_deleted': services_deleted,
                'success': True
            }
            
        except Exception as e:
            print(f"❌ Error deleting all project reviews: {e}")
            import traceback
            traceback.print_exc()
            
            try:
                self.db.rollback()
                print("🔄 Database rolled back")
            except Exception as rollback_error:
                print(f"❌ Rollback failed: {rollback_error}")
            
            return {
                'reviews_deleted': 0,
                'services_deleted': 0,
                'success': False,
                'error': str(e)
            }

    def rebuild_service_reviews(self, service_id: int, commit: bool = True) -> bool:

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



        self.delete_service_reviews(service_id, commit=commit)

        cycles = self.generate_review_cycles(

            service_id=service_id,

            unit_qty=int(unit_qty),

            start_date=start_date,

            end_date=end_date,

            cadence=frequency,

            disciplines=service.get('phase', 'All') or 'All',

            commit=commit,

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


    def set_non_review_service_status(self, service_id: int, status: str) -> bool:
        """Set status for a non-review service and map to progress_pct.

        planned -> progress_pct = 0
        in_progress -> progress_pct = 50
        completed -> progress_pct = 100

        Only applies when ProjectServices.unit_type != 'review'.
        """
        try:
            valid = {"planned", "in_progress", "completed"}
            if status not in valid:
                raise ValueError(f"Invalid status: {status}")

            # Check unit type first
            self.cursor.execute(
                "SELECT unit_type FROM ProjectServices WHERE service_id = ?",
                (service_id,)
            )
            row = self.cursor.fetchone()
            if not row:
                raise ValueError(f"Service not found: {service_id}")
            unit_type = (row[0] or '').lower()
            if unit_type == 'review':
                # Do not override review-driven progress here
                raise ValueError("Cannot set status directly on review services; manage via review cycles.")

            pct = 0
            if status == 'planned':
                pct = 0
            elif status == 'in_progress':
                pct = 50
            elif status == 'completed':
                pct = 100

            self.cursor.execute(
                """
                UPDATE ProjectServices
                SET status = ?, progress_pct = ?
                WHERE service_id = ?
                """,
                (status, pct, service_id)
            )
            self.db.commit()
            return True
        except Exception as e:
            print(f"Error setting non-review service status: {e}")
            return False

    def get_billable_by_stage(self, project_id: int) -> List[Dict]:
        """Aggregate billed amount by phase (stage) for a project."""
        try:
            services = self.get_service_progress_summary(project_id)
            totals = {}
            for svc in services:
                phase = svc.get('phase') or 'Unassigned'
                billed = float(svc.get('billed_amount') or 0.0)
                totals[phase] = totals.get(phase, 0.0) + billed
            # Return sorted by phase name
            return [
                {'phase': phase, 'billed_amount': round(amount, 2)}
                for phase, amount in sorted(totals.items(), key=lambda x: (x[0] or ""))
            ]
        except Exception as e:
            print(f"Error aggregating billable by stage: {e}")
            return []

    def get_billable_by_month(self, project_id: int) -> List[Dict]:
        """Aggregate total billed per month from BillingClaims/Lines by claim period_start."""
        try:
            # Group by calendar month of period_start; use claim lines sum
            query = """
                SELECT
                    YEAR(bc.period_start) AS yr,
                    MONTH(bc.period_start) AS mo,
                    COALESCE(SUM(bcl.amount_this_claim), 0) AS total_amount
                FROM BillingClaims bc
                LEFT JOIN BillingClaimLines bcl ON bc.claim_id = bcl.claim_id
                WHERE bc.project_id = ?
                GROUP BY YEAR(bc.period_start), MONTH(bc.period_start)
                ORDER BY YEAR(bc.period_start) DESC, MONTH(bc.period_start) DESC
            """
            self.cursor.execute(query, (project_id,))
            rows = self.cursor.fetchall()
            results = []
            for yr, mo, total in rows:
                # Format month name and year label for better readability
                month_names = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                label = f"{month_names[int(mo)]} {int(yr):04d}"
                results.append({'month': label, 'total_billed': round(float(total or 0.0), 2)})
            return results
        except Exception as e:
            print(f"Error getting billable by month: {e}")
            return []

    def get_service_regeneration_signature(self, service_id: int) -> str:
        """Get a signature string for detecting when service parameters that require regeneration have changed"""
        try:
            service = self.get_service_by_id(service_id)
            if not service:
                return ""
            
            # Create signature from parameters that should trigger regeneration
            # Include only the fields that actually matter for schedule generation
            signature_parts = [
                str(service.get('unit_qty', 0)),
                str(service.get('schedule_start', '')),
                str(service.get('schedule_end', '')),
                str(service.get('schedule_frequency', '')),
                # Include service name to detect if service was changed
                str(service.get('service_name', ''))
            ]
            signature = '|'.join(signature_parts)
            
            # Debug logging for signature changes
            print(f"🔍 Service {service_id} signature: {signature}")
            
            return signature
        except Exception as e:
            print(f"❌ Error getting service regeneration signature for {service_id}: {e}")
            return ""
    
    def should_regenerate_service_reviews(self, service_id: int) -> bool:
        """Check if service reviews need to be regenerated based on parameter changes"""
        try:
            # Get current signature
            current_signature = self.get_service_regeneration_signature(service_id)
            
            # Check if we have a stored signature for this service
            self.cursor.execute("""
                SELECT TOP 1 regeneration_signature FROM ServiceReviews 
                WHERE service_id = ?
            """, (service_id,))
            result = self.cursor.fetchone()
            
            if not result:
                # No existing reviews, should generate
                print(f"🔄 No existing reviews for service {service_id}, will generate new ones")
                return True
            
            stored_signature = result[0] if result[0] else ""
            
            # Compare signatures
            params_changed = current_signature != stored_signature
            if params_changed:
                print(f"🔄 Service {service_id} parameters changed: '{stored_signature}' -> '{current_signature}'")
            else:
                print(f"✅ Service {service_id} parameters unchanged: '{current_signature}'")
                
            return params_changed
            
        except Exception as e:
            print(f"❌ Error checking regeneration for service {service_id}: {e}")
            print(f"   🔧 Being conservative: preserving existing reviews to avoid data loss")
            # On error, be conservative and DON'T regenerate to avoid destroying data
            return False
    
    def store_service_regeneration_signature(self, service_id: int):
        """Store the current regeneration signature for a service"""
        try:
            signature = self.get_service_regeneration_signature(service_id)
            
            # Update all review cycles for this service with the current signature
            self.cursor.execute("""
                UPDATE ServiceReviews 
                SET regeneration_signature = ?
                WHERE service_id = ?
            """, (signature, service_id))
            self.db.commit()
            
        except Exception as e:
            print(f"Error storing service regeneration signature: {e}")

    def generate_service_reviews(self, project_id: int, force_regenerate: bool = False) -> List[Dict]:

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

                
                # Only regenerate if service parameters changed or forced
                should_regenerate = force_regenerate or self.should_regenerate_service_reviews(service_id)
                
                if should_regenerate:
                    if force_regenerate:
                        print(f"🔄 Force regenerating review cycles for service {service_id}")
                    else:
                        print(f"🔄 Regenerating review cycles for service {service_id} (parameters changed)")
                    
                    # Use safer deletion that warns about data loss
                    self.delete_service_reviews(service_id, preserve_data=True)
                    
                    cycles = self.generate_review_cycles(
                        service_id=service_id,
                        unit_qty=unit_qty,
                        start_date=start_date,
                        end_date=end_date,
                        cadence=frequency,
                        disciplines=service.get('phase', 'All') or 'All'
                    )
                    # Store the signature for future change detection
                    self.store_service_regeneration_signature(service_id)
                    reviews_created.extend(cycles)
                else:
                    print(f"✅ Preserving existing review cycles for service {service_id} (no parameter changes)")
                    # Add existing cycles to the created list for consistency
                    existing_cycles = self.get_service_reviews(service_id)
                    reviews_created.extend(existing_cycles)



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
        """Get service reviews for a project from the ServiceReviews table"""
        try:
            if cycle_id:
                # Get reviews for a specific cycle (cycle_no in ServiceReviews)
                self.cursor.execute("""
                    SELECT sr.review_id, sr.service_id, sr.cycle_no, sr.planned_date, 
                           sr.due_date, sr.disciplines, sr.deliverables, sr.status, 
                           sr.weight_factor, sr.invoice_reference, sr.evidence_links, sr.actual_issued_at,
                           sr.source_phase, sr.billing_phase, sr.billing_rate, sr.billing_amount, sr.is_billed,
                           ps.service_name, ps.phase
                    FROM ServiceReviews sr
                    JOIN ProjectServices ps ON sr.service_id = ps.service_id
                    WHERE ps.project_id = ? AND sr.cycle_no = ?
                    ORDER BY sr.cycle_no, sr.planned_date
                """, (project_id, cycle_id))
            else:
                # Get all service reviews for the project
                self.cursor.execute("""
                    SELECT sr.review_id, sr.service_id, sr.cycle_no, sr.planned_date, 
                           sr.due_date, sr.disciplines, sr.deliverables, sr.status, 
                           sr.weight_factor, sr.invoice_reference, sr.evidence_links, sr.actual_issued_at,
                           sr.source_phase, sr.billing_phase, sr.billing_rate, sr.billing_amount, sr.is_billed,
                           ps.service_name, ps.phase
                    FROM ServiceReviews sr
                    JOIN ProjectServices ps ON sr.service_id = ps.service_id
                    WHERE ps.project_id = ?
                    ORDER BY sr.cycle_no, sr.planned_date
                """, (project_id,))
            
            reviews = self.cursor.fetchall()
            columns = [desc[0] for desc in self.cursor.description]
            return [dict(zip(columns, review)) for review in reviews]
            
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

    def update_project_service(self, service_id: int, service_data: Dict) -> bool:
        """Update an existing project service"""
        try:
            # Validate service data
            validation_errors = validate_service_data(service_data)
            if validation_errors:
                error_msg = f"Service validation failed: {', '.join([str(e) for e in validation_errors])}"
                print(error_msg)
                return False
            
            # Sanitize input data
            service_data = sanitize_input(service_data)
            
            query = """
            UPDATE ProjectServices SET
                phase = ?, service_code = ?, service_name = ?, unit_type = ?,
                unit_qty = ?, unit_rate = ?, lump_sum_fee = ?, agreed_fee = ?, 
                bill_rule = ?, notes = ?
            WHERE service_id = ?
            """
            
            params = (
                service_data['phase'],
                service_data['service_code'],
                service_data['service_name'],
                service_data['unit_type'],
                service_data.get('unit_qty'),
                service_data.get('unit_rate'),
                service_data.get('lump_sum_fee'),
                service_data['agreed_fee'],
                service_data['bill_rule'],
                service_data.get('notes', ''),
                service_id
            )
            
            self.cursor.execute(query, params)
            self.db.commit()
            
            print(f"✅ Service {service_id} updated successfully")
            return True
            
        except Exception as e:
            print(f"❌ Error updating project service {service_id}: {e}")
            self.db.rollback()
            return False

    def update_service_statuses_by_date(self, project_id: int = None, respect_overrides: bool = True) -> Dict:
        """Automatically update service review statuses based on meeting dates and workflow progression.
        
        PROGRESSIVE WORKFLOW APPROACH:
        - Reviews past their meeting date (due_date) are marked as 'completed'
        - The next upcoming review (closest future date) is set to 'in_progress'
        - All other future reviews remain 'planned'
        - This creates a natural workflow progression based on actual meeting dates
        
        Args:
            project_id: Optional project ID to filter by (None = all projects)
            respect_overrides: If True, skip reviews with manual status overrides (default: True)
        """
        try:
            from datetime import datetime, date
            
            today = date.today()
            updated_count = 0
            skipped_count = 0
            
            print(f"🔄 Updating review statuses based on meeting dates (today: {today})")
            if respect_overrides:
                print(f"   🔒 Manual overrides will be preserved")
            
            # Build query with optional project filter - get all reviews INCLUDING OVERRIDE FLAG
            base_query = """
                SELECT sr.review_id, sr.service_id, sr.planned_date, sr.due_date, 
                       sr.status, sr.actual_issued_at, ps.service_name,
                       ISNULL(sr.status_override, 0) as status_override
                FROM ServiceReviews sr
                INNER JOIN ProjectServices ps ON sr.service_id = ps.service_id
            """
            
            if project_id:
                query = f"""
                    {base_query}
                    WHERE ps.project_id = ?
                    ORDER BY sr.service_id, sr.due_date ASC
                """
                self.cursor.execute(query, (project_id,))
            else:
                query = f"{base_query} ORDER BY sr.service_id, sr.due_date ASC"
                self.cursor.execute(query)
            
            reviews = self.cursor.fetchall()
            
            # Group reviews by service for proper workflow progression
            reviews_by_service = {}
            for review in reviews:
                review_id, service_id, planned_date, due_date, current_status, actual_issued_at, service_name, status_override = review
                
                if service_id not in reviews_by_service:
                    reviews_by_service[service_id] = {
                        'service_name': service_name,
                        'reviews': []
                    }
                
                reviews_by_service[service_id]['reviews'].append({
                    'review_id': review_id,
                    'planned_date': planned_date,
                    'due_date': due_date,
                    'current_status': current_status,
                    'actual_issued_at': actual_issued_at,
                    'status_override': status_override
                })
            
            # Process each service's reviews for workflow progression
            for service_id, service_data in reviews_by_service.items():
                service_name = service_data['service_name']
                reviews = service_data['reviews']
                
                print(f"\n📋 Processing {service_name} ({len(reviews)} reviews)")
                
                # Sort reviews by due date to establish chronological order
                reviews.sort(key=lambda r: datetime.strptime(r['due_date'], '%Y-%m-%d').date() if isinstance(r['due_date'], str) else r['due_date'])
                
                next_in_progress_set = False
                
                for review in reviews:
                    review_id = review['review_id']
                    due_date = review['due_date']
                    current_status = review['current_status']
                    status_override = review.get('status_override', 0)
                    
                    # RESPECT MANUAL OVERRIDES - Skip if manually set
                    if respect_overrides and status_override == 1:
                        print(f"   🔒 Review {review_id} ({due_date}): {current_status} (manual override - skipped)")
                        skipped_count += 1
                        continue
                    
                    # Convert date strings to date objects if needed
                    if isinstance(due_date, str):
                        due_date = datetime.strptime(due_date, '%Y-%m-%d').date()
                    
                    new_status = None
                    
                    # Determine new status based on workflow progression
                    if due_date < today:
                        # Past meeting dates should be completed
                        if current_status != 'completed':
                            new_status = 'completed'
                            
                    elif due_date >= today and not next_in_progress_set:
                        # Next upcoming meeting should be in_progress
                        if current_status != 'in_progress':
                            new_status = 'in_progress'
                            next_in_progress_set = True
                            
                    elif due_date > today:
                        # Future meetings should be planned
                        if current_status not in ['planned', 'in_progress']:
                            new_status = 'planned'
                        # Keep existing 'in_progress' if it's the next one, otherwise change to 'planned'
                        elif current_status == 'in_progress' and next_in_progress_set:
                            new_status = 'planned'
                    
                    # Update status if change is needed (DO NOT set override flag for auto-updates)
                    if new_status and new_status != current_status:
                        update_query = """
                            UPDATE ServiceReviews 
                            SET status = ?, 
                                actual_issued_at = CASE 
                                    WHEN ? = 'completed' THEN COALESCE(actual_issued_at, SYSDATETIME()) 
                                    ELSE actual_issued_at 
                                END,
                                status_override = 0,
                                status_override_by = NULL,
                                status_override_at = NULL
                            WHERE review_id = ?
                        """
                        self.cursor.execute(update_query, (new_status, new_status, review_id))
                        updated_count += 1
                        print(f"   ✅ Review {review_id} ({due_date}): {current_status} → {new_status}")
                    else:
                        print(f"   ➖ Review {review_id} ({due_date}): {current_status} (no change)")
            
            self.db.commit()
            
            print(f"\n🎯 Status update summary: {updated_count} reviews updated, {skipped_count} manual overrides preserved")
            
            return {
                'success': True,
                'updated_count': updated_count,
                'skipped_count': skipped_count,
                'message': f"Updated {updated_count} service review statuses ({skipped_count} manual overrides preserved)"
            }
            
        except Exception as e:
            print(f"❌ Error updating service statuses by date: {e}")
            self.db.rollback()
            return {
                'success': False,
                'updated_count': 0,
                'error': str(e)
            }

    def refresh_review_cycles_by_date(self, project_id: int = None) -> Dict:
        """Comprehensive refresh of review cycles based on meeting dates with UI update.
        
        This method:
        1. Updates review statuses based on meeting dates
        2. Recalculates service completion percentages
        3. Updates project KPIs
        4. Returns data needed for UI refresh
        """
        try:
            print(f"🔄 Starting comprehensive review cycle refresh for project {project_id}")
            
            # Step 1: Update review statuses based on dates
            status_update = self.update_service_statuses_by_date(project_id)
            print(f"🔍 Status update result: {status_update}")
            
            # Check if status update was successful
            if not status_update.get('success', False):
                error_msg = status_update.get('error', 'Status update failed with unknown error')
                print(f"❌ Status update failed: {error_msg}")
                return {
                    'success': False,
                    'reviews_updated': 0,
                    'project_kpis': {},
                    'service_percentages': {},
                    'error': f"Status update failed: {error_msg}",
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            
            # Step 2: Get updated project KPIs for Project Setup tab
            project_kpis = self.get_project_review_kpis(project_id)
            print(f"🔍 Project KPIs retrieved: {len(project_kpis) if project_kpis else 0} items")
            
            # Step 3: Get updated service completion percentages for Service Review Planning
            services = self.get_project_services(project_id) if project_id else []
            service_percentages = {}
            
            print(f"🔍 Processing {len(services)} services for percentage calculation")
            for service in services:
                service_id = service['service_id']  # Access dictionary key, not index
                completion_pct = self.calculate_service_review_completion_percentage(service_id)
                service_percentages[service_id] = completion_pct
                print(f"   Service {service_id}: {completion_pct}%")
            
            # Step 4: Compile comprehensive results
            reviews_updated = status_update.get('updated_count', 0)
            results = {
                'success': True,
                'reviews_updated': reviews_updated,
                'project_kpis': project_kpis,
                'service_percentages': service_percentages,
                'message': f"Refreshed review cycles: {reviews_updated} reviews updated",
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            if 'error' in status_update:
                results['warnings'] = [f"Status update warning: {status_update['error']}"]
            
            print(f"✅ Review cycle refresh completed successfully: {reviews_updated} reviews updated")
            return results
            
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Error in comprehensive review cycle refresh: {error_msg}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'reviews_updated': 0,
                'project_kpis': {},
                'service_percentages': {},
                'error': error_msg,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

    def calculate_overall_review_status(self, project_id: int) -> Dict:
        """Calculate overall review status for project based on individual service review statuses"""
        try:
            # Get all service reviews for the project
            query = """
                SELECT sr.status, COUNT(*) as count
                FROM ServiceReviews sr
                INNER JOIN ProjectServices ps ON sr.service_id = ps.service_id
                WHERE ps.project_id = ?
                GROUP BY sr.status
            """
            self.cursor.execute(query, (project_id,))
            status_counts = dict(self.cursor.fetchall())
            
            total_reviews = sum(status_counts.values())
            if total_reviews == 0:
                return {
                    'overall_status': 'no_reviews',
                    'status_summary': 'No reviews scheduled',
                    'progress_percentage': 0,
                    'details': status_counts
                }
            
            # Calculate percentages
            completed_count = status_counts.get('completed', 0) + status_counts.get('report_issued', 0) + status_counts.get('closed', 0)
            in_progress_count = status_counts.get('in_progress', 0)
            planned_count = status_counts.get('planned', 0)
            
            completed_pct = (completed_count / total_reviews) * 100
            in_progress_pct = (in_progress_count / total_reviews) * 100
            
            # Determine overall status
            if completed_pct == 100:
                overall_status = 'completed'
                status_summary = 'All reviews completed'
            elif completed_pct >= 80:
                overall_status = 'mostly_complete'
                status_summary = f'{completed_pct:.0f}% complete, {in_progress_count + planned_count} remaining'
            elif in_progress_pct > 0 or completed_pct > 0:
                overall_status = 'in_progress'
                status_summary = f'{completed_pct:.0f}% complete, {in_progress_count} in progress, {planned_count} planned'
            else:
                overall_status = 'planned'
                status_summary = f'{total_reviews} reviews planned'
            
            return {
                'overall_status': overall_status,
                'status_summary': status_summary,
                'progress_percentage': completed_pct,
                'total_reviews': total_reviews,
                'completed_reviews': completed_count,
                'in_progress_reviews': in_progress_count,
                'planned_reviews': planned_count,
                'details': status_counts
            }
            
        except Exception as e:
            print(f"❌ Error calculating overall review status: {e}")
            return {
                'overall_status': 'error',
                'status_summary': f'Error calculating status: {e}',
                'progress_percentage': 0,
                'details': {}
            }

    def update_service_progress_from_reviews(self, service_id: int) -> bool:
        """Update service progress percentage based on completed reviews"""
        try:
            # Calculate progress based on completed reviews
            query = """
                SELECT 
                    COUNT(*) as total_reviews,
                    SUM(CASE WHEN status IN ('completed', 'report_issued', 'closed') THEN 1 ELSE 0 END) as completed_count
                FROM ServiceReviews 
                WHERE service_id = ?
            """
            self.cursor.execute(query, (service_id,))
            result = self.cursor.fetchone()
            
            if result:
                total_reviews, completed_count = result
                
                if total_reviews > 0:
                    progress_pct = (completed_count / total_reviews) * 100
                else:
                    progress_pct = 0
                
                # Update service progress
                update_query = """
                    UPDATE ProjectServices 
                    SET progress_pct = ?, status = CASE 
                        WHEN ? >= 100 THEN 'completed'
                        WHEN ? > 0 THEN 'in_progress' 
                        ELSE 'planned' 
                    END
                    WHERE service_id = ?
                """
                self.cursor.execute(update_query, (progress_pct, progress_pct, progress_pct, service_id))
                self.db.commit()
                
                print(f"✅ Updated service {service_id} progress to {progress_pct:.1f}%")
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ Error updating service progress from reviews: {e}")
            self.db.rollback()
            return False

    def refresh_all_project_statuses(self, project_id: int) -> Dict:
        """Comprehensive refresh of all project statuses - reviews, services, and overall status"""
        try:
            results = {
                'reviews_updated': 0,
                'services_updated': 0,
                'overall_status': {},
                'errors': []
            }
            
            # Step 1: Update service review statuses based on dates
            review_update = self.update_service_statuses_by_date(project_id)
            results['reviews_updated'] = review_update.get('updated_count', 0)
            if 'error' in review_update:
                results['errors'].append(f"Review status update: {review_update['error']}")
            
            # Step 2: Update service progress from their reviews
            services = self.get_project_services(project_id)
            for service in services:
                service_id = service['service_id']
                if self.update_service_progress_from_reviews(service_id):
                    results['services_updated'] += 1
            
            # Step 3: Calculate overall project status
            results['overall_status'] = self.calculate_overall_review_status(project_id)
            
            print(f"🔄 Project {project_id} status refresh complete:")
            print(f"   📋 Reviews updated: {results['reviews_updated']}")
            print(f"   🔧 Services updated: {results['services_updated']}")
            print(f"   📊 Overall status: {results['overall_status']['status_summary']}")
            
            return results
            
        except Exception as e:
            error_msg = f"Error in comprehensive status refresh: {e}"
            print(f"❌ {error_msg}")
            return {
                'reviews_updated': 0,
                'services_updated': 0,
                'overall_status': {},
                'errors': [error_msg]
            }

    def calculate_service_review_completion_percentage(self, service_id: int) -> float:
        """Calculate completion percentage for a service based on its review cycles"""
        try:
            # Get all reviews for this service
            query = """
                SELECT status, COUNT(*) as count
                FROM ServiceReviews 
                WHERE service_id = ?
                GROUP BY status
            """
            self.cursor.execute(query, (service_id,))
            status_counts = dict(self.cursor.fetchall())
            
            if not status_counts:
                return 0.0
            
            # Define status weights for completion calculation
            status_weights = {
                'planned': 0.0,
                'in_progress': 0.5,
                'completed': 1.0,
                'report_issued': 1.0,
                'closed': 1.0,
                'cancelled': 0.0
            }
            
            total_reviews = sum(status_counts.values())
            weighted_completion = 0.0
            
            for status, count in status_counts.items():
                weight = status_weights.get(status, 0.0)
                weighted_completion += (count * weight)
            
            completion_percentage = (weighted_completion / total_reviews) * 100.0
            return round(completion_percentage, 1)
            
        except Exception as e:
            print(f"Error calculating service review completion: {e}")
            return 0.0

    def get_project_review_kpis(self, project_id: int) -> Dict:
        """Get comprehensive review KPIs for project dashboard"""
        try:
            kpis = {
                'total_services': 0,
                'total_reviews': 0,
                'completed_reviews': 0,
                'in_progress_reviews': 0,
                'planned_reviews': 0,
                'overdue_reviews': 0,
                'overall_completion_percentage': 0.0,
                'services_by_status': {},
                'reviews_by_status': {},
                'upcoming_reviews': [],
                'overdue_reviews_detail': []
            }
            
            # Get service count
            service_query = """
                SELECT COUNT(*) FROM ProjectServices WHERE project_id = ?
            """
            self.cursor.execute(service_query, (project_id,))
            kpis['total_services'] = self.cursor.fetchone()[0]
            
            # Get detailed review statistics
            review_query = """
                SELECT sr.status, COUNT(*) as count,
                       COUNT(CASE WHEN sr.due_date < GETDATE() AND sr.status NOT IN ('completed', 'report_issued', 'closed') THEN 1 END) as overdue_count
                FROM ServiceReviews sr
                INNER JOIN ProjectServices ps ON sr.service_id = ps.service_id
                WHERE ps.project_id = ?
                GROUP BY sr.status
            """
            self.cursor.execute(review_query, (project_id,))
            review_stats = self.cursor.fetchall()
            
            total_reviews = 0
            for status, count, overdue_count in review_stats:
                kpis['reviews_by_status'][status] = count
                total_reviews += count
                
                if status == 'completed':
                    kpis['completed_reviews'] = count
                elif status == 'in_progress':
                    kpis['in_progress_reviews'] = count
                elif status == 'planned':
                    kpis['planned_reviews'] = count
                    
                kpis['overdue_reviews'] += overdue_count or 0
            
            kpis['total_reviews'] = total_reviews
            
            # Calculate overall completion percentage
            if total_reviews > 0:
                completed_count = kpis['completed_reviews']
                in_progress_count = kpis['in_progress_reviews']
                # Give partial credit for in-progress reviews
                weighted_completion = completed_count + (in_progress_count * 0.5)
                kpis['overall_completion_percentage'] = round((weighted_completion / total_reviews) * 100, 1)
            
            # Get upcoming reviews (next 7 days)
            upcoming_query = """
                SELECT sr.review_id, sr.planned_date, sr.status, ps.service_name
                FROM ServiceReviews sr
                INNER JOIN ProjectServices ps ON sr.service_id = ps.service_id
                WHERE ps.project_id = ? 
                  AND sr.planned_date BETWEEN GETDATE() AND DATEADD(day, 7, GETDATE())
                  AND sr.status IN ('planned', 'in_progress')
                ORDER BY sr.planned_date
            """
            self.cursor.execute(upcoming_query, (project_id,))
            upcoming_reviews = self.cursor.fetchall()
            
            for review_id, planned_date, status, service_name in upcoming_reviews:
                kpis['upcoming_reviews'].append({
                    'review_id': review_id,
                    'service_name': service_name,
                    'planned_date': planned_date.strftime('%Y-%m-%d') if planned_date else '',
                    'status': status
                })
            
            # Get overdue review details
            overdue_query = """
                SELECT sr.review_id, sr.planned_date, sr.due_date, sr.status, ps.service_name
                FROM ServiceReviews sr
                INNER JOIN ProjectServices ps ON sr.service_id = ps.service_id
                WHERE ps.project_id = ? 
                  AND sr.due_date < GETDATE()
                  AND sr.status NOT IN ('completed', 'report_issued', 'closed')
                ORDER BY sr.due_date
            """
            self.cursor.execute(overdue_query, (project_id,))
            overdue_reviews = self.cursor.fetchall()
            
            for review_id, planned_date, due_date, status, service_name in overdue_reviews:
                days_overdue = (datetime.now().date() - due_date).days if due_date else 0
                kpis['overdue_reviews_detail'].append({
                    'review_id': review_id,
                    'service_name': service_name,
                    'due_date': due_date.strftime('%Y-%m-%d') if due_date else '',
                    'status': status,
                    'days_overdue': days_overdue
                })
            
            return kpis
            
        except Exception as e:
            print(f"Error getting project review KPIs: {e}")
            return kpis

    def get_service_review_status_summary(self, service_id: int) -> Dict:
        """Get review status summary for a specific service"""
        try:
            query = """
                SELECT 
                    COUNT(*) as total_reviews,
                    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed,
                    COUNT(CASE WHEN status = 'in_progress' THEN 1 END) as in_progress,
                    COUNT(CASE WHEN status = 'planned' THEN 1 END) as planned,
                    COUNT(CASE WHEN due_date < GETDATE() AND status NOT IN ('completed', 'report_issued', 'closed') THEN 1 END) as overdue
                FROM ServiceReviews 
                WHERE service_id = ?
            """
            self.cursor.execute(query, (service_id,))
            result = self.cursor.fetchone()
            
            if result:
                total, completed, in_progress, planned, overdue = result
                completion_pct = self.calculate_service_review_completion_percentage(service_id)
                
                return {
                    'total_reviews': total,
                    'completed_reviews': completed,
                    'in_progress_reviews': in_progress,
                    'planned_reviews': planned,
                    'overdue_reviews': overdue,
                    'completion_percentage': completion_pct,
                    'status_display': f"{completion_pct:.1f}%"
                }
            
            return {
                'total_reviews': 0,
                'completed_reviews': 0,
                'in_progress_reviews': 0,
                'planned_reviews': 0,
                'overdue_reviews': 0,
                'completion_percentage': 0.0,
                'status_display': "0.0%"
            }
            
        except Exception as e:
            print(f"Error getting service review status summary: {e}")
            return {
                'total_reviews': 0,
                'completed_reviews': 0,
                'in_progress_reviews': 0,
                'planned_reviews': 0,
                'overdue_reviews': 0,
                'completion_percentage': 0.0,
                'status_display': "0.0%"
            }

