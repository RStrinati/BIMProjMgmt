from check_schema import (
    load_required_schema,
    table_to_class,
    column_to_const,
    generate_create_table_sql,
)
from constants import schema as S


def test_load_required_schema_contains_projects():
    required = load_required_schema()
    assert S.Projects.TABLE in required
    assert S.Projects.NAME in required[S.Projects.TABLE]


def test_table_and_column_helpers():
    assert table_to_class("tblACCDocs") == "ACCDocs"
    assert table_to_class("review_tasks") == "ReviewTasks"
    assert column_to_const("my-column") == "MY_COLUMN"


def test_generate_create_table_sql():
    sql = generate_create_table_sql("Demo", ["a", "b"])
    assert "CREATE TABLE [Demo]" in sql
    assert "[a] NVARCHAR(MAX)" in sql
    assert "[b] NVARCHAR(MAX)" in sql
