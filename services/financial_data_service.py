"""
Financial Data Service

Provides unified access to financial data (line items, reconciliation, etc.)
using the FeeResolverService to compute final fees from existing schema columns.

All database access uses database_pool.py and schema.py constants.
"""

from typing import Dict, List, Optional, Any
from decimal import Decimal

from database_pool import get_db_connection
from constants.schema import ServiceReviews, ServiceItems, ProjectServices
from services.fee_resolver_service import FeeResolverService


class FinancialDataService:
    """
    Retrieves and computes financial data for projects, services, reviews, and items.
    
    Combines data from:
    - ServiceReviews (per-review fees)
    - ServiceItems (per-item deliverables)
    - ProjectServices (service-level agreement fees)
    """

    @staticmethod
    def get_line_items(
        project_id: int,
        service_id: Optional[int] = None,
        invoice_status: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Retrieve all line items (reviews + items) for a project.
        
        Args:
            project_id: Project ID
            service_id: Optional filter by service
            invoice_status: Optional filter by invoice status (draft, ready, issued, paid)
        
        Returns:
            {
              'project_id': int,
              'line_items': [
                {
                  'type': 'review' | 'item',
                  'id': str,
                  'service_id': int,
                  'service_code': str,
                  'service_name': str,
                  'phase': str,
                  'title': str,
                  'planned_date': str (ISO),
                  'due_date': str (ISO),
                  'status': str,
                  'fee': float,
                  'fee_source': str,
                  'invoice_status': str,
                  'invoice_reference': str | null,
                  'invoice_date': str | null,
                  'invoice_month': str (YYYY-MM),
                  'is_billed': int
                },
                ...
              ],
              'totals': {
                'total_fee': float,
                'billed_fee': float,
                'outstanding_fee': float
              }
            }
        """
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Fetch reviews with their services
                reviews_query = f"""
                SELECT 
                    sr.{ServiceReviews.REVIEW_ID} as id,
                    'review' as type,
                    sr.{ServiceReviews.SERVICE_ID},
                    ps.{ProjectServices.SERVICE_CODE},
                    ps.{ProjectServices.SERVICE_NAME},
                    sr.{ServiceReviews.BILLING_PHASE} as phase,
                    COALESCE(sr.{ServiceReviews.DELIVERABLES}, '') as title,
                    sr.{ServiceReviews.PLANNED_DATE},
                    sr.{ServiceReviews.DUE_DATE},
                    sr.{ServiceReviews.STATUS},
                    sr.{ServiceReviews.FEE_AMOUNT},
                    sr.{ServiceReviews.IS_USER_MODIFIED},
                    sr.{ServiceReviews.INVOICE_STATUS},
                    sr.{ServiceReviews.INVOICE_REFERENCE},
                    sr.{ServiceReviews.INVOICE_DATE},
                    sr.{ServiceReviews.INVOICE_MONTH_FINAL},
                    sr.{ServiceReviews.IS_BILLED},
                    ps.{ProjectServices.AGREED_FEE},
                    ps.{ProjectServices.REVIEW_COUNT_PLANNED}
                FROM {ServiceReviews.TABLE} sr
                JOIN {ProjectServices.TABLE} ps ON sr.{ServiceReviews.SERVICE_ID} = ps.{ProjectServices.SERVICE_ID}
                WHERE ps.{ProjectServices.PROJECT_ID} = ?
                  AND COALESCE(ps.{ProjectServices.EXECUTION_INTENT}, 'planned') = 'planned'
                """
                
                params = [project_id]
                if service_id:
                    reviews_query += f" AND sr.{ServiceReviews.SERVICE_ID} = ?"
                    params.append(service_id)
                if invoice_status:
                    reviews_query += f" AND sr.{ServiceReviews.INVOICE_STATUS} = ?"
                    params.append(invoice_status)
                
                cursor.execute(reviews_query, params)
                reviews = cursor.fetchall()
                reviews_cols = [col[0] for col in cursor.description]
                
                # Fetch items with their services
                items_query = f"""
                SELECT 
                    si.{ServiceItems.ITEM_ID} as id,
                    'item' as type,
                    si.{ServiceItems.SERVICE_ID},
                    ps.{ProjectServices.SERVICE_CODE},
                    ps.{ProjectServices.SERVICE_NAME},
                    CAST(NULL AS VARCHAR) as phase,
                    si.{ServiceItems.TITLE},
                    si.{ServiceItems.PLANNED_DATE},
                    si.{ServiceItems.DUE_DATE},
                    si.{ServiceItems.STATUS},
                    si.{ServiceItems.FEE_AMOUNT},
                    si.{ServiceItems.IS_USER_MODIFIED},
                    si.{ServiceItems.INVOICE_STATUS},
                    si.{ServiceItems.INVOICE_REFERENCE},
                    si.{ServiceItems.INVOICE_DATE},
                    CAST(NULL AS VARCHAR) as invoice_month_final,
                    si.{ServiceItems.IS_BILLED}
                FROM {ServiceItems.TABLE} si
                JOIN {ProjectServices.TABLE} ps ON si.{ServiceItems.SERVICE_ID} = ps.{ProjectServices.SERVICE_ID}
                WHERE ps.{ProjectServices.PROJECT_ID} = ?
                  AND COALESCE(ps.{ProjectServices.EXECUTION_INTENT}, 'planned') = 'planned'
                """
                
                items_params = [project_id]
                if service_id:
                    items_query += f" AND si.{ServiceItems.SERVICE_ID} = ?"
                    items_params.append(service_id)
                if invoice_status:
                    items_query += f" AND si.{ServiceItems.INVOICE_STATUS} = ?"
                    items_params.append(invoice_status)
                
                cursor.execute(items_query, items_params)
                items = cursor.fetchall()
                items_cols = [col[0] for col in cursor.description]
                
                # Convert rows to dicts and apply fee resolution
                line_items = []
                total_fee = 0.0
                billed_fee = 0.0
                
                # Calculate actual review count per service for equal split
                service_review_counts = {}
                for row in reviews:
                    row_dict = dict(zip(reviews_cols, row))
                    service_id = row_dict.get(ServiceReviews.SERVICE_ID)
                    service_review_counts[service_id] = service_review_counts.get(service_id, 0) + 1
                
                # Process reviews
                for row in reviews:
                    row_dict = dict(zip(reviews_cols, row))
                    service_id = row_dict.get(ServiceReviews.SERVICE_ID)
                    actual_review_count = service_review_counts.get(service_id, 0)
                    
                    # Build service row for fee resolution
                    service_row = {
                        ProjectServices.AGREED_FEE: row_dict.get(ProjectServices.AGREED_FEE),
                        ProjectServices.REVIEW_COUNT_PLANNED: row_dict.get(ProjectServices.REVIEW_COUNT_PLANNED),
                    }
                    
                    review_fee, fee_source = FeeResolverService.resolve_review_fee(
                        review_row=row_dict,
                        service_row=service_row,
                        actual_review_count=actual_review_count
                    )
                    
                    invoice_month = FeeResolverService.calculate_invoice_month_final(
                        override=row_dict.get(ServiceReviews.INVOICE_MONTH_OVERRIDE),
                        auto_derived=row_dict.get(ServiceReviews.INVOICE_MONTH_AUTO),
                        due_date=row_dict.get(ServiceReviews.DUE_DATE)
                    )
                    
                    line_item = {
                        'type': 'review',
                        'id': row_dict.get('id'),
                        'service_id': row_dict.get(ServiceReviews.SERVICE_ID),
                        'service_code': row_dict.get(ProjectServices.SERVICE_CODE),
                        'service_name': row_dict.get(ProjectServices.SERVICE_NAME),
                        'phase': row_dict.get('phase'),  # Aliased in query
                        'title': row_dict.get('title'),  # Aliased in query
                        'planned_date': row_dict.get(ServiceReviews.PLANNED_DATE).isoformat() if row_dict.get(ServiceReviews.PLANNED_DATE) else None,
                        'due_date': row_dict.get(ServiceReviews.DUE_DATE).isoformat() if row_dict.get(ServiceReviews.DUE_DATE) else None,
                        'status': row_dict.get(ServiceReviews.STATUS),
                        'fee': float(review_fee),
                        'fee_source': fee_source,
                        'invoice_status': row_dict.get(ServiceReviews.INVOICE_STATUS),
                        'invoice_reference': row_dict.get(ServiceReviews.INVOICE_REFERENCE),
                        'invoice_date': row_dict.get(ServiceReviews.INVOICE_DATE).isoformat() if row_dict.get(ServiceReviews.INVOICE_DATE) else None,
                        'invoice_month': invoice_month,
                        'is_billed': int(row_dict.get(ServiceReviews.IS_BILLED) or 0)
                    }
                    line_items.append(line_item)
                    total_fee += review_fee
                    if line_item['is_billed']:
                        billed_fee += review_fee
                
                # Process items
                for row in items:
                    row_dict = dict(zip(items_cols, row))
                    
                    # Items only use fee_amount - no service inheritance
                    item_fee, fee_source = FeeResolverService.resolve_item_fee(row_dict)
                    
                    # Items don't use invoice_month_final; derive from due_date
                    due_date = row_dict.get(ServiceItems.DUE_DATE)
                    invoice_month = FeeResolverService.calculate_invoice_month_final(
                        override=None,
                        auto_derived=None,
                        due_date=due_date.isoformat() if due_date else None
                    )
                    
                    line_item = {
                        'type': 'item',
                        'id': row_dict.get('id'),
                        'service_id': row_dict.get(ServiceItems.SERVICE_ID),
                        'service_code': row_dict.get(ProjectServices.SERVICE_CODE),
                        'service_name': row_dict.get(ProjectServices.SERVICE_NAME),
                        'phase': row_dict.get('phase'),  # Aliased in query as NULL
                        'title': row_dict.get(ServiceItems.TITLE),
                        'planned_date': row_dict.get(ServiceItems.PLANNED_DATE).isoformat() if row_dict.get(ServiceItems.PLANNED_DATE) else None,
                        'due_date': due_date.isoformat() if due_date else None,
                        'status': row_dict.get(ServiceItems.STATUS),
                        'fee': float(item_fee),
                        'fee_source': fee_source,
                        'invoice_status': row_dict.get(ServiceItems.INVOICE_STATUS),
                        'invoice_reference': row_dict.get(ServiceItems.INVOICE_REFERENCE),
                        'invoice_date': row_dict.get(ServiceItems.INVOICE_DATE).isoformat() if row_dict.get(ServiceItems.INVOICE_DATE) else None,
                        'invoice_month': invoice_month,
                        'is_billed': int(row_dict.get(ServiceItems.IS_BILLED) or 0)
                    }
                    line_items.append(line_item)
                    total_fee += item_fee
                    if line_item['is_billed']:
                        billed_fee += item_fee
                
                return {
                    'project_id': project_id,
                    'line_items': line_items,
                    'totals': {
                        'total_fee': float(total_fee),
                        'billed_fee': float(billed_fee),
                        'outstanding_fee': float(total_fee - billed_fee)
                    }
                }
        
        except Exception as e:
            return {'error': f'Error fetching line items: {str(e)}'}

    @staticmethod
    def get_reconciliation(project_id: int) -> Dict[str, Any]:
        """
        Compute financial reconciliation by service and project.
        
        Returns:
            {
              'project': {
                'project_id': int,
                'agreed_fee': float,
                'line_items_total_fee': float,
                'billed_total_fee': float,
                'outstanding_total_fee': float,
                'variance': float,
                'review_count': int,
                'item_count': int
              },
              'by_service': [
                {
                  'service_id': int,
                  'service_code': str,
                  'service_name': str,
                  'agreed_fee': float,
                  'line_items_total_fee': float,
                  'billed_total_fee': float,
                  'outstanding_total_fee': float,
                  'variance': float,
                  'review_count': int,
                  'item_count': int
                },
                ...
              ]
            }
        """
        # Get line items data
        line_items_result = FinancialDataService.get_line_items(project_id)
        if 'error' in line_items_result:
            return line_items_result
        
        line_items = line_items_result['line_items']
        
        # Get service-level agreement fees
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Fetch all services for this project
                services_query = f"""
                SELECT 
                    {ProjectServices.SERVICE_ID},
                    {ProjectServices.SERVICE_CODE},
                    {ProjectServices.SERVICE_NAME},
                    {ProjectServices.AGREED_FEE}
                FROM {ProjectServices.TABLE}
                WHERE {ProjectServices.PROJECT_ID} = ?
                ORDER BY {ProjectServices.SERVICE_ID}
                """
                
                cursor.execute(services_query, [project_id])
                services = cursor.fetchall()
                services_cols = [col[0] for col in cursor.description]
                
                # Map services by ID
                services_map = {}
                for row in services:
                    row_dict = dict(zip(services_cols, row))
                    services_map[row_dict[ProjectServices.SERVICE_ID]] = row_dict
                
                # Aggregate line items by service
                by_service = {}
                project_totals = {
                    'agreed_fee': 0.0,
                    'line_items_total_fee': 0.0,
                    'billed_total_fee': 0.0,
                    'review_count': 0,
                    'item_count': 0
                }
                
                for item in line_items:
                    service_id = item['service_id']
                    
                    # Initialize service aggregate if needed
                    if service_id not in by_service:
                        service_data = services_map.get(service_id, {})
                        by_service[service_id] = {
                            'service_id': service_id,
                            'service_code': service_data.get(ProjectServices.SERVICE_CODE),
                            'service_name': service_data.get(ProjectServices.SERVICE_NAME),
                            'agreed_fee': float(service_data.get(ProjectServices.AGREED_FEE) or 0),
                            'line_items_total_fee': 0.0,
                            'billed_total_fee': 0.0,
                            'review_count': 0,
                            'item_count': 0
                        }
                        project_totals['agreed_fee'] += by_service[service_id]['agreed_fee']
                    
                    # Accumulate fees
                    by_service[service_id]['line_items_total_fee'] += item['fee']
                    if item['is_billed']:
                        by_service[service_id]['billed_total_fee'] += item['fee']
                    
                    # Count reviews and items
                    if item['type'] == 'review':
                        by_service[service_id]['review_count'] += 1
                    else:
                        by_service[service_id]['item_count'] += 1
                    
                    # Accumulate project totals
                    project_totals['line_items_total_fee'] += item['fee']
                    if item['is_billed']:
                        project_totals['billed_total_fee'] += item['fee']
                    if item['type'] == 'review':
                        project_totals['review_count'] += 1
                    else:
                        project_totals['item_count'] += 1
                
                # Compute outstanding and variance
                for service in by_service.values():
                    service['outstanding_total_fee'] = service['line_items_total_fee'] - service['billed_total_fee']
                    service['variance'] = FeeResolverService.compute_reconciliation_variance(
                        service['agreed_fee'],
                        service['line_items_total_fee']
                    )
                
                project_totals['outstanding_total_fee'] = (
                    project_totals['line_items_total_fee'] - project_totals['billed_total_fee']
                )
                project_totals['variance'] = FeeResolverService.compute_reconciliation_variance(
                    project_totals['agreed_fee'],
                    project_totals['line_items_total_fee']
                )
                
                return {
                    'project': {
                        'project_id': project_id,
                        **project_totals
                    },
                    'by_service': sorted(by_service.values(), key=lambda x: x['service_id'])
                }
        
        except Exception as e:
            return {'error': f'Error computing reconciliation: {str(e)}'}

    @staticmethod
    def get_projects_finance_summary(status: Optional[str] = None) -> Dict[str, Any]:
        """
        Get batch finance summary for all projects using deterministic fee model.
        
        Args:
            status: Optional filter by project status (e.g., 'active')
        
        Returns:
            {
              'projects': [
                {
                  'project_id': int,
                  'agreed_fee_total': float,
                  'line_items_total': float,
                  'billed_total': float,
                  'unbilled_total': float,
                  'earned_value': float,
                  'pipeline_this_month': float
                },
                ...
              ]
            }
        
        Implementation uses SQL Server CTEs to:
        1. Compute service-level review counts
        2. Resolve review fees (fee_amount override OR equal split)
        3. Resolve item fees (fee_amount OR 0)
        4. Aggregate by project with billed/earned/pipeline filters
        
        Performance: Single batch query, no N+1 calls.
        """
        try:
            from datetime import datetime
            from constants.schema import Projects
            
            # Current month for pipeline calculation (YYYY-MM format)
            current_month = datetime.now().strftime('%Y-%m')
            
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Build status filter if provided
                status_filter = ""
                if status:
                    status_filter = f"WHERE p.{Projects.STATUS} = ?"
                
                # CTE-based batch query using deterministic fee model
                query = f"""
                -- CTE 1: Services scoped to projects (base set)
                WITH svc AS (
                  SELECT
                    ps.{ProjectServices.PROJECT_ID},
                    ps.{ProjectServices.SERVICE_ID},
                    ps.{ProjectServices.AGREED_FEE},
                    ps.{ProjectServices.SERVICE_CODE},
                    ps.{ProjectServices.SERVICE_NAME},
                    ps.{ProjectServices.EXECUTION_INTENT}
                  FROM {ProjectServices.TABLE} ps
                  INNER JOIN {Projects.TABLE} p 
                    ON p.{Projects.ID} = ps.{ProjectServices.PROJECT_ID}
                  {status_filter}
                ),
                
                -- CTE 2: Actual review count per service
                svc_review_counts AS (
                  SELECT
                    sr.{ServiceReviews.SERVICE_ID},
                    COUNT(*) AS actual_review_count
                  FROM {ServiceReviews.TABLE} sr
                  INNER JOIN svc ON svc.{ProjectServices.SERVICE_ID} = sr.{ServiceReviews.SERVICE_ID}
                  GROUP BY sr.{ServiceReviews.SERVICE_ID}
                ),
                
                -- CTE 3: Reviews with resolved fee + invoice month bucket + flags
                reviews_resolved AS (
                  SELECT
                    svc.{ProjectServices.PROJECT_ID},
                    sr.{ServiceReviews.REVIEW_ID} AS line_id,
                    'review' AS line_type,
                    sr.{ServiceReviews.SERVICE_ID},
                    sr.{ServiceReviews.STATUS} AS line_status,
                    
                    -- Fee resolved: fee_amount override else equal split
                    CAST(
                      CASE
                        WHEN sr.{ServiceReviews.FEE_AMOUNT} IS NOT NULL THEN sr.{ServiceReviews.FEE_AMOUNT}
                        WHEN COALESCE(svc.{ProjectServices.AGREED_FEE}, 0) > 0
                             AND COALESCE(rc.actual_review_count, 0) > 0
                          THEN svc.{ProjectServices.AGREED_FEE} / rc.actual_review_count
                        ELSE 0
                      END
                    AS DECIMAL(18,2)) AS fee_resolved,
                    
                    -- Billed flag
                    CASE
                      WHEN sr.{ServiceReviews.INVOICE_STATUS} = 'unbilled' THEN 0
                      WHEN sr.{ServiceReviews.IS_BILLED} = 1 THEN 1
                      WHEN sr.{ServiceReviews.INVOICE_STATUS} IN ('issued','paid') THEN 1
                      ELSE 0
                    END AS is_billed_resolved,
                    
                    -- Earned flag: completed status
                    CASE
                      WHEN sr.{ServiceReviews.STATUS} IN ('complete','completed','submitted') THEN 1
                      ELSE 0
                    END AS is_earned_resolved,
                    
                    -- Invoice month bucket
                    COALESCE(
                      sr.{ServiceReviews.INVOICE_MONTH_FINAL},
                      CONVERT(VARCHAR(7), sr.{ServiceReviews.INVOICE_DATE}, 120),
                      CONVERT(VARCHAR(7), sr.{ServiceReviews.DUE_DATE}, 120),
                      CONVERT(VARCHAR(7), sr.{ServiceReviews.PLANNED_DATE}, 120),
                      'Unscheduled'
                    ) AS invoice_month_bucket
                  
                  FROM {ServiceReviews.TABLE} sr
                  INNER JOIN svc ON svc.{ProjectServices.SERVICE_ID} = sr.{ServiceReviews.SERVICE_ID}
                  LEFT JOIN svc_review_counts rc ON rc.{ServiceReviews.SERVICE_ID} = sr.{ServiceReviews.SERVICE_ID}
                  WHERE COALESCE(svc.{ProjectServices.EXECUTION_INTENT}, 'planned') = 'planned'
                ),
                
                -- CTE 4: Items with resolved fee + invoice month bucket + flags
                items_resolved AS (
                  SELECT
                    svc.{ProjectServices.PROJECT_ID},
                    si.{ServiceItems.ITEM_ID} AS line_id,
                    'item' AS line_type,
                    si.{ServiceItems.SERVICE_ID},
                    si.{ServiceItems.STATUS} AS line_status,
                    
                    CAST(COALESCE(si.{ServiceItems.FEE_AMOUNT}, 0) AS DECIMAL(18,2)) AS fee_resolved,
                    
                    CASE
                      WHEN si.{ServiceItems.INVOICE_STATUS} = 'unbilled' THEN 0
                      WHEN si.{ServiceItems.IS_BILLED} = 1 THEN 1
                      WHEN si.{ServiceItems.INVOICE_STATUS} IN ('issued','paid') THEN 1
                      ELSE 0
                    END AS is_billed_resolved,
                    
                    CASE
                      WHEN si.{ServiceItems.STATUS} IN ('complete','completed','submitted') THEN 1
                      ELSE 0
                    END AS is_earned_resolved,
                    
                    COALESCE(
                      CONVERT(VARCHAR(7), si.{ServiceItems.INVOICE_DATE}, 120),
                      CONVERT(VARCHAR(7), si.{ServiceItems.DUE_DATE}, 120),
                      CONVERT(VARCHAR(7), si.{ServiceItems.PLANNED_DATE}, 120),
                      'Unscheduled'
                    ) AS invoice_month_bucket
                  
                  FROM {ServiceItems.TABLE} si
                  INNER JOIN svc ON svc.{ProjectServices.SERVICE_ID} = si.{ServiceItems.SERVICE_ID}
                  WHERE COALESCE(svc.{ProjectServices.EXECUTION_INTENT}, 'planned') = 'planned'
                ),
                
                -- CTE 5: Unified line items
                line_items AS (
                  SELECT * FROM reviews_resolved
                  UNION ALL
                  SELECT * FROM items_resolved
                ),
                
                -- CTE 6: Project rollups (totals + billed + earned)
                project_rollup AS (
                  SELECT
                    li.{ProjectServices.PROJECT_ID},
                    SUM(li.fee_resolved) AS line_items_total,
                    SUM(CASE WHEN li.is_billed_resolved = 1 THEN li.fee_resolved ELSE 0 END) AS billed_total,
                    SUM(CASE WHEN li.is_earned_resolved = 1 THEN li.fee_resolved ELSE 0 END) AS earned_total
                  FROM line_items li
                  GROUP BY li.{ProjectServices.PROJECT_ID}
                ),
                
                -- CTE 7: Pipeline "this month" rollup
                pipeline_this_month AS (
                  SELECT
                    li.{ProjectServices.PROJECT_ID},
                    SUM(li.fee_resolved) AS pipeline_this_month
                  FROM line_items li
                  WHERE li.invoice_month_bucket = ?
                    AND LOWER(ISNULL(li.line_status, '')) <> 'cancelled'
                    AND li.is_billed_resolved = 0
                  GROUP BY li.{ProjectServices.PROJECT_ID}
                ),
                
                -- CTE 8: Services agreed fee per project
                agreed_by_project AS (
                  SELECT
                    {ProjectServices.PROJECT_ID},
                    SUM(COALESCE({ProjectServices.AGREED_FEE}, 0)) AS agreed_fee_total
                  FROM svc
                  GROUP BY {ProjectServices.PROJECT_ID}
                )
                
                -- Final select
                SELECT
                  a.{ProjectServices.PROJECT_ID},
                  COALESCE(a.agreed_fee_total, 0) AS agreed_fee_total,
                  COALESCE(r.line_items_total, 0) AS line_items_total,
                  COALESCE(r.billed_total, 0) AS billed_total,
                  COALESCE(r.earned_total, 0) AS earned_value,
                  COALESCE(r.line_items_total, 0) - COALESCE(r.billed_total, 0) AS unbilled_total,
                  COALESCE(pm.pipeline_this_month, 0) AS pipeline_this_month
                FROM agreed_by_project a
                LEFT JOIN project_rollup r ON r.{ProjectServices.PROJECT_ID} = a.{ProjectServices.PROJECT_ID}
                LEFT JOIN pipeline_this_month pm ON pm.{ProjectServices.PROJECT_ID} = a.{ProjectServices.PROJECT_ID}
                ORDER BY a.{ProjectServices.PROJECT_ID};
                """
                
                # Execute query with parameters
                params = []
                if status:
                    params.append(status)
                params.append(current_month)  # For pipeline_this_month CTE
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                # Build response
                projects = []
                for row in rows:
                    projects.append({
                        'project_id': row[0],
                        'agreed_fee_total': float(row[1]) if row[1] is not None else 0.0,
                        'line_items_total': float(row[2]) if row[2] is not None else 0.0,
                        'billed_total': float(row[3]) if row[3] is not None else 0.0,
                        'earned_value': float(row[4]) if row[4] is not None else 0.0,
                        'unbilled_total': float(row[5]) if row[5] is not None else 0.0,
                        'pipeline_this_month': float(row[6]) if row[6] is not None else 0.0
                    })
                
                return {'projects': projects}
        
        except Exception as e:
            return {'error': f'Error computing projects finance summary: {str(e)}'}
