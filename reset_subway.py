import sys
import os

# scripts/data_import 경로를 sys.path에 추가하여 config 모듈을 찾을 수 있게 함
sys.path.append(os.path.join(os.getcwd(), 'scripts', 'data_import'))

from scripts.data_import.database import Database

def reset_subway():
    driver = Database.get_driver()
    with driver.session() as session:
        print("1. 지하철역 데이터 삭제 중...")
        session.run("MATCH (s:SubwayStation) DETACH DELETE s")
        
        print("2. 제약 조건 확인 및 삭제 중...")
        # 모든 제약 조건 조회
        result = session.run("SHOW CONSTRAINTS")
        for record in result:
            # SubwayStation 라벨이 포함된 제약 조건 찾기
            if "SubwayStation" in str(record):
                name = record["name"]
                print(f" - 제약 조건 삭제: {name}")
                session.run(f"DROP CONSTRAINT {name}")
                
    print("완료! 이제 main.py를 다시 실행해 보세요.")
    driver.close()

if __name__ == "__main__":
    reset_subway()
