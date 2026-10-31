import psycopg2
import json
from app.config import settings

def inspect_foreign_keys():
    conn = psycopg2.connect(
        dbname=settings.DB_NAME,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD,
        host=settings.DB_HOST,
        port=settings.DB_PORT
    )
    cur = conn.cursor()

    query = """
    SELECT
        tc.table_name AS source_table,
        kcu.column_name AS source_column,
        ccu.table_name AS referenced_table,
        ccu.column_name AS referenced_column,
        rc.delete_rule AS on_delete,
        rc.update_rule AS on_update,
        tc.constraint_name
    FROM information_schema.table_constraints AS tc
    JOIN information_schema.key_column_usage AS kcu
        ON tc.constraint_name = kcu.constraint_name
        AND tc.table_schema = kcu.table_schema
    JOIN information_schema.referential_constraints AS rc
        ON tc.constraint_name = rc.constraint_name
    JOIN information_schema.constraint_column_usage AS ccu
        ON rc.unique_constraint_name = ccu.constraint_name
        AND rc.unique_constraint_schema = ccu.constraint_schema
    WHERE tc.constraint_type = 'FOREIGN KEY'
        AND tc.table_schema = 'public'
    ORDER BY tc.table_name, kcu.column_name;
    """

    cur.execute(query)
    rows = cur.fetchall()
    
    # Also check pg_constraint directly to verify composite keys or count differences
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
    pg_rows = cur.fetchall()

    print(f"Information Schema FK Count: {len(rows)}")
    print(f"pg_constraint FK Count: {len(pg_rows)}")

    # Distinct constraints
    cur.execute("""
    SELECT count(*) 
    FROM pg_constraint 
    WHERE contype = 'f' AND connamespace = 'public'::regnamespace;
    """)
    distinct_fks = cur.fetchone()[0]
    print(f"Distinct Foreign Key Constraints: {distinct_fks}")

    with open("fk_details.json", "w") as f:
        json.dump([
            {
                "index": i + 1,
                "source_table": r[0],
                "source_column": r[1],
                "referenced_table": r[2],
                "referenced_column": r[3],
                "on_delete": r[4],
                "on_update": r[5],
                "constraint_name": r[6]
            }
            for i, r in enumerate(pg_rows)
        ], f, indent=2)

    cur.close()
    conn.close()

if __name__ == "__main__":
    inspect_foreign_keys()
