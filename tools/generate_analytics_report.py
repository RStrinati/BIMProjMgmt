"""
Generate comprehensive issue analytics report
Shows pain points by project and discipline with recommendations
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.issue_analytics_service import IssueAnalyticsService
from datetime import datetime
import json

def generate_report(output_file: str = None):
    """Generate comprehensive analytics report"""
    
    service = IssueAnalyticsService()
    
    print("\n" + "="*80)
    print("ISSUE ANALYTICS REPORT")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    # Get all analytics
    print("\n📊 Calculating analytics...")
    projects = service.calculate_pain_points_by_project()
    disciplines = service.calculate_pain_points_by_discipline()
    patterns = service.identify_recurring_patterns()
    
    # Section 1: Executive Summary
    print("\n\n" + "="*80)
    print("EXECUTIVE SUMMARY")
    print("="*80)
    
    total_issues = sum(p['total_issues'] for p in projects)
    total_open = sum(p['open_issues'] for p in projects)
    total_closed = sum(p['closed_issues'] for p in projects)
    
    print(f"\n📈 Overall Statistics:")
    print(f"   Total Issues Analyzed: {total_issues:,}")
    print(f"   Open Issues: {total_open:,} ({total_open/total_issues*100:.1f}%)")
    print(f"   Closed Issues: {total_closed:,} ({total_closed/total_issues*100:.1f}%)")
    print(f"   Projects: {len(projects)}")
    print(f"   Recurring Patterns: {len(patterns)}")
    
    # Top pain points
    top_project = max(projects, key=lambda x: x['pain_point_score'])
    top_discipline = max(disciplines, key=lambda x: x['pain_point_score'])
    
    print(f"\n🔴 Highest Pain Points:")
    print(f"   Project: {top_project['project_name']} (Score: {top_project['pain_point_score']:.2f})")
    print(f"   Discipline: {top_discipline['discipline']} (Score: {top_discipline['pain_point_score']:.2f})")
    
    # Section 2: Project Analysis
    print("\n\n" + "="*80)
    print("PROJECT PAIN POINT ANALYSIS")
    print("="*80)
    
    for i, proj in enumerate(projects, 1):
        print(f"\n{i}. {proj['project_name']} ({proj['source']})")
        print(f"   {'='*75}")
        print(f"   Total Issues: {proj['total_issues']:,}")
        print(f"   Status: Open={proj['open_issues']:,} ({proj['open_issues']/proj['total_issues']*100:.1f}%) | " + 
              f"Closed={proj['closed_issues']:,} ({proj['closed_issues']/proj['total_issues']*100:.1f}%)")
        print(f"   Pain Score: {proj['pain_point_score']:.2f}/1.00")
        
        if proj['avg_resolution_days']:
            print(f"   Avg Resolution Time: {proj['avg_resolution_days']:.0f} days")
        
        print(f"\n   Discipline Breakdown:")
        discs = [
            ("Electrical", proj['electrical_issues']),
            ("Hydraulic/Plumbing", proj['hydraulic_issues']),
            ("Mechanical", proj['mechanical_issues']),
            ("Structural", proj['structural_issues']),
            ("Architectural", proj['architectural_issues'])
        ]
        discs.sort(key=lambda x: x[1], reverse=True)
        for disc_name, count in discs[:3]:
            pct = (count / proj['total_issues'] * 100) if proj['total_issues'] > 0 else 0
            print(f"      • {disc_name}: {count:,} ({pct:.1f}%)")
        
        print(f"\n   Issue Type Breakdown:")
        types = [
            ("Clash/Coordination", proj['clash_issues']),
            ("Information Request", proj['info_issues']),
            ("Design Issue", proj['design_issues']),
            ("Constructability", proj['constructability_issues'])
        ]
        types.sort(key=lambda x: x[1], reverse=True)
        for type_name, count in types:
            if count > 0:
                pct = (count / proj['total_issues'] * 100) if proj['total_issues'] > 0 else 0
                print(f"      • {type_name}: {count:,} ({pct:.1f}%)")
        
        # Recommendations
        print(f"\n   💡 Recommendations:")
        if proj['open_issues'] / proj['total_issues'] > 0.4:
            print(f"      ⚠️  HIGH: {proj['open_issues']/proj['total_issues']*100:.0f}% open rate - Review workflow bottlenecks")
        if proj['clash_issues'] / proj['total_issues'] > 0.5:
            print(f"      ⚠️  HIGH: {proj['clash_issues']/proj['total_issues']*100:.0f}% clash issues - Improve coordination")
        if proj['electrical_issues'] > proj['total_issues'] * 0.3:
            print(f"      • Focus on electrical coordination ({proj['electrical_issues']/proj['total_issues']*100:.0f}% of issues)")
        if proj['hydraulic_issues'] > proj['total_issues'] * 0.2:
            print(f"      • Review hydraulic/plumbing workflows ({proj['hydraulic_issues']/proj['total_issues']*100:.0f}% of issues)")
    
    # Section 3: Discipline Analysis
    print("\n\n" + "="*80)
    print("DISCIPLINE PAIN POINT ANALYSIS")
    print("="*80)
    
    for i, disc in enumerate(disciplines, 1):
        print(f"\n{i}. {disc['discipline']}")
        print(f"   {'='*75}")
        print(f"   Total Issues: {disc['total_issues']:,} across {disc['project_count']} projects")
        print(f"   Issues per Project: {disc['issues_per_project']:.1f}")
        print(f"   Pain Score: {disc['pain_point_score']:.2f}/1.00")
        print(f"   Status: Open={disc['open_issues']:,} ({disc['open_issues']/disc['total_issues']*100:.1f}%) | " +
              f"Closed={disc['closed_issues']:,} ({disc['closed_issues']/disc['total_issues']*100:.1f}%)")
        
        if disc['avg_resolution_days']:
            print(f"   Avg Resolution Time: {disc['avg_resolution_days']:.0f} days")
        
        print(f"\n   Top Issue Types:")
        types = [
            ("Clash/Coordination", disc['clash_issues']),
            ("Information Request", disc['info_issues']),
            ("Design Issue", disc['design_issues']),
            ("Constructability", disc['constructability_issues'])
        ]
        types.sort(key=lambda x: x[1], reverse=True)
        for type_name, count in types:
            if count > 0:
                pct = (count / disc['total_issues'] * 100) if disc['total_issues'] > 0 else 0
                print(f"      • {type_name}: {count:,} ({pct:.1f}%)")
        
        # Recommendations
        print(f"\n   💡 Recommendations:")
        if disc['pain_point_score'] > 0.2:
            print(f"      ⚠️  HIGH PAIN: Review {disc['discipline']} workflows and resources")
        if disc['clash_issues'] > disc['total_issues'] * 0.5:
            print(f"      • Improve coordination protocols for {disc['discipline']}")
        if disc['info_issues'] > disc['total_issues'] * 0.1:
            print(f"      • Establish better information flow processes")
        if disc['open_issues'] / disc['total_issues'] > 0.35:
            print(f"      • Address high open rate ({disc['open_issues']/disc['total_issues']*100:.0f}%)")
    
    # Section 4: Recurring Patterns
    print("\n\n" + "="*80)
    print("RECURRING ISSUE PATTERNS")
    print("="*80)
    print(f"\nIdentified {len(patterns)} recurring patterns (showing top 10)")
    
    for i, pattern in enumerate(patterns[:10], 1):
        print(f"\n{i}. Pattern #{pattern['pattern_id']}")
        print(f"   Keywords: {pattern['common_keywords']}")
        print(f"   Occurrences: {pattern['occurrence_count']} across {pattern['project_count']} project(s)")
        print(f"   Primary Discipline: {pattern['top_discipline']}")
        print(f"   Primary Issue Type: {pattern['top_issue_type']}")
        print(f"   Examples:")
        for ex in pattern['example_titles'][:2]:
            print(f"      • {ex[:70]}...")
        
        # Pattern-specific recommendations
        if pattern['occurrence_count'] > 100:
            print(f"   💡 Recommendation: HIGH FREQUENCY PATTERN - Create standard workflow/checklist")
        elif pattern['occurrence_count'] > 50:
            print(f"   💡 Recommendation: Consider proactive measures to prevent this pattern")
    
    # Section 5: Key Insights
    print("\n\n" + "="*80)
    print("KEY INSIGHTS & RECOMMENDATIONS")
    print("="*80)
    
    print("\n🎯 Main Pain Points:")
    print(f"   1. {top_discipline['discipline']} discipline has highest pain score")
    print(f"   2. {sum(d['clash_issues'] for d in disciplines):,} clash/coordination issues across all projects")
    print(f"   3. {sum(p['open_issues'] for p in projects):,} unresolved issues require attention")
    
    # Calculate averages
    avg_resolution = sum(p.get('avg_resolution_days', 0) or 0 for p in projects if p.get('avg_resolution_days')) / len([p for p in projects if p.get('avg_resolution_days')])
    
    print(f"\n📊 Performance Metrics:")
    print(f"   • Average Resolution Time: {avg_resolution:.0f} days")
    print(f"   • Overall Open Rate: {total_open/total_issues*100:.1f}%")
    print(f"   • Projects Analyzed: {len(projects)}")
    
    print(f"\n🎯 Actionable Recommendations:")
    print(f"   1. Focus coordination efforts on {top_discipline['discipline']} ({top_discipline['total_issues']:,} issues)")
    print(f"   2. Implement clash detection protocols for high-frequency patterns")
    print(f"   3. Review workflows for projects with >40% open rate")
    print(f"   4. Establish discipline-specific quality checklists")
    print(f"   5. Consider additional resources for top 3 disciplines")
    
    # Save to file if requested
    if output_file:
        report_data = {
            'generated_at': datetime.now().isoformat(),
            'summary': {
                'total_issues': total_issues,
                'total_open': total_open,
                'total_closed': total_closed,
                'project_count': len(projects),
                'pattern_count': len(patterns)
            },
            'projects': projects,
            'disciplines': disciplines,
            'patterns': patterns[:20]  # Top 20 patterns
        }
        
        with open(output_file, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        print(f"\n\n✅ Report data saved to: {output_file}")
    
    print("\n\n" + "="*80)
    print("REPORT COMPLETE")
    print("="*80)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate Issue Analytics Report')
    parser.add_argument('--output', '-o', help='Output JSON file path', default=None)
    args = parser.parse_args()
    
    generate_report(args.output)
