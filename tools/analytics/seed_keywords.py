"""
Seed Issue Category Keywords
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database_pool import get_db_connection

def get_category_id(cursor, name, level):
    """Get category ID by name and level."""
    cursor.execute(f"""
        SELECT category_id 
        FROM IssueCategories 
        WHERE category_name = ? AND category_level = ?
    """, (name, level))
    result = cursor.fetchone()
    return result[0] if result else None

def seed_discipline_keywords(cursor, conn):
    """Seed discipline-level keywords."""
    print("Seeding discipline keywords...")
    
    disciplines = {
        'Structural': ['structural', 'structure', 'steel', 'concrete', 'column', 'beam', 'slab', 
                      'foundation', 'reinforcement', 'rebar', 'footing', 'str'],
        'Architectural': ['architectural', 'architecture', 'façade', 'facade', 'cladding', 'interior',
                         'finish', 'wall', 'door', 'window', 'ceiling', 'partition', 'arch'],
        'Mechanical (HVAC)': ['mechanical', 'hvac', 'ductwork', 'duct', 'ventilation', 'ahu',
                             'air handling', 'chiller', 'cooling', 'heating', 'exhaust', 'mech'],
        'Electrical': ['electrical', 'electric', 'power', 'lighting', 'cable', 'conduit',
                      'switchboard', 'distribution', 'socket', 'outlet', 'transformer', 'panel',
                      'ele', 'elec', 'low voltage', 'cable tray'],
        'Hydraulic/Plumbing': ['hydraulic', 'plumbing', 'pipework', 'pipe', 'drainage', 'water',
                              'sanitary', 'sewer', 'waste', 'pump', 'valve', 'hyd', 'drain',
                              'gas', 'hot water', 'cold water'],
        'Fire Protection': ['fire protection', 'fire', 'sprinkler', 'hydrant', 'fire hose',
                           'fire alarm', 'smoke detector', 'fire suppression', 'fire rated',
                           'fire safety', 'fire exit'],
        'Civil': ['civil', 'siteworks', 'earthworks', 'excavation', 'external drainage',
                 'stormwater', 'pavement', 'retaining wall', 'site', 'grading', 'survey']
    }
    
    weights = {
        'Structural': [1.0, 0.95, 0.90, 0.90, 0.85, 0.85, 0.85, 0.85, 0.80, 0.80, 0.80, 0.75],
        'Architectural': [1.0, 0.95, 0.90, 0.90, 0.90, 0.85, 0.80, 0.75, 0.75, 0.75, 0.75, 0.80, 0.70],
        'Mechanical (HVAC)': [1.0, 1.0, 0.95, 0.90, 0.90, 0.95, 0.95, 0.90, 0.80, 0.80, 0.85, 0.75],
        'Electrical': [1.0, 0.95, 0.90, 0.90, 0.85, 0.90, 0.95, 0.80, 0.80, 0.80, 0.85, 0.75, 0.70, 0.75, 0.85, 0.90],
        'Hydraulic/Plumbing': [1.0, 1.0, 0.95, 0.85, 0.95, 0.85, 0.90, 0.90, 0.85, 0.80, 0.75, 0.75, 0.85, 0.80, 0.85, 0.85],
        'Fire Protection': [1.0, 0.90, 0.95, 0.95, 0.95, 0.95, 0.90, 0.95, 0.85, 0.90, 0.85],
        'Civil': [1.0, 0.95, 0.95, 0.90, 0.95, 0.90, 0.85, 0.90, 0.70, 0.85, 0.75]
    }
    
    count = 0
    for disc_name, keywords in disciplines.items():
        disc_id = get_category_id(cursor, disc_name, 1)
        if not disc_id:
            print(f"⚠️  Discipline not found: {disc_name}")
            continue
        
        disc_weights = weights.get(disc_name, [1.0] * len(keywords))
        
        for i, keyword in enumerate(keywords):
            weight = disc_weights[i] if i < len(disc_weights) else 1.0
            try:
                cursor.execute("""
                    INSERT INTO IssueCategoryKeywords (category_id, keyword, weight)
                    VALUES (?, ?, ?)
                """, (disc_id, keyword.lower(), weight))
                count += 1
            except Exception as e:
                if 'duplicate' not in str(e).lower():
                    print(f"⚠️  Error adding keyword '{keyword}': {e}")
    
    conn.commit()
    print(f"✓ Added {count} discipline keywords")

def seed_type_keywords(cursor, conn):
    """Seed issue type keywords."""
    print("Seeding issue type keywords...")
    
    type_keywords = {
        'Clash/Coordination': [
            ('clash', 0.95), ('conflict', 0.90), ('overlap', 0.90),
            ('interference', 0.85), ('coordination', 0.85), ('clashing', 0.90),
            ('clearance', 0.85), ('space', 0.70)
        ],
        'Design Issue': [
            ('design', 0.90), ('error', 0.85), ('incorrect', 0.85),
            ('mistake', 0.85), ('wrong', 0.80), ('incomplete', 0.85),
            ('missing', 0.80), ('change', 0.75), ('revision', 0.75),
            ('redesign', 0.85)
        ],
        'Information Issue': [
            ('rfi', 0.95), ('request for information', 0.95),
            ('missing information', 0.90), ('clarification', 0.90),
            ('clarify', 0.85), ('unclear', 0.85), ('confirm', 0.75),
            ('specification', 0.75), ('detail', 0.70)
        ],
        'Code Compliance': [
            ('code', 0.90), ('compliance', 0.90), ('standard', 0.85),
            ('regulation', 0.90), ('non-compliant', 0.95), ('violation', 0.90),
            ('requirement', 0.75), ('bca', 0.95), ('as/nzs', 0.90),
            ('authority', 0.80)
        ],
        'Constructability': [
            ('constructability', 0.95), ('cannot build', 0.95),
            ('cannot install', 0.95), ('installation', 0.80),
            ('access', 0.80), ('difficult', 0.75), ('impossible', 0.90),
            ('sequence', 0.80), ('tolerance', 0.80)
        ],
        'Quality Issue': [
            ('quality', 0.90), ('defect', 0.90), ('workmanship', 0.90),
            ('poor quality', 0.95), ('material', 0.75), ('damage', 0.80),
            ('inspection', 0.75), ('failed', 0.80)
        ]
    }
    
    count = 0
    # Get all type categories (level 2)
    cursor.execute("""
        SELECT category_id, category_name, parent_category_id
        FROM IssueCategories
        WHERE category_level = 2
    """)
    
    type_cats = cursor.fetchall()
    
    for cat_id, cat_name, parent_id in type_cats:
        if cat_name in type_keywords:
            keywords = type_keywords[cat_name]
            
            for keyword, weight in keywords:
                try:
                    cursor.execute("""
                        INSERT INTO IssueCategoryKeywords (category_id, keyword, weight)
                        VALUES (?, ?, ?)
                    """, (cat_id, keyword.lower(), weight))
                    count += 1
                except Exception as e:
                    if 'duplicate' not in str(e).lower():
                        print(f"⚠️  Error adding keyword '{keyword}': {e}")
    
    conn.commit()
    print(f"✓ Added {count} type keywords")

def seed_subtype_keywords(cursor, conn):
    """Seed sub-type keywords."""
    print("Seeding sub-type keywords...")
    
    subtype_keywords = {
        'Clearance Issue': [
            ('clearance', 0.95), ('<300mm', 1.0), ('< 300mm', 1.0),
            ('insufficient space', 0.90), ('too close', 0.90),
            ('tight', 0.80), ('minimum clearance', 0.95)
        ],
        'Penetration Conflict': [
            ('peno', 0.95), ('penetration', 0.95), ('core', 0.80),
            ('hole', 0.75), ('sleeve', 0.85), ('pass-through', 0.85),
            ('opening', 0.70), ('misalignment', 0.85)
        ],
        'Hard Clash': [
            ('hard clash', 1.0), ('physical overlap', 0.95),
            ('overlap', 0.85), ('intersecting', 0.85)
        ],
        'Service Routing': [
            ('routing', 0.90), ('path', 0.75), ('route', 0.85),
            ('service run', 0.90)
        ]
    }
    
    count = 0
    # Get all subtype categories (level 3)
    cursor.execute("""
        SELECT category_id, category_name
        FROM IssueCategories
        WHERE category_level = 3
    """)
    
    subtype_cats = cursor.fetchall()
    
    for cat_id, cat_name in subtype_cats:
        if cat_name in subtype_keywords:
            keywords = subtype_keywords[cat_name]
            
            for keyword, weight in keywords:
                try:
                    cursor.execute("""
                        INSERT INTO IssueCategoryKeywords (category_id, keyword, weight)
                        VALUES (?, ?, ?)
                    """, (cat_id, keyword.lower(), weight))
                    count += 1
                except Exception as e:
                    if 'duplicate' not in str(e).lower():
                        print(f"⚠️  Error adding keyword '{keyword}': {e}")
    
    conn.commit()
    print(f"✓ Added {count} sub-type keywords")

if __name__ == "__main__":
    print("=" * 70)
    print("Seeding Issue Category Keywords")
    print("=" * 70)
    
    with get_db_connection('ProjectManagement') as conn:
    if not conn:
        print("❌ Database connection failed")
        exit(1)
    
    try:
        cursor = conn.cursor()
        
        # Clear existing keywords
        cursor.execute("DELETE FROM IssueCategoryKeywords")
        conn.commit()
        print("✓ Cleared existing keywords\n")
        
        # Seed keywords
        seed_discipline_keywords(cursor, conn)
        seed_type_keywords(cursor, conn)
        seed_subtype_keywords(cursor, conn)
        
        # Verify
        cursor.execute("SELECT COUNT(*) FROM IssueCategoryKeywords")
        total = cursor.fetchone()[0]
        
        print("\n" + "=" * 70)
        print(f"✓ Seeding complete: {total} keywords added")
        print("=" * 70)
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
