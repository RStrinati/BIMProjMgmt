"""
Review Management System - Backend Services
Comprehensive scope → schedule → progress → billing workflow
"""

import json
import sqlite3
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Optional, Tuple
import os


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
            print("✅ ServiceReviews table created successfully")
            
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
            print("✅ ServiceDeliverables table created successfully")
            
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
            print("✅ BillingClaims and BillingClaimLines tables created successfully")
            
        except Exception as e:
            print(f"Error creating billing tables: {e}")
            self.db.rollback()
    
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
                
                service_id = self.create_project_service(service_data)
                service_data['service_id'] = service_id
                services_created.append(service_data)
            
            return services_created
            
        except Exception as e:
            print(f"Error applying template: {e}")
            return []
    
    def create_project_service(self, service_data: Dict) -> int:
        """Create a new project service"""
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
            cycles_created = []
            
            # Calculate interval days
            interval_days = {
                'weekly': 7,
                'fortnightly': 14,
                'monthly': 30
            }.get(cadence, 7)
            
            # Distribute cycles across the window
            total_days = (end_date - start_date).days
            if unit_qty <= 1:
                dates = [start_date]
            else:
                # Spread evenly across the period
                interval = total_days / (unit_qty - 1) if unit_qty > 1 else 0
                dates = [start_date + timedelta(days=int(i * interval)) for i in range(unit_qty)]
            
            # Create review records
            for i, planned_date in enumerate(dates):
                due_date = planned_date + timedelta(days=7)  # Default 1 week turnaround
                
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
        query = """
        INSERT INTO ServiceReviews (
            service_id, cycle_no, planned_date, due_date, disciplines,
            deliverables, status, weight_factor
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
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
        self.db.commit()
        return self.cursor.lastrowid
    
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
    
    def generate_claim(self, project_id: int, period_start: datetime, 
                      period_end: datetime, po_ref: str = None) -> Dict:
        """Generate billing claim for period"""
        try:
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
        SELECT service_id, project_id, phase, service_code, service_name,
               unit_type, unit_qty, unit_rate, lump_sum_fee, agreed_fee,
               bill_rule, status, progress_pct, claimed_to_date, notes
        FROM ProjectServices 
        WHERE project_id = ?
        ORDER BY phase, service_code
        """
        
        self.cursor.execute(query, (project_id,))
        rows = self.cursor.fetchall()
        
        columns = [desc[0] for desc in self.cursor.description]
        return [dict(zip(columns, row)) for row in rows]
    
    def get_service_reviews(self, service_id: int) -> List[Dict]:
        """Get all reviews for a service"""
        query = """
        SELECT review_id, service_id, cycle_no, planned_date, due_date,
               disciplines, deliverables, status, weight_factor,
               evidence_links, actual_issued_at
        FROM ServiceReviews 
        WHERE service_id = ?
        ORDER BY cycle_no
        """
        
        self.cursor.execute(query, (service_id,))
        rows = self.cursor.fetchall()
        
        columns = [desc[0] for desc in self.cursor.description]
        return [dict(zip(columns, row)) for row in rows]
    
    def get_last_claimed_percentage(self, service_id: int, exclude_claim_id: int = None) -> float:
        """Get the last claimed percentage for a service"""
        query = """
        SELECT curr_pct 
        FROM BillingClaimLines bcl
        JOIN BillingClaims bc ON bc.claim_id = bcl.claim_id
        WHERE bcl.service_id = ?
        """
        params = [service_id]
        
        if exclude_claim_id:
            query += " AND bcl.claim_id != ?"
            params.append(exclude_claim_id)
        
        query += " ORDER BY bc.created_at DESC LIMIT 1"
        
        self.cursor.execute(query, params)
        result = self.cursor.fetchone()
        return result[0] if result else 0.0
    
    def load_template(self, template_name: str) -> Dict:
        """Load service template from JSON file"""
        try:
            templates_path = os.path.join(os.path.dirname(__file__), 'templates', 'service_templates.json')
            with open(templates_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for template in data['templates']:
                if template['name'] == template_name:
                    return template
            
            return None
            
        except Exception as e:
            print(f"Error loading template: {e}")
            return None
    
    def get_available_templates(self) -> List[Dict]:
        """Get list of available service templates"""
        try:
            templates_path = os.path.join(os.path.dirname(__file__), 'templates', 'service_templates.json')
            with open(templates_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return [{'name': t['name'], 'sector': t['sector'], 'notes': t.get('notes', '')} 
                   for t in data['templates']]
            
        except Exception as e:
            print(f"Error getting templates: {e}")
            return []
    
    def delete_project_service(self, service_id: int) -> bool:
        """Delete a specific project service"""
        try:
            query = "DELETE FROM ProjectServices WHERE service_id = ?"
            self.cursor.execute(query, (service_id,))
            self.db.commit()
            
            # Check if any rows were affected
            return self.cursor.rowcount > 0
            
        except Exception as e:
            print(f"Error deleting service: {e}")
            return False
    
    def clear_all_project_services(self, project_id: int) -> int:
        """Clear all services for a project"""
        try:
            # Get count before deletion for confirmation
            count_query = "SELECT COUNT(*) FROM ProjectServices WHERE project_id = ?"
            self.cursor.execute(count_query, (project_id,))
            count = self.cursor.fetchone()[0]
            
            # Delete all services for the project
            delete_query = "DELETE FROM ProjectServices WHERE project_id = ?"
            self.cursor.execute(delete_query, (project_id,))
            self.db.commit()
            
            return count
            
        except Exception as e:
            print(f"Error clearing services: {e}")
            return 0
    
    def update_project_service(self, service_id: int, service_data: Dict) -> bool:
        """Update a project service with new data"""
        try:
            query = """
            UPDATE ProjectServices SET
                phase = ?, service_code = ?, service_name = ?, unit_type = ?,
                unit_qty = ?, unit_rate = ?, lump_sum_fee = ?, agreed_fee = ?,
                bill_rule = ?, status = ?, progress_pct = ?, claimed_to_date = ?,
                notes = ?, updated_at = GETDATE()
            WHERE service_id = ?
            """
            
            params = (
                service_data.get('phase'),
                service_data.get('service_code'),
                service_data.get('service_name'),
                service_data.get('unit_type'),
                service_data.get('unit_qty'),
                service_data.get('unit_rate'),
                service_data.get('lump_sum_fee'),
                service_data.get('agreed_fee'),
                service_data.get('bill_rule'),
                service_data.get('status'),
                service_data.get('progress_pct'),
                service_data.get('claimed_to_date'),
                service_data.get('notes'),
                service_id
            )
            
            self.cursor.execute(query, params)
            self.db.commit()
            
            # Check if any rows were affected
            return self.cursor.rowcount > 0
            
        except Exception as e:
            print(f"Error updating service: {e}")
            return False
    
    def update_service_progress(self, service_id: int) -> float:
        """Update and return service progress percentage"""
        try:
            # Get service details
            query = "SELECT unit_type FROM ProjectServices WHERE service_id = ?"
            self.cursor.execute(query, (service_id,))
            result = self.cursor.fetchone()
            
            if not result:
                return 0.0
            
            unit_type = result[0]
            progress_pct = 0.0
            
            if unit_type == 'review':
                # Calculate based on completed reviews
                query = """
                SELECT 
                    SUM(CASE WHEN status IN ('report_issued', 'closed') THEN weight_factor ELSE 0 END) as completed,
                    SUM(weight_factor) as total
                FROM ServiceReviews 
                WHERE service_id = ?
                """
                self.cursor.execute(query, (service_id,))
                result = self.cursor.fetchone()
                
                if result and result[1] > 0:
                    progress_pct = (result[0] / result[1]) * 100
            
            elif unit_type == 'audit':
                # Check if deliverable is issued
                query = """
                SELECT COUNT(*) FROM ServiceDeliverables 
                WHERE service_id = ? AND status = 'issued'
                """
                self.cursor.execute(query, (service_id,))
                result = self.cursor.fetchone()
                progress_pct = 100.0 if result and result[0] > 0 else 0.0
            
            # Update progress in database
            query = "UPDATE ProjectServices SET progress_pct = ? WHERE service_id = ?"
            self.cursor.execute(query, (progress_pct, service_id))
            self.db.commit()
            
            return progress_pct
            
        except Exception as e:
            print(f"Error updating service progress: {e}")
            return 0.0


class ClaimExporter:
    """Export claims to various formats"""
    
    @staticmethod
    def export_to_csv(claim_data: Dict, filepath: str) -> bool:
        """Export claim to CSV format"""
        try:
            import csv
            
            with open(filepath, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                
                # Header
                writer.writerow(['Stage/Phase', 'Service', 'Previous %', 'Current %', 
                               'Delta %', 'Amount This Claim'])
                
                # Lines
                for line in claim_data.get('lines', []):
                    delta = line['curr_pct'] - line['prev_pct']
                    writer.writerow([
                        line['stage_label'],
                        line.get('service_name', ''),
                        f"{line['prev_pct']:.2f}%",
                        f"{line['curr_pct']:.2f}%",
                        f"{delta:.2f}%",
                        f"${line['amount_this_claim']:,.2f}"
                    ])
                
                # Total
                writer.writerow([])
                writer.writerow(['TOTAL', '', '', '', '', 
                               f"${claim_data.get('total_amount', 0):,.2f}"])
            
            return True
            
        except Exception as e:
            print(f"Error exporting to CSV: {e}")
            return False
