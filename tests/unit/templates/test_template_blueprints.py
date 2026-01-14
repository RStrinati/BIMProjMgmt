import unittest
from unittest.mock import MagicMock, patch

from review_management_service import ReviewManagementService


class TemplateBlueprintTests(unittest.TestCase):
    """Validate template blueprint export helpers."""

    def setUp(self):
        self.mock_db = MagicMock()
        self.mock_cursor = MagicMock()
        self.mock_db.cursor.return_value = self.mock_cursor

        with patch.object(ReviewManagementService, 'ensure_tables_exist', return_value=None):
            self.service = ReviewManagementService(self.mock_db)

    def test_build_template_from_project_includes_blueprints(self):
        mock_services = [
            {
                'service_id': 101,
                'phase': 'Phase A',
                'service_code': 'SVC-A',
                'service_name': 'Alpha Coordination',
                'unit_type': 'review',
                'unit_qty': 4,
                'unit_rate': 1200,
                'lump_sum_fee': 0,
                'bill_rule': 'per_unit_complete',
                'notes': 'Existing alpha service',
            }
        ]

        with patch.object(self.service, 'get_project_services', return_value=mock_services), \
             patch.object(self.service, 'get_service_by_id', return_value={
                 'schedule_frequency': 'monthly',
                 'schedule_start': '2024-02-01',
             }), \
             patch.object(self.service, '_build_review_blueprint', return_value={
                 'total_cycles': 4,
                 'disciplines': 'ALL',
                 'deliverables': 'issues,report',
                 'weight_factor': 1.0,
             }), \
             patch.object(self.service, '_build_service_item_blueprint', return_value=[
                 {
                     'item_type': 'deliverable',
                     'title': 'Kick-off Checklist',
                     'planned_offset_days': 0,
                     'priority': 'high',
                     'status': 'planned',
                 }
             ]):

            template_items = self.service.build_template_from_project(
                project_id=55,
                include_reviews=True,
                include_items=True,
            )

        self.assertEqual(len(template_items), 1)
        item = template_items[0]
        self.assertEqual(item['service_code'], 'SVC-A')
        self.assertEqual(item['frequency'], 'monthly')
        self.assertIn('review_blueprint', item)
        self.assertEqual(item['review_blueprint']['total_cycles'], 4)
        self.assertIn('service_items', item)
        self.assertEqual(item['service_items'][0]['title'], 'Kick-off Checklist')


if __name__ == "__main__":
    unittest.main()
