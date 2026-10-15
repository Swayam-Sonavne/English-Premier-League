import sqlite3, pandas as pd
con = sqlite3.connect('epl_dw.db')
tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table'", con)
print('TABLES:', tables.name.tolist())
for t in tables.name:
    cnt = pd.read_sql(f'SELECT COUNT(*) c FROM {t}', con).c[0]
    cols = pd.read_sql(f'SELECT * FROM {t} LIMIT 1', con).columns.tolist()
    print(f'\n{t} ({cnt:,} rows):')
    print('  Cols:', cols)
    sample = pd.read_sql(f'SELECT * FROM {t} LIMIT 3', con)
    print(sample.to_string())
con.close()
