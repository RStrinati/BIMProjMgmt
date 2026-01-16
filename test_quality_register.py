"""Quick test of fixed get_model_register()"""
from database import get_model_register

# Test with project 2 (NFPS)
result = get_model_register(project_id=2, page=1, page_size=50, filter_attention=False)

print(f'Total rows: {result["total"]}')
print(f'Returned rows: {len(result["rows"])}')
print(f'Attention count: {result["attention_count"]}')

if result['rows']:
    print(f'\nFirst 3 rows:')
    for i, row in enumerate(result['rows'][:3], 1):
        print(f'\nRow {i}:')
        print(f'  modelName: {row["modelName"]}')
        print(f'  discipline: {row["discipline"]}')
        print(f'  namingStatus: {row.get("namingStatus", "N/A")}')
        print(f'  freshnessStatus: {row["freshnessStatus"]}')
        print(f'  validationOverall: {row["validationOverall"]}')
        print(f'  lastVersionDate: {row["lastVersionDateISO"]}')
else:
    print('ERROR: No rows returned!')
