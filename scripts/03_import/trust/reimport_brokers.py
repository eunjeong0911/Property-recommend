"""
JSON 원본 파일에서 중개사 정보를 직접 추출하여 landbroker 테이블에 저장

agent_info 컬럼 제거로 인해 원본 JSON 파일(data/RDB/land/*.json)에서 직접 읽어옵니다.
"""
import os
import sys
import json
import psycopg2

# Database connection
def get_db_connection():
    return psycopg2.connect(
        host=os.getenv('POSTGRES_HOST', 'localhost'),
        port=os.getenv('POSTGRES_PORT', '5432'),
        database=os.getenv('POSTGRES_DB', 'realestate'),
        user=os.getenv('POSTGRES_USER', 'postgres'),
        password=os.getenv('POSTGRES_PASSWORD', 'postgres')
    )


def import_brokers_from_json():
    """JSON 파일에서 중개사 정보 추출 및 저장"""
    print("=" * 70)
    print(" " * 15 + "중개사 정보 Import (JSON 기반)")
    print("=" * 70 + "\n")
    
    # 1. 데이터 소스 및 파일 수집
    data_sources = []
    
    # (1) RDB/land
    if os.path.exists("/app/data/RDB/land"):
        data_sources.append("/app/data/RDB/land")
    else:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        local_land = os.path.join(base_dir, "data", "RDB", "land")
        if os.path.exists(local_land):
            data_sources.append(local_land)

    # (2) zigbangland (직방)
    if os.path.exists("/app/data/zigbangland"):
         data_sources.append("/app/data/zigbangland")
         print("Docker 환경 감지: zigbangland 추가")
    else:
         base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
         local_zigbang = os.path.join(base_dir, "data", "zigbangland")
         if os.path.exists(local_zigbang):
             data_sources.append(local_zigbang)
             print(f"로컬 환경 감지: {local_zigbang} 추가")
    
    # 모든 JSON 파일 수집
    json_files = []
    for d_dir in data_sources:
        if os.path.exists(d_dir):
            found = [os.path.join(d_dir, f) for f in os.listdir(d_dir) if f.endswith('.json')]
            json_files.extend(found)
    
    print(f"1. JSON 파일 읽기 중... (총 {len(json_files)}개 파일)\n")
    
    # 2. 중개사 정보 수집 (등록번호 기준 중복 제거)
    brokers_dict = {}  # {registration_number: {info, land_nums}}
    
    for file_path in json_files:
        json_file = os.path.basename(file_path)
        if not os.path.exists(file_path):
            print(f"  ⚠ 파일 없음: {json_file}")
            continue
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"  ✓ {json_file}: {len(data)}개 매물")
        
        for item in data:
            agent_info = item.get('중개사_정보', {})
            if not agent_info:
                continue
            
            # 등록번호 추출
            reg_num = agent_info.get('registration_number') or agent_info.get('등록번호')
            land_num = item.get('매물번호')
            
            if not reg_num or not land_num:
                continue
            
            if reg_num not in brokers_dict:
                brokers_dict[reg_num] = {
                    'info': agent_info,
                    'land_nums': []
                }
            
            brokers_dict[reg_num]['land_nums'].append(land_num)
    
    print(f"\n  총 {len(brokers_dict)}개 고유 중개사 발견\n")
    
    # 3. DB에 저장
    conn = get_db_connection()
    cur = conn.cursor()
    
    print("2. LandBroker 테이블에 저장 중...\n")
    
    inserted = 0
    updated = 0
    failed = 0
    
    for reg_num, data in brokers_dict.items():
        info = data['info']
        
        # 통계 데이터 파싱
        def parse_count(value):
            if not value:
                return 0
            try:
                return int(value.replace('건', '').replace(',', '').strip())
            except:
                return 0
        
        completed_deals = parse_count(info.get('거래완료', '0'))
        registered_properties = parse_count(info.get('등록매물', '0'))
        
        # UPSERT
        query = """
        INSERT INTO landbroker (
            office_name, representative, phone, address, registration_number,
            completed_deals, registered_properties
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (registration_number) DO UPDATE SET
            office_name = COALESCE(EXCLUDED.office_name, landbroker.office_name),
            representative = COALESCE(EXCLUDED.representative, landbroker.representative),
            phone = COALESCE(EXCLUDED.phone, landbroker.phone),
            address = COALESCE(EXCLUDED.address, landbroker.address),
            completed_deals = EXCLUDED.completed_deals,
            registered_properties = EXCLUDED.registered_properties,
            updated_at = CURRENT_TIMESTAMP
        RETURNING landbroker_id, (xmax = 0) AS is_new;
        """
        
        values = (
            info.get('name') or info.get('중개사명'),
            info.get('representative') or info.get('대표자'),
            info.get('phone') or info.get('전화번호'),
            info.get('address') or info.get('주소'),
            reg_num,
            completed_deals,
            registered_properties
        )
        
        try:
            cur.execute(query, values)
            result = cur.fetchone()
            broker_id = result[0]
            is_new = result[1]
            
            # Land 테이블의 FK 업데이트
            update_query = """
            UPDATE land 
            SET landbroker_id = %s
            WHERE land_num = ANY(%s)
            """
            cur.execute(update_query, (broker_id, data['land_nums']))
            
            conn.commit()
            
            if is_new:
                inserted += 1
            else:
                updated += 1
            
            if (inserted + updated) % 50 == 0:
                print(f"  진행: {inserted + updated}/{len(brokers_dict)}")
        
        except Exception as e:
            conn.rollback()
            print(f"  ✗ 오류 ({reg_num}): {e}")
            failed += 1
    
    # 4. 결과 출력
    print("\n" + "=" * 70)
    print(" " * 20 + "Import 완료")
    print("=" * 70)
    print(f"\n  신규 삽입: {inserted}개")
    print(f"  업데이트: {updated}개")
    print(f"  실패: {failed}개")
    
    # 5. 통계
    cur.execute("SELECT COUNT(*) FROM landbroker")
    broker_count = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM land WHERE landbroker_id IS NOT NULL")
    linked_count = cur.fetchone()[0]
    
    print(f"\n  총 중개소: {broker_count}개")
    print(f"  연결된 매물: {linked_count}개")
    print("\n" + "=" * 70 + "\n")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    try:
        import_brokers_from_json()
    except Exception as e:
        print(f"\n✗ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

