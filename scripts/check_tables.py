import os
import psycopg2

conn = psycopg2.connect(
    host=os.getenv('POSTGRES_HOST', 'localhost'),
    port=os.getenv('POSTGRES_PORT', '5432'),
    database=os.getenv('POSTGRES_DB', 'realestate'),
    user=os.getenv('POSTGRES_USER', 'postgres'),
    password=os.getenv('POSTGRES_PASSWORD', 'postgres')
)
cur = conn.cursor()
cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
print('테이블 목록:')
for row in cur.fetchall():
    print(f'  - {row[0]}')
    
# landbroker 테이블 데이터 수 확인
cur.execute("SELECT COUNT(*) FROM landbroker")
count = cur.fetchone()[0]
print(f'\nlandbroker 테이블 데이터 수: {count}')

cur.close()
conn.close()
