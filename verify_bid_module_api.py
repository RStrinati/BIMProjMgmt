import json
import os
import sys
from typing import Any, Dict, Optional

import requests

BASE_URL = os.getenv('BASE_URL', 'http://localhost:5000').rstrip('/')
TIMEOUT = 15


def print_result(name: str, passed: bool, details: str = '') -> None:
    status = 'PASS' if passed else 'FAIL'
    line = f"[{status}] {name}"
    if details:
        line = f"{line} - {details}"
    print(line)


def request_json(method: str, path: str, payload: Optional[Dict[str, Any]] = None):
    url = f"{BASE_URL}{path}"
    try:
        response = requests.request(method, url, json=payload, timeout=TIMEOUT)
    except Exception as exc:
        print_result(f"{method} {path}", False, f"Request failed: {exc}")
        return None, None
    try:
        data = response.json()
    except ValueError:
        data = response.text
    return response, data


def assert_true(condition: bool, name: str, details: str = '') -> bool:
    print_result(name, condition, details if not condition else '')
    return condition


def main() -> int:
    print(f"Base URL: {BASE_URL}")

    response, data = request_json('GET', '/api/health/schema')
    if response is None:
        return 1

    if response.status_code != 200:
        print_result('GET /api/health/schema', False, f"HTTP {response.status_code}: {data}")
        return 1

    missing_tables = data.get('missing_tables') or []
    missing_columns = data.get('missing_columns') or {}
    if missing_tables or missing_columns:
        print_result('Schema health', False, f"Missing tables={missing_tables}, columns={missing_columns}")
        return 1
    print_result('Schema health', True)

    bid_payload = {
        'bid_name': 'QA Verification Bid',
        'bid_type': 'PROPOSAL',
        'status': 'DRAFT',
        'currency_code': 'AUD',
    }
    response, bid_data = request_json('POST', '/api/bids', bid_payload)
    if response is None or response.status_code not in (200, 201):
        print_result('Create bid', False, f"HTTP {getattr(response, 'status_code', 'NA')}: {bid_data}")
        return 1

    bid_id = bid_data.get('bid_id') or bid_data.get('id')
    if not assert_true(bool(bid_id), 'Create bid', 'Missing bid_id in response'):
        return 1

    scope_payload = {
        'title': 'Coordination review cycles',
        'stage_name': 'Phase 6 - Digital Production',
        'included_qty': 2,
        'unit': 'cycle',
        'unit_rate': 2500,
        'is_optional': False,
        'sort_order': 1,
    }
    response, scope_data = request_json('POST', f"/api/bids/{bid_id}/scope-items", scope_payload)
    if response is None or response.status_code not in (200, 201):
        print_result('Create scope item', False, f"HTTP {getattr(response, 'status_code', 'NA')}: {scope_data}")
        return 1

    program_payload = {
        'stage_name': 'Design Coordination',
        'cadence': 'weekly',
        'cycles_planned': 2,
        'sort_order': 1,
    }
    response, program_data = request_json('POST', f"/api/bids/{bid_id}/program-stages", program_payload)
    if response is None or response.status_code not in (200, 201):
        print_result('Create program stage', False, f"HTTP {getattr(response, 'status_code', 'NA')}: {program_data}")
        return 1

    billing_payload = {
        'period_start': '2025-01-01',
        'period_end': '2025-01-31',
        'amount': 5000,
        'notes': 'Initial billing period',
        'sort_order': 1,
    }
    response, billing_data = request_json('POST', f"/api/bids/{bid_id}/billing-schedule", billing_payload)
    if response is None or response.status_code not in (200, 201):
        print_result('Create billing line', False, f"HTTP {getattr(response, 'status_code', 'NA')}: {billing_data}")
        return 1

    sections_payload = {
        'sections': [
            {
                'section_key': 'ASSUMPTIONS',
                'content_json': {'items': ['Assumption A', 'Assumption B']},
                'sort_order': 1,
            },
            {
                'section_key': 'EXCLUSIONS',
                'content_json': {'items': ['Exclusion X']},
                'sort_order': 2,
            },
        ]
    }
    response, sections_data = request_json('PUT', f"/api/bids/{bid_id}/sections", sections_payload)
    if response is None or response.status_code != 200:
        print_result('Update bid sections', False, f"HTTP {getattr(response, 'status_code', 'NA')}: {sections_data}")
        return 1
    print_result('Update bid sections', True)

    response, bid_fetch = request_json('GET', f"/api/bids/{bid_id}")
    if response is None or response.status_code != 200:
        print_result('Fetch bid', False, f"HTTP {getattr(response, 'status_code', 'NA')}: {bid_fetch}")
        return 1
    print_result('Fetch bid', True)

    response, scope_items = request_json('GET', f"/api/bids/{bid_id}/scope-items")
    if response is None or response.status_code != 200 or not scope_items:
        print_result('Fetch scope items', False, f"HTTP {getattr(response, 'status_code', 'NA')}: {scope_items}")
        return 1
    print_result('Fetch scope items', True, f"count={len(scope_items)}")

    response, program_stages = request_json('GET', f"/api/bids/{bid_id}/program-stages")
    if response is None or response.status_code != 200 or not program_stages:
        print_result('Fetch program stages', False, f"HTTP {getattr(response, 'status_code', 'NA')}: {program_stages}")
        return 1
    print_result('Fetch program stages', True, f"count={len(program_stages)}")

    response, billing_lines = request_json('GET', f"/api/bids/{bid_id}/billing-schedule")
    if response is None or response.status_code != 200 or not billing_lines:
        print_result('Fetch billing schedule', False, f"HTTP {getattr(response, 'status_code', 'NA')}: {billing_lines}")
        return 1
    print_result('Fetch billing schedule', True, f"count={len(billing_lines)}")

    response, sections = request_json('GET', f"/api/bids/{bid_id}/sections")
    if response is None or response.status_code != 200 or not sections:
        print_result('Fetch sections', False, f"HTTP {getattr(response, 'status_code', 'NA')}: {sections}")
        return 1
    print_result('Fetch sections', True, f"count={len(sections)}")

    award_payload = {
        'create_new_project': True,
        'project_payload': {
            'project_name': 'QA Award Project',
            'status': 'Active',
        },
    }
    response, award_data = request_json('POST', f"/api/bids/{bid_id}/award", award_payload)
    if response is None or response.status_code != 200:
        print_result('Award bid', False, f"HTTP {getattr(response, 'status_code', 'NA')}: {award_data}")
        return 1

    project_id = award_data.get('project_id') if isinstance(award_data, dict) else None
    created_services = award_data.get('created_services') if isinstance(award_data, dict) else None
    created_claims = award_data.get('created_claims') if isinstance(award_data, dict) else None
    created_reviews = award_data.get('created_reviews') if isinstance(award_data, dict) else None

    if not assert_true(bool(project_id), 'Award bid', f"Missing project_id: {award_data}"):
        return 1

    print_result(
        'Award bid counts',
        True,
        f"services={created_services}, reviews={created_reviews}, claims={created_claims}",
    )

    response, award_data_repeat = request_json('POST', f"/api/bids/{bid_id}/award", award_payload)
    if response is None or response.status_code != 200:
        print_result('Award bid (idempotent)', False, f"HTTP {getattr(response, 'status_code', 'NA')}: {award_data_repeat}")
        return 1

    message = award_data_repeat.get('message') if isinstance(award_data_repeat, dict) else ''
    if 'already awarded' in str(message).lower():
        print_result('Award bid (idempotent)', True, message)
    else:
        same_counts = (
            award_data_repeat.get('created_services') == created_services
            and award_data_repeat.get('created_reviews') == created_reviews
            and award_data_repeat.get('created_claims') == created_claims
        )
        assert_true(same_counts, 'Award bid (idempotent)', f"Unexpected repeat response: {award_data_repeat}")

    response, project_data = request_json('GET', f"/api/project/{project_id}")
    if response is None or response.status_code != 200:
        print_result('Fetch project', False, f"HTTP {getattr(response, 'status_code', 'NA')}: {project_data}")
    else:
        print_result('Fetch project', True)

    response, services_data = request_json('GET', f"/api/projects/{project_id}/services")
    if response is None or response.status_code != 200:
        print_result('Fetch project services', False, f"HTTP {getattr(response, 'status_code', 'NA')}: {services_data}")
    else:
        print_result('Fetch project services', True, f"count={len(services_data) if isinstance(services_data, list) else 'n/a'}")

    response, reviews_data = request_json('GET', f"/api/reviews/{project_id}")
    if response is None or response.status_code != 200:
        print_result('Fetch review cycles', False, f"HTTP {getattr(response, 'status_code', 'NA')}: {reviews_data}")
    else:
        print_result('Fetch review cycles', True, f"count={len(reviews_data) if isinstance(reviews_data, list) else 'n/a'}")

    return 0


if __name__ == '__main__':
    sys.exit(main())
