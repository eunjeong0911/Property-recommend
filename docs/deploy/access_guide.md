# 서버 접속 가이드 (Bastion Host 경유)
App, Rag, Neo4j 서버가 모두 Private Subnet에 위치해있으므로 접속을 위해
Public cubnet에 Bastion Host를 만들어 안전하게 접속하여 진행

## 1. 서버 정보

| 서버 이름 | Private IP | 용도 | OS 유저 |
| --- | --- | --- | --- |
| **Bastion Host** | `3.38.23.94` (Public) | 점프 서버 | `ec2-user` |
| **Neo4j Server** | `10.0.130.106` | 그래프 DB | `ec2-user` |
| **RAG Server** | `10.0.140.112` | 검색/분석 | `ec2-user` |
| **App Server** | `10.0.139.182` | 웹/API | `ec2-user` |

*   **Key File**: `realestate-key.pem`

---

## 2. 접속 방법 (수동 점프 방식)

### 1단계: Bastion Host 접속
로컬 PC(Git Bash 또는 PowerShell)에서 아래 명령어로 Bastion 서버에 접속

```powershell
ssh -i "C:\Users\Playdata\Downloads\realestate-key.pem" ec2-user@3.38.23.94
```

### 2단계: Bastion 내부에 키 파일 생성
Bastion 접속 성공 후, 프라이빗 서버로 넘어가기 위한 과정 정리

1.  **로컬 PC**에서 `realestate-key.pem` 파일을 메모장으로 열어서 
2.  `-----BEGIN RSA PRIVATE KEY-----` 부터 끝까지 **전체 내용을 복사**
3.  **Bastion 터미널**에서 아래 명령어로 새 파일을 열고 
    ```bash
    nano my-key.pem
    ```
4.  마우스 우클릭으로 **붙여넣기**
5.  저장 후 나가기 (`Ctrl + O` -> `Enter` -> `Ctrl + X`)
6.  파일 권한을 설정
    ```bash
    chmod 400 my-key.pem
    ```

### 3단계: 목적지 서버로 이동
생성한 키를 이용해 원하는 서버로 이동

**Neo4j Server:**
```bash
ssh -i my-key.pem ec2-user@10.0.130.106
```

**RAG Server:**
```bash
ssh -i my-key.pem ec2-user@10.0.140.112
```

**App Server:**
```bash
ssh -i my-key.pem ec2-user@10.0.139.182
```

---

## 3. 최초 접속 시 필수 설정 (Initial Setup)

새로운 서버에 **처음 접속했을 때** 아래 명령어를 실행하여 Docker와 Git 환경을 구성

```bash
# 1. 시스템 업데이트 및 필수 도구 설치
sudo yum update -y
sudo yum install git docker -y

# 2. Docker 실행 및 사용자 권한 부여
sudo service docker start
sudo usermod -aG docker ec2-user

# 3. Docker Compose 설치
sudo curl -L https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m) -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 4. 권한 적용을 위해 접속 종료 후 다시 접속
exit
```
*   `exit` 후 **2단계의 이동 명령어(`ssh ...`)**로 다시 접속하면 Docker 명령어를 사용 가능

---

## 4. Neo4j 서버 배포 (Deployment Steps)

서버 접속 및 초기 설정 완료 후에, 아래 순서대로 배포를 진행

### 1단계: 프로젝트 코드 다운로드 및 스왑 설정
메모리 부족(OOM) 방지를 위해 스왑 메모리(4GB)를 설정

```bash
# 코드 다운로드
git clone https://github.com/SKNETWORKS-FAMILY-AICAMP/SKN18-FINAL-1TEAM.git
cd SKN18-FINAL-1TEAM
git checkout deploy/production

# 스왑 메모리 설정
chmod +x scripts/deployment/setup_swap.sh
./scripts/deployment/setup_swap.sh
```
*   `free -h` 명령어로 `Swap: 4.0Gi`가 잡혔는지 확인 가능

### 2단계: 환경변수 설정
로컬에서 작성한 `.env.production` 내용을 서버에 적용

```bash
nano .env.production
```
1.  **붙여넣기**: 로컬 PC의 `.env.production` 내용을 복사하여 붙여넣기`(우클릭)`
2.  **저장**: `Ctrl + O` -> `Enter`
3.  **종료**: `Ctrl + X`

### 3단계: Docker Compose 실행
Neo4j 서비스를 백그라운드에서 실행

```bash
docker-compose --env-file .env.production -f docker-compose.prod.neo4j.yml up -d --build
```
*   **성공 확인**: `docker ps` 명령어로 컨테이너가 정상적으로 떠 있는지(`Up`) 확인

