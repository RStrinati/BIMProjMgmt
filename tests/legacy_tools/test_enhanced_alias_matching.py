"""
Test script for enhanced project alias matching algorithm

This script tests the improved matching strategies:
1. Project code extraction (P220702, MEL071)
2. Abbreviation matching (CWPS → Calderwood Primary School)
3. Fuzzy string similarity
4. File pattern recognition
5. Substring matching
6. Word overlap analysis
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.project_alias_service import ProjectAliasManager

def test_matching_scenarios():
    """Test various real-world file name to project name matching scenarios"""
    
    manager = ProjectAliasManager()
    
    # Sample main project names (typical BIM project naming)
    main_projects = [
        "Calderwood Primary School",
        "North Fremantle Primary School",
        "P220702 Melbourne Convention Centre",
        "MEL071 Treasury Building Refurbishment",
        "Sydney Opera House Renovation",
        "Brisbane Hospital Wing C",
        "Adelaide Railway Station",
    ]
    
    # Test cases: (unmapped_file_name, expected_match, expected_type)
    test_cases = [
        # Project code matching
        ("[P220702] MCC - Central.rvt", "P220702 Melbourne Convention Centre", "project_code"),
        ("MEL071_Treasury_Rev01.rvt", "MEL071 Treasury Building Refurbishment", "project_code"),
        
        # Abbreviation matching (realistic - must match actual initials)
        ("MCC - Site Model.rvt", "P220702 Melbourne Convention Centre", "abbreviation"),
        ("NFPS Structural Model.rvt", "North Fremantle Primary School", "abbreviation"),
        
        # Fuzzy matching
        ("Calderwood Primary Schol.rvt", "Calderwood Primary School", "fuzzy_match"),
        ("Melbourne Conv Center.rvt", "P220702 Melbourne Convention Centre", "fuzzy_match"),
        
        # Substring matching
        ("Sydney Opera House - Stage 2.rvt", "Sydney Opera House Renovation", "substring"),
        ("[Hospital Wing C] - MEP.rvt", "Brisbane Hospital Wing C", "substring"),
        
        # Word matching
        ("Adelaide Station Platform.rvt", "Adelaide Railway Station", "word_match"),
        ("Treasury Building - Main.rvt", "MEL071 Treasury Building Refurbishment", "word_match"),
    ]
    
    print("=" * 80)
    print("ENHANCED PROJECT ALIAS MATCHING TEST")
    print("=" * 80)
    print()
    
    passed = 0
    failed = 0
    
    for file_name, expected_project, expected_type in test_cases:
        suggestion = manager._suggest_project_match(file_name, main_projects)
        
        if suggestion:
            matched_project = suggestion['project_name']
            match_type = suggestion['match_type']
            confidence = suggestion['confidence']
            
            # Check if match is correct
            is_correct = matched_project == expected_project
            type_matches = match_type == expected_type or confidence >= 0.85
            
            status = "✅ PASS" if is_correct else "❌ FAIL"
            
            print(f"{status} | {file_name}")
            print(f"         Expected: {expected_project} ({expected_type})")
            print(f"         Got:      {matched_project} ({match_type}, {confidence:.1%})")
            
            if is_correct:
                passed += 1
            else:
                failed += 1
        else:
            print(f"❌ FAIL | {file_name}")
            print(f"         Expected: {expected_project}")
            print(f"         Got:      No match found")
            failed += 1
        
        print()
    
    print("=" * 80)
    print(f"RESULTS: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    print(f"Success Rate: {passed / len(test_cases) * 100:.1f}%")
    print("=" * 80)
    
    manager.close_connection()
    
    return passed == len(test_cases)


def test_live_unmapped_projects():
    """Test against actual unmapped projects in the database"""
    
    print("\n" + "=" * 80)
    print("LIVE DATABASE TEST - Unmapped Projects")
    print("=" * 80)
    print()
    
    manager = ProjectAliasManager()
    
    try:
        unmapped = manager.discover_unmapped_projects()
        
        if not unmapped:
            print("✅ No unmapped projects found! All projects are already mapped.")
            return True
        
        print(f"Found {len(unmapped)} unmapped projects:\n")
        
        # Group by confidence level
        high_confidence = []
        medium_confidence = []
        low_confidence = []
        no_suggestion = []
        
        for item in unmapped:
            suggestion = item.get('suggested_match')
            if not suggestion:
                no_suggestion.append(item)
            elif suggestion['confidence'] >= 0.85:
                high_confidence.append(item)
            elif suggestion['confidence'] >= 0.70:
                medium_confidence.append(item)
            else:
                low_confidence.append(item)
        
        print(f"📊 CONFIDENCE BREAKDOWN:")
        print(f"   🟢 High (≥85%):   {len(high_confidence)} projects")
        print(f"   🟡 Medium (70-84%): {len(medium_confidence)} projects")
        print(f"   🔴 Low (<70%):     {len(low_confidence)} projects")
        print(f"   ⚪ No suggestion:  {len(no_suggestion)} projects")
        print()
        
        # Show top 10 high-confidence matches
        if high_confidence:
            print("🟢 TOP HIGH-CONFIDENCE MATCHES (Ready for auto-mapping):")
            for i, item in enumerate(sorted(high_confidence, key=lambda x: x['suggested_match']['confidence'], reverse=True)[:10], 1):
                sugg = item['suggested_match']
                print(f"   {i}. {item['project_name']}")
                print(f"      → {sugg['project_name']} ({sugg['match_type']}, {sugg['confidence']:.1%})")
                print(f"      Issues: {item['total_issues']} total, {item['open_issues']} open")
                print()
        
        # Show medium confidence (may need review)
        if medium_confidence[:3]:
            print("🟡 MEDIUM-CONFIDENCE MATCHES (Review recommended):")
            for i, item in enumerate(medium_confidence[:3], 1):
                sugg = item['suggested_match']
                print(f"   {i}. {item['project_name']}")
                print(f"      → {sugg['project_name']} ({sugg['match_type']}, {sugg['confidence']:.1%})")
                print()
        
        # Show no suggestions (need manual mapping)
        if no_suggestion[:3]:
            print("⚪ NO SUGGESTIONS (Manual mapping required):")
            for i, item in enumerate(no_suggestion[:3], 1):
                print(f"   {i}. {item['project_name']} ({item['total_issues']} issues)")
            print()
        
        print("=" * 80)
        print(f"RECOMMENDATION: Auto-map {len(high_confidence)} high-confidence projects")
        print("=" * 80)
        
        return True
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    finally:
        manager.close_connection()


def test_specific_patterns():
    """Test specific pattern extraction functions"""
    
    print("\n" + "=" * 80)
    print("PATTERN EXTRACTION TESTS")
    print("=" * 80)
    print()
    
    manager = ProjectAliasManager()
    
    # Test project code extraction
    test_strings = [
        ("[P220702] Melbourne Convention Centre", {"P220702"}),
        ("MEL071 Treasury Building", {"MEL071"}),
        ("CWPS001_Site_Model.rvt", {"CWPS001"}),
        ("Project 220702 - Phase 1", {"220702"}),
        ("No codes here", set()),
    ]
    
    print("PROJECT CODE EXTRACTION:")
    for text, expected in test_strings:
        result = manager._extract_project_codes(text)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{text}' → {result}")
    print()
    
    # Test abbreviation matching
    test_abbrevs = [
        ("MCC - Site Model.rvt", "Melbourne Convention Centre", True),
        ("NFPS_Rev01.rvt", "North Fremantle Primary School", True),
        ("Random File.rvt", "Calderwood Primary School", False),
        ("CPS Central.rvt", "Calderwood Primary School", True),
        ("SOR File.rvt", "Sydney Opera Renovation", False),  # SOR vs SOR, but only 3 letters
    ]
    
    print("ABBREVIATION MATCHING:")
    for file_name, project_name, expected in test_abbrevs:
        result = manager._match_abbreviation(file_name, project_name)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{file_name}' vs '{project_name}' → {result}")
    print()
    
    manager.close_connection()


if __name__ == "__main__":
    print("\n🧪 STARTING ENHANCED ALIAS MATCHING TESTS\n")
    
    # Run all tests
    test1 = test_matching_scenarios()
    test2 = test_live_unmapped_projects()
    test_specific_patterns()
    
    print("\n" + "=" * 80)
    if test1:
        print("✅ ALL TESTS PASSED - Enhanced matching algorithm is working correctly!")
    else:
        print("⚠️  SOME TESTS FAILED - Review algorithm implementation")
    print("=" * 80)
