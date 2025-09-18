#!/usr/bin/env python3
"""
Fixed generate_review_cycles method to ensure exactly unit_qty cycles are created
"""

def generate_review_cycles_fixed(self, service_id: int, unit_qty: int,
                                start_date, end_date,
                                cadence: str = 'weekly', disciplines: str = 'All'):
    """Generate review cycles for a service - FIXED VERSION"""
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

        dates = []

        if interval_days:
            # Generate exactly unit_qty cycles with proper interval spacing
            # Start from start_date and create cycles at regular intervals
            for i in range(unit_qty):
                cycle_date = start_date + timedelta(days=i * interval_days)
                dates.append(cycle_date)
            # DON'T cap dates - allow them to extend beyond end_date if needed
            # This ensures we always get exactly unit_qty cycles
        else:
            # Distribute cycles evenly across the date range
            total_days = max(1, (end_date - start_date).days)
            if unit_qty == 1:
                dates = [start_date]
            else:
                interval = total_days / (unit_qty - 1)
                dates = [start_date + timedelta(days=int(round(i * interval))) for i in range(unit_qty)]

        cycles_created = []
        for i, planned_date in enumerate(dates):
            # Keep dates within reasonable bounds but don't eliminate cycles
            # If planned_date is way beyond end_date, just use end_date but keep all cycles
            display_date = min(planned_date, end_date + timedelta(days=365))  # Allow 1 year extension
            
            # Calculate due date
            default_turnaround = interval_days or 7
            due_date = display_date + timedelta(days=default_turnaround)

            cycle_data = {
                'service_id': service_id,
                'cycle_no': i + 1,
                'planned_date': display_date.strftime('%Y-%m-%d'),
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