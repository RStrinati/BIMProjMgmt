#!/usr/bin/env python3
"""
Script to create a clean service_templates.json file
"""
import json
import os

# Define the templates data
templates_data = {
    "templates": [
        {
            "name": "SINSW – Melrose Park HS",
            "sector": "Education",
            "notes": "State Infrastructure NSW - Melrose Park HS Redevelopment Project",
            "items": [
                {
                    "phase": "Phase 4/5 – Digital Initiation",
                    "service_code": "INIT",
                    "service_name": "Digital Initiation (DEXP, Kickoff, ACC/Revizto setup)",
                    "unit_type": "lump_sum",
                    "default_units": 1,
                    "lump_sum_fee": 15000,
                    "bill_rule": "on_setup",
                    "notes": "Includes DEXP, project kickoff, ACC/Revizto platform setup"
                },
                {
                    "phase": "Phase 4/5 – Digital Production",
                    "service_code": "PROD",
                    "service_name": "BIM Coordination Review Cycles",
                    "unit_type": "review",
                    "default_units": 4,
                    "unit_rate": 5500,
                    "bill_rule": "per_unit_complete",
                    "notes": "DD/CD combined; 4 cycles total"
                },
                {
                    "phase": "Phase 7 – Digital Production",
                    "service_code": "PROD",
                    "service_name": "BIM Coordination Review Cycles",
                    "unit_type": "review",
                    "default_units": 12,
                    "unit_rate": 5500,
                    "bill_rule": "per_unit_complete",
                    "notes": "Construction phase weekly reviews"
                },
                {
                    "phase": "Phase 8 – Digital Handover",
                    "service_code": "HANDOVER",
                    "service_name": "PC Report",
                    "unit_type": "lump_sum",
                    "default_units": 1,
                    "lump_sum_fee": 7000,
                    "bill_rule": "on_report_issue",
                    "notes": "Practical Completion review and report"
                },
                {
                    "phase": "Phase 8 – Digital Handover",
                    "service_code": "HANDOVER",
                    "service_name": "Cupix Reviews",
                    "unit_type": "audit",
                    "default_units": 3,
                    "unit_rate": 3333.33,
                    "bill_rule": "per_unit_complete",
                    "notes": "3 image-based field validation reviews"
                }
            ]
        },
        {
            "name": "AWS – MEL081 STOCKMAN (Day 1)",
            "sector": "Data Centre",
            "notes": "Amazon Web Services - Melbourne Data Centre Project Day 1 Services",
            "items": [
                {
                    "phase": "Stage 1 – Strategic Business Case",
                    "service_code": "INIT",
                    "service_name": "BIM Strategy & Setup",
                    "unit_type": "lump_sum",
                    "default_units": 1,
                    "lump_sum_fee": 25000,
                    "bill_rule": "on_setup",
                    "notes": "Initial BIM strategy development and platform setup"
                },
                {
                    "phase": "Stage 2 – Preliminary Business Case",
                    "service_code": "COORD",
                    "service_name": "Design Coordination Reviews",
                    "unit_type": "review",
                    "default_units": 6,
                    "unit_rate": 8500,
                    "bill_rule": "per_unit_complete",
                    "notes": "Preliminary design coordination review cycles"
                },
                {
                    "phase": "Stage 3 – Final Business Case",
                    "service_code": "COORD",
                    "service_name": "Design Development Reviews",
                    "unit_type": "review",
                    "default_units": 8,
                    "unit_rate": 8500,
                    "bill_rule": "per_unit_complete",
                    "notes": "Detailed design development review cycles"
                },
                {
                    "phase": "Stage 4 – Implementation Ready",
                    "service_code": "DELIVERY",
                    "service_name": "Construction Documentation Reviews",
                    "unit_type": "review",
                    "default_units": 12,
                    "unit_rate": 7500,
                    "bill_rule": "per_unit_complete",
                    "notes": "Construction documentation review cycles"
                },
                {
                    "phase": "Stage 5 – Implementation",
                    "service_code": "CONSTRUCTION",
                    "service_name": "Construction Phase Reviews",
                    "unit_type": "review",
                    "default_units": 24,
                    "unit_rate": 6500,
                    "bill_rule": "per_unit_complete",
                    "notes": "Weekly construction phase coordination reviews"
                },
                {
                    "phase": "Stage 6 – Benefits Realisation",
                    "service_code": "HANDOVER",
                    "service_name": "Project Completion & Handover",
                    "unit_type": "lump_sum",
                    "default_units": 1,
                    "lump_sum_fee": 15000,
                    "bill_rule": "on_completion",
                    "notes": "Final project completion review and digital asset handover"
                }
            ]
        },
        {
            "name": "Standard Commercial – Office Development",
            "sector": "Commercial",
            "notes": "Standard commercial office development template for mid-scale projects",
            "items": [
                {
                    "phase": "Pre-Design – Project Setup",
                    "service_code": "INIT",
                    "service_name": "Project Initiation & BIM Setup",
                    "unit_type": "lump_sum",
                    "default_units": 1,
                    "lump_sum_fee": 12000,
                    "bill_rule": "on_setup",
                    "notes": "Project setup, BIM standards definition, and platform configuration"
                },
                {
                    "phase": "Schematic Design – Concept Review",
                    "service_code": "CONCEPT",
                    "service_name": "Concept Design Reviews",
                    "unit_type": "review",
                    "default_units": 3,
                    "unit_rate": 4500,
                    "bill_rule": "per_unit_complete",
                    "notes": "Initial concept design coordination cycles"
                },
                {
                    "phase": "Design Development – Detailed Review",
                    "service_code": "DD",
                    "service_name": "Design Development Reviews",
                    "unit_type": "review",
                    "default_units": 6,
                    "unit_rate": 5500,
                    "bill_rule": "per_unit_complete",
                    "notes": "Detailed design development coordination"
                },
                {
                    "phase": "Construction Documentation – Final Review",
                    "service_code": "CD",
                    "service_name": "Construction Documentation Reviews",
                    "unit_type": "review",
                    "default_units": 8,
                    "unit_rate": 5000,
                    "bill_rule": "per_unit_complete",
                    "notes": "Construction documentation coordination cycles"
                },
                {
                    "phase": "Construction Administration – Build Phase",
                    "service_code": "CA",
                    "service_name": "Construction Phase Reviews",
                    "unit_type": "review",
                    "default_units": 16,
                    "unit_rate": 4000,
                    "bill_rule": "per_unit_complete",
                    "notes": "Bi-weekly construction phase coordination"
                },
                {
                    "phase": "Project Closeout – Completion",
                    "service_code": "CLOSEOUT",
                    "service_name": "Project Completion Review",
                    "unit_type": "lump_sum",
                    "default_units": 1,
                    "lump_sum_fee": 8000,
                    "bill_rule": "on_completion",
                    "notes": "Final project review and closeout documentation"
                }
            ]
        }
    ]
}

# Create the templates directory if it doesn't exist
templates_dir = "templates"
if not os.path.exists(templates_dir):
    os.makedirs(templates_dir)

# Write the JSON file with proper UTF-8 encoding
templates_file = os.path.join(templates_dir, "service_templates.json")
with open(templates_file, 'w', encoding='utf-8') as f:
    json.dump(templates_data, f, indent=2, ensure_ascii=False)

print(f"✅ Created clean service_templates.json with {len(templates_data['templates'])} templates")

# Validate the JSON
try:
    with open(templates_file, 'r', encoding='utf-8') as f:
        test_data = json.load(f)
    print(f"✅ JSON validation successful!")
    for template in test_data['templates']:
        print(f"  - {template['name']} ({template['sector']}) - {len(template['items'])} items")
except Exception as e:
    print(f"❌ JSON validation failed: {e}")