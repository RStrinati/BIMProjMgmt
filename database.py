def create_service_template(template_name, description, service_type, parameters, created_by):
    """Insert a new service template."""
    try:
        if parameters is not None and not isinstance(parameters, str):
            parameters = json.dumps(parameters)
        with get_db_connection(Config.WAREHOUSE_DB) as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                INSERT INTO {S.ServiceTemplates.TABLE} (
                    {S.ServiceTemplates.TEMPLATE_NAME}, {S.ServiceTemplates.DESCRIPTION},
                    {S.ServiceTemplates.SERVICE_TYPE}, {S.ServiceTemplates.PARAMETERS},
                    {S.ServiceTemplates.CREATED_BY}
                ) VALUES (?, ?, ?, ?, ?);
                """,
                (template_name, description, service_type, parameters, created_by)
            )
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"Error creating service template: {e}")
        return False

def get_service_templates():
    """Fetch all service templates."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT {S.ServiceTemplates.ID}, {S.ServiceTemplates.TEMPLATE_NAME}, {S.ServiceTemplates.DESCRIPTION}, {S.ServiceTemplates.SERVICE_TYPE}, {S.ServiceTemplates.PARAMETERS}, {S.ServiceTemplates.CREATED_BY}, {S.ServiceTemplates.CREATED_AT}, {S.ServiceTemplates.IS_ACTIVE} FROM {S.ServiceTemplates.TABLE} WHERE {S.ServiceTemplates.IS_ACTIVE} = 1 ORDER BY {S.ServiceTemplates.ID};"
            )
            templates = [dict(
                id=row[0],
                template_name=row[1],
                description=row[2],
                service_type=row[3],
                parameters=row[4],
                created_by=row[5],
                created_at=row[6],
                is_active=row[7]
            ) for row in cursor.fetchall()]
            return templates
    except Exception as e:
        logger.error(f"Error fetching service templates: {e}")
        return []

def update_service_template(template_id, template_name=None, description=None, service_type=None, parameters=None, is_active=None):
    """Update an existing service template."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            update_fields = {}
            if template_name is not None:
                update_fields[S.ServiceTemplates.TEMPLATE_NAME] = template_name
            if description is not None:
                update_fields[S.ServiceTemplates.DESCRIPTION] = description
            if service_type is not None:
                update_fields[S.ServiceTemplates.SERVICE_TYPE] = service_type
            if parameters is not None:
                if not isinstance(parameters, str):
                    parameters = json.dumps(parameters)
                update_fields[S.ServiceTemplates.PARAMETERS] = parameters
            if is_active is not None:
                update_fields[S.ServiceTemplates.IS_ACTIVE] = is_active
            if not update_fields:
                return False
            set_clause = ', '.join([f"{field} = ?" for field in update_fields.keys()])
            values = list(update_fields.values()) + [template_id]
            cursor.execute(
                f"UPDATE {S.ServiceTemplates.TABLE} SET {set_clause} WHERE {S.ServiceTemplates.ID} = ?",
                values
            )
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"Error updating service template: {e}")
        return False

def delete_service_template(template_id):
    """Soft delete a service template by setting is_active to 0."""
    return update_service_template(template_id, is_active=0)


# --- Project Services Functions ---

def get_project_services(project_id):
    """Get all services for a project with billing metrics and derived status."""

    status_buckets = ('planned', 'in_progress', 'completed', 'overdue', 'cancelled')

    def _empty_counts():
        counts = {key: 0 for key in status_buckets}
        counts['total'] = 0
        return counts

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT ps.{S.ProjectServices.SERVICE_ID}, ps.{S.ProjectServices.PROJECT_ID}, 
                       ps.{S.ProjectServices.PHASE}, ps.{S.ProjectServices.SERVICE_CODE}, 
                       ps.{S.ProjectServices.SERVICE_NAME}, ps.{S.ProjectServices.UNIT_TYPE}, 
                       ps.{S.ProjectServices.UNIT_QTY}, ps.{S.ProjectServices.UNIT_RATE}, 
                       ps.{S.ProjectServices.LUMP_SUM_FEE}, ps.{S.ProjectServices.AGREED_FEE}, 
                       ps.{S.ProjectServices.BILL_RULE}, ps.{S.ProjectServices.NOTES}, 
                       ps.{S.ProjectServices.CREATED_AT}, ps.{S.ProjectServices.UPDATED_AT}, 
                       ps.{S.ProjectServices.STATUS}, ps.{S.ProjectServices.PROGRESS_PCT}, 
                       ps.{S.ProjectServices.CLAIMED_TO_DATE}, ps.{S.ProjectServices.ASSIGNED_USER_ID},
                       u.{S.Users.NAME} AS assigned_user_name
                FROM {S.ProjectServices.TABLE} ps
                LEFT JOIN {S.Users.TABLE} u ON ps.{S.ProjectServices.ASSIGNED_USER_ID} = u.{S.Users.ID}
                WHERE ps.{S.ProjectServices.PROJECT_ID} = ?
                ORDER BY ps.{S.ProjectServices.CREATED_AT}
                """,
                (project_id,)
            )
            rows = cursor.fetchall()
            services = [dict(
                service_id=row[0],
                project_id=row[1],
                phase=row[2],
                service_code=row[3],
                service_name=row[4],
                unit_type=row[5],
                unit_qty=row[6],
                unit_rate=row[7],
                lump_sum_fee=row[8],
                agreed_fee=row[9],
                bill_rule=row[10],
                notes=row[11],
                created_at=row[12],
                updated_at=row[13],
                status=row[14],
                progress_pct=row[15],
                claimed_to_date=row[16],
                assigned_user_id=row[17],
                assigned_user_name=row[18],
            ) for row in rows]

            if not services:
                return services

            service_ids = [svc['service_id'] for svc in services]
            activity_counts = {sid: _empty_counts() for sid in service_ids}
            billing_tracker = {sid: {'billable': 0, 'billed': 0} for sid in service_ids}

            placeholders = ', '.join('?' for _ in service_ids)

            # Aggregate review statuses
            try:
                cursor.execute(
                    f"""
                    SELECT {S.ServiceReviews.SERVICE_ID}, {S.ServiceReviews.STATUS}, COUNT(*)
                    FROM {S.ServiceReviews.TABLE}
                    WHERE {S.ServiceReviews.SERVICE_ID} IN ({placeholders})
                    GROUP BY {S.ServiceReviews.SERVICE_ID}, {S.ServiceReviews.STATUS}
                    """,
                    service_ids
                )
                for service_id, status_value, count in cursor.fetchall():
                    counts = activity_counts.get(service_id)
                    if not counts:
                        continue
                    status_key = (status_value or '').lower()
                    count = int(count or 0)
                    counts['total'] += count
                    if status_key in counts:
                        counts[status_key] += count
            except Exception as review_err:
                logger.warning(f"Failed to aggregate review statuses for services {service_ids}: {review_err}")

            # Aggregate billed review counts
            try:
                cursor.execute(
                    f"""
                    SELECT 
                        {S.ServiceReviews.SERVICE_ID},
                        SUM(CASE WHEN LOWER(ISNULL({S.ServiceReviews.STATUS}, '')) <> 'cancelled' THEN 1 ELSE 0 END) AS active_count,
                        SUM(CASE WHEN ISNULL({S.ServiceReviews.IS_BILLED}, 0) = 1 THEN 1 ELSE 0 END) AS billed_count
                    FROM {S.ServiceReviews.TABLE}
                    WHERE {S.ServiceReviews.SERVICE_ID} IN ({placeholders})
                    GROUP BY {S.ServiceReviews.SERVICE_ID}
                    """,
                    service_ids
                )
                for service_id, active_count, billed_count in cursor.fetchall():
                    tracker = billing_tracker.get(service_id)
                    if not tracker:
                        continue
                    tracker['billable'] += int(active_count or 0)
                    tracker['billed'] += int(billed_count or 0)
            except Exception as review_billing_err:
                logger.warning(f"Failed to aggregate review billing for services {service_ids}: {review_billing_err}")

            # Aggregate service item statuses
            try:
                cursor.execute(
                    f"""
                    SELECT {S.ServiceItems.SERVICE_ID}, {S.ServiceItems.STATUS}, COUNT(*)
                    FROM {S.ServiceItems.TABLE}
                    WHERE {S.ServiceItems.SERVICE_ID} IN ({placeholders})
                    GROUP BY {S.ServiceItems.SERVICE_ID}, {S.ServiceItems.STATUS}
                    """,
                    service_ids
                )
                for service_id, status_value, count in cursor.fetchall():
                    counts = activity_counts.get(service_id)
                    if not counts:
                        continue
                    status_key = (status_value or '').lower()
                    count = int(count or 0)
                    counts['total'] += count
                    if status_key in counts:
                        counts[status_key] += count
            except Exception as item_err:
                logger.warning(f"Failed to aggregate item statuses for services {service_ids}: {item_err}")

            # Aggregate billed service items
            try:
                cursor.execute(
                    f"""
                    SELECT 
                        {S.ServiceItems.SERVICE_ID},
                        SUM(CASE WHEN LOWER(ISNULL({S.ServiceItems.STATUS}, '')) <> 'cancelled' THEN 1 ELSE 0 END) AS active_count,
                        SUM(CASE WHEN ISNULL({S.ServiceItems.IS_BILLED}, 0) = 1 THEN 1 ELSE 0 END) AS billed_count
                    FROM {S.ServiceItems.TABLE}
                    WHERE {S.ServiceItems.SERVICE_ID} IN ({placeholders})
                    GROUP BY {S.ServiceItems.SERVICE_ID}
                    """,
                    service_ids
                )
                for service_id, active_count, billed_count in cursor.fetchall():
                    tracker = billing_tracker.get(service_id)
                    if not tracker:
                        continue
                    tracker['billable'] += int(active_count or 0)
                    tracker['billed'] += int(billed_count or 0)
            except Exception as item_billing_err:
                logger.warning(f"Failed to aggregate item billing for services {service_ids}: {item_billing_err}")

            status_updates = []
            now = datetime.now()

            for service in services:
                counts = activity_counts.get(service['service_id'], _empty_counts())
                original_status = service['status']
                original_progress_pct = float(service['progress_pct'] or 0.0)

                active_total = counts['total'] - counts.get('cancelled', 0)
                derived_status = original_status or 'planned'

                if counts.get('overdue', 0) > 0:
                    derived_status = 'overdue'
                elif active_total <= 0:
                    derived_status = original_status or 'planned'
                elif counts.get('completed', 0) >= active_total:
                    derived_status = 'completed'
                elif counts.get('in_progress', 0) > 0 or counts.get('completed', 0) > 0:
                    derived_status = 'in_progress'
                else:
                    derived_status = 'planned'

                agreed_fee_raw = service.get('agreed_fee')
                agreed_fee = float(agreed_fee_raw) if agreed_fee_raw is not None else 0.0

                claimed_raw = service.get('claimed_to_date')
                claimed_to_date = float(claimed_raw) if claimed_raw is not None else 0.0

                billing_snapshot = billing_tracker.get(service['service_id'], {'billable': 0, 'billed': 0})
                billable_units = int(billing_snapshot.get('billable') or 0)
                billed_units = int(billing_snapshot.get('billed') or 0)

                progress_from_flags = None
                if billable_units > 0:
                    billed_units = min(billed_units, billable_units)
                    if derived_status == 'completed':
                        billed_units = billable_units
                    progress_from_flags = (billed_units / billable_units) * 100.0
                elif derived_status == 'completed':
                    progress_from_flags = 100.0

                billed_amount = None
                if claimed_to_date > 0:
                    billed_amount = claimed_to_date
                elif progress_from_flags is not None and agreed_fee > 0:
                    billed_amount = agreed_fee * (progress_from_flags / 100.0)
                else:
                    billed_amount = agreed_fee * (original_progress_pct / 100.0)

                if derived_status == 'completed' and agreed_fee > 0:
                    billed_amount = max(billed_amount, agreed_fee)

                billed_amount = min(max(billed_amount, 0.0), agreed_fee) if agreed_fee else max(billed_amount, 0.0)
                billed_amount = round(billed_amount, 2)

                billing_progress_pct = (billed_amount / agreed_fee * 100.0) if agreed_fee else 0.0
                billing_progress_pct = max(min(billing_progress_pct, 100.0), 0.0)
                billing_progress_pct = round(billing_progress_pct, 2)

                remaining_fee = agreed_fee - billed_amount if agreed_fee else 0.0
                remaining_fee = max(round(remaining_fee, 2), 0.0)

                service['status'] = derived_status
                service['progress_pct'] = billing_progress_pct
                service['billing_progress_pct'] = billing_progress_pct
                service['billed_amount'] = billed_amount
                service['agreed_fee_remaining'] = remaining_fee

                if derived_status != original_status or abs(billing_progress_pct - original_progress_pct) > 0.01:
                    status_updates.append((derived_status, billing_progress_pct, now, service['service_id']))

            if status_updates:
                try:
                    cursor.executemany(
                        f"""
                        UPDATE {S.ProjectServices.TABLE}
                        SET {S.ProjectServices.STATUS} = ?, {S.ProjectServices.PROGRESS_PCT} = ?, 
                            {S.ProjectServices.UPDATED_AT} = ?
                        WHERE {S.ProjectServices.SERVICE_ID} = ?
                        """,
                        status_updates
                    )
                    conn.commit()
                except Exception as update_err:
                    logger.warning(f"Failed to persist service status updates: {update_err}")

            return services
    except Exception as e:
        logger.error(f"Error fetching project services: {e}")
        return []


def create_project_service(project_id, service_code, service_name, phase=None, unit_type=None, 
                          unit_qty=None, unit_rate=None, lump_sum_fee=None, agreed_fee=None, 
                          bill_rule=None, notes=None):
    """Create a new service for a project."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                INSERT INTO {S.ProjectServices.TABLE} (
                    {S.ProjectServices.PROJECT_ID}, {S.ProjectServices.SERVICE_CODE}, 
                    {S.ProjectServices.SERVICE_NAME}, {S.ProjectServices.PHASE}, 
                    {S.ProjectServices.UNIT_TYPE}, {S.ProjectServices.UNIT_QTY}, 
                    {S.ProjectServices.UNIT_RATE}, {S.ProjectServices.LUMP_SUM_FEE}, 
                    {S.ProjectServices.AGREED_FEE}, {S.ProjectServices.BILL_RULE}, 
                    {S.ProjectServices.NOTES}
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (project_id, service_code, service_name, phase, unit_type, unit_qty, 
                 unit_rate, lump_sum_fee, agreed_fee, bill_rule, notes)
            )
            conn.commit()
            return cursor.lastrowid
    except Exception as e:
        logger.error(f"Error creating project service: {e}")
        return None


def update_project_service(service_id, **kwargs):
    """Update an existing project service."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            update_fields = {}
            allowed_fields = [
                S.ProjectServices.PHASE, S.ProjectServices.SERVICE_CODE, 
                S.ProjectServices.SERVICE_NAME, S.ProjectServices.UNIT_TYPE, 
                S.ProjectServices.UNIT_QTY, S.ProjectServices.UNIT_RATE, 
                S.ProjectServices.LUMP_SUM_FEE, S.ProjectServices.AGREED_FEE, 
                S.ProjectServices.BILL_RULE, S.ProjectServices.NOTES, 
                S.ProjectServices.STATUS, S.ProjectServices.PROGRESS_PCT, 
                S.ProjectServices.CLAIMED_TO_DATE
            ]
            
            for key, value in kwargs.items():
                if key in allowed_fields:
                    update_fields[key] = value
            
            if not update_fields:
                return False
                
            set_clause = ', '.join([f"{field} = ?" for field in update_fields.keys()])
            values = list(update_fields.values()) + [service_id]
            cursor.execute(
                f"UPDATE {S.ProjectServices.TABLE} SET {set_clause}, {S.ProjectServices.UPDATED_AT} = GETDATE() WHERE {S.ProjectServices.SERVICE_ID} = ?",
                values
            )
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"Error updating project service: {e}")
        return False


def delete_project_service(service_id):
    """Delete a project service."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"DELETE FROM {S.ProjectServices.TABLE} WHERE {S.ProjectServices.SERVICE_ID} = ?",
                (service_id,)
            )
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"Error deleting project service: {e}")
        return False


# --- Service Reviews Functions ---

def get_service_reviews(service_id):
    """Get all reviews for a service."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            supports_billing = _ensure_service_review_billing_columns(cursor)
            if not supports_billing:
                logger.warning("ServiceReviews billing metadata columns not found; returning empty billing summary.")
                return {
                    'reviews': [],
                    'summary_by_phase': [],
                    'monthly_totals': [],
                    'total_amount': 0.0,
                    'total_reviews': 0
                }
            supports_billing = _ensure_service_review_billing_columns(cursor)

            if supports_billing:
                cursor.execute(
                    f"""
                    SELECT {S.ServiceReviews.REVIEW_ID}, {S.ServiceReviews.SERVICE_ID}, 
                           {S.ServiceReviews.CYCLE_NO}, {S.ServiceReviews.PLANNED_DATE}, 
                           {S.ServiceReviews.DUE_DATE}, {S.ServiceReviews.DISCIPLINES}, 
                           {S.ServiceReviews.DELIVERABLES}, {S.ServiceReviews.STATUS}, 
                           {S.ServiceReviews.WEIGHT_FACTOR}, {S.ServiceReviews.EVIDENCE_LINKS}, 
                           {S.ServiceReviews.INVOICE_REFERENCE}, {S.ServiceReviews.ACTUAL_ISSUED_AT}, 
                           {S.ServiceReviews.SOURCE_PHASE}, {S.ServiceReviews.BILLING_PHASE}, 
                           {S.ServiceReviews.BILLING_RATE}, {S.ServiceReviews.BILLING_AMOUNT}, 
                           {S.ServiceReviews.IS_BILLED}
                    FROM {S.ServiceReviews.TABLE} 
                    WHERE {S.ServiceReviews.SERVICE_ID} = ?
                    ORDER BY {S.ServiceReviews.CYCLE_NO}
                    """,
                    (service_id,)
                )
                rows = cursor.fetchall()
                reviews = [dict(
                    review_id=row[0],
                    service_id=row[1],
                    cycle_no=row[2],
                    planned_date=row[3],
                    due_date=row[4],
                    disciplines=row[5],
                    deliverables=row[6],
                    status=row[7],
                    weight_factor=float(row[8]) if row[8] is not None else None,
                    evidence_links=row[9],
                    invoice_reference=row[10],
                    actual_issued_at=row[11],
                    source_phase=row[12],
                    billing_phase=row[13],
                    billing_rate=float(row[14]) if row[14] is not None else None,
                    billing_amount=float(row[15]) if row[15] is not None else None,
                    is_billed=bool(row[16]) if row[16] is not None else False
                ) for row in rows]
            else:
                cursor.execute(
                    f"""
                    SELECT {S.ServiceReviews.REVIEW_ID}, {S.ServiceReviews.SERVICE_ID}, 
                           {S.ServiceReviews.CYCLE_NO}, {S.ServiceReviews.PLANNED_DATE}, 
                           {S.ServiceReviews.DUE_DATE}, {S.ServiceReviews.DISCIPLINES}, 
                           {S.ServiceReviews.DELIVERABLES}, {S.ServiceReviews.STATUS}, 
                           {S.ServiceReviews.WEIGHT_FACTOR}, {S.ServiceReviews.EVIDENCE_LINKS}, 
                           {S.ServiceReviews.INVOICE_REFERENCE}, {S.ServiceReviews.ACTUAL_ISSUED_AT}, 
                           {S.ServiceReviews.IS_BILLED}
                    FROM {S.ServiceReviews.TABLE} 
                    WHERE {S.ServiceReviews.SERVICE_ID} = ?
                    ORDER BY {S.ServiceReviews.CYCLE_NO}
                    """,
                    (service_id,)
                )
                rows = cursor.fetchall()
                reviews = [dict(
                    review_id=row[0],
                    service_id=row[1],
                    cycle_no=row[2],
                    planned_date=row[3],
                    due_date=row[4],
                    disciplines=row[5],
                    deliverables=row[6],
                    status=row[7],
                    weight_factor=float(row[8]) if row[8] is not None else None,
                    evidence_links=row[9],
                    invoice_reference=row[10],
                    actual_issued_at=row[11],
                    source_phase=None,
                    billing_phase=None,
                    billing_rate=None,
                    billing_amount=None,
                    is_billed=bool(row[12]) if row[12] is not None else False
                ) for row in rows]
            return reviews
    except Exception as e:
        logger.error(f"Error fetching service reviews: {e}")
        return []


def get_project_reviews(
    project_id,
    status=None,
    service_id=None,
    from_date=None,
    to_date=None,
    sort_by="planned_date",
    sort_dir="asc",
    limit=None,
    page=None,
):
    """Get all reviews for a project with optional filters."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            _set_cursor_timeout(cursor, 10)

            filters = [f"ps.{S.ProjectServices.PROJECT_ID} = ?"]
            params = [project_id]

            if status:
                filters.append(f"sr.{S.ServiceReviews.STATUS} = ?")
                params.append(status)

            if service_id:
                filters.append(f"sr.{S.ServiceReviews.SERVICE_ID} = ?")
                params.append(service_id)

            if from_date:
                filters.append(
                    f"(sr.{S.ServiceReviews.PLANNED_DATE} >= ? OR sr.{S.ServiceReviews.DUE_DATE} >= ?)"
                )
                params.extend([from_date, from_date])

            if to_date:
                filters.append(
                    f"(sr.{S.ServiceReviews.PLANNED_DATE} <= ? OR sr.{S.ServiceReviews.DUE_DATE} <= ?)"
                )
                params.extend([to_date, to_date])

            where_clause = " AND ".join(filters)

            sort_columns = {
                "planned_date": f"sr.{S.ServiceReviews.PLANNED_DATE}",
                "due_date": f"sr.{S.ServiceReviews.DUE_DATE}",
                "status": f"sr.{S.ServiceReviews.STATUS}",
                "service_name": f"ps.{S.ProjectServices.SERVICE_NAME}",
            }
            sort_column = sort_columns.get(sort_by, sort_columns["planned_date"])
            sort_direction = "DESC" if str(sort_dir).lower() == "desc" else "ASC"

            base_sql = f"""
                FROM {S.ServiceReviews.TABLE} sr
                JOIN {S.ProjectServices.TABLE} ps
                    ON sr.{S.ServiceReviews.SERVICE_ID} = ps.{S.ProjectServices.SERVICE_ID}
                WHERE {where_clause}
            """

            cursor.execute(f"SELECT COUNT(1) {base_sql}", params)
            total = int(cursor.fetchone()[0] or 0)

            select_sql = f"""
                SELECT
                    sr.{S.ServiceReviews.REVIEW_ID},
                    sr.{S.ServiceReviews.SERVICE_ID},
                    ps.{S.ProjectServices.PROJECT_ID},
                    sr.{S.ServiceReviews.CYCLE_NO},
                    sr.{S.ServiceReviews.PLANNED_DATE},
                    sr.{S.ServiceReviews.DUE_DATE},
                    sr.{S.ServiceReviews.STATUS},
                    sr.{S.ServiceReviews.DISCIPLINES},
                    sr.{S.ServiceReviews.DELIVERABLES},
                    sr.{S.ServiceReviews.IS_BILLED},
                    sr.{S.ServiceReviews.BILLING_AMOUNT},
                    sr.{S.ServiceReviews.INVOICE_REFERENCE},
                    sr.{S.ServiceReviews.INVOICE_DATE},
                    ps.{S.ProjectServices.SERVICE_NAME},
                    ps.{S.ProjectServices.SERVICE_CODE},
                    ps.{S.ProjectServices.PHASE}
                {base_sql}
                ORDER BY {sort_column} {sort_direction}
            """

            query_params = list(params)
            if limit:
                page = page if page and page > 0 else 1
                offset = max(page - 1, 0) * limit
                select_sql += " OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
                query_params.extend([offset, limit])

            cursor.execute(select_sql, query_params)
            rows = cursor.fetchall()

            items = [
                dict(
                    review_id=row[0],
                    service_id=row[1],
                    project_id=row[2],
                    cycle_no=row[3],
                    planned_date=row[4],
                    due_date=row[5],
                    status=row[6],
                    disciplines=row[7],
                    deliverables=row[8],
                    is_billed=bool(row[9]) if row[9] is not None else None,
                    billing_amount=float(row[10]) if row[10] is not None else None,
                    invoice_reference=row[11],
                    invoice_date=row[12],
                    service_name=row[13],
                    service_code=row[14],
                    phase=row[15],
                )
                for row in rows
            ]

            return {"items": items, "total": total}
    except Exception as e:
        logger.error(f"Error fetching project reviews: {e}")
        return None


def _to_decimal(value):
    """Safely convert a value to Decimal or return None."""
    if value is None or value == '':
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None


def _derive_default_review_rate(unit_type, unit_rate, unit_qty, lump_sum_fee, agreed_fee):
    """Derive a per-review rate from service financials."""
    unit_type = (unit_type or '').lower()
    unit_rate_dec = _to_decimal(unit_rate)
    unit_qty_dec = _to_decimal(unit_qty)
    lump_sum_dec = _to_decimal(lump_sum_fee)
    agreed_fee_dec = _to_decimal(agreed_fee)

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


def _ensure_service_review_billing_columns(cursor) -> bool:
    """Ensure the ServiceReviews table has billing metadata columns."""
    global _service_review_billing_columns_ready
    if _service_review_billing_columns_ready:
        return bool(_service_review_billing_columns_ready)

    table = S.ServiceReviews.TABLE

    def _column_exists(column: str) -> bool:
        try:
            cursor.execute(f"SELECT {column} FROM {table} WHERE 1 = 0")
            return True
        except Exception:
            return False

    missing = [
        (name, ddl) for name, ddl in _SERVICE_REVIEW_BILLING_COLUMN_DEFINITIONS
        if not _column_exists(name)
    ]

    if not missing:
        _service_review_billing_columns_ready = True
        return True

    for column_name, definition in missing:
        try:
            cursor.execute(f"ALTER TABLE {table} ADD {column_name} {definition}")
        except Exception as exc:
            message = str(exc).lower()
            # Already exists / duplicate column errors can be ignored silently
            if 'duplicate' in message or 'exists' in message or 'already' in message:
                continue
            logger.warning(f"Unable to add column {column_name} to {table}: {exc}")
            _service_review_billing_columns_ready = False
            return False

    connection = getattr(cursor, 'connection', None)
    if connection:
        try:
            connection.commit()
        except Exception as exc:
            logger.debug(f"Commit after altering {table} failed (continuing): {exc}")

    _service_review_billing_columns_ready = True
    return True


def create_service_review(service_id, cycle_no, planned_date, due_date=None, 
                         disciplines=None, deliverables=None, status='planned', 
                         weight_factor=1.0, evidence_links=None, invoice_reference=None,
                         source_phase=None, billing_phase=None, billing_rate=None,
                         billing_amount=None, is_billed=None):
    """Create a new review for a service."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            status = (status or 'planned')
            final_weight = weight_factor if weight_factor is not None else 1.0
            try:
                final_weight = float(final_weight)
            except (ValueError, TypeError):
                final_weight = 1.0

            effective_is_billed = is_billed
            if effective_is_billed is None:
                effective_is_billed = 1 if status.lower() == 'completed' else 0

            # Derive default billing metadata from the service record
            supports_billing = _ensure_service_review_billing_columns(cursor)
            cursor.execute(
                f"""
                SELECT {S.ProjectServices.PHASE}, {S.ProjectServices.UNIT_TYPE}, 
                       {S.ProjectServices.UNIT_QTY}, {S.ProjectServices.UNIT_RATE}, 
                       {S.ProjectServices.LUMP_SUM_FEE}, {S.ProjectServices.AGREED_FEE}
                FROM {S.ProjectServices.TABLE}
                WHERE {S.ProjectServices.SERVICE_ID} = ?
                """,
                (service_id,)
            )
            service_row = cursor.fetchone()
            service_phase = service_row[0] if service_row else None
            derived_rate = None
            if service_row:
                derived_rate = _derive_default_review_rate(
                    service_row[1], service_row[3], service_row[2], service_row[4], service_row[5]
                )

            final_source_phase = source_phase or service_phase
            final_billing_phase = billing_phase or final_source_phase or service_phase

            effective_rate = billing_rate if billing_rate is not None else derived_rate or 0.0
            try:
                effective_rate = float(effective_rate)
            except (ValueError, TypeError):
                effective_rate = 0.0

            effective_amount = billing_amount
            if effective_amount is None:
                try:
                    effective_amount = float(Decimal(str(effective_rate or 0)) * Decimal(str(final_weight or 1)))
                except (InvalidOperation, ValueError, TypeError):
                    effective_amount = float(effective_rate or 0) * float(final_weight or 1)
            else:
                try:
                    effective_amount = float(effective_amount)
                except (ValueError, TypeError):
                    effective_amount = float(effective_rate or 0) * float(final_weight or 1)

            if supports_billing:
                cursor.execute(
                    f"""
                    INSERT INTO {S.ServiceReviews.TABLE} (
                        {S.ServiceReviews.SERVICE_ID}, {S.ServiceReviews.CYCLE_NO}, 
                        {S.ServiceReviews.PLANNED_DATE}, {S.ServiceReviews.DUE_DATE}, 
                        {S.ServiceReviews.DISCIPLINES}, {S.ServiceReviews.DELIVERABLES}, 
                        {S.ServiceReviews.STATUS}, {S.ServiceReviews.WEIGHT_FACTOR}, 
                        {S.ServiceReviews.EVIDENCE_LINKS}, {S.ServiceReviews.INVOICE_REFERENCE}, 
                        {S.ServiceReviews.SOURCE_PHASE}, {S.ServiceReviews.BILLING_PHASE}, 
                        {S.ServiceReviews.BILLING_RATE}, {S.ServiceReviews.BILLING_AMOUNT},
                        {S.ServiceReviews.IS_BILLED}
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        service_id, cycle_no, planned_date, due_date, disciplines,
                        deliverables, status, final_weight, evidence_links, invoice_reference,
                        final_source_phase, final_billing_phase, effective_rate, effective_amount,
                        int(bool(effective_is_billed))
                    )
                )
            else:
                cursor.execute(
                    f"""
                    INSERT INTO {S.ServiceReviews.TABLE} (
                        {S.ServiceReviews.SERVICE_ID}, {S.ServiceReviews.CYCLE_NO}, 
                        {S.ServiceReviews.PLANNED_DATE}, {S.ServiceReviews.DUE_DATE}, 
                        {S.ServiceReviews.DISCIPLINES}, {S.ServiceReviews.DELIVERABLES}, 
                        {S.ServiceReviews.STATUS}, {S.ServiceReviews.WEIGHT_FACTOR}, 
                        {S.ServiceReviews.EVIDENCE_LINKS}, {S.ServiceReviews.INVOICE_REFERENCE}, 
                        {S.ServiceReviews.IS_BILLED}
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        service_id, cycle_no, planned_date, due_date, disciplines,
                        deliverables, status, final_weight, evidence_links, invoice_reference,
                        int(bool(effective_is_billed))
                    )
                )
            conn.commit()
            return cursor.lastrowid
    except Exception as e:
        logger.error(f"Error creating service review: {e}")
        return None


def _parse_iso_date(value):
    """Parse ISO date string (YYYY-MM-DD) or return None. Raises ValueError if invalid."""
    if value is None or value == '':
        return None
    if isinstance(value, date):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        try:
            return datetime.strptime(value.strip(), '%Y-%m-%d').date()
        except ValueError:
            raise ValueError(f"Invalid date format '{value}'. Expected YYYY-MM-DD.")
    raise ValueError(f"Invalid date value: {value!r}")


def update_service_review(review_id, **kwargs):
    """Update an existing service review with validation for deliverables fields.
    
    Supported fields:
    - due_date: DATE/nullable (ISO format YYYY-MM-DD)
    - status: nvarchar (max 60 chars)
    - invoice_reference: nvarchar
    - invoice_date: DATE/nullable (ISO format YYYY-MM-DD)
    - is_billed: boolean
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            supports_billing = _ensure_service_review_billing_columns(cursor)
            update_fields = {}
            allowed_fields = [
                S.ServiceReviews.CYCLE_NO, S.ServiceReviews.PLANNED_DATE, 
                S.ServiceReviews.DUE_DATE, S.ServiceReviews.DISCIPLINES, 
                S.ServiceReviews.DELIVERABLES, S.ServiceReviews.STATUS, 
                S.ServiceReviews.WEIGHT_FACTOR, S.ServiceReviews.EVIDENCE_LINKS, 
                S.ServiceReviews.INVOICE_REFERENCE, S.ServiceReviews.INVOICE_DATE,
                S.ServiceReviews.ACTUAL_ISSUED_AT, 
                S.ServiceReviews.IS_BILLED
            ]
            if supports_billing:
                allowed_fields.extend([
                    S.ServiceReviews.SOURCE_PHASE, S.ServiceReviews.BILLING_PHASE,
                    S.ServiceReviews.BILLING_RATE, S.ServiceReviews.BILLING_AMOUNT
                ])
            
            status_update = None
            for key, value in kwargs.items():
                if key in allowed_fields:
                    if key == S.ServiceReviews.STATUS:
                        status_update = (value or '').lower()
                        # Trim to max 60 chars
                        trimmed = (value or '').strip()[:60]
                        update_fields[key] = trimmed
                    elif key == S.ServiceReviews.IS_BILLED:
                        # Convert to boolean int (0 or 1)
                        update_fields[key] = 1 if value else 0
                    elif key in (S.ServiceReviews.DUE_DATE, S.ServiceReviews.INVOICE_DATE):
                        # Parse and validate ISO dates
                        try:
                            parsed_date = _parse_iso_date(value)
                            update_fields[key] = parsed_date.strftime('%Y-%m-%d') if parsed_date else None
                        except ValueError as e:
                            logger.error(f"Invalid date for {key}: {e}")
                            # Skip invalid date but don't fail the update
                            continue
                    elif supports_billing and key in (S.ServiceReviews.BILLING_RATE, S.ServiceReviews.BILLING_AMOUNT, S.ServiceReviews.WEIGHT_FACTOR):
                        try:
                            update_fields[key] = float(value) if value is not None else None
                        except (ValueError, TypeError):
                            update_fields[key] = None
                    elif key == S.ServiceReviews.WEIGHT_FACTOR:
                        try:
                            update_fields[key] = float(value) if value is not None else None
                        except (ValueError, TypeError):
                            update_fields[key] = None
                    else:
                        update_fields[key] = value
            
            if status_update is not None and S.ServiceReviews.IS_BILLED not in update_fields:
                # Auto-align billed flag with completed status if not explicitly provided.
                update_fields[S.ServiceReviews.IS_BILLED] = 1 if status_update == 'completed' else 0

            if supports_billing:
                needs_recalc_amount = False
                if S.ServiceReviews.BILLING_AMOUNT not in update_fields:
                    if any(field in update_fields for field in (S.ServiceReviews.BILLING_RATE, S.ServiceReviews.WEIGHT_FACTOR)):
                        needs_recalc_amount = True

                if needs_recalc_amount:
                    cursor.execute(
                        f"""
                        SELECT {S.ServiceReviews.BILLING_RATE}, {S.ServiceReviews.WEIGHT_FACTOR}
                        FROM {S.ServiceReviews.TABLE}
                        WHERE {S.ServiceReviews.REVIEW_ID} = ?
                        """,
                        (review_id,)
                    )
                    current_values = cursor.fetchone()
                    current_rate = current_values[0] if current_values else 0
                    current_weight = current_values[1] if current_values else 1
                    new_rate = update_fields.get(S.ServiceReviews.BILLING_RATE, current_rate)
                    new_weight = update_fields.get(S.ServiceReviews.WEIGHT_FACTOR, current_weight)
                    try:
                        new_amount = float(Decimal(str(new_rate or 0)) * Decimal(str(new_weight or 1)))
                    except (InvalidOperation, ValueError, TypeError):
                        new_amount = float(new_rate or 0) * float(new_weight or 1)
                    update_fields[S.ServiceReviews.BILLING_AMOUNT] = new_amount
            
            if not update_fields:
                return False
                
            set_clause = ', '.join([f"{field} = ?" for field in update_fields.keys()])
            values = [int(bool(v)) if key == S.ServiceReviews.IS_BILLED else v
                      for key, v in update_fields.items()] + [review_id]
            cursor.execute(
                f"UPDATE {S.ServiceReviews.TABLE} SET {set_clause} WHERE {S.ServiceReviews.REVIEW_ID} = ?",
                values
            )
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"Error updating service review: {e}")
        return False


def get_service_review_billing(project_id, start_date=None, end_date=None, date_field='actual_issued_at'):
    """Return detailed review-level billing data for a project, including monthly summaries."""
    date_field = (date_field or 'actual_issued_at').lower()
    valid_fields = {'actual_issued_at', 'planned_date', 'due_date'}
    if date_field not in valid_fields:
        raise ValueError("date_field must be one of 'actual_issued_at', 'planned_date', or 'due_date'")

    def _coerce_date(value):
        if value is None or value == '':
            return None
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value).date()
            except ValueError:
                try:
                    return datetime.strptime(value, '%Y-%m-%d').date()
                except ValueError as exc:
                    raise ValueError(f"Invalid date format '{value}'. Use YYYY-MM-DD.") from exc
        raise ValueError(f"Unsupported date value: {value!r}")

    start_dt = _coerce_date(start_date)
    end_dt = _coerce_date(end_date)

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            if date_field == 'actual_issued_at':
                billing_expr = f"COALESCE(sr.{S.ServiceReviews.ACTUAL_ISSUED_AT}, sr.{S.ServiceReviews.PLANNED_DATE})"
            elif date_field == 'planned_date':
                billing_expr = f"sr.{S.ServiceReviews.PLANNED_DATE}"
            else:
                billing_expr = f"sr.{S.ServiceReviews.DUE_DATE}"

            filters = [f"ps.{S.ProjectServices.PROJECT_ID} = ?"]
            params = [project_id]
            if start_dt:
                filters.append(f"CAST(({billing_expr}) AS DATE) >= ?")
                params.append(start_dt.strftime('%Y-%m-%d'))
            if end_dt:
                filters.append(f"CAST(({billing_expr}) AS DATE) <= ?")
                params.append(end_dt.strftime('%Y-%m-%d'))

            where_clause = " AND ".join(filters)

            cursor.execute(
                f"""
                SELECT sr.{S.ServiceReviews.REVIEW_ID}, sr.{S.ServiceReviews.SERVICE_ID},
                       ps.{S.ProjectServices.SERVICE_NAME}, ps.{S.ProjectServices.PHASE},
                       sr.{S.ServiceReviews.CYCLE_NO}, sr.{S.ServiceReviews.STATUS},
                       sr.{S.ServiceReviews.SOURCE_PHASE}, sr.{S.ServiceReviews.BILLING_PHASE},
                       sr.{S.ServiceReviews.BILLING_RATE}, sr.{S.ServiceReviews.BILLING_AMOUNT},
                       sr.{S.ServiceReviews.WEIGHT_FACTOR}, sr.{S.ServiceReviews.PLANNED_DATE},
                       sr.{S.ServiceReviews.DUE_DATE}, sr.{S.ServiceReviews.ACTUAL_ISSUED_AT},
                       {billing_expr} AS billing_reference_date,
                       sr.{S.ServiceReviews.INVOICE_REFERENCE}, sr.{S.ServiceReviews.IS_BILLED}
                FROM {S.ServiceReviews.TABLE} sr
                INNER JOIN {S.ProjectServices.TABLE} ps
                    ON sr.{S.ServiceReviews.SERVICE_ID} = ps.{S.ProjectServices.SERVICE_ID}
                WHERE {where_clause}
                ORDER BY billing_reference_date, sr.{S.ServiceReviews.REVIEW_ID}
                """,
                params
            )
            rows = cursor.fetchall()
    except pyodbc.Error as exc:
        logger.error(f"Error fetching review billing data: {exc}")
        return {
            'reviews': [],
            'summary_by_phase': [],
            'monthly_totals': [],
            'total_amount': 0.0,
            'total_reviews': 0
        }

    reviews: List[Dict[str, Any]] = []
    phase_summary: Dict[Tuple[str, str], Dict[str, Any]] = {}
    monthly_totals: Dict[str, Dict[str, Any]] = {}
    total_amount = 0.0

    for row in rows:
        billing_rate = float(row[8]) if row[8] is not None else 0.0
        billing_amount = float(row[9]) if row[9] is not None else 0.0
        billing_rate = round(billing_rate, 2)
        billing_amount = round(billing_amount, 2)
        weight_factor = float(row[10]) if row[10] is not None else None
        planned = row[11]
        due = row[12]
        issued = row[13]
        billing_date_value = row[14]

        if isinstance(billing_date_value, datetime):
            billing_date = billing_date_value.date()
        elif isinstance(billing_date_value, date):
            billing_date = billing_date_value
        else:
            billing_date = None

        billing_date_iso = billing_date.isoformat() if billing_date else None

        review = {
            'review_id': row[0],
            'service_id': row[1],
            'service_name': row[2],
            'service_phase': row[3],
            'cycle_no': row[4],
            'status': row[5],
            'source_phase': row[6],
            'billing_phase': row[7],
            'billing_rate': billing_rate,
            'billing_amount': billing_amount,
            'weight_factor': weight_factor,
            'planned_date': planned.isoformat() if isinstance(planned, (datetime, date)) else planned,
            'due_date': due.isoformat() if isinstance(due, (datetime, date)) else due,
            'actual_issued_at': issued.isoformat() if isinstance(issued, (datetime, date)) else issued,
            'billing_date': billing_date_iso,
            'invoice_reference': row[15],
            'is_billed': bool(row[16])
        }
        reviews.append(review)

        total_amount += billing_amount

        summary_key = (review['billing_phase'] or 'Unassigned', review['source_phase'] or 'Unassigned')
        summary_entry = phase_summary.setdefault(summary_key, {
            'billing_phase': summary_key[0],
            'source_phase': summary_key[1],
            'review_count': 0,
            'total_amount': 0.0,
            'slipped_count': 0,
            'slipped_amount': 0.0
        })
        summary_entry['review_count'] += 1
        summary_entry['total_amount'] += billing_amount
        if summary_key[0] != summary_key[1]:
            summary_entry['slipped_count'] += 1
            summary_entry['slipped_amount'] += billing_amount

        period_key = billing_date.strftime('%Y-%m') if billing_date else 'Unscheduled'
        month_entry = monthly_totals.setdefault(period_key, {'period': period_key, 'review_count': 0, 'total_amount': 0.0})
        month_entry['review_count'] += 1
        month_entry['total_amount'] += billing_amount

    summary_by_phase = []
    for entry in phase_summary.values():
        entry['total_amount'] = round(entry['total_amount'], 2)
        entry['slipped_amount'] = round(entry['slipped_amount'], 2)
        summary_by_phase.append(entry)
    summary_by_phase.sort(key=lambda item: (item['billing_phase'] or '', item['source_phase'] or ''))

    monthly_summary = []
    for entry in sorted(monthly_totals.values(), key=lambda item: item['period']):
        entry['total_amount'] = round(entry['total_amount'], 2)
        monthly_summary.append(entry)

    return {
        'reviews': reviews,
        'summary_by_phase': summary_by_phase,
        'monthly_totals': monthly_summary,
        'total_amount': round(total_amount, 2),
        'total_reviews': len(reviews)
    }
def delete_service_review(review_id):
    """Delete a service review."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"DELETE FROM {S.ServiceReviews.TABLE} WHERE {S.ServiceReviews.REVIEW_ID} = ?",
                (review_id,)
            )
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"Error deleting service review: {e}")
        return False


# ===================== Service Items Functions =====================

def get_service_items(service_id, item_type=None):
    """Get service items for a service, optionally filtered by type."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            invoice_supported = _ensure_service_item_invoice_column(cursor)
            
            columns = [
                S.ServiceItems.ITEM_ID,
                S.ServiceItems.SERVICE_ID,
                S.ServiceItems.ITEM_TYPE,
                S.ServiceItems.TITLE,
                S.ServiceItems.DESCRIPTION,
                S.ServiceItems.PLANNED_DATE,
                S.ServiceItems.DUE_DATE,
                S.ServiceItems.ACTUAL_DATE,
                S.ServiceItems.STATUS,
                S.ServiceItems.PRIORITY,
                S.ServiceItems.ASSIGNED_TO,
            ]
            if invoice_supported:
                columns.append(S.ServiceItems.INVOICE_REFERENCE)
            columns.extend([
                S.ServiceItems.EVIDENCE_LINKS,
                S.ServiceItems.NOTES,
                S.ServiceItems.CREATED_AT,
                S.ServiceItems.UPDATED_AT,
                S.ServiceItems.IS_BILLED,
            ])

            query = f"""
                SELECT {', '.join(columns)}
                FROM {S.ServiceItems.TABLE}
                WHERE {S.ServiceItems.SERVICE_ID} = ?
            """
            params = [service_id]
            
            if item_type:
                query += f" AND {S.ServiceItems.ITEM_TYPE} = ?"
                params.append(item_type)
            
            query += f" ORDER BY {S.ServiceItems.PLANNED_DATE} ASC"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            items = []
            for row in rows:
                idx = 0
                item_id = row[idx]; idx += 1
                service_id = row[idx]; idx += 1
                item_type = row[idx]; idx += 1
                title = row[idx]; idx += 1
                description = row[idx]; idx += 1
                planned_date = row[idx]; idx += 1
                due_date = row[idx]; idx += 1
                actual_date = row[idx]; idx += 1
                status = row[idx]; idx += 1
                priority = row[idx]; idx += 1
                assigned_to = row[idx]; idx += 1

                invoice_reference = None
                if invoice_supported:
                    invoice_reference = row[idx]
                    idx += 1

                evidence_links = row[idx]; idx += 1
                notes = row[idx]; idx += 1
                created_at = row[idx]; idx += 1
                updated_at = row[idx]; idx += 1
                is_billed_val = row[idx] if idx < len(row) else None

                items.append({
                    'item_id': item_id,
                    'service_id': service_id,
                    'item_type': item_type,
                    'title': title,
                    'description': description,
                    'planned_date': planned_date.isoformat() if planned_date else None,
                    'due_date': due_date.isoformat() if due_date else None,
                    'actual_date': actual_date.isoformat() if actual_date else None,
                    'status': status,
                    'priority': priority,
                    'assigned_to': assigned_to,
                    'invoice_reference': invoice_reference,
                    'evidence_links': evidence_links,
                    'notes': notes,
                    'created_at': created_at.isoformat() if created_at else None,
                    'updated_at': updated_at.isoformat() if updated_at else None,
                    'is_billed': bool(is_billed_val) if is_billed_val is not None else False,
                })
            
            return items
            
    except Exception as e:
        logger.error(f"Error fetching service items: {e}")
        return []


def create_service_item(service_id, item_type, title, planned_date, **kwargs):
    """Create a new service item."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            invoice_supported = _ensure_service_item_invoice_column(cursor)
            
            # Build dynamic insert query
            columns = [S.ServiceItems.SERVICE_ID, S.ServiceItems.ITEM_TYPE, S.ServiceItems.TITLE, 
                      S.ServiceItems.PLANNED_DATE, S.ServiceItems.CREATED_AT, S.ServiceItems.UPDATED_AT]
            values = [service_id, item_type, title, planned_date, datetime.now(), datetime.now()]
            placeholders = ['?'] * len(values)

            if 'is_billed' not in kwargs or kwargs.get('is_billed') is None:
                status_hint = kwargs.get('status')
                if status_hint and status_hint.lower() == 'completed':
                    kwargs['is_billed'] = 1
                else:
                    kwargs['is_billed'] = 0
            
            # Add optional fields
            optional_fields = {
                'description': S.ServiceItems.DESCRIPTION,
                'due_date': S.ServiceItems.DUE_DATE,
                'actual_date': S.ServiceItems.ACTUAL_DATE,
                'status': S.ServiceItems.STATUS,
                'priority': S.ServiceItems.PRIORITY,
                'assigned_to': S.ServiceItems.ASSIGNED_TO,
                'evidence_links': S.ServiceItems.EVIDENCE_LINKS,
                'notes': S.ServiceItems.NOTES,
                'is_billed': S.ServiceItems.IS_BILLED
            }
            if invoice_supported:
                optional_fields['invoice_reference'] = S.ServiceItems.INVOICE_REFERENCE
            
            for field, column in optional_fields.items():
                if field in kwargs and kwargs[field] is not None:
                    columns.append(column)
                    if field == 'is_billed':
                        values.append(int(bool(kwargs[field])))
                    else:
                        values.append(kwargs[field])
                    placeholders.append('?')
            
            query = f"""
                INSERT INTO {S.ServiceItems.TABLE} ({', '.join(columns)})
                VALUES ({', '.join(placeholders)})
            """
            
            cursor.execute(query, values)
            conn.commit()
            
            # Get the inserted item ID
            cursor.execute("SELECT @@IDENTITY")
            item_id = cursor.fetchone()[0]
            
            return item_id
            
    except Exception as e:
        logger.error(f"Error creating service item: {e}")
        return None


def update_service_item(item_id, **kwargs):
    """Update a service item."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            invoice_supported = _ensure_service_item_invoice_column(cursor)
            
            # Build dynamic update query
            updates = []
            values = []
            status_update = None
            
            field_mappings = {
                'item_type': S.ServiceItems.ITEM_TYPE,
                'title': S.ServiceItems.TITLE,
                'description': S.ServiceItems.DESCRIPTION,
                'planned_date': S.ServiceItems.PLANNED_DATE,
                'due_date': S.ServiceItems.DUE_DATE,
                'actual_date': S.ServiceItems.ACTUAL_DATE,
                'status': S.ServiceItems.STATUS,
                'priority': S.ServiceItems.PRIORITY,
                'assigned_to': S.ServiceItems.ASSIGNED_TO,
                'evidence_links': S.ServiceItems.EVIDENCE_LINKS,
                'notes': S.ServiceItems.NOTES,
                'is_billed': S.ServiceItems.IS_BILLED
            }
            if invoice_supported:
                field_mappings['invoice_reference'] = S.ServiceItems.INVOICE_REFERENCE
            
            for field, column in field_mappings.items():
                if field in kwargs:
                    updates.append(f"{column} = ?")
                    if field == 'is_billed':
                        values.append(int(bool(kwargs[field])))
                    else:
                        if field == 'status':
                            status_update = (kwargs[field] or '').lower()
                        values.append(kwargs[field])
            
            if status_update is not None and 'is_billed' not in kwargs:
                updates.append(f"{S.ServiceItems.IS_BILLED} = ?")
                values.append(1 if status_update == 'completed' else 0)
            
            if not updates:
                return False
            
            # Always update the updated_at timestamp
            updates.append(f"{S.ServiceItems.UPDATED_AT} = ?")
            values.append(datetime.now())
            
            query = f"""
                UPDATE {S.ServiceItems.TABLE}
                SET {', '.join(updates)}
                WHERE {S.ServiceItems.ITEM_ID} = ?
            """
            values.append(item_id)
            
            cursor.execute(query, values)
            conn.commit()
            
            return cursor.rowcount > 0
            
    except Exception as e:
        logger.error(f"Error updating service item: {e}")
        return False


def delete_service_item(item_id):
    """Delete a service item."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"DELETE FROM {S.ServiceItems.TABLE} WHERE {S.ServiceItems.ITEM_ID} = ?",
                (item_id,)
            )
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"Error deleting service item: {e}")
        return False


def get_service_items_statistics(service_id=None):
    """Get statistics for service items, optionally filtered by service."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            where_clause = ""
            params = []
            if service_id:
                where_clause = f"WHERE {S.ServiceItems.SERVICE_ID} = ?"
                params = [service_id]
            
            query = f"""
                SELECT 
                    {S.ServiceItems.ITEM_TYPE},
                    COUNT(*) as total_items,
                    SUM(CASE WHEN {S.ServiceItems.STATUS} = 'completed' THEN 1 ELSE 0 END) as completed_items,
                    SUM(CASE WHEN {S.ServiceItems.STATUS} = 'in_progress' THEN 1 ELSE 0 END) as in_progress_items,
                    SUM(CASE WHEN {S.ServiceItems.STATUS} = 'planned' THEN 1 ELSE 0 END) as planned_items,
                    SUM(CASE WHEN {S.ServiceItems.STATUS} = 'overdue' THEN 1 ELSE 0 END) as overdue_items,
                    SUM(CASE WHEN {S.ServiceItems.STATUS} = 'cancelled' THEN 1 ELSE 0 END) as cancelled_items,
                    MIN({S.ServiceItems.PLANNED_DATE}) as earliest_date,
                    MAX({S.ServiceItems.PLANNED_DATE}) as latest_date,
                    COUNT(CASE WHEN {S.ServiceItems.PLANNED_DATE} >= GETDATE() AND {S.ServiceItems.PLANNED_DATE} <= DATEADD(day, 30, GETDATE()) THEN 1 END) as upcoming_30_days
                FROM {S.ServiceItems.TABLE}
                {where_clause}
                GROUP BY {S.ServiceItems.ITEM_TYPE}
            """
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            stats = {}
            for row in rows:
                item_type = row[0]
                stats[item_type] = {
                    'total_items': row[1],
                    'completed_items': row[2] or 0,
                    'in_progress_items': row[3] or 0,
                    'planned_items': row[4] or 0,
                    'overdue_items': row[5] or 0,
                    'cancelled_items': row[6] or 0,
                    'earliest_date': row[7].isoformat() if row[7] else None,
                    'latest_date': row[8].isoformat() if row[8] else None,
                    'upcoming_30_days': row[9] or 0
                }
            
            return stats
            
    except Exception as e:
        logger.error(f"Error fetching service items statistics: {e}")
        return {}


import json
import pyodbc
import os
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal, InvalidOperation
from datetime import datetime, timedelta, date, time
from typing import Any, Dict, List, Optional, Tuple
from time import time as unix_time, perf_counter
import threading
from dataclasses import dataclass, field

from config import Config
import logging
from constants import schema as S
from database_pool import get_db_connection, connect_to_db  # Import both for gradual migration

logger = logging.getLogger(__name__)


@dataclass
class _WarehouseMetricsCacheEntry:
    data: Optional[Dict[str, Any]] = None
    expires_at: float = 0.0
    last_updated: float = 0.0
    lock: threading.Lock = field(default_factory=threading.Lock)


@dataclass
class _DashboardCacheEntry:
    data: Optional[Dict[str, Any]] = None
    expires_at: float = 0.0
    last_updated: float = 0.0
    lock: threading.Lock = field(default_factory=threading.Lock)


_WAREHOUSE_METRICS_CACHE: Dict[tuple, _WarehouseMetricsCacheEntry] = {}
_WAREHOUSE_METRICS_CACHE_LOCK = threading.Lock()
_WAREHOUSE_METRICS_CACHE_TTL_SECONDS = 300
_WAREHOUSE_METRICS_CACHE_MAX_ENTRIES = int(os.getenv("WAREHOUSE_METRICS_CACHE_MAX_ENTRIES", "64"))
_WAREHOUSE_ISSUE_TRENDS_DAYS = int(os.getenv("WAREHOUSE_ISSUE_TRENDS_DAYS", "90"))
_WAREHOUSE_METRICS_LOG_TIMINGS = os.getenv("WAREHOUSE_METRICS_LOG_TIMINGS", "1") == "1"
_WAREHOUSE_METRICS_AUX_TIMEOUT = int(os.getenv("WAREHOUSE_METRICS_AUX_TIMEOUT", "5"))
_WAREHOUSE_METRICS_AUX_BUDGET = float(os.getenv("WAREHOUSE_METRICS_AUX_BUDGET", "5"))
_WAREHOUSE_METRICS_QUERY_TIMEOUT = int(os.getenv("WAREHOUSE_METRICS_QUERY_TIMEOUT", "10"))
_DASHBOARD_QUERY_TIMEOUT = int(os.getenv("DASHBOARD_QUERY_TIMEOUT", "10"))
_DASHBOARD_CACHE_TTL_SECONDS = int(os.getenv("DASHBOARD_CACHE_TTL_SECONDS", "60"))
_DASHBOARD_CACHE_MAX_ENTRIES = int(os.getenv("DASHBOARD_CACHE_MAX_ENTRIES", "128"))
_DASHBOARD_CACHE: Dict[tuple, _DashboardCacheEntry] = {}
_DASHBOARD_CACHE_LOCK = threading.Lock()
_table_exists_cache: Dict[Tuple[str, str, Optional[str]], bool] = {}


def _set_cursor_timeout(cursor, seconds: int) -> None:
    """Best-effort timeout setter for pyodbc cursors."""
    try:
        cursor.timeout = max(int(seconds), 1)
    except Exception:
        return


def _normalize_id_tuple(values: Optional[List[int]]) -> tuple:
    if not values:
        return ()
    normalized = set()
    for value in values:
        if value is None:
            continue
        try:
            normalized.add(int(value))
        except (TypeError, ValueError):
            continue
    return tuple(sorted(normalized))


def _warehouse_metrics_cache_key(
    project_ids: Optional[List[int]],
    client_ids: Optional[List[int]],
    project_type_ids: Optional[List[int]],
) -> tuple:
    return (
        _normalize_id_tuple(project_ids),
        _normalize_id_tuple(client_ids),
        _normalize_id_tuple(project_type_ids),
    )


def _get_or_create_cache_entry(cache_key: tuple) -> _WarehouseMetricsCacheEntry:
    with _WAREHOUSE_METRICS_CACHE_LOCK:
        entry = _WAREHOUSE_METRICS_CACHE.get(cache_key)
        if entry is None:
            entry = _WarehouseMetricsCacheEntry()
            _WAREHOUSE_METRICS_CACHE[cache_key] = entry
            _evict_cache_if_needed_locked()
        return entry


def _evict_cache_if_needed_locked() -> None:
    if len(_WAREHOUSE_METRICS_CACHE) <= _WAREHOUSE_METRICS_CACHE_MAX_ENTRIES:
        return
    oldest_key = min(
        _WAREHOUSE_METRICS_CACHE,
        key=lambda key: _WAREHOUSE_METRICS_CACHE[key].last_updated or 0,
    )
    del _WAREHOUSE_METRICS_CACHE[oldest_key]


def _get_or_create_dashboard_cache_entry(cache_key: tuple) -> _DashboardCacheEntry:
    with _DASHBOARD_CACHE_LOCK:
        entry = _DASHBOARD_CACHE.get(cache_key)
        if entry is None:
            entry = _DashboardCacheEntry()
            _DASHBOARD_CACHE[cache_key] = entry
            _evict_dashboard_cache_if_needed_locked()
        return entry


def _evict_dashboard_cache_if_needed_locked() -> None:
    if len(_DASHBOARD_CACHE) <= _DASHBOARD_CACHE_MAX_ENTRIES:
        return
    oldest_key = min(
        _DASHBOARD_CACHE,
        key=lambda key: _DASHBOARD_CACHE[key].last_updated or 0,
    )
    del _DASHBOARD_CACHE[oldest_key]


def _dashboard_cache_key(name: str, *parts: Any) -> tuple:
    return (name,) + parts


def _get_dashboard_cached_value(cache_key: tuple, compute_fn):
    entry = _get_or_create_dashboard_cache_entry(cache_key)
    now = unix_time()
    if entry.data and entry.expires_at > now:
        return entry.data

    if not entry.lock.acquire(blocking=False):
        if entry.data:
            return entry.data
        entry.lock.acquire()
        try:
            return entry.data
        finally:
            entry.lock.release()

    try:
        result = compute_fn()
        entry.data = result
        entry.expires_at = unix_time() + _DASHBOARD_CACHE_TTL_SECONDS
        entry.last_updated = unix_time()
        return result
    finally:
        entry.lock.release()
        with _DASHBOARD_CACHE_LOCK:
            _evict_dashboard_cache_if_needed_locked()


def _get_latest_successful_issue_run(cursor) -> tuple[Optional[int], Optional[str]]:
    """Return latest successful issue import run id and snapshot date."""
    cursor.execute(
        f"""
        SELECT TOP 1 {S.IssueImportRuns.IMPORT_RUN_ID}
        FROM dbo.{S.IssueImportRuns.TABLE}
        WHERE {S.IssueImportRuns.STATUS} = 'success'
        ORDER BY {S.IssueImportRuns.COMPLETED_AT} DESC
        """
    )
    row = cursor.fetchone()
    if not row or row[0] is None:
        return None, None
    run_id = int(row[0])
    cursor.execute(
        f"""
        SELECT MAX({S.IssuesSnapshots.SNAPSHOT_DATE})
        FROM dbo.{S.IssuesSnapshots.TABLE}
        WHERE {S.IssuesSnapshots.IMPORT_RUN_ID} = ?
        """,
        (run_id,),
    )
    snapshot_row = cursor.fetchone()
    as_of = snapshot_row[0].isoformat() if snapshot_row and snapshot_row[0] else None
    return run_id, as_of


def _get_latest_issue_snapshot_date(cursor) -> Optional[str]:
    """Return the latest issue snapshot date as ISO string."""
    _, as_of = _get_latest_successful_issue_run(cursor)
    return as_of


def get_issue_reliability_report() -> Dict[str, Any]:
    """Return latest issue import run summary plus data-quality checks."""
    try:
        with get_db_connection(Config.WAREHOUSE_DB) as conn:
            cursor = conn.cursor()

            cursor.execute(
                f"""
                SELECT TOP 1
                    {S.IssueImportRuns.IMPORT_RUN_ID},
                    {S.IssueImportRuns.STATUS},
                    {S.IssueImportRuns.STARTED_AT},
                    {S.IssueImportRuns.COMPLETED_AT},
                    {S.IssueImportRuns.ROW_COUNT},
                    {S.IssueImportRuns.NOTES}
                FROM dbo.{S.IssueImportRuns.TABLE}
                ORDER BY {S.IssueImportRuns.COMPLETED_AT} DESC
                """
            )
            run_row = cursor.fetchone()
            if not run_row:
                return {"run": None, "checks": [], "counts": {}, "unmapped_statuses": []}

            run_id = int(run_row[0])
            run_payload = {
                "import_run_id": run_id,
                "status": run_row[1],
                "started_at": run_row[2].isoformat() if run_row[2] else None,
                "completed_at": run_row[3].isoformat() if run_row[3] else None,
                "row_count": int(run_row[4]) if run_row[4] is not None else None,
                "notes": run_row[5],
            }

            cursor.execute(
                f"""
                SELECT
                    {S.IssueDataQualityResults.CHECK_NAME},
                    {S.IssueDataQualityResults.SEVERITY},
                    {S.IssueDataQualityResults.PASSED},
                    {S.IssueDataQualityResults.DETAILS},
                    {S.IssueDataQualityResults.CHECKED_AT}
                FROM dbo.{S.IssueDataQualityResults.TABLE}
                WHERE {S.IssueDataQualityResults.IMPORT_RUN_ID} = ?
                ORDER BY {S.IssueDataQualityResults.CHECK_NAME}
                """,
                (run_id,),
            )
            checks = [
                {
                    "check_name": row[0],
                    "severity": row[1],
                    "passed": bool(row[2]),
                    "details": row[3],
                    "checked_at": row[4].isoformat() if row[4] else None,
                }
                for row in cursor.fetchall()
            ]

            cursor.execute(
                f"SELECT COUNT(*) FROM dbo.{S.IssuesCurrent.TABLE}"
            )
            current_count_row = cursor.fetchone()
            current_count = int(current_count_row[0] or 0)

            cursor.execute(
                f"SELECT COUNT(*) FROM dbo.{S.IssuesSnapshots.TABLE} WHERE {S.IssuesSnapshots.IMPORT_RUN_ID} = ?",
                (run_id,),
            )
            snapshot_count_row = cursor.fetchone()
            snapshot_count = int(snapshot_count_row[0] or 0)

            cursor.execute(
                """
                WITH raw_statuses AS (
                    SELECT
                        i.source_system,
                        LOWER(LTRIM(RTRIM(i.status))) AS raw_status,
                        COUNT(*) AS issue_count
                    FROM dim.issue i
                    WHERE i.current_flag = 1
                      AND i.status IS NOT NULL
                    GROUP BY i.source_system, LOWER(LTRIM(RTRIM(i.status)))
                )
                SELECT
                    r.source_system,
                    r.raw_status,
                    r.issue_count
                FROM raw_statuses r
                LEFT JOIN dbo.issue_status_map m
                    ON m.source_system = r.source_system
                   AND m.raw_status = r.raw_status
                   AND m.is_active = 1
                WHERE m.raw_status IS NULL
                ORDER BY r.source_system, r.issue_count DESC
                """
            )
            unmapped = [
                {
                    "source_system": row[0],
                    "raw_status": row[1],
                    "issue_count": int(row[2] or 0),
                }
                for row in cursor.fetchall()
            ]

            return {
                "run": run_payload,
                "checks": checks,
                "counts": {
                    "issues_current": current_count,
                    "issues_snapshots": snapshot_count,
                },
                "unmapped_statuses": unmapped,
            }
    except Exception as e:
        logger.error("Error fetching issue reliability report: %s", e)
        return {"run": None, "checks": [], "counts": {}, "unmapped_statuses": []}

_table_column_cache: Dict[Tuple[str, str, Optional[str]], bool] = {}
_control_model_metadata_supported: Optional[bool] = None
_service_review_billing_columns_ready: Optional[bool] = None
_service_item_invoice_column_ready: Optional[bool] = None
_SERVICE_REVIEW_BILLING_COLUMN_DEFINITIONS = [
    (S.ServiceReviews.SOURCE_PHASE, "NVARCHAR(200) NULL"),
    (S.ServiceReviews.BILLING_PHASE, "NVARCHAR(200) NULL"),
    (S.ServiceReviews.BILLING_RATE, "DECIMAL(18,2) NULL"),
    (S.ServiceReviews.BILLING_AMOUNT, "DECIMAL(18,2) NULL"),
]


def _serialize_datetime(value):
    """
    Safely serialize datetime/date values (including pyodbc/pandas types) to ISO strings.
    Falls back to str() for unexpected values.
    """
    if value is None:
        return None
    try:
        if isinstance(value, (datetime, date)):
            return value.isoformat()
    except Exception:
        pass
    try:
        return value.isoformat()
    except Exception:
        return str(value)


def _ensure_control_model_metadata_column(conn) -> bool:
    """Ensure tblControlModels has metadata_json column for storing structured data."""
    global _control_model_metadata_supported
    if _control_model_metadata_supported:
        return True
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT 1
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = 'dbo'
              AND TABLE_NAME = 'tblControlModels'
              AND COLUMN_NAME = 'metadata_json'
            """
        )
        exists = cursor.fetchone() is not None
        if not exists:
            cursor.execute(
                """
                ALTER TABLE ProjectManagement.dbo.tblControlModels
                ADD metadata_json NVARCHAR(MAX) NULL;
                """
            )
            try:
                conn.commit()
            except Exception:
                # Connection context managers typically commit on exit, but force it so the new column is persisted.
                pass
            cursor.execute(
                """
                SELECT 1
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = 'dbo'
                  AND TABLE_NAME = 'tblControlModels'
                  AND COLUMN_NAME = 'metadata_json'
                """
            )
            exists = cursor.fetchone() is not None
        _control_model_metadata_supported = exists
        return exists
    except Exception as exc:
        try:
            conn.rollback()
        except Exception:
            pass
        logger.warning("Control model metadata column unavailable: %s", exc)
        _control_model_metadata_supported = False
        return False


def _control_model_metadata_column_exists(conn) -> bool:
    """Check whether the metadata_json column exists on tblControlModels."""
    global _control_model_metadata_supported
    if _control_model_metadata_supported is not None:
        return _control_model_metadata_supported
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT 1
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = 'dbo'
              AND TABLE_NAME = 'tblControlModels'
              AND COLUMN_NAME = 'metadata_json'
            """
        )
        _control_model_metadata_supported = cursor.fetchone() is not None
    except Exception as exc:
        logger.warning("Failed to inspect tblControlModels metadata column: %s", exc)
        _control_model_metadata_supported = False
    return bool(_control_model_metadata_supported)


def _ensure_service_item_invoice_column(cursor) -> bool:
    """
    Ensure the ServiceItems table has the invoice_reference column.
    Keeps backward compatibility when migrations have not been applied yet.
    """
    global _service_item_invoice_column_ready
    if _service_item_invoice_column_ready is not None:
        return _service_item_invoice_column_ready

    table = S.ServiceItems.TABLE
    column = S.ServiceItems.INVOICE_REFERENCE
    try:
        cursor.execute(f"SELECT {column} FROM {table} WHERE 1 = 0")
        _service_item_invoice_column_ready = True
        return True
    except Exception:
        try:
            cursor.execute(f"ALTER TABLE {table} ADD {column} NVARCHAR(200) NULL")
            connection = getattr(cursor, 'connection', None)
            if connection:
                try:
                    connection.commit()
                except Exception:
                    pass
            _service_item_invoice_column_ready = True
            return True
        except Exception as exc:
            message = str(exc).lower()
            if 'duplicate' in message or 'exists' in message or 'already' in message:
                _service_item_invoice_column_ready = True
                return True
            logger.warning("Invoice reference column unavailable on ServiceItems: %s", exc)
            _service_item_invoice_column_ready = False
            return False

def connect_to_db(db_name=None):
    """Connect to the specified SQL Server database using environment settings."""
    try:
        driver = Config.DB_DRIVER
        server = Config.DB_SERVER
        user = Config.DB_USER
        password = Config.DB_PASSWORD
        database = db_name if db_name else Config.PROJECT_MGMT_DB

        conn_str = (
            f"DRIVER={{{driver}}};"
            f"SERVER={server};"
            f"UID={user};"
            f"PWD={password};"
            f"DATABASE={database};"
            "TrustServerCertificate=yes;"
        )

        connection = pyodbc.connect(conn_str)
        return connection

    except pyodbc.Error as e:
        print(f"❌ Database connection error ({db_name}): {e}")
        return None


    



def table_has_column(table_name: str, column_name: str, db_name: str | None = None) -> bool:
    """Check whether a given table contains the specified column."""
    key = (table_name.lower(), column_name.lower(), db_name.lower() if isinstance(db_name, str) else db_name)
    if key in _table_column_cache:
        return _table_column_cache[key]

    exists = False
    try:
        with get_db_connection(db_name) as conn:
            if conn is None:
                return False
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT 1
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = ? AND COLUMN_NAME = ?
                """,
                (table_name, column_name),
            )
            exists = cursor.fetchone() is not None
    except Exception as e:
        logger.error(f"Error checking column {table_name}.{column_name}: {e}")

    _table_column_cache[key] = exists
    return exists


def table_exists(table_name: str, schema: str = "dbo", db_name: str | None = None) -> bool:
    """Check whether a table exists in the given schema."""
    key = (schema.lower(), table_name.lower(), db_name.lower() if isinstance(db_name, str) else db_name)
    if key in _table_exists_cache:
        return _table_exists_cache[key]

    exists = False
    try:
        with get_db_connection(db_name) as conn:
            if conn is None:
                return False
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT 1
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?
                """,
                (schema, table_name),
            )
            exists = cursor.fetchone() is not None
    except Exception as e:
        logger.error("Error checking table %s.%s: %s", schema, table_name, e)

    _table_exists_cache[key] = exists
    return exists

def insert_project(project_name, folder_path, ifc_folder_path=None):
    """Insert a new project into the database with an optional IFC folder path."""
    if not os.path.exists(folder_path):
        logger.error(f"Folder does not exist: {folder_path}")
        return False

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            start_date = datetime.now().strftime('%Y-%m-%d')
            end_date = (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d')

            cursor.execute(
                f"""
                INSERT INTO {S.Projects.TABLE} (
                    {S.Projects.NAME}, {S.Projects.FOLDER_PATH}, {S.Projects.IFC_FOLDER_PATH},
                    {S.Projects.START_DATE}, {S.Projects.END_DATE}
                ) VALUES (?, ?, ?, ?, ?);
                """,
                (project_name, folder_path, ifc_folder_path, start_date, end_date),
            )

            conn.commit()
            logger.info(f"Project '{project_name}' inserted with IFC folder: {ifc_folder_path}")
            return True
    except pyodbc.Error as e:
        logger.error(f"Database Error inserting project: {e}")
        return False

def get_projects():
    """Fetch available projects."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT {S.Projects.ID}, {S.Projects.NAME} FROM {S.Projects.TABLE} ORDER BY {S.Projects.ID};"
            )
            projects = [(row[0], row[1]) for row in cursor.fetchall()]
            return projects
    except Exception as e:
        logger.error(f"Error fetching projects: {e}")
        return []

def get_project_details(project_id):
    """Fetch project details from the database including client information."""
    try:
        with get_db_connection("ProjectManagement") as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT p.{S.Projects.NAME}, p.{S.Projects.START_DATE}, p.{S.Projects.END_DATE}, 
                       p.{S.Projects.STATUS}, p.{S.Projects.PRIORITY}, p.{S.Projects.CONTRACT_NUMBER},
                       p.{S.Projects.AREA_HECTARES}, p.{S.Projects.MW_CAPACITY},
                       p.{S.Projects.ADDRESS}, p.{S.Projects.CITY}, p.{S.Projects.STATE}, p.{S.Projects.POSTCODE},
                       c.{S.Clients.CLIENT_NAME}, c.{S.Clients.CONTACT_NAME}, c.{S.Clients.CONTACT_EMAIL},
                       pt.{S.ProjectTypes.TYPE_NAME}
                FROM dbo.{S.Projects.TABLE} p
                LEFT JOIN dbo.{S.Clients.TABLE} c ON p.{S.Projects.CLIENT_ID} = c.{S.Clients.CLIENT_ID}
                LEFT JOIN dbo.{S.ProjectTypes.TABLE} pt ON p.{S.Projects.TYPE_ID} = pt.{S.ProjectTypes.TYPE_ID}
                WHERE p.{S.Projects.ID} = ?;
                """,
                (project_id,),
            )
            row = cursor.fetchone()
            
            if row:
                # Convert priority number to name
                priority_map = {1: 'Low', 2: 'Medium', 3: 'High', 4: 'Critical'}
                priority_name = priority_map.get(row[4], 'Medium')
                
                result = {
                    "project_name": row[0],
                    "start_date": row[1].strftime('%Y-%m-%d') if row[1] else "",
                    "end_date": row[2].strftime('%Y-%m-%d') if row[2] else "",
                    "status": row[3],
                    "priority": priority_name,
                    "contract_number": row[5],
                    "area": row[6],
                    "mw_capacity": row[7],
                    "address": row[8],
                    "city": row[9],
                    "state": row[10],
                    "postcode": row[11],
                    "client_name": row[12],
                    "client_contact": row[13],
                    "contact_email": row[14],
                    "project_type": row[15]
                }
                return result
            else:
                return None
    except Exception as e:
        logger.error(f"Error fetching project details: {e}")
        return None

def update_project_details(project_id, start_date, end_date, status, priority, notify_ui=None):
    """
    Update project start date, end date, status, and priority.
    
    This function now propagates date changes to related tables to maintain consistency:
    - ServiceScheduleSettings: Adjusts service-level start/end dates
    - ServiceReviews: Cancels reviews scheduled beyond new end_date
    - Tasks: Flags tasks with dates outside project bounds
    
    Args:
        project_id: Project ID to update
        start_date: New project start date
        end_date: New project end date
        status: New project status
        priority: New project priority
        notify_ui: Optional UI notification callback (ProjectNotificationSystem instance)
    
    Returns:
        bool: True if update successful, False otherwise
    """
    try:
        with get_db_connection("ProjectManagement") as conn:
            cursor = conn.cursor()
            
            # Get previous dates to detect changes
            cursor.execute(
                f"""
                SELECT {S.Projects.START_DATE}, {S.Projects.END_DATE}
                FROM dbo.{S.Projects.TABLE}
                WHERE {S.Projects.ID} = ?;
                """,
                (project_id,)
            )
            old_dates = cursor.fetchone()
            dates_changed = False
            
            if old_dates:
                old_start, old_end = old_dates
                dates_changed = (old_start != start_date or old_end != end_date)
            
            # 1. Update Projects table
            cursor.execute(
                f"""
                UPDATE dbo.{S.Projects.TABLE}
                SET {S.Projects.START_DATE} = ?, {S.Projects.END_DATE} = ?, {S.Projects.STATUS} = ?, {S.Projects.PRIORITY} = ?, {S.Projects.UPDATED_AT} = GETDATE()
                WHERE {S.Projects.ID} = ?;
                """,
                (start_date, end_date, status, priority, project_id),
            )
            
            # 2. If dates changed, propagate to related tables
            if dates_changed:
                logger.info(f"Project dates changed - propagating to related tables...")
                
                # 2a. Propagate start_date to ServiceScheduleSettings
                # Adjust service start dates to be within project bounds
                cursor.execute(
                    f"""
                    UPDATE sss
                    SET sss.{S.ServiceScheduleSettings.START_DATE} = ?
                    FROM {S.ServiceScheduleSettings.TABLE} sss
                    INNER JOIN {S.ProjectServices.TABLE} ps ON sss.{S.ServiceScheduleSettings.SERVICE_ID} = ps.{S.ProjectServices.SERVICE_ID}
                    WHERE ps.{S.ProjectServices.PROJECT_ID} = ?
                        AND sss.{S.ServiceScheduleSettings.START_DATE} < ?;
                    """,
                    (start_date, project_id, start_date)
                )
                service_start_updated = cursor.rowcount
                if service_start_updated > 0:
                    logger.info(f"  Updated {service_start_updated} service schedule start dates")
            
            # 2b. Propagate end_date to ServiceScheduleSettings
            # Adjust service end dates to be within project bounds
            cursor.execute(
                f"""
                UPDATE sss
                SET sss.{S.ServiceScheduleSettings.END_DATE} = ?
                FROM {S.ServiceScheduleSettings.TABLE} sss
                INNER JOIN {S.ProjectServices.TABLE} ps ON sss.{S.ServiceScheduleSettings.SERVICE_ID} = ps.{S.ProjectServices.SERVICE_ID}
                WHERE ps.{S.ProjectServices.PROJECT_ID} = ?
                    AND sss.{S.ServiceScheduleSettings.END_DATE} > ?;
                """,
                (end_date, project_id, end_date)
            )
            service_end_updated = cursor.rowcount
            if service_end_updated > 0:
                logger.info(f"  Updated {service_end_updated} service schedule end dates")
            
            # 2c. Cancel ServiceReviews beyond new end_date
            cursor.execute(
                f"""
                UPDATE sr
                SET sr.{S.ServiceReviews.STATUS} = 'Cancelled'
                FROM {S.ServiceReviews.TABLE} sr
                INNER JOIN {S.ProjectServices.TABLE} ps ON sr.{S.ServiceReviews.SERVICE_ID} = ps.{S.ProjectServices.SERVICE_ID}
                WHERE ps.{S.ProjectServices.PROJECT_ID} = ?
                    AND sr.{S.ServiceReviews.PLANNED_DATE} > ?
                    AND sr.{S.ServiceReviews.STATUS} != 'Cancelled';
                """,
                (project_id, end_date)
            )
            reviews_cancelled = cursor.rowcount
            if reviews_cancelled > 0:
                logger.warning(f"  Cancelled {reviews_cancelled} reviews scheduled beyond new project end date")
            
            # 2d. Flag Tasks with dates outside project bounds (optional - just log warning)
            cursor.execute(
                f"""
                SELECT COUNT(*) 
                FROM {S.Tasks.TABLE}
                WHERE {S.Tasks.PROJECT_ID} = ?
                    AND ({S.Tasks.START_DATE} < ? OR {S.Tasks.END_DATE} > ?);
                """,
                (project_id, start_date, end_date)
            )
            tasks_outside_bounds = cursor.fetchone()[0]
            if tasks_outside_bounds > 0:
                logger.warning(f"  Warning: {tasks_outside_bounds} tasks have dates outside new project bounds")
                logger.warning(f"     Consider reviewing task schedules in project {project_id}")
        
            conn.commit()
            logger.info(f"Project {project_id} details updated.")
            
            # 3. Notify UI of changes (if callback provided)
            if notify_ui and dates_changed:
                try:
                    notify_ui.notify_project_dates_changed(project_id, start_date, end_date)
                except AttributeError:
                    # Fallback if notify_project_dates_changed not implemented yet
                    notify_ui.notify_project_changed(project_id)
            
            return True
    except Exception as e:
        logger.error(f"Database Error updating project details: {e}")
        return False

def get_review_schedule(project_id, cycle_id):
    """Fetch review schedule including project name and cycle ID from the database."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(
                f"""
                SELECT {S.ReviewSchedule.ID}, {S.ReviewSchedule.REVIEW_DATE}, {S.ReviewSchedule.CYCLE_ID},
                       project_name, construction_stage, proposed_fee, assigned_users,
                       reviews_per_phase, planned_start_date, planned_completion_date,
                       actual_start_date, actual_completion_date, hold_date, resume_date, new_contract
                FROM vw_ReviewScheduleDetails
                WHERE {S.ReviewSchedule.PROJECT_ID} = ? AND {S.ReviewSchedule.CYCLE_ID} = ?
                ORDER BY {S.ReviewSchedule.REVIEW_DATE} ASC;
                """,
                (project_id, cycle_id),
            )

            result = cursor.fetchall()

            # ✅ Debugging: Print raw SQL query result
            logger.info(f"🔹 Raw SQL Query Result: {result}")

            if not result:
                logger.warning(f"⚠️ No review schedule data found for Project {project_id}, Cycle {cycle_id}")
                return pd.DataFrame(columns=["schedule_id", "review_date", "cycle_id", "project_name"]), "", ""

            # ✅ Convert query result into a Pandas DataFrame
            structured_result = [tuple(row) for row in result]
            df = pd.DataFrame(
                structured_result,
                columns=[
                    "schedule_id",
                    "review_date",
                    "cycle_id",
                    "project_name",
                    "construction_stage",
                    "proposed_fee",
                    "assigned_users",
                    "reviews_per_phase",
                    "planned_start_date",
                    "planned_completion_date",
                    "actual_start_date",
                    "actual_completion_date",
                    "hold_date",
                    "resume_date",
                    "new_contract",
                ],
            )
            df["review_date"] = pd.to_datetime(df["review_date"], errors="coerce")
            for col in [
                "planned_start_date",
                "planned_completion_date",
                "actual_start_date",
                "actual_completion_date",
                "hold_date",
                "resume_date",
            ]:
                df[col] = pd.to_datetime(df[col], errors="coerce")

            project_name = df["project_name"].iloc[0] if not df.empty else "Unknown Project"
            cycle_id = df["cycle_id"].iloc[0] if not df.empty else "Unknown Cycle"

            # ✅ Debugging: Print DataFrame structure
            logger.info(f"🔹 DataFrame Shape: {df.shape}")
            logger.info(f"🔹 DataFrame Preview:\n{df.head()}")

            return df, project_name, cycle_id
    except Exception as e:
        logger.error(f"❌ Error fetching review schedule: {str(e)}")
        return pd.DataFrame(), "", ""


def update_project_folders(project_id, models_path=None, data_path=None, ifc_path=None):
    """Update standard (models), data export, and IFC folder paths in dbo.projects."""
    try:
        with get_db_connection("ProjectManagement") as conn:
            cursor = conn.cursor()

            if models_path is not None:
                cursor.execute(
                    f"UPDATE dbo.{S.Projects.TABLE} SET {S.Projects.FOLDER_PATH} = ? WHERE {S.Projects.ID} = ?",
                    (models_path, project_id),
                )

            if data_path is not None:
                cursor.execute(
                    f"UPDATE dbo.{S.Projects.TABLE} SET {S.Projects.DATA_EXPORT_FOLDER} = ? WHERE {S.Projects.ID} = ?",
                    (data_path, project_id),
                )

            if ifc_path is not None:
                cursor.execute(
                    f"UPDATE dbo.{S.Projects.TABLE} SET {S.Projects.IFC_FOLDER_PATH} = ? WHERE {S.Projects.ID} = ?",
                    (ifc_path, project_id),
                )

            conn.commit()
            logger.info(f"Project {project_id} paths updated: models={models_path}, data={data_path}, ifc={ifc_path}")
            return True

    except Exception as e:
        logger.error(f"Database Error updating project folders: {e}")
        return False




def get_acc_import_logs(project_id):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT TOP 50 
                    {S.ACCImportLogs.LOG_ID}, 
                    {S.ACCImportLogs.PROJECT_ID}, 
                    {S.ACCImportLogs.FOLDER_NAME}, 
                    {S.ACCImportLogs.IMPORT_DATE}, 
                    COALESCE({S.ACCImportLogs.STATUS}, 'Unknown') as status,
                    COALESCE({S.ACCImportLogs.SUMMARY}, '') as summary
                FROM {S.ACCImportLogs.TABLE}
                WHERE {S.ACCImportLogs.PROJECT_ID} = ?
                ORDER BY {S.ACCImportLogs.IMPORT_DATE} DESC
                """,
                (project_id,),
            )
            rows = cursor.fetchall()
            # Convert pyodbc.Row objects to dictionaries
            result = []
            for row in rows:
                result.append({
                    'log_id': row[0] if row[0] is not None else '',
                    'project_id': row[1] if row[1] is not None else '',
                    'folder_name': row[2] if row[2] is not None else '',
                    'import_date': row[3] if row[3] is not None else '',
                    'status': row[4] if row[4] is not None else 'Unknown',
                    'summary': row[5] if row[5] is not None else ''
                })
            return result
    except Exception as e:
        logger.error(f"❌ Error retrieving import logs: {e}")
        return []



def get_project_folders(project_id):
    """Fetch both the standard and IFC folder paths for a given project from dbo.projects."""
    try:
        with get_db_connection("ProjectManagement") as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT {S.Projects.FOLDER_PATH}, {S.Projects.IFC_FOLDER_PATH} FROM dbo.{S.Projects.TABLE} WHERE {S.Projects.ID} = ?",
                (project_id,),
            )
            row = cursor.fetchone()
            
            if row:
                logger.info(f"✅ Retrieved from DB: Folder Path={row[0]}, IFC Folder Path={row[1]}")
                return row[0], row[1]  # (folder_path, ifc_folder_path)
            else:
                logger.warning(f"⚠️ No matching project found for ID: {project_id}")
                return None, None
    except Exception as e:
        logger.error(f"❌ Error fetching project folders: {str(e)}")
        return None, None



def get_cycle_ids(project_id):
    """Fetch available cycle IDs for a given project."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT DISTINCT {S.ReviewParameters.CYCLE_ID} FROM {S.ReviewParameters.TABLE}
                WHERE {S.ReviewParameters.PROJECT_ID} = ?
                ORDER BY {S.ReviewParameters.CYCLE_ID} DESC;
                """,
                (project_id,)
            )
            
            cycles = [str(row[0]) for row in cursor.fetchall()]
            
            logger.info(f"🔹 Querying Cycle IDs for Project {project_id}")
            logger.info(f"🔹 SQL Query Result: {cycles}")

            return cycles if cycles else ["No Cycles Available"]
    except Exception as e:
        logger.error(f"❌ Error fetching cycle IDs: {str(e)}")
        return ["No Cycles Available"]

def fetch_data(query):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            data = cursor.fetchall()
            return data
    except Exception as e:
        logger.error(f"Error fetching data: {e}")
        return []


def insert_files_into_tblACCDocs(project_id, folder_path, include_dirs=None):
    """Extract files from ``folder_path`` and store them in ``tblACCDocs``.

    Only records for ``project_id`` are replaced.  If ``include_dirs`` is
    provided, only directories whose paths contain any of the given strings are
    scanned.  Typical values include ``"WIP"``, ``"Work in Progress"``,
    ``"Shared"``, ``"Published"``, ``"Admin"`` and ``"Documentation"``.  Directories
    that do not match are skipped entirely so inaccessible folders do not halt
    the crawl.

    :param project_id: The project ID associated with the files.
    :param folder_path: The root folder path containing the files.
    :param include_dirs: Optional list of directory name fragments to include.
    """
    if not os.path.exists(folder_path):
        logger.error(f"Folder does not exist: {folder_path}")
        return False

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # ✅ DELETE only files related to the selected project
            cursor.execute(
                f"DELETE FROM {S.ACCDocs.TABLE} WHERE {S.ACCDocs.PROJECT_ID} = ?",
                (project_id,),
            )
            rows_deleted = cursor.rowcount
            conn.commit()
            logger.info(f"Deleted {rows_deleted} existing records for project {project_id} from tblACCDocs.")

            # Extract file metadata
            file_details = []

            def on_error(e):
                logger.warning(f"Unable to access {getattr(e, 'filename', '')}: {e}")

            for root, dirs, files in os.walk(folder_path, topdown=True, onerror=on_error):
                if include_dirs:
                    root_match = any(inc.lower() in root.lower() for inc in include_dirs)
                    if not root_match:
                        dirs[:] = [d for d in dirs if any(inc.lower() in d.lower() for inc in include_dirs)]
                        continue

                for file_name in files:
                    file_path = os.path.join(root, file_name)
                    try:
                        date_modified = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S')
                        file_type = os.path.splitext(file_name)[1][1:] if os.path.splitext(file_name)[1] else "Unknown"
                        file_size_kb = round(os.path.getsize(file_path) / 1024, 2)
                        created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    except OSError as e:
                        logger.warning(f"Skipping {file_path}: {e}")
                        continue

                    file_details.append((file_name, file_path, date_modified, file_type, file_size_kb, created_at, None, project_id))

            # ✅ Print file details for debugging
            if not file_details:
                logger.warning("No files found in the folder.")
                return False
            else:
                logger.info(f"Found {len(file_details)} files. Preparing to insert...")
                logger.info("Files to be inserted:")
                for file_detail in file_details[:5]:
                    logger.info(file_detail)  # Display the first 5 files for verification

            # ✅ Insert new records only for the selected project
            try:
                cursor.executemany(
                    f"""
                    INSERT INTO {S.ACCDocs.TABLE}
                    ({S.ACCDocs.FILE_NAME}, {S.ACCDocs.FILE_PATH}, {S.ACCDocs.DATE_MODIFIED}, {S.ACCDocs.FILE_TYPE}, {S.ACCDocs.FILE_SIZE_KB}, {S.ACCDocs.CREATED_AT}, {S.ACCDocs.DELETED_AT}, {S.ACCDocs.PROJECT_ID})
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    file_details,
                )

                rows_inserted = cursor.rowcount
                conn.commit()
                logger.info(f"{rows_inserted} files inserted into tblACCDocs for project {project_id}.")
                return True
            except pyodbc.Error as e:
                logger.error(f"Database Error during insertion: {e}")
                conn.rollback()  # Rollback if insertion fails
                return False

    except Exception as e:
        logger.error(f"Error in insert_files_into_tblACCDocs: {e}")
        return False

def store_file_details_in_db(file_details):
    """
    Store file details in the database.
    :param file_details: List of tuples (file_name, file_path, date_modified, file_type, file_size_kb)
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Clear existing records (optional: use `TRUNCATE TABLE` if necessary)
            cursor.execute(f"DELETE FROM dbo.{S.ACCDocs.TABLE}")
            conn.commit()

            # Insert new data
            cursor.executemany(
                f"""
                INSERT INTO dbo.{S.ACCDocs.TABLE} ({S.ACCDocs.FILE_NAME}, {S.ACCDocs.FILE_PATH}, {S.ACCDocs.DATE_MODIFIED}, {S.ACCDocs.FILE_TYPE}, {S.ACCDocs.FILE_SIZE_KB})
                VALUES (?, ?, ?, ?, ?)
                """,
                file_details,
            )

            conn.commit()
            logger.info("✅ File details successfully stored in the database.")

    except Exception as e:
        logger.error(f"❌ Error storing file details in the database: {e}")
        if conn:
            conn.rollback()

def get_last_export_date():
    """Retrieve the most recent export date from tblIFCData in RevitHealthCheckDB."""
    try:
        with get_db_connection("RevitHealthCheckDB") as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT TOP 1 date_exported FROM dbo.tblIFCData 
                ORDER BY date_exported DESC;
            """)
            row = cursor.fetchone()
            
            if row:
                return row[0]  # Return the latest date
            else:
                return "No exports found"
    
    except Exception as e:
        logger.error(f"Error fetching last export date: {e}")
        return "Error fetching data"

def save_acc_folder_path(project_id, folder_path):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                MERGE INTO {S.ACCImportFolders.TABLE} AS target
                USING (SELECT ? AS {S.ACCImportFolders.PROJECT_ID}, ? AS {S.ACCImportFolders.ACC_FOLDER_PATH}) AS source
                ON target.{S.ACCImportFolders.PROJECT_ID} = source.{S.ACCImportFolders.PROJECT_ID}
                WHEN MATCHED THEN UPDATE SET {S.ACCImportFolders.ACC_FOLDER_PATH} = source.{S.ACCImportFolders.ACC_FOLDER_PATH}
                WHEN NOT MATCHED THEN INSERT ({S.ACCImportFolders.PROJECT_ID}, {S.ACCImportFolders.ACC_FOLDER_PATH})
                    VALUES (source.{S.ACCImportFolders.PROJECT_ID}, source.{S.ACCImportFolders.ACC_FOLDER_PATH});
                """,
                (project_id, folder_path),
            )
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"Error saving ACC folder path: {e}")
        return False

def get_acc_folder_path(project_id):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT {S.ACCImportFolders.ACC_FOLDER_PATH} FROM {S.ACCImportFolders.TABLE} WHERE {S.ACCImportFolders.PROJECT_ID} = ?",
                (project_id,)
            )
            row = cursor.fetchone()
            return row[0] if row else None
    except Exception as e:
        logger.error(f"Error getting ACC folder path: {e}")
        return None

def log_acc_import(project_id, folder_name, summary):
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                INSERT INTO {S.ACCImportLogs.TABLE} ({S.ACCImportLogs.PROJECT_ID}, {S.ACCImportLogs.FOLDER_NAME}, {S.ACCImportLogs.IMPORT_DATE}, {S.ACCImportLogs.SUMMARY})
                VALUES (?, ?, GETDATE(), ?)
                """,
                (project_id, folder_name, summary),
            )
            conn.commit()
    except Exception as e:
        logger.error(f"Error logging ACC import: {e}")


# Control file management ===========================================

CONTROL_VALIDATION_TARGETS: Tuple[str, ...] = ('naming', 'coordinates', 'levels')

def get_project_health_files(project_id):
    """Return distinct Revit file names from vw_LatestRvtFiles for a project."""
    try:
        with get_db_connection("RevitHealthCheckDB") as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT strRvtFileName
                FROM dbo.vw_LatestRvtFiles
                WHERE pm_project_id = ?
                ORDER BY strRvtFileName;
            """, (project_id,))
            return [row[0] for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"Error fetching health files: {e}")
        return []


def revalidate_revit_naming(project_ids: Optional[List[int]] = None) -> Dict[str, Any]:
    """Trigger a Revit naming revalidation run (placeholder)."""
    return {
        "projects_requested": project_ids or [],
        "projects_processed": 0,
        "invalidated": 0,
        "validated": 0,
        "message": "Naming revalidation not configured in this environment.",
    }


def get_control_models(project_id) -> List[Dict[str, Any]]:
    """Fetch control model records for a project, including metadata when available."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            metadata_supported = _control_model_metadata_column_exists(conn)
            if metadata_supported:
                cursor.execute(
                    """
                    SELECT id, control_file_name, is_active, created_at, updated_at, metadata_json
                    FROM ProjectManagement.dbo.tblControlModels
                    WHERE project_id = ?
                    ORDER BY is_active DESC, updated_at DESC, id ASC
                    """,
                    (project_id,),
                )
            else:
                cursor.execute(
                    """
                    SELECT id, control_file_name, is_active, created_at, updated_at
                    FROM ProjectManagement.dbo.tblControlModels
                    WHERE project_id = ?
                    ORDER BY is_active DESC, updated_at DESC, id ASC
                    """,
                    (project_id,),
                )

            models: List[Dict[str, Any]] = []
            rows = cursor.fetchall()
            for row in rows:
                model = {
                    'id': row[0],
                    'control_file_name': row[1],
                    'is_active': bool(row[2]) if row[2] is not None else False,
                    'created_at': row[3],
                    'updated_at': row[4],
                }
                if metadata_supported:
                    metadata_raw = row[5]
                    if metadata_raw:
                        try:
                            model['metadata'] = json.loads(metadata_raw)
                        except json.JSONDecodeError:
                            logger.warning("Invalid control model metadata for project %s (record %s)", project_id, row[0])
                            model['metadata'] = {}
                    else:
                        model['metadata'] = {}
                models.append(model)
            return models
    except Exception as e:
        logger.error(f"Error fetching control models: {e}")
        return []


def _get_model_register_expected_mode(
    project_id: int,
    page: int = 1,
    page_size: int = 50,
    sort_by: str = "lastVersionDate",
    sort_dir: str = "desc",
    filter_attention: bool = False,
) -> Dict[str, Any]:
    """
    Phase 1C: Get quality register in expected-first mode.
    
    Returns authoritative expected models with decorated observed data and unmatched list.
    
    Args:
        project_id: Project ID
        page, page_size: Pagination for expected_rows
        sort_by, sort_dir: Sorting for expected_rows
        filter_attention: Filter to attention items only
    
    Returns:
        Dict with expected_rows, unmatched_observed, counts
    """
    from datetime import datetime
    import re
    
    try:
        # Validate sort direction
        sort_dir = sort_dir.upper()
        if sort_dir not in ('ASC', 'DESC'):
            sort_dir = 'DESC'
        
        # Step 1: Get expected models
        expected_models = get_expected_models(project_id)
        
        if not expected_models:
            # No expected models yet - return empty expected-mode response
            logger.warning(f"No expected models found for project {project_id} (expected mode)")
            return {
                'expected_rows': [],
                'unmatched_observed': [],
                'counts': {
                    'expected_total': 0,
                    'expected_missing': 0,
                    'unmatched_total': 0,
                    'attention_count': 0,
                }
            }
        
        # Step 2: Get aliases for the project
        aliases = get_expected_model_aliases(project_id)
        
        # Step 3: Get observed files (reuse existing observed logic)
        observed_data = _get_observed_data(project_id)
        observed_files_dict = {f['modelKey']: f for f in observed_data}
        
        # Step 4: Match observed files to expected models
        expected_rows = []
        matched_observed_filenames = set()
        
        for expected in expected_models:
            expected_model_id = expected['expected_model_id']
            expected_model_key = expected['expected_model_key']
            
            # Try to find matching observed file
            matched_expected_id = None
            matched_observed = None
            
            for filename, observed_row in observed_files_dict.items():
                # Use alias resolution
                resolved_id = match_observed_to_expected(
                    observed_filename=filename,
                    observed_rvt_model_key=observed_row.get('logicalModelKey'),
                    aliases=aliases
                )
                
                if resolved_id == expected_model_id:
                    matched_expected_id = expected_model_id
                    matched_observed = observed_row
                    matched_observed_filenames.add(filename)
                    break
            
            # Build expected row (with optional observed decoration)
            expected_row = {
                'expected_model_id': expected_model_id,
                'expected_model_key': expected_model_key,
                'display_name': expected['display_name'],
                'discipline': expected['discipline'],
                'is_required': expected['is_required'],
                'observed_filename': matched_observed['modelKey'] if matched_observed else None,
                'lastVersionDateISO': matched_observed['lastVersionDateISO'] if matched_observed else None,
                'observed_discipline': matched_observed['discipline'] if matched_observed else None,
                'validationOverall': matched_observed['validationOverall'] if matched_observed else 'UNKNOWN',
                'namingStatus': matched_observed['namingStatus'] if matched_observed else None,
                'isControlModel': matched_observed['isControlModel'] if matched_observed else False,
                'freshnessStatus': matched_observed['freshnessStatus'] if matched_observed else 'UNKNOWN',
                'mappingStatus': 'MAPPED' if matched_observed else 'UNMAPPED',
            }
            
            expected_rows.append(expected_row)
        
        # Step 5: Build unmatched observed list
        unmatched_observed = []
        for filename, observed_row in observed_files_dict.items():
            if filename not in matched_observed_filenames:
                unmatched_observed.append({
                    'observed_filename': filename,
                    'discipline': observed_row.get('discipline'),
                    'lastVersionDateISO': observed_row.get('lastVersionDateISO'),
                    'validationOverall': observed_row.get('validationOverall'),
                    'namingStatus': observed_row.get('namingStatus'),
                    'note': 'No matching expected model via aliases'
                })
        
        # Step 6: Count attention items
        attention_count = sum(1 for row in expected_rows if (
            row['freshnessStatus'] == 'OUT_OF_DATE'
            or row['validationOverall'] in ('FAIL', 'WARN')
            or row['mappingStatus'] == 'UNMAPPED'
        ))
        attention_count += len(unmatched_observed)  # Unmatched files are attention items
        
        # Step 7: Sort and paginate expected rows
        if sort_by not in ('lastVersionDate', 'expected_model_key', 'freshnessStatus', 'validationOverall', 'mappingStatus'):
            sort_by = 'expected_model_key'
        
        # Sort expected_rows
        reverse = (sort_dir == 'DESC')
        if sort_by == 'lastVersionDate':
            expected_rows.sort(key=lambda r: r['lastVersionDateISO'] or '', reverse=reverse)
        elif sort_by == 'expected_model_key':
            expected_rows.sort(key=lambda r: r['expected_model_key'], reverse=reverse)
        elif sort_by == 'freshnessStatus':
            expected_rows.sort(key=lambda r: r['freshnessStatus'], reverse=reverse)
        elif sort_by == 'validationOverall':
            expected_rows.sort(key=lambda r: r['validationOverall'], reverse=reverse)
        elif sort_by == 'mappingStatus':
            expected_rows.sort(key=lambda r: r['mappingStatus'], reverse=reverse)
        
        # Paginate
        total_expected = len(expected_rows)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_expected = expected_rows[start_idx:end_idx]
        
        logger.info(f"Quality register (expected mode): {len(paginated_expected)} expected rows, {len(unmatched_observed)} unmatched observed")
        
        return {
            'expected_rows': paginated_expected,
            'unmatched_observed': unmatched_observed,
            'counts': {
                'expected_total': total_expected,
                'expected_missing': sum(1 for r in expected_rows if r['mappingStatus'] == 'UNMAPPED'),
                'unmatched_total': len(unmatched_observed),
                'attention_count': attention_count,
            },
            'page': page,
            'page_size': page_size,
        }
    
    except Exception as e:
        logger.error(f"Error fetching model register (expected mode) for project {project_id}: {e}", exc_info=True)
        return {
            'expected_rows': [],
            'unmatched_observed': [],
            'counts': {
                'expected_total': 0,
                'expected_missing': 0,
                'unmatched_total': 0,
                'attention_count': 0,
            }
        }


def _get_observed_data(project_id: int) -> List[Dict[str, Any]]:
    """
    Helper function to get observed files from health data.
    This is the same logic as the observed-mode query.
    
    Returns list of observed file dicts with all health fields.
    """
    from datetime import datetime
    
    try:
        # Get control models and next review date (ProjectManagement)
        with get_db_connection() as pm_conn:
            pm_cursor = pm_conn.cursor()
            
            pm_cursor.execute(f"""
                SELECT {S.ControlModels.ID}, {S.ControlModels.CONTROL_FILE_NAME}, {S.ControlModels.IS_ACTIVE}
                FROM ProjectManagement.dbo.{S.ControlModels.TABLE}
                WHERE {S.ControlModels.PROJECT_ID} = ?
            """, (project_id,))
            
            control_models = {}
            for row in pm_cursor.fetchall():
                control_models[row[1].strip()] = {
                    'id': row[0],
                    'is_active': bool(row[2]) if row[2] is not None else False
                }
            
            pm_cursor.execute(f"""
                SELECT MIN({S.ReviewSchedule.REVIEW_DATE})
                FROM ProjectManagement.dbo.{S.ReviewSchedule.TABLE}
                WHERE {S.ReviewSchedule.PROJECT_ID} = ?
                  AND {S.ReviewSchedule.REVIEW_DATE} > GETDATE()
            """, (project_id,))
            next_review_row = pm_cursor.fetchone()
            next_review_date = next_review_row[0] if next_review_row and next_review_row[0] else None
            pm_cursor.close()
        
        # Query observed files (RevitHealthCheckDB)
        with get_db_connection("RevitHealthCheckDB") as health_conn:
            health_cursor = health_conn.cursor()
            
            query = f"""
            SELECT 
                h.[nId],
                h.[strRvtFileName],
                h.[project_name],
                h.[discipline_full_name],
                h.[ConvertedExportedDate],
                h.[pm_project_id],
                h.[rvt_model_key],
                hp.[validation_status],
                hp.[validation_reason],
                hp.[validated_date],
                hp.[strClientName]
            FROM dbo.vw_LatestRvtFiles h
            LEFT JOIN (
                SELECT 
                    strRvtFileName,
                    validation_status,
                    validation_reason,
                    validated_date,
                    strClientName,
                    ROW_NUMBER() OVER (PARTITION BY strRvtFileName ORDER BY validated_date DESC, nId DESC) as rn
                FROM dbo.tblRvtProjHealth
            ) hp
                ON h.[strRvtFileName] = hp.[strRvtFileName]
                AND hp.rn = 1
            WHERE h.[pm_project_id] = ?
            ORDER BY h.[ConvertedExportedDate] DESC
            """
            
            health_cursor.execute(query, (project_id,))
            all_rows = health_cursor.fetchall()
            health_cursor.close()
        
        # Process rows (same as observed-mode logic)
        def normalize_model_key(filename: str) -> Optional[str]:
            if not filename:
                return None
            filename_clean = filename.strip()
            misname_indicators = ['_detached', '_OLD', '_old', '__', '_001', '_0001']
            if any(ind in filename_clean for ind in misname_indicators):
                return None
            if filename != filename_clean:
                return None
            if '-' not in filename_clean:
                return None
            base = filename_clean.split('.')[0] if '.' in filename_clean else filename_clean
            parts = base.split('-')
            if len(parts) >= 3:
                key = '-'.join(parts[:3])
                return key
            return None
        
        raw_rows = []
        for row in all_rows:
            model_filename = row[1]
            last_version_date = row[4]
            model_key = row[6]
            validation_status_raw = row[7]
            
            is_control = model_filename in control_models and control_models[model_filename]['is_active']
            
            if last_version_date and next_review_date:
                days_until_review = (next_review_date - last_version_date).days
                if days_until_review < 0:
                    freshness_status = 'OUT_OF_DATE'
                elif days_until_review <= 7:
                    freshness_status = 'DUE_SOON'
                else:
                    freshness_status = 'CURRENT'
            elif last_version_date and not next_review_date:
                freshness_status = 'UNKNOWN'
            elif not last_version_date:
                freshness_status = 'UNKNOWN'
            else:
                freshness_status = 'UNKNOWN'
            
            if validation_status_raw:
                validation_status_raw_upper = str(validation_status_raw).upper()
                if validation_status_raw_upper in ('VALID', 'PASS'):
                    validation_status = 'PASS'
                elif validation_status_raw_upper in ('INVALID', 'FAIL'):
                    validation_status = 'FAIL'
                elif validation_status_raw_upper == 'WARN':
                    validation_status = 'WARN'
                else:
                    validation_status = 'UNKNOWN'
            else:
                validation_status = 'UNKNOWN'
            
            normalized_key = normalize_model_key(model_filename)
            
            raw_rows.append({
                'modelKey': model_filename,
                'modelName': model_filename,
                'logicalModelKey': model_key,
                'normalizedKey': normalized_key,
                'discipline': row[3],
                'company': row[10],
                'lastVersionDate': last_version_date,
                'lastVersionDateISO': last_version_date.isoformat() if last_version_date else None,
                'source': 'REVIT_HEALTH',
                'isControlModel': is_control,
                'freshnessStatus': freshness_status,
                'validationOverall': validation_status,
                'primaryServiceId': None,
                'mappingStatus': 'UNMAPPED',
                'namingStatus': 'CORRECT' if normalized_key else 'MISNAMED',
            })
        
        # Phase B deduplication
        processed_rows = []
        by_normalized_key = {}
        
        for row in raw_rows:
            if row['normalizedKey']:
                nk = row['normalizedKey']
                if nk not in by_normalized_key:
                    by_normalized_key[nk] = []
                by_normalized_key[nk].append(row)
            else:
                row['namingStatus'] = 'MISNAMED'
                processed_rows.append(row)
        
        for normalized_key, rows_group in by_normalized_key.items():
            latest = max(rows_group, key=lambda r: r['lastVersionDate'] or datetime.min)
            latest['namingStatus'] = 'CORRECT'
            processed_rows.append(latest)
        
        return processed_rows
    
    except Exception as e:
        logger.error(f"Error fetching observed data for project {project_id}: {e}", exc_info=True)
        return []


def get_model_register(
    project_id: int,
    page: int = 1,
    page_size: int = 50,
    sort_by: str = "lastVersionDate",
    sort_dir: str = "desc",
    filter_attention: bool = False,
    mode: str = "observed",  # Phase 1C: NEW - "observed" or "expected"
) -> Dict[str, Any]:
    """
    Fetch quality register rows for a project.
    
    PHASE A FIX (Jan 2026):
    - Root cause was querying non-existent VALIDATION_STATUS in vw_LatestRvtFiles
    - Solution: LEFT JOIN vw_LatestRvtFiles to tblRvtProjHealth for validation data
    - Result: Actual data (12 rows for project 2) now returned instead of empty
    
    PHASE B FIX:
    - Normalizes model names to deduplicate misnamed files
    - Groups by canonical model key; keeps latest version
    - Marks misnamed files with namingStatus='MISNAMED' for audit trail
    
    PHASE 1C (NEW):
    - Supports mode parameter: "observed" (default, existing behavior) or "expected" (new)
    - Expected mode requires ExpectedModels table and alias resolution
    - Integrates with ExpectedModelAliases for observed→expected mapping
    
    Args:
        project_id: Project ID
        page: Page number (1-indexed)
        page_size: Results per page
        sort_by: Sort column (lastVersionDate, modelName, freshnessStatus, validationOverall)
        sort_dir: Sort direction (asc, desc)
        filter_attention: If true, only return rows needing attention
        mode: "observed" (default - current behavior) or "expected" (Phase 1C - new)
    
    Returns:
        Dict with rows, pagination info, and attention_count
        For mode="expected", returns expected_rows, unmatched_observed, counts
    """
    import re
    from datetime import datetime
    
    # Phase 1C: Validate mode parameter
    mode = mode.lower() if mode else "observed"
    if mode not in ("observed", "expected"):
        mode = "observed"
    
    # If mode is "expected", delegate to new handler
    if mode == "expected":
        return _get_model_register_expected_mode(
            project_id=project_id,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_dir=sort_dir,
            filter_attention=filter_attention,
        )
    
    # Otherwise, continue with existing observed-mode logic
    try:
        # Validate sort direction
        sort_dir = sort_dir.upper()
        if sort_dir not in ('ASC', 'DESC'):
            sort_dir = 'DESC'
        
        # Naming pattern for model key extraction (Phase B)
        # Format: Project-Discipline-Zone-Zone-M3-Type-Number (flexible to match actual data)
        # Examples: NFPS-ACO-00-00-M3-C-0001, MEL071-A-AR-M-0010
        # Detect MISNAMED: files with unusual patterns like spaces, underscores, duplicate names
        
        def normalize_model_key(filename: str) -> Optional[str]:
            """
            Extract canonical model key from filename.
            A file is MISNAMED if:
            - Contains trailing/leading spaces
            - Has '_detached', '_OLD', '_old', duplicate keywords
            - Doesn't follow basic dash-separated structure
            """
            if not filename:
                return None
            
            filename_clean = filename.strip()
            
            # Check for obvious misname indicators
            misname_indicators = ['_detached', '_OLD', '_old', '__', '_001', '_0001']
            if any(ind in filename_clean for ind in misname_indicators):
                return None  # Misnamed
            
            # Check if filename has leading/trailing spaces (indicating import issues)
            if filename != filename_clean:
                return None  # Misnamed
            
            # Basic structure check: should have dashes
            if '-' not in filename_clean:
                return None  # Misnamed
            
            # Extract the base model key (everything before .rvt or last extension)
            # Handle files like "NFPS-ACO-00-00-M3-C-0001.rvt" or "CWPS-BAT-ZZ-ZZ-M3-A-0001"
            base = filename_clean.split('.')[0] if '.' in filename_clean else filename_clean
            
            # For canonical key, use first N components before file number
            # Examples:
            #   "NFPS-ACO-00-00-M3-C-0001" → "NFPS-ACO-00"
            #   "MEL071-A-AR-M-0010" → "MEL071-A-AR"
            parts = base.split('-')
            if len(parts) >= 3:
                # Use first 3 components as the model key
                key = '-'.join(parts[:3])
                return key
            
            return None  # Can't extract key
        
        # Step 1 & 2: Get control models and next review date from ProjectManagement
        with get_db_connection() as pm_conn:
            pm_cursor = pm_conn.cursor()
            
            pm_cursor.execute(f"""
                SELECT {S.ControlModels.ID}, {S.ControlModels.CONTROL_FILE_NAME}, {S.ControlModels.IS_ACTIVE}
                FROM ProjectManagement.dbo.{S.ControlModels.TABLE}
                WHERE {S.ControlModels.PROJECT_ID} = ?
            """, (project_id,))
            
            control_models = {}
            for row in pm_cursor.fetchall():
                control_models[row[1].strip()] = {
                    'id': row[0],
                    'is_active': bool(row[2]) if row[2] is not None else False
                }
            
            # Get next review date from ProjectManagement
            pm_cursor.execute(f"""
                SELECT MIN({S.ReviewSchedule.REVIEW_DATE})
                FROM ProjectManagement.dbo.{S.ReviewSchedule.TABLE}
                WHERE {S.ReviewSchedule.PROJECT_ID} = ?
                  AND {S.ReviewSchedule.REVIEW_DATE} > GETDATE()
            """, (project_id,))
            next_review_row = pm_cursor.fetchone()
            next_review_date = next_review_row[0] if next_review_row and next_review_row[0] else None
            pm_cursor.close()
        
        # Step 3: Query latest files with validation data (PHASE A FIX: LEFT JOIN to tblRvtProjHealth)
        with get_db_connection("RevitHealthCheckDB") as health_conn:
            health_cursor = health_conn.cursor()
            
            # CRITICAL FIX: vw_LatestRvtFiles does NOT have VALIDATION_STATUS column
            # Must LEFT JOIN to tblRvtProjHealth where validation data actually lives
            # Note: Must ensure we only join to LATEST record in tblRvtProjHealth per filename
            query = f"""
            SELECT 
                h.[nId],
                h.[strRvtFileName],
                h.[project_name],
                h.[discipline_full_name],
                h.[ConvertedExportedDate],
                h.[pm_project_id],
                h.[rvt_model_key],
                hp.[validation_status],
                hp.[validation_reason],
                hp.[validated_date],
                hp.[strClientName]
            FROM dbo.vw_LatestRvtFiles h
            LEFT JOIN (
                -- Get LATEST validation record per filename
                SELECT 
                    strRvtFileName,
                    validation_status,
                    validation_reason,
                    validated_date,
                    strClientName,
                    ROW_NUMBER() OVER (PARTITION BY strRvtFileName ORDER BY validated_date DESC, nId DESC) as rn
                FROM dbo.tblRvtProjHealth
            ) hp
                ON h.[strRvtFileName] = hp.[strRvtFileName]
                AND hp.rn = 1
            WHERE h.[pm_project_id] = ?
            ORDER BY h.[ConvertedExportedDate] DESC
            """
            
            health_cursor.execute(query, (project_id,))
            all_rows = health_cursor.fetchall()
            logger.info(f"Quality register: Loaded {len(all_rows)} rows from vw_LatestRvtFiles (with deduped validation JOIN)")
            health_cursor.close()
        
        # Step 4: Process rows with Phase B deduplication
        raw_rows = []
        
        for row in all_rows:
            model_filename = row[1]  # strRvtFileName
            last_version_date = row[4]  # ConvertedExportedDate
            model_key = row[6]  # rvt_model_key (from vw_LatestRvtFiles)
            validation_status_raw = row[7]  # validation_status from tblRvtProjHealth
            
            # Check if this is a control model
            is_control = model_filename in control_models and control_models[model_filename]['is_active']
            
            # Compute freshness status
            if last_version_date and next_review_date:
                days_until_review = (next_review_date - last_version_date).days
                if days_until_review < 0:
                    freshness_status = 'OUT_OF_DATE'
                elif days_until_review <= 7:  # DUE_SOON_WINDOW_DAYS
                    freshness_status = 'DUE_SOON'
                else:
                    freshness_status = 'CURRENT'
            elif last_version_date and not next_review_date:
                freshness_status = 'UNKNOWN'
            elif not last_version_date:
                freshness_status = 'UNKNOWN'
            else:
                freshness_status = 'UNKNOWN'
            
            # Map validation status
            # Database values: "Valid", "Invalid" (note capitalization)
            if validation_status_raw:
                validation_status_raw_upper = str(validation_status_raw).upper()
                if validation_status_raw_upper in ('VALID', 'PASS'):
                    validation_status = 'PASS'
                elif validation_status_raw_upper in ('INVALID', 'FAIL'):
                    validation_status = 'FAIL'
                elif validation_status_raw_upper == 'WARN':
                    validation_status = 'WARN'
                else:
                    validation_status = 'UNKNOWN'
            else:
                validation_status = 'UNKNOWN'
            
            # Phase B: Normalize model name and compute naming status
            normalized_key = normalize_model_key(model_filename)
            
            raw_rows.append({
                'modelKey': model_filename,
                'modelName': model_filename,
                'logicalModelKey': model_key,
                'normalizedKey': normalized_key,
                'discipline': row[3],  # discipline_full_name
                'company': row[10],  # strClientName
                'lastVersionDate': last_version_date,
                'lastVersionDateISO': last_version_date.isoformat() if last_version_date else None,
                'source': 'REVIT_HEALTH',
                'isControlModel': is_control,
                'freshnessStatus': freshness_status,
                'validationOverall': validation_status,
                'primaryServiceId': None,  # TODO: Phase C - service mapping
                'mappingStatus': 'UNMAPPED',
                'namingStatus': 'CORRECT' if normalized_key else 'MISNAMED',
            })
        
        # Phase B: Deduplicate by normalized key
        # For correctly-named models, keep only latest version per normalized key
        # For misnamed models, keep all (marked separately)
        
        processed_rows = []
        by_normalized_key = {}
        
        for row in raw_rows:
            if row['normalizedKey']:
                # Correctly-named: group by normalized key
                nk = row['normalizedKey']
                if nk not in by_normalized_key:
                    by_normalized_key[nk] = []
                by_normalized_key[nk].append(row)
            else:
                # Misnamed: keep separate, mark explicitly
                row['namingStatus'] = 'MISNAMED'
                processed_rows.append(row)
        
        # For each normalized group, keep only latest version date
        for normalized_key, rows_group in by_normalized_key.items():
            latest = max(rows_group, key=lambda r: r['lastVersionDate'] or datetime.min)
            latest['namingStatus'] = 'CORRECT'
            processed_rows.append(latest)
        
        # Apply attention filter
        if filter_attention:
            filtered_rows = []
            for row in processed_rows:
                is_attention = (
                    row['freshnessStatus'] == 'OUT_OF_DATE'
                    or row['validationOverall'] in ('FAIL', 'WARN')
                    or row['namingStatus'] == 'MISNAMED'
                    or row['mappingStatus'] == 'UNMAPPED'
                )
                if is_attention:
                    filtered_rows.append(row)
            processed_rows = filtered_rows
        
        # Count attention items (total, before pagination)
        attention_count = sum(1 for row in processed_rows if (
            row['freshnessStatus'] == 'OUT_OF_DATE'
            or row['validationOverall'] in ('FAIL', 'WARN')
            or row['namingStatus'] == 'MISNAMED'
            or row['mappingStatus'] == 'UNMAPPED'
        ))
        
        # Pagination
        total = len(processed_rows)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_rows = processed_rows[start_idx:end_idx]
        
        # Remove internal fields before returning
        for row in paginated_rows:
            del row['logicalModelKey']
            del row['normalizedKey']
            del row['lastVersionDate']
        
        logger.info(f"Quality register: Returning {len(paginated_rows)} rows (total: {total}, attention: {attention_count})")
        
        return {
            'rows': paginated_rows,
            'page': page,
            'page_size': page_size,
            'total': total,
            'attention_count': attention_count,
        }
    except Exception as e:
        logger.error(f"Error fetching model register for project {project_id}: {e}", exc_info=True)
        return {
            'rows': [],
            'page': page,
            'page_size': page_size,
            'total': 0,
            'attention_count': 0,
        }


def get_revizto_project_mappings(active_only: bool = True) -> List[Dict[str, Any]]:
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            filter_sql = "WHERE rpm.is_active = 1" if active_only else ""
            cursor.execute(
                f"""
                SELECT rpm.revizto_project_uuid, rpm.pm_project_id, rpm.project_name_override,
                       rpm.is_active, rpm.created_at, rpm.updated_at,
                       p.{S.Projects.NAME} AS pm_project_name
                FROM ProjectManagement.dbo.revizto_project_map rpm
                LEFT JOIN ProjectManagement.dbo.{S.Projects.TABLE} p
                  ON p.{S.Projects.ID} = rpm.pm_project_id
                {filter_sql}
                ORDER BY rpm.revizto_project_uuid
                """
            )
            rows = cursor.fetchall()
            return [
                {
                    "revizto_project_uuid": row[0],
                    "pm_project_id": row[1],
                    "project_name_override": row[2],
                    "is_active": bool(row[3]) if row[3] is not None else False,
                    "created_at": row[4],
                    "updated_at": row[5],
                    "pm_project_name": row[6],
                }
                for row in rows
            ]
    except Exception as exc:
        logger.error("Error fetching revizto project mappings: %s", exc)
        return []


def upsert_revizto_project_mapping(
    revizto_project_uuid: str,
    pm_project_id: Optional[int],
    project_name_override: Optional[str] = None,
) -> bool:
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                MERGE ProjectManagement.dbo.revizto_project_map AS target
                USING (SELECT ? AS revizto_project_uuid) AS source
                   ON target.revizto_project_uuid = source.revizto_project_uuid
                WHEN MATCHED THEN
                    UPDATE SET pm_project_id = ?, project_name_override = ?, is_active = 1, updated_at = SYSUTCDATETIME()
                WHEN NOT MATCHED THEN
                    INSERT (revizto_project_uuid, pm_project_id, project_name_override, is_active)
                    VALUES (?, ?, ?, 1);
                """,
                (revizto_project_uuid, pm_project_id, project_name_override, revizto_project_uuid, pm_project_id, project_name_override),
            )
            conn.commit()
            return True
    except Exception as exc:
        logger.error("Error upserting revizto mapping: %s", exc)
        return False


def deactivate_revizto_project_mapping(revizto_project_uuid: str) -> bool:
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE ProjectManagement.dbo.revizto_project_map
                SET is_active = 0, updated_at = SYSUTCDATETIME()
                WHERE revizto_project_uuid = ?
                """,
                (revizto_project_uuid,),
            )
            conn.commit()
            return True
    except Exception as exc:
        logger.error("Error deactivating revizto mapping: %s", exc)
        return False


def get_issue_attribute_mappings(active_only: bool = True) -> List[Dict[str, Any]]:
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            filter_sql = "WHERE m.is_active = 1" if active_only else ""
            cursor.execute(
                f"""
                SELECT m.map_id, m.project_id, m.source_system, m.raw_attribute_name,
                       m.mapped_field_name, m.data_type, m.priority, m.is_active,
                       m.created_at, m.updated_at
                FROM ProjectManagement.dbo.issue_attribute_map m
                {filter_sql}
                ORDER BY m.source_system, m.project_id, m.raw_attribute_name
                """
            )
            rows = cursor.fetchall()
            return [
                {
                    "map_id": row[0],
                    "project_id": row[1],
                    "source_system": row[2],
                    "raw_attribute_name": row[3],
                    "mapped_field_name": row[4],
                    "data_type": row[5],
                    "priority": row[6],
                    "is_active": bool(row[7]) if row[7] is not None else False,
                    "created_at": row[8],
                    "updated_at": row[9],
                }
                for row in rows
            ]
    except Exception as exc:
        logger.error("Error fetching issue attribute mappings: %s", exc)
        return []


def create_issue_attribute_mapping(payload: Dict[str, Any]) -> Optional[int]:
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO ProjectManagement.dbo.issue_attribute_map
                    (project_id, source_system, raw_attribute_name, mapped_field_name, data_type, priority, is_active)
                OUTPUT INSERTED.map_id
                VALUES (?, ?, ?, ?, ?, ?, 1)
                """,
                (
                    payload.get("project_id"),
                    payload.get("source_system"),
                    payload.get("raw_attribute_name"),
                    payload.get("mapped_field_name"),
                    payload.get("data_type"),
                    payload.get("priority", 100),
                ),
            )
            row = cursor.fetchone()
            conn.commit()
            return row[0] if row else None
    except Exception as exc:
        logger.error("Error creating issue attribute mapping: %s", exc)
        return None


def update_issue_attribute_mapping(map_id: int, payload: Dict[str, Any]) -> bool:
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE ProjectManagement.dbo.issue_attribute_map
                SET project_id = ?, source_system = ?, raw_attribute_name = ?,
                    mapped_field_name = ?, data_type = ?, priority = ?, updated_at = SYSUTCDATETIME()
                WHERE map_id = ?
                """,
                (
                    payload.get("project_id"),
                    payload.get("source_system"),
                    payload.get("raw_attribute_name"),
                    payload.get("mapped_field_name"),
                    payload.get("data_type"),
                    payload.get("priority", 100),
                    map_id,
                ),
            )
            conn.commit()
            return True
    except Exception as exc:
        logger.error("Error updating issue attribute mapping: %s", exc)
        return False


def deactivate_issue_attribute_mapping(map_id: int) -> bool:
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE ProjectManagement.dbo.issue_attribute_map
                SET is_active = 0, updated_at = SYSUTCDATETIME()
                WHERE map_id = ?
                """,
                (map_id,),
            )
            conn.commit()
            return True
    except Exception as exc:
        logger.error("Error deactivating issue attribute mapping: %s", exc)
        return False


def set_control_models(project_id: int, models: List[Dict[str, Any]]) -> bool:
    """Persist the control models (and metadata) assigned to a project."""
    normalized: List[Dict[str, Any]] = []
    seen: set[str] = set()

    for entry in models:
        file_name = entry.get('file_name') or entry.get('control_file_name')
        if not file_name:
            continue
        file_name = str(file_name).strip()
        if not file_name or file_name.lower() == "no files":
            continue
        if file_name in seen:
            continue

        metadata = entry.get('metadata') or {}

        targets = entry.get('validation_targets') or metadata.get('validation_targets')
        if targets:
            normalised_targets = sorted(
                {
                    str(target).lower()
                    for target in targets
                    if str(target).strip().lower() in CONTROL_VALIDATION_TARGETS
                }
            )
            if not normalised_targets:
                normalised_targets = sorted(CONTROL_VALIDATION_TARGETS)
            metadata['validation_targets'] = normalised_targets
        else:
            metadata.setdefault('validation_targets', sorted(CONTROL_VALIDATION_TARGETS))

        volume_label = entry.get('volume_label') or metadata.get('volume_label')
        metadata['volume_label'] = str(volume_label).strip() if volume_label else None
        notes = entry.get('notes') or metadata.get('notes')
        metadata['notes'] = str(notes).strip() if notes else None
        zone_code = entry.get('zone_code') or metadata.get('zone_code')
        metadata['zone_code'] = str(zone_code).strip() if zone_code else None
        metadata['is_primary'] = bool(entry.get('is_primary') or metadata.get('is_primary'))

        normalized.append({'file_name': file_name, 'metadata': metadata})
        seen.add(file_name)

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            metadata_supported = _ensure_control_model_metadata_column(conn)
            logger.info(
                "Persisting control models for project %s (metadata_supported=%s): %s",
                project_id,
                metadata_supported,
                normalized,
            )

            cursor.execute(
                """
                UPDATE ProjectManagement.dbo.tblControlModels
                SET is_active = 0
                WHERE project_id = ?
                """,
                (project_id,),
            )

            if not normalized:
                conn.commit()
                return True

            primary_candidates = [model for model in normalized if model['metadata'].get('is_primary')]
            if not primary_candidates:
                normalized[0]['metadata']['is_primary'] = True
                primary_candidates = [normalized[0]]

            ordered_models = [
                model for model in normalized if not model['metadata'].get('is_primary')
            ] + primary_candidates

            cursor.execute(
                """
                SELECT control_file_name
                FROM ProjectManagement.dbo.tblControlModels
                WHERE project_id = ?
                """,
                (project_id,),
            )
            existing_names = {row[0] for row in cursor.fetchall()}

            for entry in ordered_models:
                file_name = entry['file_name']
                metadata = entry['metadata']
                cleaned_metadata = {
                    key: value
                    for key, value in metadata.items()
                    if value not in (None, '', [])
                }
                metadata_json = json.dumps(cleaned_metadata) if cleaned_metadata and metadata_supported else None

                if file_name in existing_names:
                    if metadata_supported:
                        cursor.execute(
                            """
                            UPDATE ProjectManagement.dbo.tblControlModels
                            SET is_active = 1,
                                metadata_json = ?,
                                updated_at = GETDATE()
                            WHERE project_id = ? AND control_file_name = ?
                            """,
                            (metadata_json, project_id, file_name),
                        )
                    else:
                        cursor.execute(
                            """
                            UPDATE ProjectManagement.dbo.tblControlModels
                            SET is_active = 1,
                                updated_at = GETDATE()
                            WHERE project_id = ? AND control_file_name = ?
                            """,
                            (project_id, file_name),
                        )
                else:
                    if metadata_supported:
                        cursor.execute(
                            """
                            INSERT INTO ProjectManagement.dbo.tblControlModels
                                (project_id, control_file_name, is_active, metadata_json, created_at, updated_at)
                            VALUES (?, ?, 1, ?, GETDATE(), GETDATE())
                            """,
                            (project_id, file_name, metadata_json),
                        )
                    else:
                        cursor.execute(
                            """
                            INSERT INTO ProjectManagement.dbo.tblControlModels
                                (project_id, control_file_name, is_active, created_at, updated_at)
                            VALUES (?, ?, 1, GETDATE(), GETDATE())
                            """,
                            (project_id, file_name),
                        )

            conn.commit()
            logger.info(
                "Control models persisted for project %s. Active count: %s",
                project_id,
                len(ordered_models),
            )
            return True
    except Exception as e:
        logger.error(f"Error saving control models: {e}")
        return False


def get_control_file(project_id):
    """Retrieve the primary control file for the given project."""
    models = get_control_models(project_id)
    for model in models:
        if model.get('is_active') and (model.get('metadata') or {}).get('is_primary'):
            return model['control_file_name']
    for model in models:
        if model.get('is_active'):
            return model['control_file_name']
    return None


def set_control_file(project_id, file_name):
    """Save a single control file for the project (legacy helper)."""
    if not file_name:
        return set_control_models(project_id, [])
    return set_control_models(
        project_id,
        [{
            'file_name': file_name,
            'metadata': {
                'validation_targets': sorted(CONTROL_VALIDATION_TARGETS),
                'is_primary': True,
            },
        }],
    )


def update_file_validation_status(file_name, status, reason, regex_used,
                                  failed_field=None, failed_value=None, failed_reason=None, discipline=None, discipline_full=None):
    # Convert everything to string if not None
    file_name = str(file_name) if file_name is not None else ""
    status = str(status) if status is not None else ""
    reason = str(reason) if reason is not None else ""
    regex_used = str(regex_used) if regex_used is not None else ""
    failed_field = str(failed_field) if failed_field is not None else None
    failed_value = str(failed_value) if failed_value is not None else None
    failed_reason = str(failed_reason) if failed_reason is not None else None
    discipline = str(discipline) if discipline is not None else None
    discipline_full = str(discipline_full) if discipline_full is not None else None

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE RevitHealthCheckDB.dbo.tblRvtProjHealth
                SET validation_status = ?, 
                    validation_reason = ?, 
                    compiled_regex = ?, 
                    validated_date = GETDATE(),
                    failed_field_name = ?, 
                    failed_field_value = ?, 
                    failed_field_reason = ?,
                    discipline_code = ?,         
                    discipline_full_name = ?  
                WHERE strRvtFileName = ?
            """, status, reason, regex_used, failed_field, failed_value, failed_reason, discipline, discipline_full, file_name)
            conn.commit()
    except Exception as e:
        logger.error(f"❌ Failed to update validation for {file_name}: {e}")



def get_users_list():
    """Return a list of (user_id, name) tuples from the users table."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT {S.Users.ID}, {S.Users.NAME} FROM {S.Users.TABLE} ORDER BY {S.Users.NAME};"
            )
            return [(row[0], row[1]) for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"Error fetching users: {e}")
        return []


def get_review_tasks(project_id, cycle_id):
    """Return review schedule tasks for a project and cycle."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT rs.{S.ReviewSchedule.ID}, rs.{S.ReviewSchedule.REVIEW_DATE},
                       u.{S.Users.NAME}, rs.{S.ReviewSchedule.STATUS}
                FROM {S.ReviewSchedule.TABLE} rs
                LEFT JOIN {S.Users.TABLE} u ON rs.{S.ReviewSchedule.ASSIGNED_TO} = u.{S.Users.ID}
                WHERE rs.{S.ReviewSchedule.PROJECT_ID} = ? AND rs.{S.ReviewSchedule.CYCLE_ID} = ?
                ORDER BY rs.{S.ReviewSchedule.REVIEW_DATE} ASC;
                """,
                (project_id, cycle_id),
            )
            return [
                (row[0], row[1], row[2], row[3])
                for row in cursor.fetchall()
            ]
    except Exception as e:
        logger.error(f"❌ Error fetching review tasks: {e}")
        return []

def get_review_schedules_by_date_range(start_date, end_date, project_id=None):
    """Return review schedules between start_date (inclusive) and end_date (exclusive)."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            params = [start_date, end_date]
            project_filter = ""
            if project_id is not None:
                project_filter = f" AND rs.{S.ReviewSchedule.PROJECT_ID} = ?"
                params.append(project_id)
            cursor.execute(
                f"""
                SELECT rs.{S.ReviewSchedule.SCHEDULE_ID},
                       rs.{S.ReviewSchedule.PROJECT_ID},
                       rs.{S.ReviewSchedule.CYCLE_ID},
                       rs.{S.ReviewSchedule.REVIEW_DATE},
                       rs.{S.ReviewSchedule.ASSIGNED_TO},
                       rs.{S.ReviewSchedule.STATUS}
                FROM {S.ReviewSchedule.TABLE} rs
                WHERE rs.{S.ReviewSchedule.REVIEW_DATE} >= ?
                  AND rs.{S.ReviewSchedule.REVIEW_DATE} < ?
                  {project_filter}
                ORDER BY rs.{S.ReviewSchedule.REVIEW_DATE} ASC;
                """,
                tuple(params),
            )
            return [
                {
                    "schedule_id": row[0],
                    "project_id": row[1],
                    "cycle_id": row[2],
                    "review_date": row[3],
                    "assigned_to": row[4],
                    "status": row[5],
                }
                for row in cursor.fetchall()
            ]
    except Exception as e:
        logger.error(f"ƒ?O Error fetching review schedules by date range: {e}")
        return []


# ------------------------------------------------------------
# Review cycle detail functions
# ------------------------------------------------------------

def insert_review_cycle_details(
    project_id,
    cycle_id,
    construction_stage,
    proposed_fee,
    assigned_users,
    reviews_per_phase,
    planned_start_date,
    planned_completion_date,
    actual_start_date,
    actual_completion_date,
    hold_date,
    resume_date,
    new_contract,
):
    """Insert details for a review cycle."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                INSERT INTO {S.ReviewCycleDetails.TABLE} (
                    {S.ReviewCycleDetails.PROJECT_ID},
                    {S.ReviewCycleDetails.CYCLE_ID},
                    {S.ReviewCycleDetails.CONSTRUCTION_STAGE},
                    {S.ReviewCycleDetails.PROPOSED_FEE},
                    {S.ReviewCycleDetails.ASSIGNED_USERS},
                    {S.ReviewCycleDetails.REVIEWS_PER_PHASE},
                    {S.ReviewCycleDetails.PLANNED_START},
                    {S.ReviewCycleDetails.PLANNED_COMPLETION},
                    {S.ReviewCycleDetails.ACTUAL_START},
                    {S.ReviewCycleDetails.ACTUAL_COMPLETION},
                    {S.ReviewCycleDetails.HOLD_DATE},
                    {S.ReviewCycleDetails.RESUME_DATE},
                    {S.ReviewCycleDetails.NEW_CONTRACT}
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    project_id,
                    cycle_id,
                    construction_stage,
                    proposed_fee,
                    assigned_users,
                    reviews_per_phase,
                    planned_start_date,
                    planned_completion_date,
                    actual_start_date,
                    actual_completion_date,
                    hold_date,
                    resume_date,
                    int(new_contract),
                ),
            )
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"Error inserting review cycle details: {e}")
        return False


def update_review_task_assignee(schedule_id, user_id):
    """Update the assigned reviewer for a review task."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"UPDATE {S.ReviewSchedule.TABLE} SET {S.ReviewSchedule.ASSIGNED_TO} = ? WHERE {S.ReviewSchedule.ID} = ?",
                (user_id, schedule_id),
            )
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"❌ Error updating review task assignee: {e}")
        return False

def update_review_cycle_details(
    project_id,
    cycle_id,
    construction_stage,
    proposed_fee,
    assigned_users,
    reviews_per_phase,
    planned_start_date,
    planned_completion_date,
    actual_start_date,
    actual_completion_date,
    hold_date,
    resume_date,
    new_contract,
):
    """Update details for a review cycle."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                UPDATE {S.ReviewCycleDetails.TABLE}
                SET {S.ReviewCycleDetails.CONSTRUCTION_STAGE} = ?,
                    {S.ReviewCycleDetails.PROPOSED_FEE} = ?,
                    {S.ReviewCycleDetails.ASSIGNED_USERS} = ?,
                    {S.ReviewCycleDetails.REVIEWS_PER_PHASE} = ?,
                    {S.ReviewCycleDetails.PLANNED_START} = ?,
                    {S.ReviewCycleDetails.PLANNED_COMPLETION} = ?,
                    {S.ReviewCycleDetails.ACTUAL_START} = ?,
                    {S.ReviewCycleDetails.ACTUAL_COMPLETION} = ?,
                    {S.ReviewCycleDetails.HOLD_DATE} = ?,
                    {S.ReviewCycleDetails.RESUME_DATE} = ?,
                    {S.ReviewCycleDetails.NEW_CONTRACT} = ?
                WHERE {S.ReviewCycleDetails.PROJECT_ID} = ? AND {S.ReviewCycleDetails.CYCLE_ID} = ?;
                """,
                (
                    construction_stage,
                    proposed_fee,
                    assigned_users,
                    reviews_per_phase,
                    planned_start_date,
                    planned_completion_date,
                    actual_start_date,
                    actual_completion_date,
                    hold_date,
                    resume_date,
                    int(new_contract),
                    project_id,
                    cycle_id,
                ),
            )
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"Error updating review cycle details: {e}")
        return False


def upsert_project_review_progress(project_id, cycle_id, scoped_reviews, completed_reviews=0):
    """Create or update progress metrics for a project's review cycle."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                MERGE {S.ProjectReviews.TABLE} AS tgt
                USING (SELECT ? AS {S.ProjectReviews.PROJECT_ID}, ? AS {S.ProjectReviews.CYCLE_ID}) AS src
                ON tgt.{S.ProjectReviews.PROJECT_ID} = src.{S.ProjectReviews.PROJECT_ID}
                   AND tgt.{S.ProjectReviews.CYCLE_ID} = src.{S.ProjectReviews.CYCLE_ID}
                WHEN MATCHED THEN
                    UPDATE SET {S.ProjectReviews.SCOPED_REVIEWS} = ?,
                               {S.ProjectReviews.COMPLETED_REVIEWS} = ?,
                               {S.ProjectReviews.LAST_UPDATED} = GETDATE()
                WHEN NOT MATCHED THEN
                    INSERT ({S.ProjectReviews.PROJECT_ID}, {S.ProjectReviews.CYCLE_ID}, {S.ProjectReviews.SCOPED_REVIEWS}, {S.ProjectReviews.COMPLETED_REVIEWS}, {S.ProjectReviews.LAST_UPDATED})
                    VALUES (?, ?, ?, ?, GETDATE());
                """,
                (
                    project_id,
                    cycle_id,
                    scoped_reviews,
                    completed_reviews,
                    project_id,
                    cycle_id,
                    scoped_reviews,
                    completed_reviews,
                ),
            )
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"❌ Error updating project review progress: {e}")
        return False


def get_project_review_progress(project_id, cycle_id):
    """Fetch scoped/completed review counts and last update timestamp."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT {S.ProjectReviews.SCOPED_REVIEWS}, {S.ProjectReviews.COMPLETED_REVIEWS}, {S.ProjectReviews.LAST_UPDATED} FROM {S.ProjectReviews.TABLE} WHERE {S.ProjectReviews.PROJECT_ID} = ? AND {S.ProjectReviews.CYCLE_ID} = ?",
                (project_id, cycle_id),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return {
                "scoped_reviews": row[0],
                "completed_reviews": row[1],
                "last_updated": row[2].strftime("%Y-%m-%d %H:%M") if row[2] else "",
            }
    except Exception as e:
        logger.error(f"❌ Error fetching review progress: {e}")
        return None


def get_review_summary(project_id, cycle_id):
    """Return key summary information for a review cycle."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT p.{S.Projects.NAME},
                       rp.{S.ReviewParameters.CYCLE_ID},
                       d.{S.ReviewCycleDetails.CONSTRUCTION_STAGE},
                       rp.{S.ReviewParameters.LICENSE_START},
                       DATEDIFF(month, rp.{S.ReviewParameters.LICENSE_START}, rp.{S.ReviewParameters.LICENSE_END}) AS license_months,
                       pr.{S.ProjectReviews.SCOPED_REVIEWS},
                       pr.{S.ProjectReviews.COMPLETED_REVIEWS},
                       pr.{S.ProjectReviews.LAST_UPDATED}
                FROM {S.Projects.TABLE} p
                JOIN {S.ReviewParameters.TABLE} rp ON p.{S.Projects.ID} = rp.{S.ReviewParameters.PROJECT_ID} AND rp.{S.ReviewParameters.CYCLE_ID} = ?
                LEFT JOIN {S.ReviewCycleDetails.TABLE} d ON d.{S.ReviewCycleDetails.PROJECT_ID} = rp.{S.ReviewParameters.PROJECT_ID} AND d.{S.ReviewCycleDetails.CYCLE_ID} = rp.{S.ReviewParameters.CYCLE_ID}
                LEFT JOIN {S.ProjectReviews.TABLE} pr ON pr.{S.ProjectReviews.PROJECT_ID} = rp.{S.ReviewParameters.PROJECT_ID} AND pr.{S.ProjectReviews.CYCLE_ID} = rp.{S.ReviewParameters.CYCLE_ID}
                WHERE p.{S.Projects.ID} = ?;
                """,
                (cycle_id, project_id),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return {
                "project_name": row[0],
                "cycle_id": row[1],
                "construction_stage": row[2] or "",
                "license_start": row[3].strftime("%Y-%m-%d") if row[3] else "",
                "license_duration": row[4],
                "scoped_reviews": row[5] if row[5] is not None else 0,
                "completed_reviews": row[6] if row[6] is not None else 0,
                "last_updated": row[7].strftime("%Y-%m-%d %H:%M") if row[7] else "",
            }
    except Exception as e:
        logger.error(f"❌ Error fetching review summary: {e}")
        return None


def insert_contractual_link(project_id, review_cycle_id, bep_clause, billing_event, amount_due, status="Pending"):
    """Insert a contractual link record."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                INSERT INTO {S.ContractualLinks.TABLE} (
                    {S.ContractualLinks.PROJECT_ID},
                    {S.ContractualLinks.REVIEW_CYCLE_ID},
                    {S.ContractualLinks.BEP_CLAUSE},
                    {S.ContractualLinks.BILLING_EVENT},
                    {S.ContractualLinks.AMOUNT_DUE},
                    {S.ContractualLinks.STATUS}
                ) VALUES (?, ?, ?, ?, ?, ?);
                """,
                (project_id, review_cycle_id, bep_clause, billing_event, amount_due, status),
            )
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"❌ Error inserting contractual link: {e}")
        return False


def get_contractual_links(project_id, review_cycle_id=None):
    """Fetch contractual links for a project, optionally filtered by cycle."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            if review_cycle_id:
                cursor.execute(
                    f"""
                    SELECT {S.ContractualLinks.BEP_CLAUSE}, {S.ContractualLinks.BILLING_EVENT}, {S.ContractualLinks.AMOUNT_DUE}, {S.ContractualLinks.STATUS}
                    FROM {S.ContractualLinks.TABLE}
                    WHERE {S.ContractualLinks.PROJECT_ID} = ? AND {S.ContractualLinks.REVIEW_CYCLE_ID} = ?
                    ORDER BY {S.ContractualLinks.ID};
                    """,
                    (project_id, review_cycle_id),
                )
            else:
                cursor.execute(
                    f"""
                    SELECT {S.ContractualLinks.BEP_CLAUSE}, {S.ContractualLinks.BILLING_EVENT}, {S.ContractualLinks.AMOUNT_DUE}, {S.ContractualLinks.STATUS}
                    FROM {S.ContractualLinks.TABLE}
                    WHERE {S.ContractualLinks.PROJECT_ID} = ?
                    ORDER BY {S.ContractualLinks.ID};
                    """,
                    (project_id,),
                )
            return [tuple(row) for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"❌ Error fetching contractual links: {e}")
        return []


def get_review_cycles(project_id):
    """Return review cycles for the given project from ServiceReviews table."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT sr.review_id, ps.service_name, sr.cycle_no, sr.planned_date, 
                       sr.due_date, sr.status, sr.disciplines,
                       ISNULL(sr.status_override, 0) as status_override
                FROM ServiceReviews sr
                LEFT JOIN ProjectServices ps ON sr.service_id = ps.service_id
                WHERE ps.project_id = ?
                ORDER BY sr.planned_date, sr.cycle_no;
                """,
                (project_id,),
            )
            return [tuple(row) for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"❌ Error fetching review cycles: {e}")
        return []


def create_review_cycle(project_id, stage_id, start_date, end_date, num_reviews, created_by):
    """Insert a new review cycle and return the cycle ID."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                INSERT INTO {S.ReviewCycles.TABLE}
                ({S.ReviewCycles.PROJECT_ID}, {S.ReviewCycles.STAGE_ID}, {S.ReviewCycles.START_DATE}, {S.ReviewCycles.END_DATE}, {S.ReviewCycles.NUM_REVIEWS}, {S.ReviewCycles.CREATED_BY})
                VALUES (?, ?, ?, ?, ?, ?);
                SELECT SCOPE_IDENTITY();
                """,
                (project_id, stage_id, start_date, end_date, num_reviews, created_by),
            )
            new_id = cursor.fetchone()[0]
            conn.commit()
            return int(new_id)
    except Exception as e:
        logger.error(f"❌ Error creating review cycle: {e}")
        return None


def update_review_cycle(review_cycle_id, start_date=None, end_date=None, num_reviews=None, stage_id=None):
    """Update an existing review cycle."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                UPDATE {S.ReviewCycles.TABLE}
                SET {S.ReviewCycles.START_DATE} = COALESCE(?, {S.ReviewCycles.START_DATE}),
                    {S.ReviewCycles.END_DATE} = COALESCE(?, {S.ReviewCycles.END_DATE}),
                    {S.ReviewCycles.NUM_REVIEWS} = COALESCE(?, {S.ReviewCycles.NUM_REVIEWS}),
                    {S.ReviewCycles.STAGE_ID} = COALESCE(?, {S.ReviewCycles.STAGE_ID})
                WHERE {S.ReviewCycles.ID} = ?;
                """,
                (start_date, end_date, num_reviews, stage_id, review_cycle_id),
            )
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"❌ Error updating review cycle: {e}")
        return False


def delete_review_cycle(review_cycle_id):
    """Delete a review cycle."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"DELETE FROM {S.ReviewCycles.TABLE} WHERE {S.ReviewCycles.ID} = ?;",
                (review_cycle_id,),
            )
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"❌ Error deleting review cycle: {e}")
        return False


def get_review_cycle_tasks(schedule_id):
    """Return tasks linked to a review schedule."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT {S.ReviewTasks.ID}, {S.ReviewTasks.TASK_ID}, {S.ReviewTasks.ASSIGNED_TO}, {S.ReviewTasks.STATUS}
                FROM {S.ReviewTasks.TABLE}
                WHERE {S.ReviewTasks.SCHEDULE_ID} = ?
                ORDER BY {S.ReviewTasks.ID};
                """,
                (schedule_id,)
            )
            return [tuple(row) for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"❌ Error fetching review tasks: {e}")
        return []


def update_review_cycle_task(review_task_id, assigned_to=None, status=None):
    """Update a review task's status or assignee."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                UPDATE {S.ReviewTasks.TABLE}
                SET {S.ReviewTasks.ASSIGNED_TO} = COALESCE(?, {S.ReviewTasks.ASSIGNED_TO}),
                    {S.ReviewTasks.STATUS} = COALESCE(?, {S.ReviewTasks.STATUS})
                WHERE {S.ReviewTasks.ID} = ?;
                """,
                (assigned_to, status, review_task_id),
            )
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"❌ Error updating review task: {e}")
        return False


def get_bep_matrix(project_id):
    """Return BEP section data for a project."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT s.id, s.section_title, p.responsible_user_id, p.status, p.notes
                FROM bep_sections s
                LEFT JOIN project_bep_sections p ON s.id = p.section_id AND p.project_id = ?
                ORDER BY s.id;
                """,
                (project_id,)
            )
            return [tuple(row) for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"❌ Error fetching BEP matrix: {e}")
        return []


def get_projects_full():
    """Return all rows from the vw_projects_full view."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM vw_projects_full")
            columns = [c[0] for c in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"❌ Error fetching full projects: {e}")
        return []


def get_projects_with_health():
    """Return all projects with calculated health percentage.
    
    Health is calculated as:
    - Primary: percentage of completed services (completed_services / total_services)
    - Fallback: percentage of completed reviews (completed_reviews / total_reviews)
    - If neither available: null
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Get all projects with service and review completion metrics
            cursor.execute(f"""
                SELECT 
                    p.{S.Projects.ID},
                    p.{S.Projects.NAME},
                    p.{S.Projects.STATUS},
                    p.{S.Projects.PRIORITY},
                    p.{S.Projects.INTERNAL_LEAD},
                    p.{S.Projects.END_DATE},
                    COALESCE(
                        CASE 
                            WHEN Svc.total_services > 0 
                            THEN (SVC.completed_services * 100) / SVC.total_services
                            WHEN Rev.total_reviews > 0 
                            THEN (Rev.completed_reviews * 100) / Rev.total_reviews
                            ELSE NULL
                        END,
                        NULL
                    ) AS health_pct,
                    COALESCE(SVC.total_services, 0) AS total_services,
                    COALESCE(SVC.completed_services, 0) AS completed_services,
                    COALESCE(Rev.total_reviews, 0) AS total_reviews,
                    COALESCE(Rev.completed_reviews, 0) AS completed_reviews
                FROM {S.Projects.TABLE} p
                LEFT JOIN (
                    SELECT 
                        {S.ProjectServices.PROJECT_ID},
                        COUNT(*) AS total_services,
                        SUM(CASE WHEN {S.ProjectServices.STATUS} = 'completed' THEN 1 ELSE 0 END) AS completed_services
                    FROM {S.ProjectServices.TABLE}
                    GROUP BY {S.ProjectServices.PROJECT_ID}
                ) SVC ON p.{S.Projects.ID} = SVC.{S.ProjectServices.PROJECT_ID}
                LEFT JOIN (
                    SELECT 
                        ps.{S.ProjectServices.PROJECT_ID} AS project_id,
                        COUNT(sr.{S.ServiceReviews.REVIEW_ID}) AS total_reviews,
                        SUM(CASE WHEN sr.{S.ServiceReviews.STATUS} = 'completed' THEN 1 ELSE 0 END) AS completed_reviews
                    FROM {S.ServiceReviews.TABLE} sr
                    INNER JOIN {S.ProjectServices.TABLE} ps ON sr.{S.ServiceReviews.SERVICE_ID} = ps.{S.ProjectServices.SERVICE_ID}
                    GROUP BY ps.{S.ProjectServices.PROJECT_ID}
                ) Rev ON p.{S.Projects.ID} = Rev.project_id
                ORDER BY p.{S.Projects.NAME}
            """)
            
            columns = [c[0] for c in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"❌ Error fetching projects with health: {e}")
        return []


def upsert_bep_section(project_id, section_id, responsible_user_id, status, notes):
    """Create or update a project BEP section record."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                MERGE project_bep_sections AS tgt
                USING (SELECT ? AS project_id, ? AS section_id) AS src
                ON tgt.project_id = src.project_id AND tgt.section_id = src.section_id
                WHEN MATCHED THEN
                    UPDATE SET responsible_user_id = ?, status = ?, notes = ?
                WHEN NOT MATCHED THEN
                    INSERT (project_id, section_id, responsible_user_id, status, notes)
                    VALUES (src.project_id, src.section_id, ?, ?, ?);
                """,
                (
                    project_id,
                    section_id,
                    responsible_user_id,
                    status,
                    notes,
                    responsible_user_id,
                    status,
                    notes,
                ),
            )
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"❌ Error upserting BEP section: {e}")
        return False


def update_project_financials(project_id, contract_value=None, payment_terms=None):
    """Update financial fields in the projects table."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            sets = []
            params = []
            if contract_value is not None:
                sets.append("contract_value = ?")
                params.append(contract_value)
            if payment_terms is not None:
                sets.append("payment_terms = ?")
                params.append(payment_terms)
            if sets:
                sql = "UPDATE projects SET " + ", ".join(sets) + " WHERE project_id = ?"
                params.append(project_id)
                cursor.execute(sql, params)
                conn.commit()
            return True
    except Exception as e:
        logger.error(f"❌ Error updating project financials: {e}")
        return False



def update_bep_status(project_id, section_id, status):
    """Update the status of a BEP section for a project."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE project_bep_sections SET status = ? WHERE project_id = ? AND section_id = ?;",
                (status, project_id, section_id),
            )
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"❌ Error updating BEP status: {e}")
        return False


def update_client_info(project_id, client_contact=None, contact_email=None):
    """Update client contact details for a project."""
    try:
        with get_db_connection("ProjectManagement") as conn:
            cursor = conn.cursor()
            
            # First, get the client_id for this project
            cursor.execute(
                f"SELECT {S.Projects.CLIENT_ID} FROM dbo.{S.Projects.TABLE} WHERE {S.Projects.ID} = ?",
                (project_id,)
            )
            result = cursor.fetchone()
            
            if not result or not result[0]:
                logger.warning(f"No client_id found for project {project_id}")
                return False
                
            client_id = result[0]
            
            # Update the client information
            sets = []
            params = []
            if client_contact is not None:
                sets.append(f"{S.Clients.CONTACT_NAME} = ?")
                params.append(client_contact)
            if contact_email is not None:
                sets.append(f"{S.Clients.CONTACT_EMAIL} = ?")
                params.append(contact_email)
                
            if sets:
                sql = f"UPDATE dbo.{S.Clients.TABLE} SET " + ", ".join(sets) + f" WHERE {S.Clients.CLIENT_ID} = ?"
                params.append(client_id)
                cursor.execute(sql, params)
                conn.commit()
                logger.info(f"Updated client info for client_id {client_id}")
                
            return True
    except Exception as e:
        logger.error(f"Error updating client info: {e}")
        return False


def get_available_clients():
    """Return list of all available clients."""
    try:
        with get_db_connection("ProjectManagement") as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT {S.Clients.CLIENT_ID}, {S.Clients.CLIENT_NAME}, 
                       {S.Clients.CONTACT_NAME}, {S.Clients.CONTACT_EMAIL},
                       {S.Clients.NAMING_CONVENTION}
                FROM dbo.{S.Clients.TABLE}
                ORDER BY {S.Clients.CLIENT_NAME};
                """
            )
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"Error fetching clients: {e}")
        return []


CLIENT_DB_FIELD_MAP = {
    'client_name': S.Clients.CLIENT_NAME,
    'contact_name': S.Clients.CONTACT_NAME,
    'contact_email': S.Clients.CONTACT_EMAIL,
    'contact_phone': S.Clients.CONTACT_PHONE,
    'address': S.Clients.ADDRESS,
    'city': S.Clients.CITY,
    'state': S.Clients.STATE,
    'postcode': S.Clients.POSTCODE,
    'country': S.Clients.COUNTRY,
    'naming_convention': S.Clients.NAMING_CONVENTION,
}


def _prepare_client_payload(client_data):
    """Normalise client payload by trimming strings and coalescing blanks to None."""
    if not client_data:
        return {}
    prepared = {}
    for key, value in client_data.items():
        if isinstance(value, str):
            value = value.strip()
            if value == '':
                value = None
        prepared[key] = value

    # Support both 'name' and 'client_name' keys from different callers
    if 'name' in prepared and 'client_name' not in prepared:
        prepared['client_name'] = prepared.pop('name')

    return prepared


def _row_to_client_dict(row):
    """Convert a database client row into a dictionary."""
    if row is None:
        return None
    return {
        'client_id': row[0],
        'client_name': row[1],
        'contact_name': row[2],
        'contact_email': row[3],
        'contact_phone': row[4],
        'address': row[5],
        'city': row[6],
        'state': row[7],
        'postcode': row[8],
        'country': row[9],
        'naming_convention': row[10],
    }


def get_client_by_id(client_id):
    """Fetch a single client by ID."""
    try:
        with get_db_connection("ProjectManagement") as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT {S.Clients.CLIENT_ID}, {S.Clients.CLIENT_NAME},
                       {S.Clients.CONTACT_NAME}, {S.Clients.CONTACT_EMAIL},
                       {S.Clients.CONTACT_PHONE}, {S.Clients.ADDRESS},
                       {S.Clients.CITY}, {S.Clients.STATE},
                       {S.Clients.POSTCODE}, {S.Clients.COUNTRY},
                       {S.Clients.NAMING_CONVENTION}
                FROM dbo.{S.Clients.TABLE}
                WHERE {S.Clients.CLIENT_ID} = ?
                """,
                (client_id,)
            )
            row = cursor.fetchone()
            return _row_to_client_dict(row)
    except Exception as e:
        logger.error(f"Error fetching client {client_id}: {e}")
        return None


def get_clients_detailed():
    """Fetch all clients with detailed fields as dictionaries."""
    try:
        with get_db_connection("ProjectManagement") as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT {S.Clients.CLIENT_ID}, {S.Clients.CLIENT_NAME},
                       {S.Clients.CONTACT_NAME}, {S.Clients.CONTACT_EMAIL},
                       {S.Clients.CONTACT_PHONE}, {S.Clients.ADDRESS},
                       {S.Clients.CITY}, {S.Clients.STATE},
                       {S.Clients.POSTCODE}, {S.Clients.COUNTRY},
                       {S.Clients.NAMING_CONVENTION}
                FROM dbo.{S.Clients.TABLE}
                ORDER BY {S.Clients.CLIENT_NAME}
                """
            )
            return [_row_to_client_dict(row) for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"Error fetching detailed clients: {e}")
        return []


def create_client(client_data):
    """Create a client record and return the inserted client."""
    data = _prepare_client_payload(client_data or {})
    client_name = data.get('client_name')
    if not client_name:
        raise ValueError("Client name is required")

    try:
        with get_db_connection("ProjectManagement") as conn:
            cursor = conn.cursor()
            columns = []
            values = []
            for key, column in CLIENT_DB_FIELD_MAP.items():
                if key in data:
                    columns.append(column)
                    values.append(data[key])

            placeholders = ', '.join(['?'] * len(values))
            cursor.execute(
                f"""
                INSERT INTO dbo.{S.Clients.TABLE} ({', '.join(columns)})
                VALUES ({placeholders})
                """,
                values
            )
            conn.commit()

            cursor.execute("SELECT @@IDENTITY")
            client_id = cursor.fetchone()[0]
            return get_client_by_id(client_id)
    except Exception as e:
        logger.error(f"Error creating client '{client_name}': {e}")
        return None


def update_client(client_id, client_data):
    """Update a client and return the updated record."""
    data = _prepare_client_payload(client_data or {})
    if not data:
        return get_client_by_id(client_id)

    try:
        with get_db_connection("ProjectManagement") as conn:
            cursor = conn.cursor()
            sets = []
            values = []
            for key, column in CLIENT_DB_FIELD_MAP.items():
                if key in data:
                    sets.append(f"{column} = ?")
                    values.append(data[key])

            if not sets:
                return get_client_by_id(client_id)

            values.append(client_id)
            cursor.execute(
                f"""
                UPDATE dbo.{S.Clients.TABLE}
                SET {', '.join(sets)}
                WHERE {S.Clients.CLIENT_ID} = ?
                """,
                values
            )
            conn.commit()

            if cursor.rowcount == 0:
                return None

            return get_client_by_id(client_id)
    except Exception as e:
        logger.error(f"Error updating client {client_id}: {e}")
        return None


def delete_client(client_id):
    """Delete a client record if it is not attached to any projects."""
    try:
        with get_db_connection("ProjectManagement") as conn:
            cursor = conn.cursor()

            cursor.execute(
                f"""
                SELECT COUNT(*) FROM dbo.{S.Projects.TABLE}
                WHERE {S.Projects.CLIENT_ID} = ?
                """,
                (client_id,)
            )
            if cursor.fetchone()[0] > 0:
                return False, "Client is assigned to one or more projects."

            cursor.execute(
                f"DELETE FROM dbo.{S.Clients.TABLE} WHERE {S.Clients.CLIENT_ID} = ?",
                (client_id,)
            )
            conn.commit()
            return cursor.rowcount > 0, None
    except Exception as e:
        logger.error(f"Error deleting client {client_id}: {e}")
        return False, str(e)


def get_available_project_types():
    """Return list of all available project types."""
    try:
        with get_db_connection("ProjectManagement") as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT {S.ProjectTypes.TYPE_ID}, {S.ProjectTypes.TYPE_NAME}
                FROM dbo.{S.ProjectTypes.TABLE}
                ORDER BY {S.ProjectTypes.TYPE_NAME};
                """
            )
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"Error fetching project types: {e}")
        return []


def get_available_sectors():
    """Return list of all available sectors."""
    try:
        with get_db_connection("ProjectManagement") as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT {S.Sectors.SECTOR_ID}, {S.Sectors.SECTOR_NAME}
                FROM dbo.{S.Sectors.TABLE}
                ORDER BY {S.Sectors.SECTOR_NAME};
                """
            )
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"Error fetching sectors: {e}")
        return []


def get_available_delivery_methods():
    """Return list of all available delivery methods."""
    try:
        with get_db_connection("ProjectManagement") as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT {S.DeliveryMethods.DELIVERY_METHOD_ID}, {S.DeliveryMethods.DELIVERY_METHOD_NAME}
                FROM dbo.{S.DeliveryMethods.TABLE}
                ORDER BY {S.DeliveryMethods.DELIVERY_METHOD_NAME};
                """
            )
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"Error fetching delivery methods: {e}")
        return []


def get_available_construction_phases():
    """Return list of all available construction phases."""
    try:
        with get_db_connection("ProjectManagement") as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT {S.ProjectPhases.PROJECT_PHASE_ID}, {S.ProjectPhases.PROJECT_PHASE_NAME}
                FROM dbo.{S.ProjectPhases.TABLE}
                ORDER BY {S.ProjectPhases.PROJECT_PHASE_NAME};
                """
            )
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"Error fetching construction phases: {e}")
        return []


def get_available_construction_stages():
    """Return list of all available construction stages."""
    try:
        with get_db_connection("ProjectManagement") as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT {S.ConstructionStages.CONSTRUCTION_STAGE_ID}, {S.ConstructionStages.CONSTRUCTION_STAGE_NAME}
                FROM dbo.{S.ConstructionStages.TABLE}
                ORDER BY {S.ConstructionStages.CONSTRUCTION_STAGE_NAME};
                """
            )
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"Error fetching construction stages: {e}")
        return []


def get_available_users():
    """Return list of all available users for project managers and leads."""
    try:
        with get_db_connection("ProjectManagement") as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT {S.Users.ID}, {S.Users.NAME}, {S.Users.EMAIL}
                FROM dbo.{S.Users.TABLE}
                ORDER BY {S.Users.NAME};
                """
            )
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"Error fetching users: {e}")
        return []


def insert_client(client_data):
    """Insert a new client into the database (backwards compatible wrapper)."""
    try:
        client = create_client(client_data)
        return client is not None
    except Exception as e:
        logger.error(f"Error creating client: {e}")
        return False


def assign_client_to_project(project_id, client_id):
    """Assign a client to a project by updating the project's client_id."""
    try:
        with get_db_connection("ProjectManagement") as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                UPDATE dbo.{S.Projects.TABLE} 
                SET {S.Projects.CLIENT_ID} = ? 
                WHERE {S.Projects.ID} = ?
                """,
                (client_id, project_id)
            )
            conn.commit()
            logger.info(f"Assigned client {client_id} to project {project_id}")
            return True
    except Exception as e:
        logger.error(f"Error assigning client to project: {e}")
        return False


def create_new_client(client_data):
    """Create a new client in the database and return the client_id."""
    client = create_client(client_data)
    if client:
        logger.info(f"Created new client: {client.get('client_name')} (ID: {client.get('client_id')})")
        return client.get('client_id')
    return None


def get_reference_options(table):
    """Return (id, name) tuples from a reference table."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            id_col = table.rstrip('s') + '_id'
            name_col = table.rstrip('s') + '_name'
            cursor.execute(f"SELECT {id_col}, {name_col} FROM {table} ORDER BY {name_col};")
            return [(row[0], row[1]) for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"❌ Error fetching {table}: {e}")
        return []


def insert_project_full(data):
    """Insert a project record with arbitrary fields.

    SQL Server is strict about data types, so values coming from the
    frontend (often as strings) need to be coerced into the proper
    numeric types before insertion. Without this, pyodbc tries to insert
    NVARCHAR values into numeric columns and the database raises
    "Error converting data type nvarchar to numeric".
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cols = list(data.keys())
            if not cols:
                return False

            # Columns expected to be numeric in the projects table
            numeric_fields = {
                S.Projects.CLIENT_ID,
                S.Projects.TYPE_ID,
                S.Projects.SECTOR_ID,
                S.Projects.METHOD_ID,
                S.Projects.PHASE_ID,
                S.Projects.STAGE_ID,
                S.Projects.PROJECT_MANAGER,
                S.Projects.INTERNAL_LEAD,
                S.Projects.CONTRACT_VALUE,
                S.Projects.AGREED_FEE,
                S.Projects.PRIORITY,
                # New numeric fields added for enhanced project creation
                S.Projects.AREA_HECTARES,
                S.Projects.MW_CAPACITY,
            }

            values = []
            for c in cols:
                val = data.get(c)

                if val in ("", None):
                    values.append(None)
                elif c in numeric_fields:
                    try:
                        values.append(float(val) if "." in str(val) else int(val))
                    except (ValueError, TypeError):
                        values.append(None)
                else:
                    values.append(val)

            placeholders = ', '.join(['?'] * len(cols))
            sql = f"INSERT INTO projects ({', '.join(cols)}) VALUES ({placeholders})"
            cursor.execute(sql, values)
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"Error inserting project: {e}")
        return False


def update_project_record(project_id, data):
    """Update arbitrary project fields for a given project_id."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cols = [c for c in data.keys() if c]
            if not cols:
                return False

            numeric_fields = {
                S.Projects.CLIENT_ID,
                S.Projects.TYPE_ID,
                S.Projects.SECTOR_ID,
                S.Projects.METHOD_ID,
                S.Projects.PHASE_ID,
                S.Projects.STAGE_ID,
                S.Projects.PROJECT_MANAGER,
                S.Projects.INTERNAL_LEAD,
                S.Projects.CONTRACT_VALUE,
                S.Projects.AGREED_FEE,
                S.Projects.PRIORITY,
                S.Projects.AREA_HECTARES,
                S.Projects.MW_CAPACITY,
            }

            values = []
            for c in cols:
                val = data.get(c)
                if val in ('', None):
                    values.append(None)
                elif c in numeric_fields:
                    try:
                        str_val = str(val)
                        values.append(float(str_val) if '.' in str_val else int(str_val))
                    except (ValueError, TypeError):
                        values.append(None)
                else:
                    values.append(val)

            set_clause = ', '.join([f"{c} = ?" for c in cols])
            sql = f"UPDATE projects SET {set_clause} WHERE project_id = ?"
            cursor.execute(sql, values + [project_id])
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"Error updating project: {e}")
        return False
# ===================== Project Bookmarks Functions =====================

def get_project_bookmarks(project_id):
    """Get all bookmarks for a specific project."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT {S.ProjectBookmarks.ID}, {S.ProjectBookmarks.NAME}, 
                       {S.ProjectBookmarks.URL}, {S.ProjectBookmarks.DESCRIPTION}, 
                       {S.ProjectBookmarks.CATEGORY}, {S.ProjectBookmarks.TAGS},
                       {S.ProjectBookmarks.NOTES}, {S.ProjectBookmarks.CREATED_AT}
                FROM {S.ProjectBookmarks.TABLE} 
                WHERE {S.ProjectBookmarks.PROJECT_ID} = ?
                ORDER BY {S.ProjectBookmarks.CATEGORY}, {S.ProjectBookmarks.NAME}
                """,
                (project_id,)
            )
            bookmarks = []
            for row in cursor.fetchall():
                bookmarks.append({
                    'id': row[0],
                    'name': row[1],
                    'url': row[2],
                    'description': row[3],
                    'category': row[4],
                    'tags': row[5],
                    'notes': row[6],
                    'created_at': row[7]
                })
            return bookmarks
    except Exception as e:
        logger.error(f"❌ Error fetching bookmarks: {e}")
        return []

def add_bookmark(project_id, name, url, description="", category="General", tags="", notes=""):
    """Add a new bookmark for a project."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            created_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            cursor.execute(
                f"""
                INSERT INTO {S.ProjectBookmarks.TABLE} (
                    {S.ProjectBookmarks.PROJECT_ID}, {S.ProjectBookmarks.NAME}, 
                    {S.ProjectBookmarks.URL}, {S.ProjectBookmarks.DESCRIPTION}, 
                    {S.ProjectBookmarks.CATEGORY}, {S.ProjectBookmarks.TAGS},
                    {S.ProjectBookmarks.NOTES}, {S.ProjectBookmarks.CREATED_AT}
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (project_id, name, url, description, category, tags, notes, created_at)
            )
            
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"❌ Error adding bookmark: {e}")
        return False

def update_bookmark(bookmark_id, name=None, url=None, description=None, category=None, tags=None, notes=None):
    """Update an existing bookmark."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Build dynamic update query
            update_fields = {}
            if name is not None:
                update_fields[S.ProjectBookmarks.NAME] = name
            if url is not None:
                update_fields[S.ProjectBookmarks.URL] = url
            if description is not None:
                update_fields[S.ProjectBookmarks.DESCRIPTION] = description
            if category is not None:
                update_fields[S.ProjectBookmarks.CATEGORY] = category
            if tags is not None:
                update_fields[S.ProjectBookmarks.TAGS] = tags
            if notes is not None:
                update_fields[S.ProjectBookmarks.NOTES] = notes
                
            if not update_fields:
                return False
                
            set_clause = ', '.join([f"{field} = ?" for field in update_fields.keys()])
            values = list(update_fields.values()) + [bookmark_id]
            
            cursor.execute(
                f"UPDATE {S.ProjectBookmarks.TABLE} SET {set_clause} WHERE {S.ProjectBookmarks.ID} = ?",
                values
            )
            
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"❌ Error updating bookmark: {e}")
        return False

def delete_bookmark(bookmark_id):
    """Delete a bookmark by ID."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"DELETE FROM {S.ProjectBookmarks.TABLE} WHERE {S.ProjectBookmarks.ID} = ?",
                (bookmark_id,)
            )
            
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"❌ Error deleting bookmark: {e}")
        return False

def get_bookmark_categories(project_id):
    """Get distinct categories for a project's bookmarks."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT DISTINCT {S.ProjectBookmarks.CATEGORY}
                FROM {S.ProjectBookmarks.TABLE} 
                WHERE {S.ProjectBookmarks.PROJECT_ID} = ?
                ORDER BY {S.ProjectBookmarks.CATEGORY}
                """,
                (project_id,)
            )
            categories = [row[0] for row in cursor.fetchall()]
            return categories
    except Exception as e:
        logger.error(f"❌ Error fetching bookmark categories: {e}")
        return []
        
def delete_project(project_id):
    """Delete a project and all related data from the database."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Delete in order of dependencies (child tables first)
            
            # Project-specific documents and clauses
            cursor.execute(f"DELETE FROM {S.ProjectClauses.TABLE} WHERE EXISTS (SELECT 1 FROM {S.ProjectSections.TABLE} ps INNER JOIN {S.ProjectDocuments.TABLE} pd ON ps.{S.ProjectSections.PROJECT_DOCUMENT_ID} = pd.{S.ProjectDocuments.PROJECT_DOCUMENT_ID} WHERE {S.ProjectClauses.TABLE}.{S.ProjectClauses.PROJECT_SECTION_ID} = ps.{S.ProjectSections.PROJECT_SECTION_ID} AND pd.{S.ProjectDocuments.PROJECT_ID} = ?)", (project_id,))
            cursor.execute(f"DELETE FROM {S.ProjectSections.TABLE} WHERE EXISTS (SELECT 1 FROM {S.ProjectDocuments.TABLE} pd WHERE {S.ProjectSections.TABLE}.{S.ProjectSections.PROJECT_DOCUMENT_ID} = pd.{S.ProjectDocuments.PROJECT_DOCUMENT_ID} AND pd.{S.ProjectDocuments.PROJECT_ID} = ?)", (project_id,))
            cursor.execute(f"DELETE FROM {S.DocumentRevisions.TABLE} WHERE EXISTS (SELECT 1 FROM {S.ProjectDocuments.TABLE} pd WHERE {S.DocumentRevisions.TABLE}.{S.DocumentRevisions.PROJECT_DOCUMENT_ID} = pd.{S.ProjectDocuments.PROJECT_DOCUMENT_ID} AND pd.{S.ProjectDocuments.PROJECT_ID} = ?)", (project_id,))
            cursor.execute(f"DELETE FROM {S.PublishedFiles.TABLE} WHERE EXISTS (SELECT 1 FROM {S.DocumentRevisions.TABLE} dr INNER JOIN {S.ProjectDocuments.TABLE} pd ON dr.{S.DocumentRevisions.PROJECT_DOCUMENT_ID} = pd.{S.ProjectDocuments.PROJECT_DOCUMENT_ID} WHERE {S.PublishedFiles.TABLE}.{S.PublishedFiles.REVISION_ID} = dr.{S.DocumentRevisions.REVISION_ID} AND pd.{S.ProjectDocuments.PROJECT_ID} = ?)", (project_id,))
            cursor.execute(f"DELETE FROM {S.ProjectDocuments.TABLE} WHERE {S.ProjectDocuments.PROJECT_ID} = ?", (project_id,))
            
            # Clause assignments
            cursor.execute(f"DELETE FROM {S.ClauseAssignments.TABLE} WHERE EXISTS (SELECT 1 FROM {S.ProjectClauses.TABLE} pc INNER JOIN {S.ProjectSections.TABLE} ps ON pc.{S.ProjectClauses.PROJECT_SECTION_ID} = ps.{S.ProjectSections.PROJECT_SECTION_ID} INNER JOIN {S.ProjectDocuments.TABLE} pd ON ps.{S.ProjectSections.PROJECT_DOCUMENT_ID} = pd.{S.ProjectDocuments.PROJECT_DOCUMENT_ID} WHERE {S.ClauseAssignments.TABLE}.{S.ClauseAssignments.PROJECT_CLAUSE_ID} = pc.{S.ProjectClauses.PROJECT_CLAUSE_ID} AND pd.{S.ProjectDocuments.PROJECT_ID} = ?)", (project_id,))
            
            # Service-related data
            cursor.execute(f"DELETE FROM {S.ServiceReviews.TABLE} WHERE EXISTS (SELECT 1 FROM {S.ProjectServices.TABLE} ps WHERE ps.{S.ProjectServices.SERVICE_ID} = {S.ServiceReviews.TABLE}.{S.ServiceReviews.SERVICE_ID} AND ps.{S.ProjectServices.PROJECT_ID} = ?)", (project_id,))
            cursor.execute(f"DELETE FROM {S.ServiceScheduleSettings.TABLE} WHERE EXISTS (SELECT 1 FROM {S.ProjectServices.TABLE} ps WHERE ps.{S.ProjectServices.SERVICE_ID} = {S.ServiceScheduleSettings.TABLE}.{S.ServiceScheduleSettings.SERVICE_ID} AND ps.{S.ProjectServices.PROJECT_ID} = ?)", (project_id,))
            cursor.execute(f"DELETE FROM {S.ServiceDeliverables.TABLE} WHERE EXISTS (SELECT 1 FROM {S.ProjectServices.TABLE} ps WHERE ps.{S.ProjectServices.SERVICE_ID} = {S.ServiceDeliverables.TABLE}.{S.ServiceDeliverables.SERVICE_ID} AND ps.{S.ProjectServices.PROJECT_ID} = ?)", (project_id,))
            cursor.execute(f"DELETE FROM {S.ProjectServices.TABLE} WHERE {S.ProjectServices.PROJECT_ID} = ?", (project_id,))
            
            # Billing data
            cursor.execute(f"DELETE FROM {S.BillingClaimLines.TABLE} WHERE EXISTS (SELECT 1 FROM {S.BillingClaims.TABLE} bc WHERE {S.BillingClaimLines.TABLE}.{S.BillingClaimLines.CLAIM_ID} = bc.{S.BillingClaims.CLAIM_ID} AND bc.{S.BillingClaims.PROJECT_ID} = ?)", (project_id,))
            cursor.execute(f"DELETE FROM {S.BillingClaims.TABLE} WHERE {S.BillingClaims.PROJECT_ID} = ?", (project_id,))
            
            # Review and task data
            cursor.execute(f"DELETE FROM {S.ReviewAssignments.TABLE} WHERE EXISTS (SELECT 1 FROM {S.ReviewSchedule.TABLE} rs WHERE {S.ReviewAssignments.TABLE}.{S.ReviewAssignments.SCHEDULE_ID} = rs.{S.ReviewSchedule.SCHEDULE_ID} AND rs.{S.ReviewSchedule.PROJECT_ID} = ?)", (project_id,))
            cursor.execute(f"DELETE FROM {S.ReviewTasks.TABLE} WHERE EXISTS (SELECT 1 FROM {S.ReviewSchedule.TABLE} rs WHERE {S.ReviewTasks.TABLE}.{S.ReviewTasks.SCHEDULE_ID} = rs.{S.ReviewSchedule.SCHEDULE_ID} AND rs.{S.ReviewSchedule.PROJECT_ID} = ?)", (project_id,))
            cursor.execute(f"DELETE FROM {S.ReviewSchedule.TABLE} WHERE {S.ReviewSchedule.PROJECT_ID} = ?", (project_id,))
            cursor.execute(f"DELETE FROM {S.ReviewSchedules.TABLE} WHERE {S.ReviewSchedules.PROJECT_ID} = ?", (project_id,))
            cursor.execute(f"DELETE FROM {S.ReviewCycleDetails.TABLE} WHERE {S.ReviewCycleDetails.PROJECT_ID} = ?", (project_id,))
            cursor.execute(f"DELETE FROM {S.ReviewStages.TABLE} WHERE {S.ReviewStages.PROJECT_ID} = ?", (project_id,))
            cursor.execute(f"DELETE FROM {S.ReviewParameters.TABLE} WHERE {S.ReviewParameters.PROJECT_ID} = ?", (project_id,))
            cursor.execute(f"DELETE FROM {S.ContractualLinks.TABLE} WHERE {S.ContractualLinks.PROJECT_ID} = ?", (project_id,))
            
            # Project phases and reviews
            cursor.execute(f"DELETE FROM {S.ProjectReviews.TABLE} WHERE {S.ProjectReviews.PROJECT_ID} = ?", (project_id,))
            cursor.execute(f"DELETE FROM {S.ProjectReviewCycles.TABLE} WHERE {S.ProjectReviewCycles.PROJECT_ID} = ?", (project_id,))
            cursor.execute(f"DELETE FROM {S.ProjectHolds.TABLE} WHERE {S.ProjectHolds.PROJECT_ID} = ?", (project_id,))
            cursor.execute(f"DELETE FROM {S.ProjectBEPSections.TABLE} WHERE {S.ProjectBEPSections.PROJECT_ID} = ?", (project_id,))
            
            # BEP approvals
            cursor.execute(f"DELETE FROM {S.BEPApprovals.TABLE} WHERE {S.BEPApprovals.PROJECT_ID} = ?", (project_id,))
            
            # Tasks
            cursor.execute(f"DELETE FROM {S.Tasks.TABLE} WHERE {S.Tasks.PROJECT_ID} = ?", (project_id,))
            
            # Bookmarks
            cursor.execute(f"DELETE FROM {S.ProjectBookmarks.TABLE} WHERE {S.ProjectBookmarks.PROJECT_ID} = ?", (project_id,))
            
            # ACC and document data
            cursor.execute(f"DELETE FROM {S.ACCImportLogs.TABLE} WHERE {S.ACCImportLogs.PROJECT_ID} = ?", (project_id,))
            cursor.execute(f"DELETE FROM {S.ACCImportFolders.TABLE} WHERE {S.ACCImportFolders.PROJECT_ID} = ?", (project_id,))
            cursor.execute(f"DELETE FROM {S.ACCDocs.TABLE} WHERE {S.ACCDocs.PROJECT_ID} = ?", (project_id,))
            
            # Finally, delete the project itself
            cursor.execute(f"DELETE FROM {S.Projects.TABLE} WHERE {S.Projects.ID} = ?", (project_id,))
            
            conn.commit()
            logger.info(f"Project {project_id} and all related data deleted successfully.")
            return True
            
    except Exception as e:
        logger.error(f"Error deleting project {project_id}: {e}")
        return False


if __name__ == "__main__":
    from database_pool import get_db_connection
    try:
        with get_db_connection() as conn:
            print("✅ Connected to database successfully.")
    except Exception as e:
        print(f"❌ Failed to connect: {e}")


def delete_project_service(service_id: int) -> bool:
    """Delete a single project service and all related data"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Delete in order of dependencies (child tables first)

            # Service-related data
            cursor.execute(f"DELETE FROM {S.ServiceReviews.TABLE} WHERE {S.ServiceReviews.SERVICE_ID} = ?", (service_id,))
            cursor.execute(f"DELETE FROM {S.ServiceScheduleSettings.TABLE} WHERE {S.ServiceScheduleSettings.SERVICE_ID} = ?", (service_id,))
            cursor.execute(f"DELETE FROM {S.ServiceDeliverables.TABLE} WHERE {S.ServiceDeliverables.SERVICE_ID} = ?", (service_id,))

            # Finally delete the service itself
            cursor.execute(f"DELETE FROM {S.ProjectServices.TABLE} WHERE {S.ProjectServices.SERVICE_ID} = ?", (service_id,))

            conn.commit()
            return True

    except Exception as e:
        logger.error(f"Error deleting project service: {e}")
        return False


def get_current_month_activities(project_id):
    """Get current month review activities for a project"""
    from datetime import datetime
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            current_month = datetime.now().month
            current_year = datetime.now().year

            # Get reviews scheduled for current month
            cursor.execute(
                f"""
                SELECT rs.{S.ReviewSchedule.REVIEW_DATE}, rs.{S.ReviewSchedule.STATUS},
                       rcd.{S.ReviewCycleDetails.CONSTRUCTION_STAGE}, rcd.{S.ReviewCycleDetails.REVIEWS_PER_PHASE}
                FROM {S.ReviewSchedule.TABLE} rs
                LEFT JOIN {S.ReviewCycleDetails.TABLE} rcd ON rs.{S.ReviewSchedule.CYCLE_ID} = rcd.{S.ReviewCycleDetails.CYCLE_ID}
                WHERE rs.{S.ReviewSchedule.PROJECT_ID} = ?
                AND MONTH(rs.{S.ReviewSchedule.REVIEW_DATE}) = ?
                AND YEAR(rs.{S.ReviewSchedule.REVIEW_DATE}) = ?
                ORDER BY rs.{S.ReviewSchedule.REVIEW_DATE}
                """,
                (project_id, current_month, current_year)
            )

            activities = []
            for row in cursor.fetchall():
                activities.append({
                    'review_date': row[0],
                    'status': row[1] or 'Scheduled',
                    'stage': row[2] or 'Unknown',
                    'reviews_per_phase': row[3] or 1
                })

            return activities
    except Exception as e:
        logger.error(f"❌ Error getting current month activities: {e}")
        return []


def get_current_month_billing(project_id):
    """Get billing amounts due for current month"""
    from datetime import datetime
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            current_month = datetime.now().month
            current_year = datetime.now().year

            # Get billing claims for current month
            cursor.execute(
                f"""
                SELECT SUM(bcl.{S.BillingClaimLines.AMOUNT_THIS_CLAIM})
                FROM {S.BillingClaims.TABLE} bc
                JOIN {S.BillingClaimLines.TABLE} bcl ON bc.{S.BillingClaims.CLAIM_ID} = bcl.{S.BillingClaimLines.CLAIM_ID}
                WHERE bc.{S.BillingClaims.PROJECT_ID} = ?
                AND MONTH(bc.{S.BillingClaims.PERIOD_END}) = ?
                AND YEAR(bc.{S.BillingClaims.PERIOD_END}) = ?
                AND bc.{S.BillingClaims.STATUS} IN ('Pending', 'Approved')
                """,
                (project_id, current_month, current_year)
            )

            result = cursor.fetchone()
            return result[0] if result[0] else 0
    except Exception as e:
        logger.error(f"❌ Error getting current month billing: {e}")
        return 0


def get_scope_remaining(project_id):
    """Get remaining scope (upcoming reviews)"""
    from datetime import datetime
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            today = datetime.now().date()

            # Get upcoming reviews
            cursor.execute(
                f"""
                SELECT rs.{S.ReviewSchedule.REVIEW_DATE}, rcd.{S.ReviewCycleDetails.CONSTRUCTION_STAGE},
                       rs.{S.ReviewSchedule.STATUS}
                FROM {S.ReviewSchedule.TABLE} rs
                LEFT JOIN {S.ReviewCycleDetails.TABLE} rcd ON rs.{S.ReviewSchedule.CYCLE_ID} = rcd.{S.ReviewCycleDetails.CYCLE_ID}
                WHERE rs.{S.ReviewSchedule.PROJECT_ID} = ?
                AND rs.{S.ReviewSchedule.REVIEW_DATE} >= ?
                AND rs.{S.ReviewSchedule.STATUS} NOT IN ('Completed', 'Cancelled')
                ORDER BY rs.{S.ReviewSchedule.REVIEW_DATE}
                """,
                (project_id, today)
            )

            reviews = []
            for row in cursor.fetchall():
                reviews.append({
                    'date': row[0],
                    'stage': row[1] or 'Unknown',
                    'status': row[2] or 'Scheduled'
                })

            return reviews
    except Exception as e:
        logger.error(f"❌ Error getting scope remaining: {e}")
        return []


def get_project_completion_estimate(project_id):
    """Get estimated project completion dates"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            # Get the latest review cycle details for completion estimates
            cursor.execute(
                f"""
                SELECT TOP 1 rcd.{S.ReviewCycleDetails.PLANNED_COMPLETION_DATE},
                       p.{S.Projects.END_DATE}
                FROM {S.ReviewCycleDetails.TABLE} rcd
                JOIN {S.Projects.TABLE} p ON rcd.{S.ReviewCycleDetails.PROJECT_ID} = p.{S.Projects.ID}
                WHERE rcd.{S.ReviewCycleDetails.PROJECT_ID} = ?
                ORDER BY rcd.{S.ReviewCycleDetails.PLANNED_COMPLETION_DATE} DESC
                """,
                (project_id,)
            )

            result = cursor.fetchone()
            if result:
                return {
                    'phase_completion': result[0],
                    'project_completion': result[1]
                }
            else:
                # Fallback to project end date
                cursor.execute(
                    f"SELECT {S.Projects.END_DATE} FROM {S.Projects.TABLE} WHERE {S.Projects.ID} = ?",
                    (project_id,)
                )
                result = cursor.fetchone()
                return {
                    'phase_completion': None,
                    'project_completion': result[0] if result else None
                }
    except Exception as e:
        logger.error(f"❌ Error getting project completion estimate: {e}")
        return {'phase_completion': None, 'project_completion': None}


def get_project_details_summary(project_id):
    """Get comprehensive project details summary for the UI"""
    from datetime import datetime

    activities = get_current_month_activities(project_id)
    billing = get_current_month_billing(project_id)
    scope = get_scope_remaining(project_id)
    completion = get_project_completion_estimate(project_id)

    # Process activities for current month
    current_month_reviews = []
    for activity in activities:
        if activity['stage'].lower().startswith('phase 7'):
            current_month_reviews.append(f"{activity['reviews_per_phase']} x Phase 7 coordination reviews")

    # Process scope remaining
    scope_remaining = []
    phase_7_count = 0
    cupix_count = 0
    pc_report_count = 0

    for review in scope:
        stage = review['stage'].lower()
        if 'phase 7' in stage and 'audit' in stage:
            phase_7_count += 1
        elif 'cupix' in stage:
            cupix_count += 1
        elif 'pc report' in stage or 'progress claim' in stage:
            pc_report_count += 1

    if phase_7_count > 0:
        scope_remaining.append(f"{phase_7_count} x Phase 7 audit")
    if cupix_count > 0:
        scope_remaining.append(f"{cupix_count} x Cupix Reviews")
    if pc_report_count > 0:
        scope_remaining.append(f"{pc_report_count} x PC Report")

    # Format completion dates
    phase_completion = None
    project_completion = None

    if completion['phase_completion']:
        phase_completion = completion['phase_completion'].strftime('%B %Y')

    if completion['project_completion']:
        project_completion = completion['project_completion'].strftime('%B %Y')

    return {
        'current_activities': current_month_reviews,
        'billing_amount': billing,
        'scope_remaining': scope_remaining,
        'phase_completion': phase_completion,
        'project_completion': project_completion
    }




# ===================== Revizto Extraction Run Functions =====================

def start_revizto_extraction_run(export_folder=None, notes=None):
    """Start a new Revizto extraction run and return the run_id."""
    from datetime import datetime
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            # Generate a run_id based on timestamp
            run_id = f"run_{int(datetime.utcnow().timestamp())}"
            
            cursor.execute(
                f"""
                INSERT INTO {S.ReviztoExtractionRuns.TABLE} (
                    {S.ReviztoExtractionRuns.RUN_ID},
                    {S.ReviztoExtractionRuns.START_TIME},
                    {S.ReviztoExtractionRuns.STATUS},
                    {S.ReviztoExtractionRuns.EXPORT_FOLDER},
                    {S.ReviztoExtractionRuns.NOTES}
                ) VALUES (?, GETUTCDATE(), 'running', ?, ?);
                """,
                (run_id, export_folder, notes)
            )
            
            conn.commit()
            return run_id
    except Exception as e:
        logger.error(f"❌ Error starting Revizto extraction run: {e}")
        return None


def complete_revizto_extraction_run(run_id, projects_extracted=0, issues_extracted=0, licenses_extracted=0, status='completed'):
    """Complete a Revizto extraction run with final statistics."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                UPDATE {S.ReviztoExtractionRuns.TABLE}
                SET {S.ReviztoExtractionRuns.END_TIME} = GETUTCDATE(),
                    {S.ReviztoExtractionRuns.STATUS} = ?,
                    {S.ReviztoExtractionRuns.PROJECTS_EXTRACTED} = ?,
                    {S.ReviztoExtractionRuns.ISSUES_EXTRACTED} = ?,
                    {S.ReviztoExtractionRuns.LICENSES_EXTRACTED} = ?
                WHERE {S.ReviztoExtractionRuns.RUN_ID} = ?;
                """,
                (status, projects_extracted, issues_extracted, licenses_extracted, run_id)
            )
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"❌ Error completing Revizto extraction run: {e}")
        return False


def get_revizto_extraction_runs(limit=50):
    """Get recent Revizto extraction runs."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT {S.ReviztoExtractionRuns.RUN_ID},
                       {S.ReviztoExtractionRuns.START_TIME},
                       {S.ReviztoExtractionRuns.END_TIME},
                       {S.ReviztoExtractionRuns.STATUS},
                       {S.ReviztoExtractionRuns.PROJECTS_EXTRACTED},
                       {S.ReviztoExtractionRuns.ISSUES_EXTRACTED},
                       {S.ReviztoExtractionRuns.LICENSES_EXTRACTED},
                       {S.ReviztoExtractionRuns.EXPORT_FOLDER},
                       {S.ReviztoExtractionRuns.NOTES}
                FROM {S.ReviztoExtractionRuns.TABLE}
                ORDER BY {S.ReviztoExtractionRuns.START_TIME} DESC
                OFFSET 0 ROWS FETCH NEXT ? ROWS ONLY;
                """,
                (limit,)
            )
            runs = []
            for row in cursor.fetchall():
                runs.append({
                    'run_id': row[0],
                    'start_time': row[1],
                    'end_time': row[2],
                    'status': row[3],
                    'projects_extracted': row[4] or 0,
                    'issues_extracted': row[5] or 0,
                    'licenses_extracted': row[6] or 0,
                    'export_folder': row[7],
                    'notes': row[8]
                })
            return runs
    except Exception as e:
        logger.error(f"❌ Error fetching Revizto extraction runs: {e}")
        return []


def get_last_revizto_extraction_run():
    """Get the most recent completed Revizto extraction run."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT TOP 1 {S.ReviztoExtractionRuns.RUN_ID},
                       {S.ReviztoExtractionRuns.START_TIME},
                       {S.ReviztoExtractionRuns.END_TIME},
                       {S.ReviztoExtractionRuns.STATUS},
                       {S.ReviztoExtractionRuns.PROJECTS_EXTRACTED},
                       {S.ReviztoExtractionRuns.ISSUES_EXTRACTED},
                       {S.ReviztoExtractionRuns.LICENSES_EXTRACTED},
                       {S.ReviztoExtractionRuns.EXPORT_FOLDER},
                       {S.ReviztoExtractionRuns.NOTES}
                FROM {S.ReviztoExtractionRuns.TABLE}
                WHERE {S.ReviztoExtractionRuns.STATUS} = 'completed'
                ORDER BY {S.ReviztoExtractionRuns.START_TIME} DESC;
                """
            )
            row = cursor.fetchone()
            if row:
                return {
                    'run_id': row[0],
                    'start_time': row[1],
                    'end_time': row[2],
                    'status': row[3],
                    'projects_extracted': row[4] or 0,
                    'issues_extracted': row[5] or 0,
                    'licenses_extracted': row[6] or 0,
                    'export_folder': row[7],
                    'notes': row[8]
                }
            return None
    except Exception as e:
        logger.error(f"❌ Error fetching last Revizto extraction run: {e}")
        return None


def get_revizto_projects_since_last_run():
    """Get Revizto projects that have been updated since the last extraction run."""
    last_run = get_last_revizto_extraction_run()
    if not last_run or not last_run['end_time']:
        # If no previous run, return all projects
        return get_revizto_projects()

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT {S.TblReviztoProjects.PROJECT_ID},
                       {S.TblReviztoProjects.PROJECT_UUID},
                       {S.TblReviztoProjects.TITLE},
                       {S.TblReviztoProjects.CREATED},
                       {S.TblReviztoProjects.UPDATED},
                       {S.TblReviztoProjects.REGION},
                       {S.TblReviztoProjects.ARCHIVED},
                       {S.TblReviztoProjects.FROZEN},
                       {S.TblReviztoProjects.OWNER_EMAIL}
                FROM {S.TblReviztoProjects.TABLE}
                WHERE {S.TblReviztoProjects.UPDATED} > ?
                ORDER BY {S.TblReviztoProjects.UPDATED} DESC;
                """,
                (last_run['end_time'],)
            )
            projects = []
            for row in cursor.fetchall():
                projects.append({
                    'project_id': row[0],
                    'project_uuid': row[1],
                    'title': row[2],
                    'created': row[3],
                    'updated': row[4],
                    'region': row[5],
                    'archived': row[6],
                    'frozen': row[7],
                    'owner_email': row[8]
                })
            return projects
    except Exception as e:
        logger.error(f"❌ Error fetching Revizto projects since last run: {e}")
        return []


def get_revizto_projects():
    """Get all Revizto projects."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT {S.TblReviztoProjects.PROJECT_ID},
                       {S.TblReviztoProjects.PROJECT_UUID},
                       {S.TblReviztoProjects.TITLE},
                       {S.TblReviztoProjects.CREATED},
                       {S.TblReviztoProjects.UPDATED},
                       {S.TblReviztoProjects.REGION},
                       {S.TblReviztoProjects.ARCHIVED},
                       {S.TblReviztoProjects.FROZEN},
                       {S.TblReviztoProjects.OWNER_EMAIL}
                FROM {S.TblReviztoProjects.TABLE}
                ORDER BY {S.TblReviztoProjects.TITLE};
                """
            )
            projects = []
            for row in cursor.fetchall():
                projects.append({
                    'project_id': row[0],
                    'project_uuid': row[1],
                    'title': row[2],
                    'created': row[3],
                    'updated': row[4],
                    'region': row[5],
                    'archived': row[6],
                    'frozen': row[7],
                    'owner_email': row[8]
                })
            return projects
    except Exception as e:
        logger.error(f"❌ Error fetching Revizto projects: {e}")
        return []


def get_project_combined_issues_overview(project_id):
    """Get combined ACC and Revizto issues overview for a specific project."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get project name and all its aliases
            cursor.execute(f"""
                SELECT {S.Projects.NAME} FROM {S.Projects.TABLE} WHERE {S.Projects.ID} = ?
            """, (project_id,))
            project_row = cursor.fetchone()
            if not project_row:
                return {'summary': {'total_issues': 0}, 'recent_issues': []}
            
            project_name = project_row[0]
            
            # Get all aliases for this project (including the main project name)
            cursor.execute("""
                SELECT alias_name FROM project_aliases WHERE pm_project_id = ?
            """, (project_id,))
            aliases = [row[0] for row in cursor.fetchall()]
            
            # Include the main project name as well
            all_project_names = [project_name] + aliases
            
            # Create placeholders for the IN clause
            placeholders = ','.join(['?' for _ in all_project_names])
            
            # Get issue summary statistics using all possible project names
            cursor.execute(f"""
                SELECT 
                    source,
                    status,
                    COUNT(*) as count
                FROM vw_ProjectManagement_AllIssues
                WHERE project_name IN ({placeholders})
                GROUP BY source, status
            """, all_project_names)
            
            stats = cursor.fetchall()
            
            # Build summary statistics
            summary = {
                'total_issues': 0,
                'acc_issues': {'total': 0, 'open': 0, 'closed': 0},
                'revizto_issues': {'total': 0, 'open': 0, 'closed': 0},
                'overall': {'open': 0, 'closed': 0}
            }
            
            for source, status, count in stats:
                summary['total_issues'] += count
                if source == 'ACC':
                    summary['acc_issues']['total'] += count
                    summary['acc_issues'][status] = count
                elif source == 'Revizto':
                    summary['revizto_issues']['total'] += count
                    summary['revizto_issues'][status] = count
                
                summary['overall'][status] = summary['overall'].get(status, 0) + count
            
            # Get recent issues (last 10) - use all project names
            cursor.execute(f"""
                SELECT TOP 10
                    source,
                    issue_id,
                    title,
                    status,
                    created_at,
                    assignee,
                    priority
                FROM vw_ProjectManagement_AllIssues
                WHERE project_name IN ({placeholders})
                ORDER BY created_at DESC
            """, all_project_names)
            
            recent_issues = []
            for row in cursor.fetchall():
                recent_issues.append({
                    'source': row[0],
                    'issue_id': row[1],
                    'title': row[2],
                    'status': row[3],
                    'created_at': row[4],
                    'assignee': row[5],
                    'priority': row[6]
                })
            
            return {
                'summary': summary,
                'recent_issues': recent_issues
            }
            
    except Exception as e:
        logger.error(f"Error fetching project issues overview: {e}")
        return {'summary': {}, 'recent_issues': []}


def get_project_issues_by_status(project_id, status='open'):
    """Get all issues for a project filtered by status."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get project name and all its aliases
            cursor.execute(f"""
                SELECT {S.Projects.NAME} FROM {S.Projects.TABLE} WHERE {S.Projects.ID} = ?
            """, (project_id,))
            project_row = cursor.fetchone()
            if not project_row:
                return []
            
            project_name = project_row[0]
            
            # Get all aliases for this project
            cursor.execute("""
                SELECT alias_name FROM project_aliases WHERE pm_project_id = ?
            """, (project_id,))
            aliases = [row[0] for row in cursor.fetchall()]
            
            # Include the main project name as well
            all_project_names = [project_name] + aliases
            
            # Create placeholders for the IN clause
            placeholders = ','.join(['?' for _ in all_project_names])
            
            cursor.execute(f"""
                SELECT 
                    source,
                    issue_id,
                    title,
                    status,
                    created_at,
                    closed_at,
                    assignee,
                    author,
                    priority,
                    web_link
                FROM vw_ProjectManagement_AllIssues
                WHERE project_name IN ({placeholders}) AND status = ?
                ORDER BY created_at DESC
            """, all_project_names + [status])
            
            issues = []
            for row in cursor.fetchall():
                issues.append({
                    'source': row[0],
                    'issue_id': row[1],
                    'title': row[2],
                    'status': row[3],
                    'created_at': row[4],
                    'closed_at': row[5],
                    'assignee': row[6],
                    'author': row[7],
                    'priority': row[8],
                    'web_link': row[9]
                })
            
            return issues
            
    except Exception as e:
        logger.error(f"Error fetching project issues by status: {e}")
        return []


def get_all_projects_issues_overview():
    """Get combined ACC and Revizto issues overview for all projects."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get issue summary statistics for all projects
            cursor.execute(f"""
                SELECT 
                    source,
                    status,
                    COUNT(*) as count
                FROM vw_ProjectManagement_AllIssues
                GROUP BY source, status
            """)
            
            stats = cursor.fetchall()
            
            # Build summary statistics
            summary = {
                'total_issues': 0,
                'acc_issues': {'total': 0, 'open': 0, 'closed': 0},
                'revizto_issues': {'total': 0, 'open': 0, 'closed': 0},
                'overall': {'open': 0, 'closed': 0}
            }
            
            for source, status, count in stats:
                summary['total_issues'] += count
                if source == 'ACC':
                    summary['acc_issues']['total'] += count
                    summary['acc_issues'][status] = count
                elif source == 'Revizto':
                    summary['revizto_issues']['total'] += count
                    summary['revizto_issues'][status] = count
                
                summary['overall'][status] = summary['overall'].get(status, 0) + count
            
            # Get issues summary by project
            cursor.execute(f"""
                SELECT 
                    project_name,
                    source,
                    status,
                    COUNT(*) as count
                FROM vw_ProjectManagement_AllIssues
                GROUP BY project_name, source, status
                ORDER BY project_name
            """)
            
            project_stats = cursor.fetchall()
            
            # Group by project
            projects_summary = {}
            for project_name, source, status, count in project_stats:
                if project_name not in projects_summary:
                    projects_summary[project_name] = {
                        'total_issues': 0,
                        'acc_issues': {'total': 0, 'open': 0, 'closed': 0},
                        'revizto_issues': {'total': 0, 'open': 0, 'closed': 0},
                        'overall': {'open': 0, 'closed': 0}
                    }
                
                projects_summary[project_name]['total_issues'] += count
                if source == 'ACC':
                    projects_summary[project_name]['acc_issues']['total'] += count
                    projects_summary[project_name]['acc_issues'][status] = count
                elif source == 'Revizto':
                    projects_summary[project_name]['revizto_issues']['total'] += count
                    projects_summary[project_name]['revizto_issues'][status] = count
                
                projects_summary[project_name]['overall'][status] = projects_summary[project_name]['overall'].get(status, 0) + count
            
            # Get recent issues (last 20 across all projects)
            cursor.execute(f"""
                SELECT TOP 20
                    project_name,
                    source,
                    issue_id,
                    title,
                    status,
                    created_at,
                    assignee,
                    priority
                FROM vw_ProjectManagement_AllIssues
                ORDER BY created_at DESC
            """)
            
            recent_issues = []
            for row in cursor.fetchall():
                recent_issues.append({
                    'project_name': row[0],
                    'source': row[1],
                    'issue_id': row[2],
                    'title': row[3],
                    'status': row[4],
                    'created_at': row[5],
                    'assignee': row[6],
                    'priority': row[7]
                })
            
            return {
                'summary': summary,
                'projects': projects_summary,
                'recent_issues': recent_issues
            }
            
    except Exception as e:
        logger.error(f"Error fetching all projects issues overview: {e}")
        return {
            'summary': {'total_issues': 0},
            'projects': {},
            'recent_issues': []
        }


def get_project_review_statistics(project_ids: Optional[List[int]] = None):
    """Get review statistics for projects (optionally filtered by IDs)."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get review statistics per project
            query = f"""
                SELECT 
                    ps.{S.ProjectServices.PROJECT_ID},
                    COUNT(sr.{S.ServiceReviews.REVIEW_ID}) as total_reviews,
                    SUM(CASE WHEN sr.{S.ServiceReviews.STATUS} = 'completed' THEN 1 ELSE 0 END) as completed_reviews,
                    SUM(CASE WHEN sr.{S.ServiceReviews.STATUS} = 'planned' THEN 1 ELSE 0 END) as planned_reviews,
                    SUM(CASE WHEN sr.{S.ServiceReviews.STATUS} = 'in_progress' THEN 1 ELSE 0 END) as in_progress_reviews,
                    SUM(CASE WHEN sr.{S.ServiceReviews.STATUS} = 'overdue' THEN 1 ELSE 0 END) as overdue_reviews,
                    MIN(sr.{S.ServiceReviews.PLANNED_DATE}) as earliest_review_date,
                    MAX(sr.{S.ServiceReviews.PLANNED_DATE}) as latest_review_date,
                    COUNT(CASE WHEN sr.{S.ServiceReviews.PLANNED_DATE} >= GETDATE() AND sr.{S.ServiceReviews.PLANNED_DATE} <= DATEADD(day, 30, GETDATE()) THEN 1 END) as upcoming_reviews_30_days
                FROM {S.ProjectServices.TABLE} ps
                LEFT JOIN {S.ServiceReviews.TABLE} sr ON ps.{S.ProjectServices.SERVICE_ID} = sr.{S.ServiceReviews.SERVICE_ID}
            """

            params: List[Any] = []
            if project_ids:
                placeholders = ', '.join('?' for _ in project_ids)
                query += f" WHERE ps.{S.ProjectServices.PROJECT_ID} IN ({placeholders})"
                params.extend(project_ids)

            query += f" GROUP BY ps.{S.ProjectServices.PROJECT_ID}"
            
            cursor.execute(query, tuple(params))
            results = cursor.fetchall()
            
            # Convert to dictionary format
            stats = {}
            for row in results:
                project_id = row[0]
                stats[project_id] = {
                    'total_reviews': row[1] or 0,
                    'completed_reviews': row[2] or 0,
                    'planned_reviews': row[3] or 0,
                    'in_progress_reviews': row[4] or 0,
                    'overdue_reviews': row[5] or 0,
                    'earliest_review_date': row[6].isoformat() if row[6] else None,
                    'latest_review_date': row[7].isoformat() if row[7] else None,
                    'upcoming_reviews_30_days': row[8] or 0
                }
            
            return stats
            
    except Exception as e:
        logger.error(f"Error fetching project review statistics: {e}")
        return {}


def get_dashboard_timeline(
    months: Optional[int] = None,
    project_ids: Optional[List[int]] = None,
    client_ids: Optional[List[int]] = None,
    type_ids: Optional[List[int]] = None,
    manager: Optional[str] = None,
):
    """Aggregate project timelines and review schedule data for dashboard visualisations."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()

            months_filter = months if months and months > 0 else None
            params: List[Any] = []
            where_clauses: List[str] = []

            if months_filter:
                where_clauses.append(
                    f"""
                    (
                        (p.{S.Projects.START_DATE} IS NOT NULL AND p.{S.Projects.START_DATE} >= DATEADD(month, ?, CAST(GETDATE() AS date)))
                        OR
                        (p.{S.Projects.END_DATE} IS NOT NULL AND p.{S.Projects.END_DATE} >= DATEADD(month, ?, CAST(GETDATE() AS date)))
                        OR
                        (UPPER(ISNULL(p.{S.Projects.STATUS}, '')) IN ('ACTIVE', 'IN PROGRESS'))
                        OR
                        (p.{S.Projects.START_DATE} IS NULL AND p.{S.Projects.END_DATE} IS NULL)
                    )
                    """
                )
                # negative months to look back
                params.extend([-months_filter, -months_filter])
            if project_ids:
                placeholders = ", ".join("?" for _ in project_ids)
                where_clauses.append(f"p.{S.Projects.ID} IN ({placeholders})")
                params.extend(project_ids)
            if client_ids:
                placeholders = ", ".join("?" for _ in client_ids)
                where_clauses.append(f"p.{S.Projects.CLIENT_ID} IN ({placeholders})")
                params.extend(client_ids)
            if type_ids:
                placeholders = ", ".join("?" for _ in type_ids)
                where_clauses.append(f"p.{S.Projects.TYPE_ID} IN ({placeholders})")
                params.extend(type_ids)
            if manager:
                where_clauses.append(f"LOWER(ISNULL(p.{S.Projects.PROJECT_MANAGER},'')) = LOWER(?)")
                params.append(manager)

            where_sql = ""
            if where_clauses:
                where_sql = "WHERE " + " AND ".join(where_clauses)

            cursor.execute(
                f"""
                SELECT 
                    p.{S.Projects.ID},
                    p.{S.Projects.NAME},
                    p.{S.Projects.START_DATE},
                    p.{S.Projects.END_DATE},
                    p.{S.Projects.PROJECT_MANAGER},
                    p.{S.Projects.CLIENT_ID},
                    c.{S.Clients.CLIENT_NAME},
                    p.{S.Projects.TYPE_ID},
                    pt.{S.ProjectTypes.TYPE_NAME}
                FROM {S.Projects.TABLE} p
                LEFT JOIN {S.Clients.TABLE} c
                    ON p.{S.Projects.CLIENT_ID} = c.{S.Clients.CLIENT_ID}
                LEFT JOIN {S.ProjectTypes.TABLE} pt
                    ON p.{S.Projects.TYPE_ID} = pt.{S.ProjectTypes.TYPE_ID}
                {where_sql}
                ORDER BY p.{S.Projects.NAME}
                """
            , tuple(params))

            project_rows = cursor.fetchall()
            project_map: Dict[int, Dict[str, Any]] = {}
            timeline_dates: List[date] = []

            def _as_iso(value: Any) -> Optional[str]:
                if isinstance(value, (datetime, date)):
                    return value.isoformat()
                if value is None:
                    return None
                try:
                    return value.isoformat()  # type: ignore[attr-defined]
                except AttributeError:
                    return str(value)

            def _as_date(value: Any) -> Optional[date]:
                if isinstance(value, datetime):
                    return value.date()
                if isinstance(value, date):
                    return value
                return None

            def _as_int(value: Any) -> Optional[int]:
                if value is None:
                    return None
                try:
                    return int(value)
                except (TypeError, ValueError):
                    return None

            for row in project_rows:
                project_id = row[0]
                start_value = row[2]
                end_value = row[3]

                start_date = _as_date(start_value)
                end_date = _as_date(end_value)
                if start_date:
                    timeline_dates.append(start_date)
                if end_date:
                    timeline_dates.append(end_date)

                project_map[project_id] = {
                    "project_id": project_id,
                    "project_name": row[1],
                    "start_date": _as_iso(start_value),
                    "end_date": _as_iso(end_value),
                    "project_manager": row[4],
                    "client_id": _as_int(row[5]),
                    "client_name": row[6],
                    "type_id": _as_int(row[7]),
                    "project_type": row[8],
                    "review_items": [],
                }

            if not project_map:
                return {"projects": [], "date_range": None}

            placeholders = ", ".join(["?"] * len(project_map))
            cursor.execute(
                f"""
                SELECT 
                    ps.{S.ProjectServices.PROJECT_ID},
                    sr.{S.ServiceReviews.REVIEW_ID},
                    sr.{S.ServiceReviews.PLANNED_DATE},
                    sr.{S.ServiceReviews.DUE_DATE},
                    sr.{S.ServiceReviews.STATUS},
                    ps.{S.ProjectServices.SERVICE_NAME}
                FROM {S.ServiceReviews.TABLE} sr
                INNER JOIN {S.ProjectServices.TABLE} ps
                    ON sr.{S.ServiceReviews.SERVICE_ID} = ps.{S.ProjectServices.SERVICE_ID}
                WHERE ps.{S.ProjectServices.PROJECT_ID} IN ({placeholders})
                ORDER BY 
                    ps.{S.ProjectServices.PROJECT_ID},
                    sr.{S.ServiceReviews.PLANNED_DATE},
                    sr.{S.ServiceReviews.REVIEW_ID}
                """,
                tuple(project_map.keys()),
            )

            review_rows = cursor.fetchall()
            for row in review_rows:
                project_id = row[0]
                if project_id not in project_map:
                    continue

                planned_value = row[2]
                due_value = row[3]

                planned_date = _as_date(planned_value)
                due_date = _as_date(due_value)
                if planned_date:
                    timeline_dates.append(planned_date)
                if due_date:
                    timeline_dates.append(due_date)

                project_map[project_id]["review_items"].append(
                    {
                        "review_id": row[1],
                        "planned_date": _as_iso(planned_value),
                        "due_date": _as_iso(due_value),
                        "status": row[4],
                        "service_name": row[5],
                    }
                )

            date_range: Optional[Dict[str, str]] = None
            if timeline_dates:
                min_date = min(timeline_dates)
                max_date = max(timeline_dates)
                date_range = {
                    "min": min_date.isoformat(),
                    "max": max_date.isoformat(),
                }

            return {
                "projects": list(project_map.values()),
                "date_range": date_range,
                "as_of": date_range["max"] if date_range else None,
            }

    except Exception as e:
        logger.error(f"Error fetching dashboard timeline data: {e}")
        return {"projects": [], "date_range": None}




def _parse_time_input(value: Any) -> Optional[time]:
    """Convert supported time formats into a time object."""
    if value in (None, "", "null"):
        return None
    if isinstance(value, time):
        return value
    if isinstance(value, datetime):
        return value.time()
    if isinstance(value, str):
        cleaned = value.strip().lower()
        if not cleaned or cleaned == "null":
            return None
        normalised = cleaned.replace(".", ":")
        if ":" not in normalised:
            normalised = f"{normalised}:00"
        for fmt in ("%H:%M", "%H:%M:%S"):
            try:
                return datetime.strptime(normalised, fmt).time()
            except ValueError:
                continue
    return None


def _coerce_date_input(value: Any) -> Optional[date]:
    """Convert supported date formats into a date object."""
    if value in (None, "", "null"):
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        cleaned = value.strip()
        if not cleaned:
            return None
        try:
            return datetime.fromisoformat(cleaned).date()
        except ValueError:
            for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"):
                try:
                    return datetime.strptime(cleaned, fmt).date()
                except ValueError:
                    continue
    return None


def _calculate_duration_minutes(start_value: Any, end_value: Any) -> Optional[int]:
    """Derive a duration in minutes when both start and end times are available."""
    start_time = _parse_time_input(start_value)
    end_time = _parse_time_input(end_value)
    if not start_time or not end_time:
        return None

    start_dt = datetime.combine(date.today(), start_time)
    end_dt = datetime.combine(date.today(), end_time)
    if end_dt < start_dt:
        end_dt += timedelta(days=1)
    return int((end_dt - start_dt).total_seconds() // 60)


def _format_task_notes_row(row: tuple) -> Dict[str, Any]:
    """Transform a raw SQL row into a serialisable task record."""
    if not row:
        return {}

    raw_items = row[12]
    task_items: List[Dict[str, Any]] = []
    if raw_items:
        try:
            parsed_items = json.loads(raw_items)
            if isinstance(parsed_items, list):
                task_items = parsed_items
        except (ValueError, TypeError):
            logger.warning("Unable to parse task_items JSON for task_id=%s", row[0])

    return {
        'task_id': row[0],
        'task_name': row[1],
        'project_id': row[2],
        'project_name': row[3],
        'cycle_id': row[4],
        'task_date': row[5].isoformat() if row[5] else None,
        'time_start': row[6].strftime("%H:%M") if row[6] else None,
        'time_end': row[7].strftime("%H:%M") if row[7] else None,
        'time_spent_minutes': row[8],
        'status': row[9],
        'assigned_to': row[10],
        'assigned_to_name': row[11],
        'task_items': task_items,
        'notes': row[13],
        'created_at': row[14].isoformat() if row[14] else None,
        'updated_at': row[15].isoformat() if row[15] else None,
        }


def _calculate_warehouse_dashboard_metrics(
    project_ids: Optional[List[int]] = None,
    client_ids: Optional[List[int]] = None,
    project_type_ids: Optional[List[int]] = None,
) -> Dict[str, Any]:
    """
    Retrieve curated warehouse metrics for the dashboard.

    Pulls from mart/fact views so the UI can surface project health,
    issue trends, review performance, and service/financial signals
    without bespoke per-widget queries.
    """
    try:
        with get_db_connection(Config.WAREHOUSE_DB) as conn:
            cursor = conn.cursor()
            _set_cursor_timeout(cursor, _DASHBOARD_QUERY_TIMEOUT)
            _set_cursor_timeout(cursor, _DASHBOARD_QUERY_TIMEOUT)
            timer_base = perf_counter()
            _set_cursor_timeout(cursor, _WAREHOUSE_METRICS_QUERY_TIMEOUT)

            def _in_clause(column: str, values: Optional[List[int]]) -> tuple[str, List[int]]:
                if not values:
                    return "", []
                placeholders = ", ".join("?" for _ in values)
                return f" AND {column} IN ({placeholders})", list(values)

            proj_filter_sql, proj_params = _in_clause("p.project_bk", project_ids)
            client_filter_sql, client_params = _in_clause("c.client_bk", client_ids)
            type_filter_sql, type_params = _in_clause("pt.project_type_bk", project_type_ids)
            filter_params = proj_params + client_params + type_params

            cursor.execute("SELECT MAX(month_date_sk) FROM fact.project_kpi_monthly")
            latest_kpi_month_sk = cursor.fetchone()[0]
            cursor.execute("SELECT MAX(month_date_sk) FROM fact.service_monthly")
            latest_service_month_sk = cursor.fetchone()[0]
            cursor.execute("SELECT MAX(snapshot_date_sk) FROM fact.issue_snapshot")
            latest_issue_snapshot_sk = cursor.fetchone()[0]

            issue_trends_daily_available = table_exists("issue_trends_daily", "mart", Config.WAREHOUSE_DB)
            timer_base = perf_counter()

            def _fetch_project_health():
                query_start = perf_counter()
                ph_row = None
                try:
                    with get_db_connection(Config.WAREHOUSE_DB) as project_conn:
                        project_cursor = project_conn.cursor()
                        _set_cursor_timeout(project_cursor, _WAREHOUSE_METRICS_QUERY_TIMEOUT)
                        kpi_filter_sql = ""
                        kpi_params: List[Any] = []
                        if latest_kpi_month_sk is not None:
                            kpi_filter_sql = " AND k.month_date_sk = ?"
                            kpi_params.append(latest_kpi_month_sk)
                        project_cursor.execute(
                            f"""
                            SELECT
                                COUNT(DISTINCT p.project_sk) AS projects,
                                SUM(ISNULL(k.open_issues, 0)) AS open_issues,
                                SUM(ISNULL(k.high_priority_issues, 0)) AS high_priority_issues,
                                AVG(NULLIF(k.avg_resolution_days, 0)) AS avg_resolution_days,
                                SUM(ISNULL(k.review_count, 0)) AS review_count,
                                SUM(ISNULL(k.completed_reviews, 0)) AS completed_reviews,
                                SUM(ISNULL(k.overdue_reviews, 0)) AS overdue_reviews,
                                SUM(ISNULL(k.services_in_progress, 0)) AS services_in_progress,
                                SUM(ISNULL(k.services_completed, 0)) AS services_completed,
                                SUM(ISNULL(k.earned_value, 0)) AS earned_value,
                                SUM(ISNULL(k.claimed_to_date, 0)) AS claimed_to_date,
                                SUM(ISNULL(k.variance_fee, 0)) AS variance_fee
                            FROM dim.project p WITH (NOLOCK)
                            LEFT JOIN fact.project_kpi_monthly k
                                ON k.project_sk = p.project_sk
                               {kpi_filter_sql}
                            LEFT JOIN dim.client c ON c.client_sk = COALESCE(k.client_sk, p.client_sk)
                            LEFT JOIN dim.project_type pt ON pt.project_type_sk = COALESCE(k.project_type_sk, p.project_type_sk)
                            WHERE p.current_flag = 1
                            {proj_filter_sql}
                            {client_filter_sql}
                            {type_filter_sql}
                            """,
                            tuple(kpi_params + filter_params),
                        )
                        ph_row = project_cursor.fetchone()
                except Exception as exc:
                    logger.warning("Failed to load project health quickly: %s", exc)
                    return {
                        "projects": 0,
                        "open_issues": 0,
                        "high_priority_issues": 0,
                        "avg_resolution_days": None,
                        "review_count": 0,
                        "completed_reviews": 0,
                        "overdue_reviews": 0,
                        "services_in_progress": 0,
                        "services_completed": 0,
                        "earned_value": 0.0,
                        "claimed_to_date": 0.0,
                        "variance_fee": 0.0,
                    }
                finally:
                    if _WAREHOUSE_METRICS_LOG_TIMINGS:
                        logger.info(
                            "warehouse metrics: project_health query %.2fs",
                            perf_counter() - query_start,
                        )
                return {
                    "projects": ph_row[0] or 0 if ph_row else 0,
                    "open_issues": ph_row[1] or 0 if ph_row else 0,
                    "high_priority_issues": ph_row[2] or 0 if ph_row else 0,
                    "avg_resolution_days": float(ph_row[3]) if ph_row and ph_row[3] is not None else None,
                    "review_count": ph_row[4] or 0 if ph_row else 0,
                    "completed_reviews": ph_row[5] or 0 if ph_row else 0,
                    "overdue_reviews": ph_row[6] or 0 if ph_row else 0,
                    "services_in_progress": ph_row[7] or 0 if ph_row else 0,
                    "services_completed": ph_row[8] or 0 if ph_row else 0,
                    "earned_value": float(ph_row[9]) if ph_row and ph_row[9] is not None else 0.0,
                    "claimed_to_date": float(ph_row[10]) if ph_row and ph_row[10] is not None else 0.0,
                    "variance_fee": float(ph_row[11]) if ph_row and ph_row[11] is not None else 0.0,
                }

            def _fetch_issue_trends():
                query_start = perf_counter()
                try:
                    with get_db_connection(Config.WAREHOUSE_DB) as trends_conn:
                        trends_cursor = trends_conn.cursor()
                        _set_cursor_timeout(trends_cursor, _WAREHOUSE_METRICS_QUERY_TIMEOUT)
                        trends_cursor.execute(
                            f"""
                            WITH recent_dates AS (
                                SELECT
                                    d.[date],
                                    DATEFROMPARTS(YEAR(d.[date]), MONTH(d.[date]), 1) AS month_start
                                FROM dim.date d
                                WHERE d.[date] >= DATEADD(day, -?, CAST(GETDATE() AS date))
                            ),
                            month_latest AS (
                                SELECT
                                    month_start,
                                    MAX([date]) AS snapshot_date
                                FROM recent_dates
                                GROUP BY month_start
                            ),
                            snapshots AS (
                                SELECT
                                    s.*,
                                    d.[date] AS snapshot_date,
                                    m.month_start
                                FROM fact.issue_snapshot s WITH (NOLOCK)
                                JOIN dim.date d ON s.snapshot_date_sk = d.date_sk
                                JOIN month_latest m ON d.[date] = m.snapshot_date
                            )
                            SELECT
                                s.month_start,
                                COUNT(DISTINCT CASE WHEN s.is_open = 1 THEN s.issue_sk END) AS open_issues,
                                COUNT(DISTINCT CASE WHEN s.is_closed = 1 THEN s.issue_sk END) AS closed_issues,
                                AVG(NULLIF(s.backlog_age_days, 0)) AS avg_backlog_days,
                                AVG(NULLIF(s.resolution_days, 0)) AS avg_resolution_days,
                                AVG(NULLIF(s.urgency_score, 0)) AS avg_urgency,
                                AVG(NULLIF(s.sentiment_score, 0)) AS avg_sentiment
                            FROM snapshots s
                            LEFT JOIN dim.project p ON s.project_sk = p.project_sk
                            LEFT JOIN dim.client c ON s.client_sk = c.client_sk
                            LEFT JOIN dim.project_type pt ON s.project_type_sk = pt.project_type_sk
                            WHERE (p.current_flag = 1 OR p.current_flag IS NULL)
                            {proj_filter_sql}
                            {client_filter_sql}
                            {type_filter_sql}
                            GROUP BY s.month_start
                            ORDER BY s.month_start
                            """,
                            tuple([_WAREHOUSE_ISSUE_TRENDS_DAYS] + filter_params),
                        )
                        rows = trends_cursor.fetchall()
                except Exception as exc:
                    logger.warning("Failed to load issue trends quickly: %s", exc)
                    return []
                finally:
                    if _WAREHOUSE_METRICS_LOG_TIMINGS:
                        logger.info(
                            "warehouse metrics: issue_trends query %.2fs",
                            perf_counter() - query_start,
                        )
                return [
                    {
                        "date": (row[0].isoformat() if isinstance(row[0], (datetime, date)) else str(row[0]))
                        if row[0] is not None
                        else None,
                        "open_issues": int(row[1] or 0),
                        "closed_issues": int(row[2] or 0),
                        "avg_backlog_days": float(row[3]) if row[3] is not None else None,
                        "avg_resolution_days": float(row[4]) if row[4] is not None else None,
                        "avg_urgency": float(row[5]) if row[5] is not None else None,
                        "avg_sentiment": float(row[6]) if row[6] is not None else None,
                    }
                    for row in rows
                ]

            def _fetch_review_performance():
                query_start = perf_counter()
                try:
                    with get_db_connection(Config.WAREHOUSE_DB) as reviews_conn:
                        reviews_cursor = reviews_conn.cursor()
                        _set_cursor_timeout(reviews_cursor, _WAREHOUSE_METRICS_QUERY_TIMEOUT)
                        reviews_cursor.execute(
                            f"""
                            SELECT
                                COUNT(1) AS total_reviews,
                                SUM(CASE WHEN ISNULL(f.is_completed, 0) = 1 THEN 1 ELSE 0 END) AS completed_reviews,
                                SUM(CASE WHEN ISNULL(f.is_overdue, 0) = 1 THEN 1 ELSE 0 END) AS overdue_reviews,
                                AVG(CAST(f.planned_vs_actual_days AS FLOAT)) AS avg_planned_vs_actual_days
                            FROM fact.review_cycle f WITH (NOLOCK)
                            JOIN dim.service s ON f.service_sk = s.service_sk
                            JOIN dim.project p ON f.project_sk = p.project_sk
                            LEFT JOIN dim.client c ON f.client_sk = c.client_sk
                            LEFT JOIN dim.project_type pt ON f.project_type_sk = pt.project_type_sk
                            WHERE p.current_flag = 1
                            {proj_filter_sql}
                            {client_filter_sql}
                            {type_filter_sql}
                            """,
                            tuple(filter_params),
                        )
                        rv_row = reviews_cursor.fetchone()
                except Exception as exc:
                    logger.warning("Failed to load review performance quickly: %s", exc)
                    return {
                        "total_reviews": 0,
                        "completed_reviews": 0,
                        "overdue_reviews": 0,
                        "avg_planned_vs_actual_days": None,
                        "on_time_rate": None,
                    }
                finally:
                    if _WAREHOUSE_METRICS_LOG_TIMINGS:
                        logger.info(
                            "warehouse metrics: review_performance query %.2fs",
                            perf_counter() - query_start,
                        )
                completed_reviews = rv_row[1] or 0 if rv_row else 0
                overdue_reviews = rv_row[2] or 0 if rv_row else 0
                total_reviews = rv_row[0] or 0 if rv_row else 0
                on_time_completed = max(completed_reviews - overdue_reviews, 0)
                on_time_rate = (
                    round(on_time_completed / completed_reviews, 4) if completed_reviews > 0 else None
                )
                return {
                    "total_reviews": total_reviews,
                    "completed_reviews": completed_reviews,
                    "overdue_reviews": overdue_reviews,
                    "avg_planned_vs_actual_days": float(rv_row[3]) if rv_row and rv_row[3] is not None else None,
                    "on_time_rate": on_time_rate,
                }

            def _fetch_service_financials():
                query_start = perf_counter()
                try:
                    with get_db_connection(Config.WAREHOUSE_DB) as service_conn:
                        service_cursor = service_conn.cursor()
                        _set_cursor_timeout(service_cursor, _WAREHOUSE_METRICS_QUERY_TIMEOUT)
                        service_filter_sql = ""
                        service_params: List[Any] = []
                        if latest_service_month_sk is not None:
                            service_filter_sql = "AND sm.month_date_sk = ?"
                            service_params.append(latest_service_month_sk)
                        service_cursor.execute(
                            f"""
                            SELECT
                                SUM(ISNULL(sm.earned_value, 0)) AS earned_value,
                                SUM(ISNULL(sm.claimed_to_date, 0)) AS claimed_to_date,
                                SUM(ISNULL(sm.variance_fee, 0)) AS variance_fee,
                                AVG(NULLIF(sm.progress_pct, 0)) AS avg_progress_pct
                            FROM fact.service_monthly sm WITH (NOLOCK)
                            JOIN dim.project p ON sm.project_sk = p.project_sk
                            LEFT JOIN dim.client c ON sm.client_sk = c.client_sk
                            LEFT JOIN dim.project_type pt ON sm.project_type_sk = pt.project_type_sk
                            WHERE (p.current_flag = 1 OR p.current_flag IS NULL)
                            {service_filter_sql}
                            {proj_filter_sql}
                            {client_filter_sql}
                            {type_filter_sql}
                            """,
                            tuple(service_params + filter_params),
                        )
                        sf_row = service_cursor.fetchone()
                except Exception as exc:
                    logger.warning("Failed to load service financials quickly: %s", exc)
                    return {
                        "earned_value": 0.0,
                        "claimed_to_date": 0.0,
                        "variance_fee": 0.0,
                        "avg_progress_pct": None,
                    }
                finally:
                    if _WAREHOUSE_METRICS_LOG_TIMINGS:
                        logger.info(
                            "warehouse metrics: service_financials query %.2fs",
                            perf_counter() - query_start,
                        )
                return {
                    "earned_value": float(sf_row[0]) if sf_row and sf_row[0] is not None else 0.0,
                    "claimed_to_date": float(sf_row[1]) if sf_row and sf_row[1] is not None else 0.0,
                    "variance_fee": float(sf_row[2]) if sf_row and sf_row[2] is not None else 0.0,
                    "avg_progress_pct": float(sf_row[3]) if sf_row and sf_row[3] is not None else None,
                }

            def _fetch_backlog_age():
                query_start = perf_counter()
                try:
                    with get_db_connection(Config.WAREHOUSE_DB) as backlog_conn:
                        backlog_cursor = backlog_conn.cursor()
                        _set_cursor_timeout(backlog_cursor, _WAREHOUSE_METRICS_QUERY_TIMEOUT)
                        snapshot_filter_sql = ""
                        snapshot_params: List[Any] = []
                        if latest_issue_snapshot_sk is not None:
                            snapshot_filter_sql = "AND s.snapshot_date_sk = ?"
                            snapshot_params.append(latest_issue_snapshot_sk)
                        backlog_cursor.execute(
                            f"""
                            SELECT
                                SUM(CASE WHEN ISNULL(s.is_open, 0) = 1 AND ISNULL(s.backlog_age_days, 0) BETWEEN 0 AND 7 THEN 1 ELSE 0 END) AS bucket_0_7,
                                SUM(CASE WHEN ISNULL(s.is_open, 0) = 1 AND ISNULL(s.backlog_age_days, 0) BETWEEN 8 AND 30 THEN 1 ELSE 0 END) AS bucket_8_30,
                                SUM(CASE WHEN ISNULL(s.is_open, 0) = 1 AND ISNULL(s.backlog_age_days, 0) BETWEEN 31 AND 90 THEN 1 ELSE 0 END) AS bucket_31_90,
                                SUM(CASE WHEN ISNULL(s.is_open, 0) = 1 AND ISNULL(s.backlog_age_days, 0) > 90 THEN 1 ELSE 0 END) AS bucket_90_plus,
                                AVG(NULLIF(s.backlog_age_days, 0)) AS avg_age_days
                            FROM fact.issue_snapshot s WITH (NOLOCK)
                            LEFT JOIN dim.project p ON s.project_sk = p.project_sk
                            LEFT JOIN dim.client c ON s.client_sk = c.client_sk
                            LEFT JOIN dim.project_type pt ON s.project_type_sk = pt.project_type_sk
                            WHERE (p.current_flag = 1 OR p.current_flag IS NULL)
                            {snapshot_filter_sql}
                            {proj_filter_sql}
                            {client_filter_sql}
                            {type_filter_sql}
                            """,
                            tuple(snapshot_params + filter_params),
                        )
                        backlog_row = backlog_cursor.fetchone()
                except Exception as exc:
                    logger.warning("Failed to load backlog age quickly: %s", exc)
                    return {
                        "bucket_0_7": 0,
                        "bucket_8_30": 0,
                        "bucket_31_90": 0,
                        "bucket_90_plus": 0,
                        "avg_age_days": None,
                    }
                finally:
                    if _WAREHOUSE_METRICS_LOG_TIMINGS:
                        logger.info(
                            "warehouse metrics: backlog_age query %.2fs",
                            perf_counter() - query_start,
                        )
                backlog_row = backlog_row or [0, 0, 0, 0, None]
                return {
                    "bucket_0_7": int(backlog_row[0] or 0),
                    "bucket_8_30": int(backlog_row[1] or 0),
                    "bucket_31_90": int(backlog_row[2] or 0),
                    "bucket_90_plus": int(backlog_row[3] or 0),
                    "avg_age_days": float(backlog_row[4]) if backlog_row[4] is not None else None,
                }

            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = {
                    "project_health": executor.submit(_fetch_project_health),
                    "issue_trends": executor.submit(_fetch_issue_trends),
                    "review_performance": executor.submit(_fetch_review_performance),
                    "service_financials": executor.submit(_fetch_service_financials),
                    "backlog_age": executor.submit(_fetch_backlog_age),
                }
                project_health = futures["project_health"].result()
                issue_trends = futures["issue_trends"].result()
                review_performance = futures["review_performance"].result()
                service_financials = futures["service_financials"].result()
                backlog_age = futures["backlog_age"].result()

            aux_elapsed = perf_counter() - timer_base
# Model readiness (control model coverage) from project DB
            ctrl_models = {"projects_with_control_models": 0, "projects_missing_control_models": 0}
            aux_elapsed = perf_counter() - timer_base
            if aux_elapsed <= _WAREHOUSE_METRICS_AUX_BUDGET:
                try:
                    query_start = perf_counter()
                    with get_db_connection() as pm_conn:
                        pm_cursor = pm_conn.cursor()
                        _set_cursor_timeout(pm_cursor, _WAREHOUSE_METRICS_AUX_TIMEOUT)
                        ctrl_params: List[Any] = []
                        ctrl_filter_sql = ""
                        if project_ids:
                            placeholders = ", ".join("?" for _ in project_ids)
                            ctrl_filter_sql = f" AND project_id IN ({placeholders})"
                            ctrl_params.extend(project_ids)
                        pm_cursor.execute(
                            f"""
                            SELECT COUNT(DISTINCT project_id)
                            FROM ProjectManagement.dbo.tblControlModels
                            WHERE ISNULL(is_active, 0) = 1
                            {ctrl_filter_sql}
                            """
                        , tuple(ctrl_params))
                        active_count = pm_cursor.fetchone()
                        active_value = int(active_count[0] or 0) if active_count else 0
                        total_projects = int(project_health.get("projects") or 0)
                        ctrl_models["projects_with_control_models"] = active_value
                        ctrl_models["projects_missing_control_models"] = max(total_projects - active_value, 0)
                    if _WAREHOUSE_METRICS_LOG_TIMINGS:
                        logger.info(
                            "warehouse metrics: control_models query %.2fs",
                            perf_counter() - query_start,
                        )
                except Exception as ctrl_exc:
                    logger.warning("Failed to compute control model readiness: %s", ctrl_exc)
            elif _WAREHOUSE_METRICS_LOG_TIMINGS:
                logger.info(
                    "warehouse metrics: skipping aux sections (elapsed %.2fs > budget %.2fs)",
                    aux_elapsed,
                    _WAREHOUSE_METRICS_AUX_BUDGET,
                )

            # Data freshness from latest Revizto and ACC imports
            data_freshness = {
                "revizto_last_run": None,
                "revizto_projects_extracted": None,
                "acc_last_import": None,
                "acc_last_import_project_id": None,
            }
            if aux_elapsed <= _WAREHOUSE_METRICS_AUX_BUDGET:
                try:
                    query_start = perf_counter()
                    last_run = get_last_revizto_extraction_run()
                    if last_run:
                        data_freshness["revizto_last_run"] = _serialize_datetime(last_run.get("end_time") or last_run.get("start_time"))
                        data_freshness["revizto_projects_extracted"] = last_run.get("projects_extracted")
                    if _WAREHOUSE_METRICS_LOG_TIMINGS:
                        logger.info(
                            "warehouse metrics: revizto_freshness query %.2fs",
                            perf_counter() - query_start,
                        )
                except Exception as rev_exc:
                    logger.warning("Failed to fetch last Revizto run: %s", rev_exc)

            if aux_elapsed <= _WAREHOUSE_METRICS_AUX_BUDGET:
                try:
                    query_start = perf_counter()
                    with get_db_connection() as pm_conn:
                        pm_cursor = pm_conn.cursor()
                        _set_cursor_timeout(pm_cursor, _WAREHOUSE_METRICS_AUX_TIMEOUT)
                        acc_params: List[Any] = []
                        acc_filter_sql = ""
                        if project_ids:
                            placeholders = ", ".join("?" for _ in project_ids)
                            acc_filter_sql = f" WHERE project_id IN ({placeholders})"
                            acc_params.extend(project_ids)
                        pm_cursor.execute(
                            f"""
                            SELECT TOP 1 project_id, import_date
                            FROM {S.ACCImportLogs.TABLE}
                            {acc_filter_sql}
                            ORDER BY import_date DESC
                            """
                        , tuple(acc_params))
                        acc_row = pm_cursor.fetchone()
                        if acc_row:
                            data_freshness["acc_last_import_project_id"] = acc_row[0]
                            data_freshness["acc_last_import"] = _serialize_datetime(acc_row[1])
                    if _WAREHOUSE_METRICS_LOG_TIMINGS:
                        logger.info(
                            "warehouse metrics: acc_freshness query %.2fs",
                            perf_counter() - query_start,
                        )
                except Exception as acc_exc:
                    logger.warning("Failed to fetch ACC import freshness: %s", acc_exc)

            data_quality = {
                "last_run_id": None,
                "last_run_status": None,
                "last_run_completed_at": None,
                "checks_total": 0,
                "checks_failed": 0,
                "checks_failed_high": 0,
                "checks_failed_medium": 0,
            }
            if aux_elapsed <= _WAREHOUSE_METRICS_AUX_BUDGET:
                try:
                    query_start = perf_counter()
                    prev_timeout = getattr(cursor, "timeout", 0)
                    _set_cursor_timeout(cursor, _WAREHOUSE_METRICS_AUX_TIMEOUT)
                    cursor.execute(
                        """
                        SELECT TOP 1 run_id, status, completed_at
                        FROM ctl.etl_run
                        WHERE pipeline_name = 'warehouse_full_load'
                        ORDER BY run_id DESC
                        """
                    )
                    run_row = cursor.fetchone()
                    if run_row:
                        run_id = run_row[0]
                        data_quality["last_run_id"] = run_id
                        data_quality["last_run_status"] = run_row[1]
                        data_quality["last_run_completed_at"] = _serialize_datetime(run_row[2]) if run_row[2] else None
                        cursor.execute(
                            """
                            SELECT
                                COUNT(*) AS total,
                                SUM(CASE WHEN passed = 0 THEN 1 ELSE 0 END) AS failed,
                                SUM(CASE WHEN passed = 0 AND severity = 'high' THEN 1 ELSE 0 END) AS failed_high,
                                SUM(CASE WHEN passed = 0 AND severity = 'medium' THEN 1 ELSE 0 END) AS failed_medium
                            FROM ctl.data_quality_result
                            WHERE run_id = ?
                            """,
                            (run_id,),
                        )
                        dq_row = cursor.fetchone()
                        if dq_row:
                            data_quality["checks_total"] = int(dq_row[0] or 0)
                            data_quality["checks_failed"] = int(dq_row[1] or 0)
                            data_quality["checks_failed_high"] = int(dq_row[2] or 0)
                            data_quality["checks_failed_medium"] = int(dq_row[3] or 0)
                    if prev_timeout:
                        _set_cursor_timeout(cursor, prev_timeout)
                    if _WAREHOUSE_METRICS_LOG_TIMINGS:
                        logger.info(
                            "warehouse metrics: data_quality query %.2fs",
                            perf_counter() - query_start,
                        )
                except Exception as dq_exc:
                    logger.warning("Failed to fetch data quality summary: %s", dq_exc)

            result = {
                "project_health": project_health,
                "issue_trends": issue_trends,
                "review_performance": review_performance,
                "service_financials": service_financials,
                "backlog_age": backlog_age,
                "control_models": ctrl_models,
                "data_freshness": data_freshness,
                "data_quality": data_quality,
                "as_of": _get_latest_issue_snapshot_date(cursor),
            }
            if _WAREHOUSE_METRICS_LOG_TIMINGS:
                logger.info(
                    "warehouse metrics: total %.2fs",
                    perf_counter() - timer_base,
                )
            return result
    except Exception as e:
        logger.error(f"Error fetching warehouse dashboard metrics: {e}")
        return {
            "project_health": {},
            "issue_trends": [],
            "review_performance": {},
            "service_financials": {},
            "error": str(e),
        }


def get_warehouse_dashboard_metrics(
    project_ids: Optional[List[int]] = None,
    client_ids: Optional[List[int]] = None,
    project_type_ids: Optional[List[int]] = None,
) -> Dict[str, Any]:
    cache_key = _warehouse_metrics_cache_key(project_ids, client_ids, project_type_ids)
    entry = _get_or_create_cache_entry(cache_key)
    now = unix_time()

    if entry.data and entry.expires_at > now:
        return entry.data

    if not entry.lock.acquire(blocking=False):
        if entry.data:
            return entry.data
        entry.lock.acquire()
        try:
            return entry.data
        finally:
            entry.lock.release()

    try:
        result = _calculate_warehouse_dashboard_metrics(project_ids, client_ids, project_type_ids)
        entry.data = result
        entry.expires_at = unix_time() + _WAREHOUSE_METRICS_CACHE_TTL_SECONDS
        entry.last_updated = unix_time()
        return result
    finally:
        entry.lock.release()
        with _WAREHOUSE_METRICS_CACHE_LOCK:
            _evict_cache_if_needed_locked()


def get_warehouse_issues_history(
    project_ids: Optional[List[int]] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    discipline: Optional[str] = None,
    zone: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Return weekly issue status counts using canonical snapshots.

    Uses Issues_Snapshots filtered to the latest successful run per snapshot date.
    """
    try:
        with get_db_connection(Config.WAREHOUSE_DB) as conn:
            cursor = conn.cursor()

            params: List[Any] = []
            where_filters: List[str] = []
            if project_ids:
                placeholders = ", ".join("?" for _ in project_ids)
                where_filters.append(f"TRY_CAST(s.{S.IssuesSnapshots.PROJECT_ID} AS INT) IN ({placeholders})")
                params.extend(project_ids)
            if status:
                where_filters.append(f"LOWER(ISNULL(s.{S.IssuesSnapshots.STATUS_NORMALIZED},'')) = LOWER(?)")
                params.append(status)
            if priority:
                where_filters.append(f"LOWER(ISNULL(s.{S.IssuesSnapshots.PRIORITY_NORMALIZED},'')) = LOWER(?)")
                params.append(priority)
            if discipline:
                where_filters.append(f"LOWER(ISNULL(s.{S.IssuesSnapshots.DISCIPLINE_NORMALIZED},'')) = LOWER(?)")
                params.append(discipline)
            if zone:
                where_filters.append(f"LOWER(ISNULL(s.{S.IssuesSnapshots.LOCATION_ROOT},'')) = LOWER(?)")
                params.append(zone)
            where_sql = " AND " + " AND ".join(where_filters) if where_filters else ""

            cursor.execute(
                f"""
                WITH successful_runs AS (
                    SELECT {S.IssueImportRuns.IMPORT_RUN_ID}, {S.IssueImportRuns.COMPLETED_AT}
                    FROM dbo.{S.IssueImportRuns.TABLE}
                    WHERE {S.IssueImportRuns.STATUS} = 'success'
                ),
                latest_run_per_date AS (
                    SELECT
                        s.{S.IssuesSnapshots.SNAPSHOT_DATE} AS snapshot_date,
                        MAX(r.{S.IssueImportRuns.COMPLETED_AT}) AS latest_completed_at
                    FROM dbo.{S.IssuesSnapshots.TABLE} s
                    JOIN successful_runs r
                        ON s.{S.IssuesSnapshots.IMPORT_RUN_ID} = r.{S.IssueImportRuns.IMPORT_RUN_ID}
                    GROUP BY s.{S.IssuesSnapshots.SNAPSHOT_DATE}
                ),
                filtered AS (
                    SELECT s.*
                    FROM dbo.{S.IssuesSnapshots.TABLE} s
                    JOIN successful_runs r
                        ON s.{S.IssuesSnapshots.IMPORT_RUN_ID} = r.{S.IssueImportRuns.IMPORT_RUN_ID}
                    JOIN latest_run_per_date l
                        ON s.{S.IssuesSnapshots.SNAPSHOT_DATE} = l.snapshot_date
                       AND r.{S.IssueImportRuns.COMPLETED_AT} = l.latest_completed_at
                    WHERE 1 = 1
                    {where_sql}
                )
                SELECT
                    d.week_start_date,
                    s.{S.IssuesSnapshots.STATUS_NORMALIZED} AS status,
                    COUNT(DISTINCT s.{S.IssuesSnapshots.ISSUE_KEY}) AS issue_count
                FROM filtered s
                JOIN dim.date d ON s.{S.IssuesSnapshots.SNAPSHOT_DATE} = d.[date]
                GROUP BY d.week_start_date, s.{S.IssuesSnapshots.STATUS_NORMALIZED}
                ORDER BY d.week_start_date
                """,
                tuple(params),
            )

            rows = cursor.fetchall()
            items = [
                {
                    "week_start": row[0].isoformat() if row[0] else None,
                    "status": row[1] or "unknown",
                    "count": int(row[2] or 0),
                }
                for row in rows
            ]
            return {
                "items": items,
                "as_of": _get_latest_issue_snapshot_date(cursor),
            }
    except Exception as e:
        logger.error(f"Error fetching warehouse issues history: {e}")
        return {"items": [], "as_of": None}

def get_revit_health_dashboard_summary(
    project_ids: Optional[List[int]] = None,
    discipline: Optional[str] = None,
) -> Dict[str, Any]:
    """Return aggregated Revit health metrics for the dashboard."""
    return {
        "summary": {
            "total_files": 0,
            "projects": 0,
            "avg_health_score": None,
            "min_health_score": None,
            "max_health_score": None,
            "good_files": 0,
            "fair_files": 0,
            "poor_files": 0,
            "critical_files": 0,
            "files_with_link_issues": 0,
            "total_warnings": 0,
            "total_critical_warnings": 0,
            "latest_check_date": None,
        },
        "trend": [],
        "categories": {
            "good": {"count": 0, "pct": None},
            "fair": {"count": 0, "pct": None},
            "poor": {"count": 0, "pct": None},
            "critical": {"count": 0, "pct": None},
        },
        "by_discipline": [],
        "top_files": [],
    }


def get_naming_compliance_dashboard_metrics(
    project_ids: Optional[List[int]] = None,
    discipline: Optional[str] = None,
) -> Dict[str, Any]:
    """Return naming compliance metrics for the dashboard."""
    return {
        "summary": {
            "total_files": 0,
            "valid_files": 0,
            "invalid_files": 0,
            "compliance_pct": None,
            "latest_validated": None,
        },
        "by_discipline": [],
        "recent_invalid": [],
    }


def get_naming_compliance_table(
    project_ids: Optional[List[int]] = None,
    discipline: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
    sort_by: str = "validated_date",
    sort_dir: str = "desc",
) -> Dict[str, Any]:
    """Return paginated naming compliance rows."""
    return {
        "page": page,
        "page_size": page_size,
        "total_count": 0,
        "rows": [],
    }


def get_control_points_dashboard(
    project_ids: Optional[List[int]] = None,
    discipline: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
    sort_by: str = "project_name",
    sort_dir: str = "asc",
) -> Dict[str, Any]:
    """Return control point dashboard data (placeholder)."""
    return {
        "items": [],
        "total": 0,
        "page": page,
        "page_size": page_size,
    }


def get_coordinate_alignment_dashboard(
    project_ids: Optional[List[int]] = None,
    discipline: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
    sort_by: str = "model_file_name",
    sort_dir: str = "asc",
) -> Dict[str, Any]:
    """Return coordinate alignment dashboard data (placeholder)."""
    return {
        "control_base_points": [],
        "control_survey_points": [],
        "model_base_points": [],
        "model_survey_points": [],
        "total": 0,
        "page": page,
        "page_size": page_size,
    }


def get_grid_alignment_dashboard(
    project_ids: Optional[List[int]] = None,
    discipline: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
    sort_by: str = "project_name",
    sort_dir: str = "asc",
) -> Dict[str, Any]:
    """Return grid alignment rows (placeholder)."""
    return {
        "items": [],
        "total": 0,
        "page": page,
        "page_size": page_size,
    }


def get_level_alignment_dashboard(
    project_ids: Optional[List[int]] = None,
    discipline: Optional[str] = None,
    tolerance_mm: float = 5.0,
    page: int = 1,
    page_size: int = 50,
    sort_by: str = "project_name",
    sort_dir: str = "asc",
) -> Dict[str, Any]:
    """Return level alignment rows (placeholder)."""
    return {
        "items": [],
        "total": 0,
        "page": page,
        "page_size": page_size,
        "tolerance_mm": tolerance_mm,
    }


def get_dashboard_issues_kpis(
    project_ids: Optional[List[int]] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    discipline: Optional[str] = None,
    zone: Optional[str] = None,
) -> Dict[str, Any]:
    """Return KPI counts for the Issues dashboard section."""
    cache_key = _dashboard_cache_key(
        "issues_kpis",
        _normalize_id_tuple(project_ids),
        (status or "").lower(),
        (priority or "").lower(),
        (discipline or "").lower(),
        (zone or "").lower(),
    )

    def _compute():
        try:
            with get_db_connection(Config.WAREHOUSE_DB) as conn:
                cursor = conn.cursor()
                run_id, as_of = _get_latest_successful_issue_run(cursor)
                if run_id is None:
                    return {
                        "total_issues": 0,
                        "active_issues": 0,
                        "over_30_days": 0,
                        "closed_since_review": 0,
                        "as_of": None,
                    }

                base_params: List[Any] = [run_id]
                where_clauses = [f"ic.{S.IssuesCurrent.IMPORT_RUN_ID} = ?"]
                if project_ids:
                    placeholders = ", ".join("?" for _ in project_ids)
                    where_clauses.append(
                        f"TRY_CAST(ic.{S.IssuesCurrent.PROJECT_ID} AS INT) IN ({placeholders})"
                    )
                    base_params.extend(project_ids)
                if status:
                    where_clauses.append(f"LOWER(ISNULL(ic.{S.IssuesCurrent.STATUS_NORMALIZED},'')) = LOWER(?)")
                    base_params.append(status)
                if priority:
                    where_clauses.append(f"LOWER(ISNULL(ic.{S.IssuesCurrent.PRIORITY_NORMALIZED},'')) = LOWER(?)")
                    base_params.append(priority)
                if discipline:
                    where_clauses.append(f"LOWER(ISNULL(ic.{S.IssuesCurrent.DISCIPLINE_NORMALIZED},'')) = LOWER(?)")
                    base_params.append(discipline)
                if zone:
                    where_clauses.append(f"LOWER(ISNULL(ic.{S.IssuesCurrent.LOCATION_ROOT},'')) = LOWER(?)")
                    base_params.append(zone)
                where_sql = "WHERE " + " AND ".join(where_clauses)

                open_clause = (
                    f"(LOWER(ISNULL(ic.{S.IssuesCurrent.STATUS_NORMALIZED},'')) LIKE '%open%' "
                    f"OR LOWER(ISNULL(ic.{S.IssuesCurrent.STATUS_NORMALIZED},'')) LIKE '%progress%')"
                )
                cursor.execute(
                    f"""
                    SELECT
                        COUNT(DISTINCT ic.{S.IssuesCurrent.ISSUE_KEY}) AS total_issues,
                        SUM(CASE WHEN {open_clause} THEN 1 ELSE 0 END) AS active_issues,
                        SUM(
                            CASE
                                WHEN {open_clause}
                                 AND ic.{S.IssuesCurrent.CREATED_AT} IS NOT NULL
                                 AND DATEDIFF(day, ic.{S.IssuesCurrent.CREATED_AT}, COALESCE(?, SYSUTCDATETIME())) > 30
                                THEN 1
                                ELSE 0
                            END
                        ) AS over_30_days
                    FROM dbo.{S.IssuesCurrent.TABLE} ic
                    {where_sql}
                    """,
                    tuple(base_params + [as_of]),
                )
                row = cursor.fetchone()
                totals = {
                    "total_issues": int(row[0] or 0) if row else 0,
                    "active_issues": int(row[1] or 0) if row else 0,
                    "over_30_days": int(row[2] or 0) if row else 0,
                }

                cursor.execute(
                    f"""
                    WITH review_anchor AS (
                        SELECT
                            svc.project_sk,
                            MAX(COALESCE(rc.due_date_sk, rc.planned_date_sk)) AS last_review_date_sk
                        FROM dim.review_cycle rc
                        JOIN dim.service svc ON rc.service_sk = svc.service_sk
                        WHERE rc.current_flag = 1
                        GROUP BY svc.project_sk
                    ),
                    review_dates AS (
                        SELECT
                            ra.project_sk,
                            d.[date] AS last_review_date
                        FROM review_anchor ra
                        JOIN dim.date d ON ra.last_review_date_sk = d.date_sk
                    )
                    SELECT
                        COUNT(DISTINCT ic.{S.IssuesCurrent.ISSUE_KEY}) AS closed_since_review
                    FROM dbo.{S.IssuesCurrent.TABLE} ic
                    JOIN dim.project p
                        ON TRY_CAST(ic.{S.IssuesCurrent.PROJECT_ID} AS INT) = p.project_bk
                    JOIN review_dates rd ON rd.project_sk = p.project_sk
                    {where_sql}
                      AND ic.{S.IssuesCurrent.CLOSED_AT} IS NOT NULL
                      AND ic.{S.IssuesCurrent.CLOSED_AT} >= rd.last_review_date
                    """,
                    tuple(base_params),
                )
                row = cursor.fetchone()
                totals["closed_since_review"] = int(row[0] or 0) if row else 0
                totals["as_of"] = as_of
                return totals
        except Exception as e:
            logger.error("Error fetching issues KPIs: %s", e)
            return {
                "total_issues": 0,
                "active_issues": 0,
                "over_30_days": 0,
                "closed_since_review": 0,
            }

    return _get_dashboard_cached_value(cache_key, _compute)


def get_dashboard_issues_charts(
    project_ids: Optional[List[int]] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    discipline: Optional[str] = None,
    zone: Optional[str] = None,
) -> Dict[str, Any]:
    """Return chart-ready groupings for the Issues dashboard."""
    try:
        with get_db_connection(Config.WAREHOUSE_DB) as conn:
            cursor = conn.cursor()
            _set_cursor_timeout(cursor, _DASHBOARD_QUERY_TIMEOUT)
            run_id, as_of = _get_latest_successful_issue_run(cursor)
            if run_id is None:
                return {"status": [], "priority": [], "discipline": [], "zone": [], "trend_90d": []}

            params: List[Any] = [run_id]
            where_clauses = [f"ic.{S.IssuesCurrent.IMPORT_RUN_ID} = ?"]
            if project_ids:
                placeholders = ", ".join("?" for _ in project_ids)
                where_clauses.append(f"TRY_CAST(ic.{S.IssuesCurrent.PROJECT_ID} AS INT) IN ({placeholders})")
                params.extend(project_ids)
            if status:
                where_clauses.append(f"LOWER(ISNULL(ic.{S.IssuesCurrent.STATUS_NORMALIZED},'')) = LOWER(?)")
                params.append(status)
            if priority:
                where_clauses.append(f"LOWER(ISNULL(ic.{S.IssuesCurrent.PRIORITY_NORMALIZED},'')) = LOWER(?)")
                params.append(priority)
            if discipline:
                where_clauses.append(f"LOWER(ISNULL(ic.{S.IssuesCurrent.DISCIPLINE_NORMALIZED},'')) = LOWER(?)")
                params.append(discipline)
            if zone:
                where_clauses.append(f"LOWER(ISNULL(ic.{S.IssuesCurrent.LOCATION_ROOT},'')) = LOWER(?)")
                params.append(zone)
            where_sql = "WHERE " + " AND ".join(where_clauses)

            cursor.execute(
                f"""
                SELECT ic.{S.IssuesCurrent.STATUS_NORMALIZED}, COUNT(DISTINCT ic.{S.IssuesCurrent.ISSUE_KEY}) AS issue_count
                FROM dbo.{S.IssuesCurrent.TABLE} ic
                {where_sql}
                GROUP BY ic.{S.IssuesCurrent.STATUS_NORMALIZED}
                ORDER BY issue_count DESC
                """,
                tuple(params),
            )
            status_rows = cursor.fetchall()

            cursor.execute(
                f"""
                SELECT ic.{S.IssuesCurrent.PRIORITY_NORMALIZED}, COUNT(DISTINCT ic.{S.IssuesCurrent.ISSUE_KEY}) AS issue_count
                FROM dbo.{S.IssuesCurrent.TABLE} ic
                {where_sql}
                GROUP BY ic.{S.IssuesCurrent.PRIORITY_NORMALIZED}
                ORDER BY issue_count DESC
                """,
                tuple(params),
            )
            priority_rows = cursor.fetchall()

            cursor.execute(
                f"""
                SELECT ic.{S.IssuesCurrent.DISCIPLINE_NORMALIZED}, COUNT(DISTINCT ic.{S.IssuesCurrent.ISSUE_KEY}) AS issue_count
                FROM dbo.{S.IssuesCurrent.TABLE} ic
                {where_sql}
                GROUP BY ic.{S.IssuesCurrent.DISCIPLINE_NORMALIZED}
                ORDER BY issue_count DESC
                """,
                tuple(params),
            )
            discipline_rows = cursor.fetchall()

            cursor.execute(
                f"""
                SELECT ic.{S.IssuesCurrent.LOCATION_ROOT}, COUNT(DISTINCT ic.{S.IssuesCurrent.ISSUE_KEY}) AS issue_count
                FROM dbo.{S.IssuesCurrent.TABLE} ic
                {where_sql}
                GROUP BY ic.{S.IssuesCurrent.LOCATION_ROOT}
                ORDER BY issue_count DESC
                """,
                tuple(params),
            )
            zone_rows = cursor.fetchall()

            cursor.execute(
                """
                SELECT 1
                FROM sys.tables t
                JOIN sys.schemas s ON t.schema_id = s.schema_id
                WHERE s.name = 'mart' AND t.name = 'issue_trends_monthly'
                """,
            )
            has_monthly_trends = cursor.fetchone() is not None
            cursor.execute(
                """
                SELECT 1
                FROM sys.tables t
                JOIN sys.schemas s ON t.schema_id = s.schema_id
                WHERE s.name = 'mart' AND t.name = 'issue_trends_weekly'
                """,
            )
            has_weekly_trends = cursor.fetchone() is not None
            can_use_trends = not (status or priority or discipline or zone)

            trend_weekly_rows = []
            trend_monthly_rows = []

            if has_weekly_trends and can_use_trends:
                trend_params: List[Any] = [as_of] if as_of else [None]
                trend_filters: List[str] = []
                if project_ids:
                    placeholders = ", ".join("?" for _ in project_ids)
                    trend_filters.append(f"p.project_bk IN ({placeholders})")
                    trend_params.extend(project_ids)
                trend_filter_sql = " AND " + " AND ".join(trend_filters) if trend_filters else ""

                cursor.execute(
                    f"""
                    SELECT
                        w.week_start,
                        SUM(w.open_issues) AS open_issues,
                        SUM(w.closed_issues) AS closed_issues,
                        SUM(w.total_issues) AS total_issues
                    FROM mart.issue_trends_weekly w
                    LEFT JOIN dim.project p ON w.project_sk = p.project_sk
                    WHERE w.week_start >= DATEADD(day, -90, COALESCE(?, SYSUTCDATETIME()))
                    {trend_filter_sql}
                    GROUP BY w.week_start
                    ORDER BY w.week_start
                    """,
                    tuple(trend_params),
                )
                trend_weekly_rows = cursor.fetchall()
            else:
                trend_params = [as_of] if as_of else [None]
                trend_filters = []
                if project_ids:
                    placeholders = ", ".join("?" for _ in project_ids)
                    trend_filters.append(f"TRY_CAST(s.{S.IssuesSnapshots.PROJECT_ID} AS INT) IN ({placeholders})")
                    trend_params.extend(project_ids)
                if status:
                    trend_filters.append(f"LOWER(ISNULL(s.{S.IssuesSnapshots.STATUS_NORMALIZED},'')) = LOWER(?)")
                    trend_params.append(status)
                if priority:
                    trend_filters.append(f"LOWER(ISNULL(s.{S.IssuesSnapshots.PRIORITY_NORMALIZED},'')) = LOWER(?)")
                    trend_params.append(priority)
                if discipline:
                    trend_filters.append(f"LOWER(ISNULL(s.{S.IssuesSnapshots.DISCIPLINE_NORMALIZED},'')) = LOWER(?)")
                    trend_params.append(discipline)
                if zone:
                    trend_filters.append(f"LOWER(ISNULL(s.{S.IssuesSnapshots.LOCATION_ROOT},'')) = LOWER(?)")
                    trend_params.append(zone)
                trend_filter_sql = " AND " + " AND ".join(trend_filters) if trend_filters else ""

                cursor.execute(
                    f"""
                    WITH successful_runs AS (
                        SELECT {S.IssueImportRuns.IMPORT_RUN_ID}, {S.IssueImportRuns.COMPLETED_AT}
                        FROM dbo.{S.IssueImportRuns.TABLE}
                        WHERE {S.IssueImportRuns.STATUS} = 'success'
                    ),
                    latest_run_per_date AS (
                        SELECT
                            s.{S.IssuesSnapshots.SNAPSHOT_DATE} AS snapshot_date,
                            MAX(r.{S.IssueImportRuns.COMPLETED_AT}) AS latest_completed_at
                        FROM dbo.{S.IssuesSnapshots.TABLE} s
                        JOIN successful_runs r
                            ON s.{S.IssuesSnapshots.IMPORT_RUN_ID} = r.{S.IssueImportRuns.IMPORT_RUN_ID}
                        GROUP BY s.{S.IssuesSnapshots.SNAPSHOT_DATE}
                    ),
                    filtered AS (
                        SELECT s.*
                        FROM dbo.{S.IssuesSnapshots.TABLE} s
                        JOIN successful_runs r
                            ON s.{S.IssuesSnapshots.IMPORT_RUN_ID} = r.{S.IssueImportRuns.IMPORT_RUN_ID}
                        JOIN latest_run_per_date l
                            ON s.{S.IssuesSnapshots.SNAPSHOT_DATE} = l.snapshot_date
                           AND r.{S.IssueImportRuns.COMPLETED_AT} = l.latest_completed_at
                        WHERE s.{S.IssuesSnapshots.SNAPSHOT_DATE} >= DATEADD(day, -90, COALESCE(?, SYSUTCDATETIME()))
                        {trend_filter_sql}
                    )
                    SELECT
                        d.week_start_date,
                        SUM(CASE WHEN s.{S.IssuesSnapshots.IS_OPEN} = 1 THEN 1 ELSE 0 END) AS open_issues,
                        SUM(CASE WHEN s.{S.IssuesSnapshots.IS_CLOSED} = 1 THEN 1 ELSE 0 END) AS closed_issues,
                        COUNT(DISTINCT s.{S.IssuesSnapshots.ISSUE_KEY}) AS total_issues
                    FROM filtered s
                    JOIN dim.date d ON s.{S.IssuesSnapshots.SNAPSHOT_DATE} = d.[date]
                    GROUP BY d.week_start_date
                    ORDER BY d.week_start_date
                    """,
                    tuple(trend_params),
                )
                trend_weekly_rows = cursor.fetchall()

            if has_monthly_trends and can_use_trends:
                trend_params = []
                trend_filters = []
                if project_ids:
                    placeholders = ", ".join("?" for _ in project_ids)
                    trend_filters.append(f"p.project_bk IN ({placeholders})")
                    trend_params.extend(project_ids)
                trend_filter_sql = " AND " + " AND ".join(trend_filters) if trend_filters else ""

                cursor.execute(
                    f"""
                    SELECT
                        m.month_start,
                        SUM(m.open_issues) AS open_issues,
                        SUM(m.closed_issues) AS closed_issues,
                        SUM(m.total_issues) AS total_issues
                    FROM mart.issue_trends_monthly m
                    LEFT JOIN dim.project p ON m.project_sk = p.project_sk
                    WHERE 1 = 1
                    {trend_filter_sql}
                    GROUP BY m.month_start
                    ORDER BY m.month_start
                    """,
                    tuple(trend_params),
                )
                trend_monthly_rows = cursor.fetchall()

            return {
                "status": [{"label": row[0], "value": int(row[1] or 0)} for row in status_rows if row[0] is not None],
                "priority": [{"label": row[0], "value": int(row[1] or 0)} for row in priority_rows if row[0] is not None],
                "discipline": [{"label": row[0], "value": int(row[1] or 0)} for row in discipline_rows if row[0] is not None],
                "zone": [{"label": row[0], "value": int(row[1] or 0)} for row in zone_rows if row[0] is not None],
                "trend_90d": [
                    {
                        "date": row[0].isoformat() if row[0] else None,
                        "open": int(row[1] or 0),
                        "closed": int(row[2] or 0),
                        "total": int(row[3] or 0),
                    }
                    for row in trend_weekly_rows
                ],
                "trend_90d_weekly": [
                    {
                        "date": row[0].isoformat() if row[0] else None,
                        "open": int(row[1] or 0),
                        "closed": int(row[2] or 0),
                        "total": int(row[3] or 0),
                    }
                    for row in trend_weekly_rows
                ],
                "trend_all_time_monthly": [
                    {
                        "date": row[0].isoformat() if row[0] else None,
                        "open": int(row[1] or 0),
                        "closed": int(row[2] or 0),
                        "total": int(row[3] or 0),
                    }
                    for row in trend_monthly_rows
                ],
                "as_of": as_of,
            }
    except Exception as e:
        logger.error("Error fetching issues charts: %s", e)
        return {"status": [], "priority": [], "discipline": [], "zone": [], "trend_90d": []}

def get_dashboard_issues_table(
    project_ids: Optional[List[int]] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    discipline: Optional[str] = None,
    zone: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
    sort_by: str = "created_at",
    sort_dir: str = "desc",
) -> Dict[str, Any]:
    """Return paginated issues rows for dashboard drill-down."""
    allowed_sort = {
        "created_at": "created_at",
        "status": "status",
        "priority": "priority",
        "project_name": "project_name",
        "issue_id": "issue_id",
    }
    sort_col = allowed_sort.get(sort_by, "created_at")
    sort_direction = "DESC" if str(sort_dir).lower() == "desc" else "ASC"
    offset = max(page - 1, 0) * page_size

    try:
        with get_db_connection(Config.WAREHOUSE_DB) as conn:
            cursor = conn.cursor()
            _set_cursor_timeout(cursor, _DASHBOARD_QUERY_TIMEOUT)
            run_id, as_of = _get_latest_successful_issue_run(cursor)
            if run_id is None:
                return {"page": page, "page_size": page_size, "total_count": 0, "rows": [], "as_of": None}

            params: List[Any] = [run_id]
            where_clauses = [f"ic.{S.IssuesCurrent.IMPORT_RUN_ID} = ?"]
            if project_ids:
                placeholders = ", ".join("?" for _ in project_ids)
                where_clauses.append(f"TRY_CAST(ic.{S.IssuesCurrent.PROJECT_ID} AS INT) IN ({placeholders})")
                params.extend(project_ids)
            if status:
                where_clauses.append(f"LOWER(ISNULL(ic.{S.IssuesCurrent.STATUS_NORMALIZED},'')) = LOWER(?)")
                params.append(status)
            if priority:
                where_clauses.append(f"LOWER(ISNULL(ic.{S.IssuesCurrent.PRIORITY_NORMALIZED},'')) = LOWER(?)")
                params.append(priority)
            if discipline:
                where_clauses.append(f"LOWER(ISNULL(ic.{S.IssuesCurrent.DISCIPLINE_NORMALIZED},'')) = LOWER(?)")
                params.append(discipline)
            if zone:
                where_clauses.append(f"LOWER(ISNULL(ic.{S.IssuesCurrent.LOCATION_ROOT},'')) = LOWER(?)")
                params.append(zone)
            where_sql = "WHERE " + " AND ".join(where_clauses)

            cursor.execute(
                f"""
                WITH acc_issues AS (
                    SELECT
                        ve.*,
                        ROW_NUMBER() OVER (
                            PARTITION BY ve.display_id, ve.project_id
                            ORDER BY ve.created_at DESC, ve.issue_id DESC
                        ) AS rn
                    FROM acc_data_schema.dbo.vw_issues_expanded ve
                ),
                base AS (
                    SELECT
                        ic.{S.IssuesCurrent.ISSUE_KEY},
                        ic.{S.IssuesCurrent.SOURCE_ISSUE_ID} AS issue_id,
                        ic.{S.IssuesCurrent.SOURCE_SYSTEM} AS source,
                        p.project_name,
                        ic.{S.IssuesCurrent.STATUS_NORMALIZED} AS status,
                        ic.{S.IssuesCurrent.PRIORITY_NORMALIZED} AS priority,
                        di.clash_level,
                        di.title,
                        ve.latest_comment,
                        ve.Company AS company,
                        COALESCE(ic.{S.IssuesCurrent.LOCATION_ROOT}, 'Unassigned') AS zone,
                        ic.{S.IssuesCurrent.LOCATION_ROOT} AS location_root,
                        ic.{S.IssuesCurrent.LOCATION_BUILDING} AS location_building,
                        ic.{S.IssuesCurrent.LOCATION_LEVEL} AS location_level,
                        ic.{S.IssuesCurrent.CREATED_AT} AS created_at
                    FROM dbo.{S.IssuesCurrent.TABLE} ic
                    LEFT JOIN dim.project p
                        ON TRY_CAST(ic.{S.IssuesCurrent.PROJECT_ID} AS INT) = p.project_bk
                    LEFT JOIN dim.issue di
                        ON di.source_system = ic.{S.IssuesCurrent.SOURCE_SYSTEM}
                       AND COALESCE(NULLIF(di.source_issue_id, ''), di.issue_bk) = ic.{S.IssuesCurrent.SOURCE_ISSUE_ID}
                       AND COALESCE(NULLIF(di.source_project_id, ''), ic.{S.IssuesCurrent.SOURCE_PROJECT_ID})
                           = ic.{S.IssuesCurrent.SOURCE_PROJECT_ID}
                       AND di.current_flag = 1
                    LEFT JOIN acc_issues ve
                        ON ic.{S.IssuesCurrent.SOURCE_SYSTEM} = 'ACC'
                       AND CAST(ve.display_id AS NVARCHAR(255)) = ic.{S.IssuesCurrent.SOURCE_ISSUE_ID}
                       AND CAST(ve.project_id AS NVARCHAR(255)) = ic.{S.IssuesCurrent.SOURCE_PROJECT_ID}
                       AND ve.rn = 1
                    {where_sql}
                ),
                numbered AS (
                    SELECT
                        *,
                        COUNT(1) OVER() AS total_count,
                        ROW_NUMBER() OVER (ORDER BY {sort_col} {sort_direction}) AS rn
                    FROM base
                )
                SELECT
                    issue_id,
                    source,
                    project_name,
                    status,
                    priority,
                    clash_level,
                    title,
                    latest_comment,
                    company,
                    zone,
                    location_root,
                    location_building,
                    location_level,
                    created_at,
                    total_count
                FROM numbered
                WHERE rn BETWEEN ? AND ?
                ORDER BY rn
                """,
                tuple(params + [offset + 1, offset + page_size]),
            )
            rows = cursor.fetchall()
            total_count = int(rows[0][-1]) if rows else 0
            return {
                "page": page,
                "page_size": page_size,
                "total_count": total_count,
                "rows": [
                    {
                        "issue_id": str(row[0]) if row[0] is not None else None,
                        "source": row[1],
                        "project_name": row[2],
                        "status": row[3],
                        "priority": row[4],
                        "clash_level": row[5],
                        "title": row[6],
                        "latest_comment": row[7],
                        "company": row[8],
                        "zone": row[9],
                        "location_root": row[10],
                        "location_building": row[11],
                        "location_level": row[12],
                        "created_at": row[13].isoformat() if row[13] else None,
                    }
                    for row in rows
                ],
                "as_of": as_of,
            }
    except Exception as e:
        logger.error("Error fetching issues table: %s", e)
        return {
            "page": page,
            "page_size": page_size,
            "total_count": 0,
            "rows": [],
        }

def get_revizto_issues_detail(
    project_uuid: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    location: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
    sort_by: str = "updated_at",
    sort_dir: str = "desc",
) -> Dict[str, Any]:
    """
    Paginated Revizto issue detail from mart.v_revizto_issues_detail.
    """
    sort_map = {
        "status": "status",
        "priority": "priority",
        "location": "location",
        "created_at": "created_at",
        "updated_at": "updated_at",
    }
    sort_column = sort_map.get(sort_by, "updated_at")
    sort_direction = "ASC" if sort_dir and sort_dir.lower() == "asc" else "DESC"
    offset = max(page - 1, 0) * page_size

    where_clauses = []
    params: List[Any] = []
    if project_uuid:
        where_clauses.append("projectUuid = ?")
        params.append(project_uuid)
    if status:
        where_clauses.append("LOWER(ISNULL(status,'')) = LOWER(?)")
        params.append(status)
    if priority:
        where_clauses.append("LOWER(ISNULL(priority,'')) = LOWER(?)")
        params.append(priority)
    if location:
        where_clauses.append("LOWER(ISNULL(location,'')) = LOWER(?)")
        params.append(location)
    where_sql = ""
    if where_clauses:
        where_sql = "WHERE " + " AND ".join(where_clauses)

    try:
        with get_db_connection(Config.WAREHOUSE_DB) as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT COUNT(*) FROM mart.v_revizto_issues_detail {where_sql}", tuple(params))
            total = int(cursor.fetchone()[0] or 0)

            cursor.execute(
                f"SELECT MAX(updated_at) FROM mart.v_revizto_issues_detail {where_sql}",
                tuple(params),
            )
            as_of_row = cursor.fetchone()
            as_of = as_of_row[0].isoformat() if as_of_row and as_of_row[0] else None

            cursor.execute(
                f"""
                SELECT
                    issueId,
                    projectUuid,
                    issue_uuid,
                    status,
                    priority,
                    title,
                    company,
                    location,
                    clash_level,
                    created_at,
                    updated_at,
                    tags_json,
                    latest_comment_text,
                    latest_comment_at
                FROM mart.v_revizto_issues_detail
                {where_sql}
                ORDER BY {sort_column} {sort_direction}
                OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
                """,
                tuple(params + [offset, page_size]),
            )
            items = []
            for row in cursor.fetchall():
                items.append(
                    {
                        "issue_id": row[0],
                        "project_uuid": str(row[1]) if row[1] is not None else None,
                        "issue_uuid": row[2],
                        "status": row[3],
                        "priority": row[4],
                        "title": row[5],
                        "company": row[6],
                        "location": row[7],
                        "clash_level": row[8],
                        "created_at": row[9],
                        "updated_at": row[10],
                        "tags_json": row[11],
                        "latest_comment_text": row[12],
                        "latest_comment_at": row[13],
                    }
                )

            return {"items": items, "total": total, "page": page, "page_size": page_size, "as_of": as_of}
    except Exception as exc:
        logger.error("Error fetching Revizto issues detail: %s", exc)
        return {"items": [], "total": 0, "page": page, "page_size": page_size, "error": str(exc)}


_TASK_NOTES_BASE_QUERY = f"""
    SELECT
        t.{S.Tasks.TASK_ID},
        t.{S.Tasks.TASK_NAME},
        t.{S.Tasks.PROJECT_ID},
        p.project_name,
        t.{S.Tasks.CYCLE_ID},
        t.{S.Tasks.TASK_DATE},
        t.{S.Tasks.TIME_START},
        t.{S.Tasks.TIME_END},
        t.{S.Tasks.TIME_SPENT_MINUTES},
        t.{S.Tasks.STATUS},
        t.{S.Tasks.ASSIGNED_TO},
        u.{S.Users.NAME} AS assigned_to_name,
        t.{S.Tasks.TASK_ITEMS},
        t.{S.Tasks.NOTES},
        t.{S.Tasks.CREATED_AT},
        t.{S.Tasks.UPDATED_AT}
    FROM {S.Tasks.TABLE} t
    LEFT JOIN Projects p ON t.{S.Tasks.PROJECT_ID} = p.project_id
    LEFT JOIN {S.Users.TABLE} u ON t.{S.Tasks.ASSIGNED_TO} = u.{S.Users.ID}
"""


def fetch_tasks_notes_view(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    project_id: Optional[int] = None,
    user_id: Optional[int] = None,
    limit: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Retrieve tasks tailored for the Tasks & Notes view with optional filters."""
    default_start = (datetime.utcnow() - timedelta(days=90)).date()
    where_clauses = ["ISNULL(t.status, 'active') <> 'archived'"]
    params: List[Any] = []

    if date_from:
        where_clauses.append(f"t.{S.Tasks.TASK_DATE} >= ?")
        params.append(date_from)
    if date_to:
        where_clauses.append(f"t.{S.Tasks.TASK_DATE} <= ?")
        params.append(date_to)
    if not date_from and not date_to:
        where_clauses.append(f"(t.{S.Tasks.TASK_DATE} IS NULL OR t.{S.Tasks.TASK_DATE} >= ?)")
        params.append(default_start)
    if project_id:
        where_clauses.append(f"t.{S.Tasks.PROJECT_ID} = ?")
        params.append(project_id)
    if user_id:
        where_clauses.append(f"t.{S.Tasks.ASSIGNED_TO} = ?")
        params.append(user_id)

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
    select_prefix = "SELECT"
    if limit:
        select_prefix = f"SELECT TOP {int(limit)}"

    query = f"""
        {select_prefix}
            t.{S.Tasks.TASK_ID},
            t.{S.Tasks.TASK_NAME},
            t.{S.Tasks.PROJECT_ID},
            p.project_name,
            t.{S.Tasks.CYCLE_ID},
            t.{S.Tasks.TASK_DATE},
            t.{S.Tasks.TIME_START},
            t.{S.Tasks.TIME_END},
            t.{S.Tasks.TIME_SPENT_MINUTES},
            t.{S.Tasks.STATUS},
            t.{S.Tasks.ASSIGNED_TO},
            u.{S.Users.NAME} AS assigned_to_name,
            t.{S.Tasks.TASK_ITEMS},
            t.{S.Tasks.NOTES},
            t.{S.Tasks.CREATED_AT},
            t.{S.Tasks.UPDATED_AT}
        FROM {S.Tasks.TABLE} t
        LEFT JOIN Projects p ON t.{S.Tasks.PROJECT_ID} = p.project_id
        LEFT JOIN {S.Users.TABLE} u ON t.{S.Tasks.ASSIGNED_TO} = u.{S.Users.ID}
        {where_sql}
        ORDER BY
            t.{S.Tasks.TASK_DATE} DESC,
            t.{S.Tasks.TIME_START} DESC,
            t.{S.Tasks.TASK_ID} DESC;
    """

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()

    return [_format_task_notes_row(row) for row in rows]


def get_task_notes_record(task_id: int) -> Optional[Dict[str, Any]]:
    """Fetch a single task with notes view fields."""
    query = f"""
        {_TASK_NOTES_BASE_QUERY}
        WHERE t.{S.Tasks.TASK_ID} = ?;
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (task_id,))
        row = cursor.fetchone()
    return _format_task_notes_row(row) if row else None


def insert_task_notes_record(payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Insert a new task record supporting notes view fields."""
    required_fields = [S.Tasks.TASK_NAME, S.Tasks.PROJECT_ID]
    for field in required_fields:
        if field not in payload or payload[field] in (None, ""):
            raise ValueError(f"{field} is required")

    status = payload.get(S.Tasks.STATUS) or "active"

    time_start = payload.get(S.Tasks.TIME_START)
    time_end = payload.get(S.Tasks.TIME_END)
    time_spent = payload.get(S.Tasks.TIME_SPENT_MINUTES)
    if time_spent is None:
        time_spent = _calculate_duration_minutes(time_start, time_end)

    task_items_value = payload.get(S.Tasks.TASK_ITEMS)
    if isinstance(task_items_value, list):
        task_items_value = json.dumps(task_items_value)
    elif task_items_value in (None, "", "null"):
        task_items_value = None
    else:
        task_items_value = str(task_items_value)

    task_date_value = _coerce_date_input(payload.get(S.Tasks.TASK_DATE))
    start_date_value = (
        _coerce_date_input(payload.get(S.Tasks.START_DATE))
        or task_date_value
        or datetime.utcnow().date()
    )
    end_date_value = _coerce_date_input(payload.get(S.Tasks.END_DATE)) or task_date_value

    columns = [
        S.Tasks.TASK_NAME,
        S.Tasks.PROJECT_ID,
        S.Tasks.CYCLE_ID,
        S.Tasks.START_DATE,
        S.Tasks.END_DATE,
        S.Tasks.TASK_DATE,
        S.Tasks.TIME_START,
        S.Tasks.TIME_END,
        S.Tasks.TIME_SPENT_MINUTES,
        S.Tasks.ASSIGNED_TO,
        S.Tasks.STATUS,
        S.Tasks.TASK_ITEMS,
        S.Tasks.NOTES,
    ]
    values = [
        payload.get(S.Tasks.TASK_NAME),
        payload.get(S.Tasks.PROJECT_ID),
        payload.get(S.Tasks.CYCLE_ID),
        start_date_value,
        end_date_value,
        task_date_value,
        _parse_time_input(time_start),
        _parse_time_input(time_end),
        time_spent,
        payload.get(S.Tasks.ASSIGNED_TO),
        status,
        task_items_value,
        payload.get(S.Tasks.NOTES),
    ]

    placeholders = ", ".join(["?"] * len(columns))
    column_sql = ", ".join(columns)

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            INSERT INTO {S.Tasks.TABLE} ({column_sql})
            OUTPUT INSERTED.{S.Tasks.TASK_ID}
            VALUES ({placeholders});
            """,
            values,
        )
        new_id = cursor.fetchone()[0]
        conn.commit()

    return get_task_notes_record(int(new_id))


def update_task_notes_record(task_id: int, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Update an existing task record and return the refreshed task."""
    if not updates:
        return get_task_notes_record(task_id)

    time_start = updates.get(S.Tasks.TIME_START)
    time_end = updates.get(S.Tasks.TIME_END)
    if S.Tasks.TIME_SPENT_MINUTES not in updates and (time_start or time_end):
        updates[S.Tasks.TIME_SPENT_MINUTES] = _calculate_duration_minutes(time_start, time_end)

    if S.Tasks.TASK_ITEMS in updates:
        items_value = updates[S.Tasks.TASK_ITEMS]
        if isinstance(items_value, list):
            updates[S.Tasks.TASK_ITEMS] = json.dumps(items_value)
        elif items_value in (None, "", "null"):
            updates[S.Tasks.TASK_ITEMS] = None
        else:
            updates[S.Tasks.TASK_ITEMS] = str(items_value)

    set_clauses = []
    params: List[Any] = []
    for column, value in updates.items():
        if column in (S.Tasks.TIME_START, S.Tasks.TIME_END):
            value = _parse_time_input(value)
        elif column in (S.Tasks.START_DATE, S.Tasks.END_DATE, S.Tasks.TASK_DATE):
            value = _coerce_date_input(value)
            if column == S.Tasks.START_DATE and value is None:
                value = datetime.utcnow().date()
        set_clauses.append(f"{column} = ?")
        params.append(value)

    set_clauses.append(f"{S.Tasks.UPDATED_AT} = ?")
    params.append(datetime.utcnow())
    params.append(task_id)

    sql = f"""
        UPDATE {S.Tasks.TABLE}
        SET {', '.join(set_clauses)}
        WHERE {S.Tasks.TASK_ID} = ?;
    """

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        conn.commit()

    return get_task_notes_record(task_id)


# --- User Assignment Management Functions ---

def assign_service_to_user(service_id, user_id):
    """Assign a project service to a specific user."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                UPDATE {S.ProjectServices.TABLE}
                SET {S.ProjectServices.ASSIGNED_USER_ID} = ?,
                    {S.ProjectServices.UPDATED_AT} = ?
                WHERE {S.ProjectServices.SERVICE_ID} = ?
                """,
                (user_id, datetime.utcnow(), service_id)
            )
            conn.commit()
            return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"Error assigning service to user: {e}")
        return False


def assign_review_to_user(review_id, user_id):
    """Assign a service review to a specific user."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                UPDATE {S.ServiceReviews.TABLE}
                SET {S.ServiceReviews.ASSIGNED_USER_ID} = ?
                WHERE {S.ServiceReviews.REVIEW_ID} = ?
                """,
                (user_id, review_id)
            )
            conn.commit()
            return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"Error assigning review to user: {e}")
        return False


def get_user_assignments(user_id):
    """Get all services and reviews assigned to a specific user."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get assigned services with project context
            cursor.execute(
                f"""
                SELECT 
                    ps.{S.ProjectServices.SERVICE_ID},
                    ps.{S.ProjectServices.SERVICE_NAME},
                    ps.{S.ProjectServices.SERVICE_CODE},
                    ps.{S.ProjectServices.STATUS},
                    p.{S.Projects.ID},
                    p.{S.Projects.NAME},
                    ps.{S.ProjectServices.PROGRESS_PCT}
                FROM {S.ProjectServices.TABLE} ps
                INNER JOIN {S.Projects.TABLE} p 
                    ON ps.{S.ProjectServices.PROJECT_ID} = p.{S.Projects.ID}
                WHERE ps.{S.ProjectServices.ASSIGNED_USER_ID} = ?
                ORDER BY ps.{S.ProjectServices.CREATED_AT} DESC
                """,
                (user_id,)
            )
            
            services = [dict(
                service_id=row[0],
                service_name=row[1],
                service_code=row[2],
                status=row[3],
                project_id=row[4],
                project_name=row[5],
                progress_pct=row[6]
            ) for row in cursor.fetchall()]
            
            # Get assigned reviews with service and project context
            cursor.execute(
                f"""
                SELECT 
                    sr.{S.ServiceReviews.REVIEW_ID},
                    sr.{S.ServiceReviews.CYCLE_NO},
                    sr.{S.ServiceReviews.STATUS},
                    sr.{S.ServiceReviews.DUE_DATE},
                    ps.{S.ProjectServices.SERVICE_NAME},
                    ps.{S.ProjectServices.SERVICE_ID},
                    p.{S.Projects.NAME},
                    p.{S.Projects.ID}
                FROM {S.ServiceReviews.TABLE} sr
                INNER JOIN {S.ProjectServices.TABLE} ps 
                    ON sr.{S.ServiceReviews.SERVICE_ID} = ps.{S.ProjectServices.SERVICE_ID}
                INNER JOIN {S.Projects.TABLE} p 
                    ON ps.{S.ProjectServices.PROJECT_ID} = p.{S.Projects.ID}
                WHERE sr.{S.ServiceReviews.ASSIGNED_USER_ID} = ?
                ORDER BY sr.{S.ServiceReviews.DUE_DATE} ASC
                """,
                (user_id,)
            )
            
            reviews = [dict(
                review_id=row[0],
                cycle_no=row[1],
                status=row[2],
                due_date=row[3].isoformat() if row[3] else None,
                service_name=row[4],
                service_id=row[5],
                project_name=row[6],
                project_id=row[7]
            ) for row in cursor.fetchall()]
            
            return {
                'services': services,
                'reviews': reviews,
                'summary': {
                    'total_services': len(services),
                    'total_reviews': len(reviews),
                    'active_reviews': len([r for r in reviews if r['status'] not in ['completed', 'cancelled']])
                }
            }
    except Exception as e:
        logger.error(f"Error getting user assignments: {e}")
        return {'services': [], 'reviews': [], 'summary': {}}


def reassign_user_work(from_user_id, to_user_id, project_id=None):
    """Reassign all services and reviews from one user to another."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Reassign services
            if project_id:
                cursor.execute(
                    f"""
                    UPDATE {S.ProjectServices.TABLE}
                    SET {S.ProjectServices.ASSIGNED_USER_ID} = ?,
                        {S.ProjectServices.UPDATED_AT} = ?
                    WHERE {S.ProjectServices.ASSIGNED_USER_ID} = ?
                      AND {S.ProjectServices.PROJECT_ID} = ?
                    """,
                    (to_user_id, datetime.utcnow(), from_user_id, project_id)
                )
            else:
                cursor.execute(
                    f"""
                    UPDATE {S.ProjectServices.TABLE}
                    SET {S.ProjectServices.ASSIGNED_USER_ID} = ?,
                        {S.ProjectServices.UPDATED_AT} = ?
                    WHERE {S.ProjectServices.ASSIGNED_USER_ID} = ?
                    """,
                    (to_user_id, datetime.utcnow(), from_user_id)
                )
            
            services_reassigned = cursor.rowcount
            
            # Reassign reviews
            if project_id:
                cursor.execute(
                    f"""
                    UPDATE {S.ServiceReviews.TABLE}
                    SET {S.ServiceReviews.ASSIGNED_USER_ID} = ?
                    WHERE {S.ServiceReviews.ASSIGNED_USER_ID} = ?
                      AND {S.ServiceReviews.SERVICE_ID} IN (
                          SELECT {S.ProjectServices.SERVICE_ID}
                          FROM {S.ProjectServices.TABLE}
                          WHERE {S.ProjectServices.PROJECT_ID} = ?
                      )
                    """,
                    (to_user_id, from_user_id, project_id)
                )
            else:
                cursor.execute(
                    f"""
                    UPDATE {S.ServiceReviews.TABLE}
                    SET {S.ServiceReviews.ASSIGNED_USER_ID} = ?
                    WHERE {S.ServiceReviews.ASSIGNED_USER_ID} = ?
                    """,
                    (to_user_id, from_user_id)
                )
            
            reviews_reassigned = cursor.rowcount
            conn.commit()
            
            return {
                'services_reassigned': services_reassigned,
                'reviews_reassigned': reviews_reassigned
            }
    except Exception as e:
        logger.error(f"Error reassigning user work: {e}")
        return {'services_reassigned': 0, 'reviews_reassigned': 0}


def get_project_lead_user_id(project_id):
    """Get the user_id of the project's internal lead."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT u.{S.Users.ID}
                FROM {S.Projects.TABLE} p
                INNER JOIN {S.Users.TABLE} u 
                    ON p.{S.Projects.INTERNAL_LEAD} = u.{S.Users.NAME}
                WHERE p.{S.Projects.ID} = ?
                """,
                (project_id,)
            )
            row = cursor.fetchone()
            return row[0] if row else None
    except Exception as e:
        logger.error(f"Error getting project lead user ID: {e}")
        return None


def get_user_workload_summary():
    """Get workload summary for all users."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT 
                    u.user_id,
                    u.name,
                    u.email,
                    u.role,
                    COUNT(DISTINCT ps.service_id) AS assigned_services,
                    COUNT(DISTINCT sr.review_id) AS assigned_reviews,
                    SUM(CASE 
                        WHEN sr.status NOT IN ('completed', 'cancelled') 
                        THEN 1 ELSE 0 
                    END) AS active_reviews,
                    SUM(CASE 
                        WHEN sr.status NOT IN ('completed', 'cancelled') 
                        AND sr.due_date < GETDATE() 
                        THEN 1 ELSE 0 
                    END) AS overdue_reviews,
                    COUNT(DISTINCT ps.project_id) AS projects
                FROM users u
                LEFT JOIN ProjectServices ps ON u.user_id = ps.assigned_user_id
                LEFT JOIN ServiceReviews sr ON u.user_id = sr.assigned_user_id
                GROUP BY u.user_id, u.name, u.email, u.role
                HAVING COUNT(DISTINCT ps.service_id) > 0 
                    OR COUNT(DISTINCT sr.review_id) > 0
                ORDER BY active_reviews DESC, assigned_reviews DESC
                """
            )
            
            return [dict(
                user_id=row[0],
                name=row[1],
                email=row[2],
                role=row[3],
                assigned_services=row[4] or 0,
                assigned_reviews=row[5] or 0,
                active_reviews=row[6] or 0,
                overdue_reviews=row[7] or 0,
                projects=row[8] or 0
            ) for row in cursor.fetchall()]
    except Exception as e:
        logger.error(f"Error getting user workload summary: {e}")
        return []


# --- User Management Functions ---

def get_all_users():
    """Fetch all users with full details."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT {S.Users.ID}, {S.Users.NAME}, {S.Users.ROLE}, 
                       {S.Users.EMAIL}, {S.Users.CREATED_AT}
                FROM {S.Users.TABLE}
                ORDER BY {S.Users.NAME};
                """
            )
            users = [dict(
                user_id=row[0],
                name=row[1],
                role=row[2],
                email=row[3],
                created_at=row[4].isoformat() if row[4] else None
            ) for row in cursor.fetchall()]
            return users
    except Exception as e:
        logger.error(f"Error fetching all users: {e}")
        return []


def create_user(name, role, email):
    """Create a new user."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                INSERT INTO {S.Users.TABLE} (
                    {S.Users.NAME}, {S.Users.ROLE}, {S.Users.EMAIL}, {S.Users.CREATED_AT}
                ) VALUES (?, ?, ?, ?);
                """,
                (name, role, email, datetime.utcnow())
            )
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        return False


def update_user(user_id, name=None, role=None, email=None):
    """Update an existing user."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            update_fields = {}
            
            if name is not None:
                update_fields[S.Users.NAME] = name
            if role is not None:
                update_fields[S.Users.ROLE] = role
            if email is not None:
                update_fields[S.Users.EMAIL] = email
            
            if not update_fields:
                return False
            
            set_clause = ', '.join([f"{field} = ?" for field in update_fields.keys()])
            values = list(update_fields.values()) + [user_id]
            
            cursor.execute(
                f"UPDATE {S.Users.TABLE} SET {set_clause} WHERE {S.Users.ID} = ?",
                values
            )
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        return False


def delete_user(user_id):
    """Delete a user."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"DELETE FROM {S.Users.TABLE} WHERE {S.Users.ID} = ?",
                (user_id,)
            )
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"Error deleting user: {e}")
        return False


def archive_task_record(task_id: int) -> bool:
    """Soft-delete a task by marking it archived."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            UPDATE {S.Tasks.TABLE}
            SET {S.Tasks.STATUS} = 'archived',
                {S.Tasks.UPDATED_AT} = ?
            WHERE {S.Tasks.TASK_ID} = ?;
            """,
            (datetime.utcnow(), task_id),
        )
        conn.commit()
        return cursor.rowcount > 0


def delete_task_record(task_id: int) -> bool:
    """Hard delete a task record."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"DELETE FROM {S.Tasks.TABLE} WHERE {S.Tasks.TASK_ID} = ?;",
            (task_id,),
        )
        conn.commit()
        return cursor.rowcount > 0


def toggle_task_item_completion(task_id: int, item_index: int) -> Optional[Dict[str, Any]]:
    """Flip the completion flag on a specific task item."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT {S.Tasks.TASK_ITEMS} FROM {S.Tasks.TABLE} WHERE {S.Tasks.TASK_ID} = ?;",
            (task_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None

        task_items_raw = row[0]
        items: List[Any] = []
        if task_items_raw:
            try:
                parsed = json.loads(task_items_raw)
                if isinstance(parsed, list):
                    items = parsed
            except (ValueError, TypeError):
                logger.warning("Unable to parse task_items JSON for task_id=%s", task_id)

        if item_index < 0 or item_index >= len(items):
            raise IndexError("Task item index out of range")

        current_item = items[item_index]
        if isinstance(current_item, dict):
            current_item['completed'] = not bool(current_item.get('completed'))
        else:
            items[item_index] = {'label': current_item, 'completed': True}

        cursor.execute(
            f"""
            UPDATE {S.Tasks.TABLE}
            SET {S.Tasks.TASK_ITEMS} = ?, {S.Tasks.UPDATED_AT} = ?
            WHERE {S.Tasks.TASK_ID} = ?;
            """,
            (json.dumps(items), datetime.utcnow(), task_id),
        )
        conn.commit()

    return get_task_notes_record(task_id)


# ===================== Bid Management Functions =====================

def get_bids(status: Optional[str] = None, project_id: Optional[int] = None, client_id: Optional[int] = None):
    """Fetch bids with optional filters and joined names."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            where_clauses = []
            params: List[Any] = []

            if status:
                where_clauses.append(f"b.{S.Bids.STATUS} = ?")
                params.append(status)
            if project_id is not None:
                where_clauses.append(f"b.{S.Bids.PROJECT_ID} = ?")
                params.append(project_id)
            if client_id is not None:
                where_clauses.append(f"b.{S.Bids.CLIENT_ID} = ?")
                params.append(client_id)

            where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

            cursor.execute(
                f"""
                SELECT
                    b.{S.Bids.BID_ID},
                    b.{S.Bids.PROJECT_ID},
                    b.{S.Bids.CLIENT_ID},
                    b.{S.Bids.BID_NAME},
                    b.{S.Bids.BID_TYPE},
                    b.{S.Bids.STATUS},
                    b.{S.Bids.PROBABILITY},
                    b.{S.Bids.OWNER_USER_ID},
                    b.{S.Bids.CURRENCY_CODE},
                    b.{S.Bids.STAGE_FRAMEWORK},
                    b.{S.Bids.VALIDITY_DAYS},
                    b.{S.Bids.GST_INCLUDED},
                    b.{S.Bids.PI_NOTES},
                    b.{S.Bids.CREATED_AT},
                    b.{S.Bids.UPDATED_AT},
                    c.{S.Clients.CLIENT_NAME},
                    u.{S.Users.NAME},
                    p.{S.Projects.NAME}
                FROM {S.Bids.TABLE} b
                LEFT JOIN {S.Clients.TABLE} c ON b.{S.Bids.CLIENT_ID} = c.{S.Clients.CLIENT_ID}
                LEFT JOIN {S.Users.TABLE} u ON b.{S.Bids.OWNER_USER_ID} = u.{S.Users.ID}
                LEFT JOIN {S.Projects.TABLE} p ON b.{S.Bids.PROJECT_ID} = p.{S.Projects.ID}
                {where_sql}
                ORDER BY b.{S.Bids.UPDATED_AT} DESC, b.{S.Bids.BID_ID} DESC
                """,
                params,
            )
            rows = cursor.fetchall()
            return [
                {
                    "bid_id": row[0],
                    "project_id": row[1],
                    "client_id": row[2],
                    "bid_name": row[3],
                    "bid_type": row[4],
                    "status": row[5],
                    "probability": row[6],
                    "owner_user_id": row[7],
                    "currency_code": row[8],
                    "stage_framework": row[9],
                    "validity_days": row[10],
                    "gst_included": bool(row[11]) if row[11] is not None else None,
                    "pi_notes": row[12],
                    "created_at": row[13],
                    "updated_at": row[14],
                    "client_name": row[15],
                    "owner_name": row[16],
                    "project_name": row[17],
                }
                for row in rows
            ]
    except Exception as e:
        logger.error(f"Error fetching bids: {e}")
        return []


def get_bid(bid_id: int):
    """Fetch a single bid by ID."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT
                    b.{S.Bids.BID_ID},
                    b.{S.Bids.PROJECT_ID},
                    b.{S.Bids.CLIENT_ID},
                    b.{S.Bids.BID_NAME},
                    b.{S.Bids.BID_TYPE},
                    b.{S.Bids.STATUS},
                    b.{S.Bids.PROBABILITY},
                    b.{S.Bids.OWNER_USER_ID},
                    b.{S.Bids.CURRENCY_CODE},
                    b.{S.Bids.STAGE_FRAMEWORK},
                    b.{S.Bids.VALIDITY_DAYS},
                    b.{S.Bids.GST_INCLUDED},
                    b.{S.Bids.PI_NOTES},
                    b.{S.Bids.CREATED_AT},
                    b.{S.Bids.UPDATED_AT},
                    c.{S.Clients.CLIENT_NAME},
                    u.{S.Users.NAME},
                    p.{S.Projects.NAME}
                FROM {S.Bids.TABLE} b
                LEFT JOIN {S.Clients.TABLE} c ON b.{S.Bids.CLIENT_ID} = c.{S.Clients.CLIENT_ID}
                LEFT JOIN {S.Users.TABLE} u ON b.{S.Bids.OWNER_USER_ID} = u.{S.Users.ID}
                LEFT JOIN {S.Projects.TABLE} p ON b.{S.Bids.PROJECT_ID} = p.{S.Projects.ID}
                WHERE b.{S.Bids.BID_ID} = ?
                """,
                (bid_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return {
                "bid_id": row[0],
                "project_id": row[1],
                "client_id": row[2],
                "bid_name": row[3],
                "bid_type": row[4],
                "status": row[5],
                "probability": row[6],
                "owner_user_id": row[7],
                "currency_code": row[8],
                "stage_framework": row[9],
                "validity_days": row[10],
                "gst_included": bool(row[11]) if row[11] is not None else None,
                "pi_notes": row[12],
                "created_at": row[13],
                "updated_at": row[14],
                "client_name": row[15],
                "owner_name": row[16],
                "project_name": row[17],
            }
    except Exception as e:
        logger.error(f"Error fetching bid {bid_id}: {e}")
        return None


def create_bid(payload: Dict[str, Any]):
    """Create a bid and return the full record."""
    columns = [
        S.Bids.PROJECT_ID,
        S.Bids.CLIENT_ID,
        S.Bids.BID_NAME,
        S.Bids.BID_TYPE,
        S.Bids.STATUS,
        S.Bids.PROBABILITY,
        S.Bids.OWNER_USER_ID,
        S.Bids.CURRENCY_CODE,
        S.Bids.STAGE_FRAMEWORK,
        S.Bids.VALIDITY_DAYS,
        S.Bids.GST_INCLUDED,
        S.Bids.PI_NOTES,
    ]
    values = [
        payload.get(S.Bids.PROJECT_ID),
        payload.get(S.Bids.CLIENT_ID),
        payload.get(S.Bids.BID_NAME),
        payload.get(S.Bids.BID_TYPE),
        payload.get(S.Bids.STATUS),
        payload.get(S.Bids.PROBABILITY),
        payload.get(S.Bids.OWNER_USER_ID),
        payload.get(S.Bids.CURRENCY_CODE),
        payload.get(S.Bids.STAGE_FRAMEWORK),
        payload.get(S.Bids.VALIDITY_DAYS),
        int(bool(payload.get(S.Bids.GST_INCLUDED))) if payload.get(S.Bids.GST_INCLUDED) is not None else None,
        payload.get(S.Bids.PI_NOTES),
    ]

    placeholders = ", ".join(["?"] * len(values))
    column_sql = ", ".join(columns)

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                INSERT INTO {S.Bids.TABLE} ({column_sql})
                OUTPUT INSERTED.{S.Bids.BID_ID}
                VALUES ({placeholders});
                """,
                values,
            )
            bid_id = cursor.fetchone()[0]
            conn.commit()
            return get_bid(int(bid_id))
    except Exception as e:
        logger.error(f"Error creating bid: {e}")
        return None


def update_bid(bid_id: int, payload: Dict[str, Any]) -> bool:
    """Update a bid."""
    allowed_fields = [
        S.Bids.PROJECT_ID,
        S.Bids.CLIENT_ID,
        S.Bids.BID_NAME,
        S.Bids.BID_TYPE,
        S.Bids.STATUS,
        S.Bids.PROBABILITY,
        S.Bids.OWNER_USER_ID,
        S.Bids.CURRENCY_CODE,
        S.Bids.STAGE_FRAMEWORK,
        S.Bids.VALIDITY_DAYS,
        S.Bids.GST_INCLUDED,
        S.Bids.PI_NOTES,
    ]
    updates = []
    params = []
    for field in allowed_fields:
        if field in payload:
            value = payload.get(field)
            if field == S.Bids.GST_INCLUDED and value is not None:
                value = int(bool(value))
            updates.append(f"{field} = ?")
            params.append(value)

    if not updates:
        return False

    updates.append(f"{S.Bids.UPDATED_AT} = SYSDATETIME()")
    params.append(bid_id)

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                UPDATE {S.Bids.TABLE}
                SET {', '.join(updates)}
                WHERE {S.Bids.BID_ID} = ?;
                """,
                params,
            )
            conn.commit()
            return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"Error updating bid {bid_id}: {e}")
        return False


def archive_bid(bid_id: int) -> bool:
    """Soft delete a bid by marking it archived."""
    return update_bid(bid_id, {S.Bids.STATUS: "ARCHIVED"})


def get_bid_sections(bid_id: int):
    """Return sections for a bid."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT {S.BidSections.BID_SECTION_ID},
                       {S.BidSections.SECTION_KEY},
                       {S.BidSections.CONTENT_JSON},
                       {S.BidSections.SORT_ORDER}
                FROM {S.BidSections.TABLE}
                WHERE {S.BidSections.BID_ID} = ?
                ORDER BY {S.BidSections.SORT_ORDER}, {S.BidSections.BID_SECTION_ID}
                """,
                (bid_id,),
            )
            return [
                {
                    "bid_section_id": row[0],
                    "section_key": row[1],
                    "content_json": row[2],
                    "sort_order": row[3],
                }
                for row in cursor.fetchall()
            ]
    except Exception as e:
        logger.error(f"Error fetching bid sections for bid {bid_id}: {e}")
        return []


def replace_bid_sections(bid_id: int, sections: List[Dict[str, Any]]) -> bool:
    """Replace bid sections with the provided list."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"DELETE FROM {S.BidSections.TABLE} WHERE {S.BidSections.BID_ID} = ?",
                (bid_id,),
            )
            rows = []
            for section in sections:
                content = section.get("content_json")
                if content is not None and not isinstance(content, str):
                    content = json.dumps(content)
                rows.append(
                    (
                        bid_id,
                        section.get("section_key"),
                        content,
                        section.get("sort_order", 0),
                    )
                )
            if rows:
                cursor.executemany(
                    f"""
                    INSERT INTO {S.BidSections.TABLE} (
                        {S.BidSections.BID_ID},
                        {S.BidSections.SECTION_KEY},
                        {S.BidSections.CONTENT_JSON},
                        {S.BidSections.SORT_ORDER}
                    ) VALUES (?, ?, ?, ?)
                    """,
                    rows,
                )
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"Error replacing bid sections for bid {bid_id}: {e}")
        return False


def get_bid_scope_items(bid_id: int):
    """Return scope items for a bid."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT {S.BidScopeItems.SCOPE_ITEM_ID},
                       {S.BidScopeItems.SERVICE_CODE},
                       {S.BidScopeItems.TITLE},
                       {S.BidScopeItems.DESCRIPTION},
                       {S.BidScopeItems.STAGE_NAME},
                       {S.BidScopeItems.DELIVERABLES_JSON},
                       {S.BidScopeItems.INCLUDED_QTY},
                       {S.BidScopeItems.UNIT},
                       {S.BidScopeItems.UNIT_RATE},
                       {S.BidScopeItems.LUMP_SUM},
                       {S.BidScopeItems.IS_OPTIONAL},
                       {S.BidScopeItems.OPTION_GROUP},
                       {S.BidScopeItems.SORT_ORDER}
                FROM {S.BidScopeItems.TABLE}
                WHERE {S.BidScopeItems.BID_ID} = ?
                ORDER BY {S.BidScopeItems.SORT_ORDER}, {S.BidScopeItems.SCOPE_ITEM_ID}
                """,
                (bid_id,),
            )
            return [
                {
                    "scope_item_id": row[0],
                    "service_code": row[1],
                    "title": row[2],
                    "description": row[3],
                    "stage_name": row[4],
                    "deliverables_json": row[5],
                    "included_qty": row[6],
                    "unit": row[7],
                    "unit_rate": row[8],
                    "lump_sum": row[9],
                    "is_optional": bool(row[10]) if row[10] is not None else False,
                    "option_group": row[11],
                    "sort_order": row[12],
                }
                for row in cursor.fetchall()
            ]
    except Exception as e:
        logger.error(f"Error fetching bid scope items for bid {bid_id}: {e}")
        return []


def create_bid_scope_item(bid_id: int, payload: Dict[str, Any]):
    """Create a scope item for a bid."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                INSERT INTO {S.BidScopeItems.TABLE} (
                    {S.BidScopeItems.BID_ID},
                    {S.BidScopeItems.SERVICE_CODE},
                    {S.BidScopeItems.TITLE},
                    {S.BidScopeItems.DESCRIPTION},
                    {S.BidScopeItems.STAGE_NAME},
                    {S.BidScopeItems.DELIVERABLES_JSON},
                    {S.BidScopeItems.INCLUDED_QTY},
                    {S.BidScopeItems.UNIT},
                    {S.BidScopeItems.UNIT_RATE},
                    {S.BidScopeItems.LUMP_SUM},
                    {S.BidScopeItems.IS_OPTIONAL},
                    {S.BidScopeItems.OPTION_GROUP},
                    {S.BidScopeItems.SORT_ORDER}
                )
                OUTPUT INSERTED.{S.BidScopeItems.SCOPE_ITEM_ID}
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    bid_id,
                    payload.get(S.BidScopeItems.SERVICE_CODE),
                    payload.get(S.BidScopeItems.TITLE),
                    payload.get(S.BidScopeItems.DESCRIPTION),
                    payload.get(S.BidScopeItems.STAGE_NAME),
                    payload.get(S.BidScopeItems.DELIVERABLES_JSON),
                    payload.get(S.BidScopeItems.INCLUDED_QTY),
                    payload.get(S.BidScopeItems.UNIT),
                    payload.get(S.BidScopeItems.UNIT_RATE),
                    payload.get(S.BidScopeItems.LUMP_SUM),
                    int(bool(payload.get(S.BidScopeItems.IS_OPTIONAL))) if payload.get(S.BidScopeItems.IS_OPTIONAL) is not None else 0,
                    payload.get(S.BidScopeItems.OPTION_GROUP),
                    payload.get(S.BidScopeItems.SORT_ORDER, 0),
                ),
            )
            scope_item_id = cursor.fetchone()[0]
            conn.commit()
            return scope_item_id
    except Exception as e:
        logger.error(f"Error creating bid scope item for bid {bid_id}: {e}")
        return None


def update_bid_scope_item(scope_item_id: int, payload: Dict[str, Any]) -> bool:
    """Update a scope item."""
    allowed_fields = [
        S.BidScopeItems.SERVICE_CODE,
        S.BidScopeItems.TITLE,
        S.BidScopeItems.DESCRIPTION,
        S.BidScopeItems.STAGE_NAME,
        S.BidScopeItems.DELIVERABLES_JSON,
        S.BidScopeItems.INCLUDED_QTY,
        S.BidScopeItems.UNIT,
        S.BidScopeItems.UNIT_RATE,
        S.BidScopeItems.LUMP_SUM,
        S.BidScopeItems.IS_OPTIONAL,
        S.BidScopeItems.OPTION_GROUP,
        S.BidScopeItems.SORT_ORDER,
    ]
    updates = []
    params = []
    for field in allowed_fields:
        if field in payload:
            value = payload.get(field)
            if field == S.BidScopeItems.IS_OPTIONAL and value is not None:
                value = int(bool(value))
            updates.append(f"{field} = ?")
            params.append(value)
    if not updates:
        return False
    params.append(scope_item_id)
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                UPDATE {S.BidScopeItems.TABLE}
                SET {', '.join(updates)}
                WHERE {S.BidScopeItems.SCOPE_ITEM_ID} = ?;
                """,
                params,
            )
            conn.commit()
            return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"Error updating bid scope item {scope_item_id}: {e}")
        return False


def delete_bid_scope_item(scope_item_id: int) -> bool:
    """Delete a scope item."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"DELETE FROM {S.BidScopeItems.TABLE} WHERE {S.BidScopeItems.SCOPE_ITEM_ID} = ?",
                (scope_item_id,),
            )
            conn.commit()
            return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"Error deleting bid scope item {scope_item_id}: {e}")
        return False


def get_bid_program_stages(bid_id: int):
    """Return program stages for a bid."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT {S.BidProgramStages.PROGRAM_STAGE_ID},
                       {S.BidProgramStages.STAGE_NAME},
                       {S.BidProgramStages.PLANNED_START},
                       {S.BidProgramStages.PLANNED_END},
                       {S.BidProgramStages.CADENCE},
                       {S.BidProgramStages.CYCLES_PLANNED},
                       {S.BidProgramStages.SORT_ORDER}
                FROM {S.BidProgramStages.TABLE}
                WHERE {S.BidProgramStages.BID_ID} = ?
                ORDER BY {S.BidProgramStages.SORT_ORDER}, {S.BidProgramStages.PROGRAM_STAGE_ID}
                """,
                (bid_id,),
            )
            return [
                {
                    "program_stage_id": row[0],
                    "stage_name": row[1],
                    "planned_start": row[2],
                    "planned_end": row[3],
                    "cadence": row[4],
                    "cycles_planned": row[5],
                    "sort_order": row[6],
                }
                for row in cursor.fetchall()
            ]
    except Exception as e:
        logger.error(f"Error fetching bid program stages for bid {bid_id}: {e}")
        return []


def create_bid_program_stage(bid_id: int, payload: Dict[str, Any]):
    """Create a program stage for a bid."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                INSERT INTO {S.BidProgramStages.TABLE} (
                    {S.BidProgramStages.BID_ID},
                    {S.BidProgramStages.STAGE_NAME},
                    {S.BidProgramStages.PLANNED_START},
                    {S.BidProgramStages.PLANNED_END},
                    {S.BidProgramStages.CADENCE},
                    {S.BidProgramStages.CYCLES_PLANNED},
                    {S.BidProgramStages.SORT_ORDER}
                )
                OUTPUT INSERTED.{S.BidProgramStages.PROGRAM_STAGE_ID}
                VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    bid_id,
                    payload.get(S.BidProgramStages.STAGE_NAME),
                    payload.get(S.BidProgramStages.PLANNED_START),
                    payload.get(S.BidProgramStages.PLANNED_END),
                    payload.get(S.BidProgramStages.CADENCE),
                    payload.get(S.BidProgramStages.CYCLES_PLANNED),
                    payload.get(S.BidProgramStages.SORT_ORDER, 0),
                ),
            )
            stage_id = cursor.fetchone()[0]
            conn.commit()
            return stage_id
    except Exception as e:
        logger.error(f"Error creating bid program stage for bid {bid_id}: {e}")
        return None


def update_bid_program_stage(program_stage_id: int, payload: Dict[str, Any]) -> bool:
    """Update a program stage."""
    allowed_fields = [
        S.BidProgramStages.STAGE_NAME,
        S.BidProgramStages.PLANNED_START,
        S.BidProgramStages.PLANNED_END,
        S.BidProgramStages.CADENCE,
        S.BidProgramStages.CYCLES_PLANNED,
        S.BidProgramStages.SORT_ORDER,
    ]
    updates = []
    params = []
    for field in allowed_fields:
        if field in payload:
            updates.append(f"{field} = ?")
            params.append(payload.get(field))
    if not updates:
        return False
    params.append(program_stage_id)
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                UPDATE {S.BidProgramStages.TABLE}
                SET {', '.join(updates)}
                WHERE {S.BidProgramStages.PROGRAM_STAGE_ID} = ?;
                """,
                params,
            )
            conn.commit()
            return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"Error updating bid program stage {program_stage_id}: {e}")
        return False


def delete_bid_program_stage(program_stage_id: int) -> bool:
    """Delete a program stage."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"DELETE FROM {S.BidProgramStages.TABLE} WHERE {S.BidProgramStages.PROGRAM_STAGE_ID} = ?",
                (program_stage_id,),
            )
            conn.commit()
            return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"Error deleting bid program stage {program_stage_id}: {e}")
        return False


def get_bid_billing_schedule(bid_id: int):
    """Return billing schedule lines for a bid."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                SELECT {S.BidBillingSchedule.BILLING_LINE_ID},
                       {S.BidBillingSchedule.PERIOD_START},
                       {S.BidBillingSchedule.PERIOD_END},
                       {S.BidBillingSchedule.AMOUNT},
                       {S.BidBillingSchedule.NOTES},
                       {S.BidBillingSchedule.SORT_ORDER}
                FROM {S.BidBillingSchedule.TABLE}
                WHERE {S.BidBillingSchedule.BID_ID} = ?
                ORDER BY {S.BidBillingSchedule.SORT_ORDER}, {S.BidBillingSchedule.BILLING_LINE_ID}
                """,
                (bid_id,),
            )
            return [
                {
                    "billing_line_id": row[0],
                    "period_start": row[1],
                    "period_end": row[2],
                    "amount": row[3],
                    "notes": row[4],
                    "sort_order": row[5],
                }
                for row in cursor.fetchall()
            ]
    except Exception as e:
        logger.error(f"Error fetching bid billing schedule for bid {bid_id}: {e}")
        return []


def create_bid_billing_line(bid_id: int, payload: Dict[str, Any]):
    """Create a billing schedule line for a bid."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                INSERT INTO {S.BidBillingSchedule.TABLE} (
                    {S.BidBillingSchedule.BID_ID},
                    {S.BidBillingSchedule.PERIOD_START},
                    {S.BidBillingSchedule.PERIOD_END},
                    {S.BidBillingSchedule.AMOUNT},
                    {S.BidBillingSchedule.NOTES},
                    {S.BidBillingSchedule.SORT_ORDER}
                )
                OUTPUT INSERTED.{S.BidBillingSchedule.BILLING_LINE_ID}
                VALUES (?, ?, ?, ?, ?, ?);
                """,
                (
                    bid_id,
                    payload.get(S.BidBillingSchedule.PERIOD_START),
                    payload.get(S.BidBillingSchedule.PERIOD_END),
                    payload.get(S.BidBillingSchedule.AMOUNT),
                    payload.get(S.BidBillingSchedule.NOTES),
                    payload.get(S.BidBillingSchedule.SORT_ORDER, 0),
                ),
            )
            line_id = cursor.fetchone()[0]
            conn.commit()
            return line_id
    except Exception as e:
        logger.error(f"Error creating bid billing schedule line for bid {bid_id}: {e}")
        return None


def update_bid_billing_line(billing_line_id: int, payload: Dict[str, Any]) -> bool:
    """Update a billing schedule line."""
    allowed_fields = [
        S.BidBillingSchedule.PERIOD_START,
        S.BidBillingSchedule.PERIOD_END,
        S.BidBillingSchedule.AMOUNT,
        S.BidBillingSchedule.NOTES,
        S.BidBillingSchedule.SORT_ORDER,
    ]
    updates = []
    params = []
    for field in allowed_fields:
        if field in payload:
            updates.append(f"{field} = ?")
            params.append(payload.get(field))
    if not updates:
        return False
    params.append(billing_line_id)
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                UPDATE {S.BidBillingSchedule.TABLE}
                SET {', '.join(updates)}
                WHERE {S.BidBillingSchedule.BILLING_LINE_ID} = ?;
                """,
                params,
            )
            conn.commit()
            return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"Error updating bid billing schedule line {billing_line_id}: {e}")
        return False


def delete_bid_billing_line(billing_line_id: int) -> bool:
    """Delete a billing schedule line."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"DELETE FROM {S.BidBillingSchedule.TABLE} WHERE {S.BidBillingSchedule.BILLING_LINE_ID} = ?",
                (billing_line_id,),
            )
            conn.commit()
            return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"Error deleting bid billing schedule line {billing_line_id}: {e}")
        return False


def create_bid_variation(payload: Dict[str, Any]):
    """Create a bid variation."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"""
                INSERT INTO {S.BidVariations.TABLE} (
                    {S.BidVariations.PROJECT_ID},
                    {S.BidVariations.BID_ID},
                    {S.BidVariations.TITLE},
                    {S.BidVariations.DESCRIPTION},
                    {S.BidVariations.BASELINE_CONTRACT_VALUE},
                    {S.BidVariations.REMAINING_VALUE},
                    {S.BidVariations.PROPOSED_CHANGE_VALUE},
                    {S.BidVariations.STATUS}
                )
                OUTPUT INSERTED.{S.BidVariations.VARIATION_ID}
                VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    payload.get(S.BidVariations.PROJECT_ID),
                    payload.get(S.BidVariations.BID_ID),
                    payload.get(S.BidVariations.TITLE),
                    payload.get(S.BidVariations.DESCRIPTION),
                    payload.get(S.BidVariations.BASELINE_CONTRACT_VALUE),
                    payload.get(S.BidVariations.REMAINING_VALUE),
                    payload.get(S.BidVariations.PROPOSED_CHANGE_VALUE),
                    payload.get(S.BidVariations.STATUS),
                ),
            )
            variation_id = cursor.fetchone()[0]
            conn.commit()
            return variation_id
    except Exception as e:
        logger.error(f"Error creating bid variation: {e}")
        return None


def list_bid_variations(project_id: Optional[int] = None, bid_id: Optional[int] = None):
    """List variations filtered by project or bid."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            where = []
            params: List[Any] = []
            if project_id is not None:
                where.append(f"{S.BidVariations.PROJECT_ID} = ?")
                params.append(project_id)
            if bid_id is not None:
                where.append(f"{S.BidVariations.BID_ID} = ?")
                params.append(bid_id)
            where_sql = f"WHERE {' AND '.join(where)}" if where else ""
            cursor.execute(
                f"""
                SELECT {S.BidVariations.VARIATION_ID},
                       {S.BidVariations.PROJECT_ID},
                       {S.BidVariations.BID_ID},
                       {S.BidVariations.TITLE},
                       {S.BidVariations.DESCRIPTION},
                       {S.BidVariations.BASELINE_CONTRACT_VALUE},
                       {S.BidVariations.REMAINING_VALUE},
                       {S.BidVariations.PROPOSED_CHANGE_VALUE},
                       {S.BidVariations.STATUS},
                       {S.BidVariations.CREATED_AT},
                       {S.BidVariations.UPDATED_AT}
                FROM {S.BidVariations.TABLE}
                {where_sql}
                ORDER BY {S.BidVariations.CREATED_AT} DESC, {S.BidVariations.VARIATION_ID} DESC
                """,
                params,
            )
            return [
                {
                    "variation_id": row[0],
                    "project_id": row[1],
                    "bid_id": row[2],
                    "title": row[3],
                    "description": row[4],
                    "baseline_contract_value": row[5],
                    "remaining_value": row[6],
                    "proposed_change_value": row[7],
                    "status": row[8],
                    "created_at": row[9],
                    "updated_at": row[10],
                }
                for row in cursor.fetchall()
            ]
    except Exception as e:
        logger.error(f"Error listing bid variations: {e}")
        return []


def _coerce_int(value: Any) -> Optional[int]:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _project_payload_to_columns(payload: Dict[str, Any], fallback_client_id: Optional[int] = None):
    """Convert project payload into insert columns and values."""
    if not payload:
        payload = {}
    project_name = payload.get("project_name") or payload.get("name")
    if not project_name:
        return None, None

    columns = [S.Projects.NAME]
    values = [project_name]

    client_id = payload.get("client_id", fallback_client_id)
    if client_id is not None:
        columns.append(S.Projects.CLIENT_ID)
        values.append(_coerce_int(client_id))

    status = payload.get("status")
    if status:
        columns.append(S.Projects.STATUS)
        values.append(status)

    priority = payload.get("priority")
    if priority is not None:
        columns.append(S.Projects.PRIORITY)
        values.append(priority)

    start_date = payload.get("start_date")
    if start_date:
        columns.append(S.Projects.START_DATE)
        values.append(start_date)

    end_date = payload.get("end_date")
    if end_date:
        columns.append(S.Projects.END_DATE)
        values.append(end_date)

    return columns, values


def _cadence_to_days(cadence: Optional[str]) -> int:
    value = (cadence or "").strip().lower()
    if value in ("weekly", "week"):
        return 7
    if value in ("fortnightly", "fortnight"):
        return 14
    if value in ("monthly", "month"):
        return 30
    return 7


def award_bid(
    bid_id: int,
    create_new_project: bool,
    project_id: Optional[int],
    project_payload: Optional[Dict[str, Any]] = None,
):
    """Award a bid and create downstream project artifacts."""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute(
            f"""
            SELECT {S.Bids.BID_ID}, {S.Bids.STATUS}, {S.Bids.PROJECT_ID}, {S.Bids.CLIENT_ID}
            FROM {S.Bids.TABLE}
            WHERE {S.Bids.BID_ID} = ?
            """,
            (bid_id,),
        )
        bid_row = cursor.fetchone()
        if not bid_row:
            raise ValueError("Bid not found.")

        bid_status = bid_row[1]
        existing_project_id = bid_row[2]
        bid_client_id = bid_row[3]

        cursor.execute(
            f"""
            SELECT {S.BidAwardSummary.PROJECT_ID},
                   {S.BidAwardSummary.CREATED_SERVICES},
                   {S.BidAwardSummary.CREATED_REVIEWS},
                   {S.BidAwardSummary.CREATED_CLAIMS},
                   {S.BidAwardSummary.SERVICE_IDS_JSON},
                   {S.BidAwardSummary.REVIEW_IDS_JSON},
                   {S.BidAwardSummary.CLAIM_IDS_JSON}
            FROM {S.BidAwardSummary.TABLE}
            WHERE {S.BidAwardSummary.BID_ID} = ?
            """,
            (bid_id,),
        )
        summary_row = cursor.fetchone()
        if summary_row:
            return {
                "project_id": summary_row[0],
                "created_services": summary_row[1],
                "created_reviews": summary_row[2],
                "created_claims": summary_row[3],
                "service_ids": json.loads(summary_row[4]) if summary_row[4] else [],
                "review_ids": json.loads(summary_row[5]) if summary_row[5] else [],
                "claim_ids": json.loads(summary_row[6]) if summary_row[6] else [],
                "message": "Bid already awarded.",
            }

        if bid_status == "AWARDED":
            raise RuntimeError("Bid already awarded but award summary is missing.")

        cursor.execute(
            f"SELECT COUNT(*) FROM {S.BidScopeItems.TABLE} WHERE {S.BidScopeItems.BID_ID} = ?",
            (bid_id,),
        )
        scope_count = cursor.fetchone()[0]
        if not scope_count:
            raise ValueError("Bid must include at least one scope item before award.")

        cursor.execute(
            f"SELECT COUNT(*) FROM {S.BidBillingSchedule.TABLE} WHERE {S.BidBillingSchedule.BID_ID} = ?",
            (bid_id,),
        )
        billing_count = cursor.fetchone()[0]
        if not billing_count:
            raise ValueError("Bid must include a billing schedule before award.")

        if create_new_project:
            columns, values = _project_payload_to_columns(project_payload, bid_client_id)
            if not columns:
                raise ValueError("project_payload with project_name is required when creating a new project.")
            cursor.execute(
                f"""
                INSERT INTO {S.Projects.TABLE} ({', '.join(columns)})
                OUTPUT INSERTED.{S.Projects.ID}
                VALUES ({', '.join(['?'] * len(values))});
                """,
                values,
            )
            project_id = cursor.fetchone()[0]
        else:
            project_id = project_id or existing_project_id
            if not project_id:
                raise ValueError("project_id is required when create_new_project is false.")
            cursor.execute(
                f"SELECT {S.Projects.ID} FROM {S.Projects.TABLE} WHERE {S.Projects.ID} = ?",
                (project_id,),
            )
            if cursor.fetchone() is None:
                raise ValueError("Project not found for award.")

        cursor.execute(
            f"""
            UPDATE {S.Bids.TABLE}
            SET {S.Bids.STATUS} = 'AWARDED',
                {S.Bids.PROJECT_ID} = ?,
                {S.Bids.UPDATED_AT} = SYSDATETIME()
            WHERE {S.Bids.BID_ID} = ?;
            """,
            (project_id, bid_id),
        )

        cursor.execute(
            f"""
            SELECT {S.BidScopeItems.SCOPE_ITEM_ID},
                   {S.BidScopeItems.SERVICE_CODE},
                   {S.BidScopeItems.TITLE},
                   {S.BidScopeItems.DESCRIPTION},
                   {S.BidScopeItems.STAGE_NAME},
                   {S.BidScopeItems.INCLUDED_QTY},
                   {S.BidScopeItems.UNIT},
                   {S.BidScopeItems.UNIT_RATE},
                   {S.BidScopeItems.LUMP_SUM},
                   {S.BidScopeItems.IS_OPTIONAL},
                   {S.BidScopeItems.OPTION_GROUP}
            FROM {S.BidScopeItems.TABLE}
            WHERE {S.BidScopeItems.BID_ID} = ?
            ORDER BY {S.BidScopeItems.SORT_ORDER}, {S.BidScopeItems.SCOPE_ITEM_ID}
            """,
            (bid_id,),
        )
        scope_rows = cursor.fetchall()

        service_ids: List[int] = []
        service_values: List[Tuple[int, float]] = []
        for row in scope_rows:
            service_code = row[1]
            title = row[2]
            description = row[3]
            stage_name = row[4]
            included_qty = row[5]
            unit = row[6]
            unit_rate = row[7]
            lump_sum = row[8]
            is_optional = bool(row[9]) if row[9] is not None else False
            option_group = row[10]

            unit_qty = _coerce_int(included_qty)
            agreed_fee = None
            if lump_sum is not None:
                agreed_fee = lump_sum
            elif unit_rate is not None and unit_qty is not None:
                agreed_fee = float(unit_rate) * unit_qty

            notes = description
            if is_optional:
                optional_note = "Optional scope item"
                if option_group:
                    optional_note = f"{optional_note} ({option_group})"
                notes = f"{notes}\n{optional_note}" if notes else optional_note

            cursor.execute(
                f"""
                INSERT INTO {S.ProjectServices.TABLE} (
                    {S.ProjectServices.PROJECT_ID},
                    {S.ProjectServices.SERVICE_CODE},
                    {S.ProjectServices.SERVICE_NAME},
                    {S.ProjectServices.PHASE},
                    {S.ProjectServices.UNIT_TYPE},
                    {S.ProjectServices.UNIT_QTY},
                    {S.ProjectServices.UNIT_RATE},
                    {S.ProjectServices.LUMP_SUM_FEE},
                    {S.ProjectServices.AGREED_FEE},
                    {S.ProjectServices.BILL_RULE},
                    {S.ProjectServices.NOTES}
                )
                OUTPUT INSERTED.{S.ProjectServices.SERVICE_ID}
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    project_id,
                    service_code,
                    title,
                    stage_name,
                    unit,
                    unit_qty,
                    unit_rate,
                    lump_sum,
                    agreed_fee,
                    "Bid Award",
                    notes,
                ),
            )
            service_id = cursor.fetchone()[0]
            service_ids.append(service_id)
            service_value = float(agreed_fee) if agreed_fee is not None else 0.0
            service_values.append((service_id, service_value))

        cursor.execute(
            f"""
            SELECT {S.BidProgramStages.PROGRAM_STAGE_ID},
                   {S.BidProgramStages.STAGE_NAME},
                   {S.BidProgramStages.PLANNED_START},
                   {S.BidProgramStages.CADENCE},
                   {S.BidProgramStages.CYCLES_PLANNED}
            FROM {S.BidProgramStages.TABLE}
            WHERE {S.BidProgramStages.BID_ID} = ?
            ORDER BY {S.BidProgramStages.SORT_ORDER}, {S.BidProgramStages.PROGRAM_STAGE_ID}
            """,
            (bid_id,),
        )
        program_rows = cursor.fetchall()
        review_ids: List[int] = []
        for row in program_rows:
            stage_name = row[1]
            planned_start = row[2] or datetime.utcnow().date()
            cadence = row[3]
            cycles_planned = int(row[4] or 0)
            interval_days = _cadence_to_days(cadence)
            for idx in range(cycles_planned):
                review_date = planned_start + timedelta(days=interval_days * idx)
                cursor.execute(
                    f"""
                    INSERT INTO {S.ReviewSchedule.TABLE} (
                        {S.ReviewSchedule.PROJECT_ID},
                        {S.ReviewSchedule.REVIEW_DATE},
                        {S.ReviewSchedule.IS_WITHIN_LICENSE_PERIOD},
                        {S.ReviewSchedule.IS_BLOCKED},
                        {S.ReviewSchedule.CYCLE_ID},
                        {S.ReviewSchedule.ASSIGNED_TO},
                        {S.ReviewSchedule.STATUS},
                        {S.ReviewSchedule.MANUAL_OVERRIDE}
                    )
                    OUTPUT INSERTED.{S.ReviewSchedule.SCHEDULE_ID}
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (project_id, review_date, None, None, None, None, "planned", stage_name),
                )
                review_ids.append(cursor.fetchone()[0])

        cursor.execute(
            f"""
            SELECT {S.BidBillingSchedule.BILLING_LINE_ID},
                   {S.BidBillingSchedule.PERIOD_START},
                   {S.BidBillingSchedule.PERIOD_END},
                   {S.BidBillingSchedule.AMOUNT},
                   {S.BidBillingSchedule.NOTES}
            FROM {S.BidBillingSchedule.TABLE}
            WHERE {S.BidBillingSchedule.BID_ID} = ?
            ORDER BY {S.BidBillingSchedule.SORT_ORDER}, {S.BidBillingSchedule.BILLING_LINE_ID}
            """,
            (bid_id,),
        )
        billing_rows = cursor.fetchall()

        claim_ids: List[int] = []
        total_service_value = sum(value for _, value in service_values)
        service_count = len(service_values)

        for row in billing_rows:
            period_start = row[1]
            period_end = row[2]
            amount = float(row[3] or 0.0)
            notes = row[4]

            cursor.execute(
                f"""
                INSERT INTO {S.BillingClaims.TABLE} (
                    {S.BillingClaims.PROJECT_ID},
                    {S.BillingClaims.PERIOD_START},
                    {S.BillingClaims.PERIOD_END},
                    {S.BillingClaims.STATUS}
                )
                OUTPUT INSERTED.{S.BillingClaims.CLAIM_ID}
                VALUES (?, ?, ?, ?);
                """,
                (project_id, period_start, period_end, "draft"),
            )
            claim_id = cursor.fetchone()[0]
            claim_ids.append(claim_id)

            allocations: List[Tuple[int, float]] = []
            if total_service_value > 0:
                for service_id, value in service_values:
                    allocations.append((service_id, amount * (value / total_service_value)))
            elif service_count > 0:
                even_amount = amount / service_count if service_count else 0.0
                allocations = [(service_id, even_amount) for service_id, _ in service_values]

            for service_id, alloc_amount in allocations:
                cursor.execute(
                    f"""
                    INSERT INTO {S.BillingClaimLines.TABLE} (
                        {S.BillingClaimLines.CLAIM_ID},
                        {S.BillingClaimLines.SERVICE_ID},
                        {S.BillingClaimLines.STAGE_LABEL},
                        {S.BillingClaimLines.PREV_PCT},
                        {S.BillingClaimLines.CURR_PCT},
                        {S.BillingClaimLines.DELTA_PCT},
                        {S.BillingClaimLines.AMOUNT_THIS_CLAIM},
                        {S.BillingClaimLines.NOTE}
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        claim_id,
                        service_id,
                        "Bid Award",
                        0,
                        0,
                        0,
                        round(alloc_amount, 2),
                        notes,
                    ),
                )

        created_services = len(service_ids)
        created_reviews = len(review_ids)
        created_claims = len(claim_ids)

        cursor.execute(
            f"""
            INSERT INTO {S.BidAwardSummary.TABLE} (
                {S.BidAwardSummary.BID_ID},
                {S.BidAwardSummary.PROJECT_ID},
                {S.BidAwardSummary.CREATED_SERVICES},
                {S.BidAwardSummary.CREATED_REVIEWS},
                {S.BidAwardSummary.CREATED_CLAIMS},
                {S.BidAwardSummary.SERVICE_IDS_JSON},
                {S.BidAwardSummary.REVIEW_IDS_JSON},
                {S.BidAwardSummary.CLAIM_IDS_JSON}
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """,
            (
                bid_id,
                project_id,
                created_services,
                created_reviews,
                created_claims,
                json.dumps(service_ids),
                json.dumps(review_ids),
                json.dumps(claim_ids),
            ),
        )

        conn.commit()

        return {
            "project_id": project_id,
            "created_services": created_services,
            "created_reviews": created_reviews,
            "created_claims": created_claims,
            "service_ids": service_ids,
            "review_ids": review_ids,
            "claim_ids": claim_ids,
        }


def get_reconciled_issues_table(
    project_id: Optional[str] = None,
    source_system: Optional[str] = None,
    status_normalized: Optional[str] = None,
    priority_normalized: Optional[str] = None,
    discipline_normalized: Optional[str] = None,
    assignee_user_key: Optional[str] = None,
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
    sort_by: str = "updated_at",
    sort_dir: str = "desc",
) -> Dict[str, Any]:
    """
    Return paginated issues from vw_Issues_Reconciled with reconciled identifiers.
    
    This view combines ACC and Revizto issues with human-friendly display_ids:
    - ACC mapped: "ACC-" + issue_number (e.g., "ACC-924")
    - ACC unmapped: "ACC-" + first 8 chars of UUID (e.g., "ACC-66C8A7AA")
    - Revizto: "REV-" + issue_id (e.g., "REV-12345")
    
    Supports filters:
    - project_id: filter by project
    - source_system: 'ACC' or 'Revizto'
    - status_normalized: issue status
    - priority_normalized: issue priority
    - discipline_normalized: discipline
    - assignee_user_key: assigned to user
    - search: search in title/issue_key/display_id
    
    Supports pagination: page (1-indexed), page_size
    Supports sorting: updated_at, created_at, priority_normalized, status_normalized, display_id
    """
    allowed_sort = {
        "updated_at": "updated_at",
        "created_at": "created_at",
        "priority_normalized": "priority_normalized",
        "status_normalized": "status_normalized",
        "display_id": "display_id",
    }
    sort_col = allowed_sort.get(sort_by, "updated_at")
    sort_direction = "DESC" if str(sort_dir).lower() == "desc" else "ASC"
    offset = max(page - 1, 0) * page_size

    try:
        with get_db_connection(Config.PROJECT_MGMT_DB) as conn:  # ProjectManagement DB (not warehouse)
            cursor = conn.cursor()
            
            # Build WHERE clause dynamically
            params = []
            where_clauses = []
            
            if project_id:
                where_clauses.append("project_id = ?")
                params.append(project_id)
            
            if source_system:
                where_clauses.append("source_system = ?")
                params.append(source_system)
            
            if status_normalized:
                where_clauses.append("LOWER(status_normalized) = LOWER(?)")
                params.append(status_normalized)
            
            if priority_normalized:
                where_clauses.append("LOWER(priority_normalized) = LOWER(?)")
                params.append(priority_normalized)
            
            if discipline_normalized:
                where_clauses.append("LOWER(discipline_normalized) = LOWER(?)")
                params.append(discipline_normalized)
            
            if assignee_user_key:
                where_clauses.append("assignee_user_key = ?")
                params.append(assignee_user_key)
            
            if search:
                search_pattern = f"%{search}%"
                where_clauses.append("(title LIKE ? OR issue_key LIKE ? OR display_id LIKE ?)")
                params.extend([search_pattern, search_pattern, search_pattern])
            
            where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
            
            # Get total count
            count_query = f"SELECT COUNT(*) FROM dbo.vw_Issues_Reconciled {where_sql}"
            cursor.execute(count_query, params)
            total_count = cursor.fetchone()[0]
            
            # Get paginated rows with all columns
            data_query = f"""
            SELECT
                issue_key,
                source_system,
                source_issue_id,
                source_project_id,
                project_id,
                display_id,
                acc_issue_number,
                acc_issue_uuid,
                acc_id_type,
                title,
                status_raw,
                status_normalized,
                priority_raw,
                priority_normalized,
                discipline_raw,
                discipline_normalized,
                assignee_user_key,
                created_at,
                updated_at,
                closed_at,
                location_root,
                location_building,
                location_level,
                acc_status,
                acc_created_at,
                acc_updated_at,
                is_deleted,
                import_run_id
            FROM dbo.vw_Issues_Reconciled
            {where_sql}
            ORDER BY {sort_col} {sort_direction}
            OFFSET {offset} ROWS FETCH NEXT {page_size} ROWS ONLY
            """
            
            cursor.execute(data_query, params)
            rows = cursor.fetchall()
            
            # Format rows as dicts
            columns = [
                'issue_key', 'source_system', 'source_issue_id', 'source_project_id',
                'project_id', 'display_id', 'acc_issue_number', 'acc_issue_uuid', 'acc_id_type',
                'title', 'status_raw', 'status_normalized', 'priority_raw', 'priority_normalized',
                'discipline_raw', 'discipline_normalized', 'assignee_user_key', 'created_at',
                'updated_at', 'closed_at', 'location_root', 'location_building', 'location_level',
                'acc_status', 'acc_created_at', 'acc_updated_at', 'is_deleted', 'import_run_id'
            ]
            
            formatted_rows = []
            for row in rows:
                row_dict = dict(zip(columns, row))
                # Convert datetime objects to ISO format strings
                for dt_field in ['created_at', 'updated_at', 'closed_at', 'acc_created_at', 'acc_updated_at']:
                    if row_dict[dt_field]:
                        row_dict[dt_field] = row_dict[dt_field].isoformat()
                formatted_rows.append(row_dict)
            
            return {
                "page": page,
                "page_size": page_size,
                "total_count": total_count,
                "rows": formatted_rows,
            }
    
    except Exception as e:
        logger.exception("Error fetching reconciled issues table")
        return {
            "page": page,
            "page_size": page_size,
            "total_count": 0,
            "rows": [],
            "error": str(e),
        }


# ===================== Phase 1: Expected Models (Quality Register) =====================

def get_expected_models(project_id: int) -> List[Dict[str, Any]]:
    """
    Fetch all expected models for a project.
    
    Args:
        project_id: Project ID
    
    Returns:
        List of expected model records
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT 
                    {S.ExpectedModels.EXPECTED_MODEL_ID},
                    {S.ExpectedModels.PROJECT_ID},
                    {S.ExpectedModels.EXPECTED_MODEL_KEY},
                    {S.ExpectedModels.DISPLAY_NAME},
                    {S.ExpectedModels.DISCIPLINE},
                    {S.ExpectedModels.COMPANY_ID},
                    {S.ExpectedModels.IS_REQUIRED},
                    {S.ExpectedModels.CREATED_AT},
                    {S.ExpectedModels.UPDATED_AT}
                FROM ProjectManagement.dbo.{S.ExpectedModels.TABLE}
                WHERE {S.ExpectedModels.PROJECT_ID} = ?
                ORDER BY {S.ExpectedModels.EXPECTED_MODEL_KEY}
            """, (project_id,))
            
            rows = []
            for row in cursor.fetchall():
                rows.append({
                    'expected_model_id': row[0],
                    'project_id': row[1],
                    'expected_model_key': row[2],
                    'display_name': row[3],
                    'discipline': row[4],
                    'company_id': row[5],
                    'is_required': bool(row[6]) if row[6] is not None else True,
                    'created_at': row[7],
                    'updated_at': row[8],
                })
            
            logger.info(f"Fetched {len(rows)} expected models for project {project_id}")
            return rows
    
    except Exception as e:
        logger.error(f"Error fetching expected models for project {project_id}: {e}", exc_info=True)
        return []


def create_expected_model(
    project_id: int,
    expected_model_key: str,
    display_name: Optional[str] = None,
    discipline: Optional[str] = None,
    company_id: Optional[int] = None,
    is_required: bool = True
) -> Optional[int]:
    """
    Create a new expected model.
    
    Args:
        project_id: Project ID
        expected_model_key: Canonical model key (must be unique per project)
        display_name: User-friendly name
        discipline: Model discipline
        company_id: Optional company/client ID
        is_required: Whether this is a required model
    
    Returns:
        ID of created expected model, or None if error
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                INSERT INTO ProjectManagement.dbo.{S.ExpectedModels.TABLE}
                (
                    {S.ExpectedModels.PROJECT_ID},
                    {S.ExpectedModels.EXPECTED_MODEL_KEY},
                    {S.ExpectedModels.DISPLAY_NAME},
                    {S.ExpectedModels.DISCIPLINE},
                    {S.ExpectedModels.COMPANY_ID},
                    {S.ExpectedModels.IS_REQUIRED}
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (project_id, expected_model_key, display_name, discipline, company_id, 1 if is_required else 0))
            
            conn.commit()
            
            # Get the ID of the inserted row
            cursor.execute(f"SELECT @@IDENTITY")
            new_id = cursor.fetchone()[0]
            
            logger.info(f"Created expected model {new_id}: {expected_model_key} for project {project_id}")
            return int(new_id)
    
    except Exception as e:
        logger.error(f"Error creating expected model: {e}", exc_info=True)
        return None


def get_expected_model_aliases(project_id: int, expected_model_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Fetch expected model aliases for a project or specific expected model.
    
    Args:
        project_id: Project ID (required for scoping)
        expected_model_id: Optional filter by expected model
    
    Returns:
        List of alias records
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            where_clause = f"{S.ExpectedModelAliases.PROJECT_ID} = ?"
            params = [project_id]
            
            if expected_model_id:
                where_clause += f" AND {S.ExpectedModelAliases.EXPECTED_MODEL_ID} = ?"
                params.append(expected_model_id)
            
            cursor.execute(f"""
                SELECT 
                    {S.ExpectedModelAliases.EXPECTED_MODEL_ALIAS_ID},
                    {S.ExpectedModelAliases.EXPECTED_MODEL_ID},
                    {S.ExpectedModelAliases.PROJECT_ID},
                    {S.ExpectedModelAliases.ALIAS_PATTERN},
                    {S.ExpectedModelAliases.MATCH_TYPE},
                    {S.ExpectedModelAliases.TARGET_FIELD},
                    {S.ExpectedModelAliases.IS_ACTIVE},
                    {S.ExpectedModelAliases.CREATED_AT}
                FROM ProjectManagement.dbo.{S.ExpectedModelAliases.TABLE}
                WHERE {where_clause}
                ORDER BY {S.ExpectedModelAliases.CREATED_AT} DESC
            """, params)
            
            rows = []
            for row in cursor.fetchall():
                rows.append({
                    'expected_model_alias_id': row[0],
                    'expected_model_id': row[1],
                    'project_id': row[2],
                    'alias_pattern': row[3],
                    'match_type': row[4],
                    'target_field': row[5],
                    'is_active': bool(row[6]) if row[6] is not None else True,
                    'created_at': row[7],
                })
            
            logger.info(f"Fetched {len(rows)} aliases for project {project_id}")
            return rows
    
    except Exception as e:
        logger.error(f"Error fetching expected model aliases: {e}", exc_info=True)
        return []


def create_expected_model_alias(
    expected_model_id: int,
    project_id: int,
    alias_pattern: str,
    match_type: str = 'exact',
    target_field: str = 'filename',
    is_active: bool = True
) -> Optional[int]:
    """
    Create a new expected model alias.
    
    Args:
        expected_model_id: Expected model ID
        project_id: Project ID (for scoping)
        alias_pattern: Pattern to match (filename, model key, regex)
        match_type: Matching strategy (exact, contains, regex)
        target_field: Field to match against (filename, rvt_model_key)
        is_active: Whether alias is enabled
    
    Returns:
        ID of created alias, or None if error
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                INSERT INTO ProjectManagement.dbo.{S.ExpectedModelAliases.TABLE}
                (
                    {S.ExpectedModelAliases.EXPECTED_MODEL_ID},
                    {S.ExpectedModelAliases.PROJECT_ID},
                    {S.ExpectedModelAliases.ALIAS_PATTERN},
                    {S.ExpectedModelAliases.MATCH_TYPE},
                    {S.ExpectedModelAliases.TARGET_FIELD},
                    {S.ExpectedModelAliases.IS_ACTIVE}
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (expected_model_id, project_id, alias_pattern, match_type, target_field, 1 if is_active else 0))
            
            conn.commit()
            
            # Get the ID of the inserted row
            cursor.execute(f"SELECT @@IDENTITY")
            new_id = cursor.fetchone()[0]
            
            logger.info(f"Created alias {new_id}: {alias_pattern} ({match_type}) for expected model {expected_model_id}")
            return int(new_id)
    
    except Exception as e:
        logger.error(f"Error creating expected model alias: {e}", exc_info=True)
        return None


def match_observed_to_expected(
    observed_filename: str,
    observed_rvt_model_key: Optional[str],
    aliases: List[Dict[str, Any]]
) -> Optional[int]:
    """
    Match an observed file to an expected model ID using alias patterns.
    
    Args:
        observed_filename: Observed filename from health data
        observed_rvt_model_key: Optional RVT model key from health data
        aliases: List of alias records to check
    
    Returns:
        expected_model_id if match found, None otherwise
    """
    import re
    
    if not aliases:
        return None
    
    # Build match results by priority
    matches = {
        'exact_filename': [],
        'exact_rvt_key': [],
        'contains': [],
        'regex': [],
    }
    
    for alias in aliases:
        if not alias['is_active']:
            continue
        
        pattern = alias['alias_pattern']
        match_type = alias['match_type']
        target_field = alias['target_field']
        expected_model_id = alias['expected_model_id']
        
        try:
            # Determine which field to match against
            if target_field == 'filename':
                field_value = observed_filename
            elif target_field == 'rvt_model_key':
                field_value = observed_rvt_model_key
            else:
                continue
            
            if not field_value:
                continue
            
            # Apply match logic
            matched = False
            priority_key = None
            
            if match_type == 'exact':
                if field_value.lower() == pattern.lower():
                    matched = True
                    priority_key = 'exact_filename' if target_field == 'filename' else 'exact_rvt_key'
            
            elif match_type == 'contains':
                if pattern.lower() in field_value.lower():
                    matched = True
                    priority_key = 'contains'
            
            elif match_type == 'regex':
                if re.search(pattern, field_value, re.IGNORECASE):
                    matched = True
                    priority_key = 'regex'
            
            if matched and priority_key:
                matches[priority_key].append({
                    'expected_model_id': expected_model_id,
                    'created_at': alias['created_at']
                })
        
        except Exception as e:
            logger.warning(f"Error matching alias pattern '{pattern}': {e}")
            continue
    
    # Return best match by priority
    for priority_key in ['exact_filename', 'exact_rvt_key', 'contains', 'regex']:
        if matches[priority_key]:
            # Sort by created_at DESC to get newest
            best_match = sorted(matches[priority_key], key=lambda x: x['created_at'], reverse=True)[0]
            return best_match['expected_model_id']
    
    return None

