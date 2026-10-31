import psycopg2
from app.config import settings
from app.models import Base

def verify():
    conn = psycopg2.connect(
        dbname=settings.DB_NAME,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        host=settings.DB_HOST,
        port=settings.DB_PORT
    )
    cur = conn.cursor()

    pg_query = """
    SELECT
        conrelid::regclass::text AS source_table,
        a.attname AS source_column,
        confrelid::regclass::text AS referenced_table,
        af.attname AS referenced_column,
        CASE confdeltype
            WHEN 'c' THEN 'CASCADE'
            WHEN 'n' THEN 'SET NULL'
            WHEN 'd' THEN 'SET DEFAULT'
            WHEN 'r' THEN 'RESTRICT'
            WHEN 'a' THEN 'NO ACTION'
        END AS on_delete,
        CASE confupdtype
            WHEN 'c' THEN 'CASCADE'
            WHEN 'n' THEN 'SET NULL'
            WHEN 'd' THEN 'SET DEFAULT'
            WHEN 'r' THEN 'RESTRICT'
            WHEN 'a' THEN 'NO ACTION'
        END AS on_update,
        conname AS constraint_name
    FROM pg_constraint c
    JOIN pg_attribute a ON a.attnum = ANY(c.conkey) AND a.attrelid = c.conrelid
    JOIN pg_attribute af ON af.attnum = ANY(c.confkey) AND af.attrelid = c.confrelid
    WHERE c.contype = 'f'
        AND c.connamespace = 'public'::regnamespace
    ORDER BY source_table, source_column;
    """
    cur.execute(pg_query)
    pg_fks = cur.fetchall()

    # Build DB map: (source_table, source_column) -> (referenced_table, referenced_column, on_delete)
    db_fk_map = {}
    for r in pg_fks:
        key = (r[0], r[1])
        db_fk_map[key] = {
            "ref_table": r[2],
            "ref_col": r[3],
            "on_delete": r[4],
            "on_update": r[5],
            "name": r[6]
        }

    # Extract all SQLAlchemy foreign keys from Base.metadata
    sa_fk_map = {}
    for table_name, table in Base.metadata.tables.items():
        for fk in table.foreign_keys:
            col_name = fk.parent.name
            ref_col_full = fk.target_fullname  # e.g. "users.id"
            ref_table, ref_col = ref_col_full.split(".")
            on_delete = (fk.ondelete or "NO ACTION").upper()
            sa_fk_map[(table_name, col_name)] = {
                "ref_table": ref_table,
                "ref_col": ref_col,
                "on_delete": on_delete
            }

    print("=== SUMMARY COUNTS ===")
    print(f"Total PostgreSQL Foreign Keys: {len(db_fk_map)}")
    print(f"Total SQLAlchemy Model Foreign Keys: {len(sa_fk_map)}")

    # Check differences
    missing_in_db = set(sa_fk_map.keys()) - set(db_fk_map.keys())
    missing_in_sa = set(db_fk_map.keys()) - set(sa_fk_map.keys())

    print(f"Foreign keys defined in SQLAlchemy but missing in PostgreSQL: {missing_in_db}")
    print(f"Foreign keys defined in PostgreSQL but missing in SQLAlchemy: {missing_in_sa}")

    # Check target table matches
    mismatched_targets = []
    for k in db_fk_map:
        if k in sa_fk_map:
            db_ref = db_fk_map[k]["ref_table"]
            sa_ref = sa_fk_map[k]["ref_table"]
            if db_ref != sa_ref:
                mismatched_targets.append((k, db_ref, sa_ref))

    print(f"Mismatched target tables: {mismatched_targets}")

    # Inspect tables with NO foreign keys (base/catalog tables)
    tables_with_fks = {k[0] for k in db_fk_map.keys()}
    all_75_tables = set(Base.metadata.tables.keys())
    tables_without_fks = sorted(all_75_tables - tables_with_fks)
    print(f"\nTables with NO outgoing foreign keys (base master tables): {tables_without_fks}")

    # Verify tables referenced by other tables
    referenced_tables = {v["ref_table"] for v in db_fk_map.values()}
    unreferenced_tables = sorted(all_75_tables - referenced_tables)
    print(f"Tables not referenced by any foreign key (leaf/transaction log tables): {unreferenced_tables}")

    # ON DELETE distribution
    on_delete_counts = {}
    for v in db_fk_map.values():
        del_rule = v["on_delete"]
        on_delete_counts[del_rule] = on_delete_counts.get(del_rule, 0) + 1
    print(f"\nON DELETE rule distribution: {on_delete_counts}")

    # ON UPDATE distribution
    on_update_counts = {}
    for v in db_fk_map.values():
        upd_rule = v["on_update"]
        on_update_counts[upd_rule] = on_update_counts.get(upd_rule, 0) + 1
    print(f"ON UPDATE rule distribution: {on_update_counts}")

    cur.close()
    conn.close()

if __name__ == "__main__":
    verify()
