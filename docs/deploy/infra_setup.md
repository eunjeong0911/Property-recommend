# AWS 초기설정 (VPC, EC2 등)

# Step 1. 네트워크

1. VPC 생성: 프로젝트용 VPC 하나 생성
2. Subnet 생성:
- Public Subnet 2개: ALB용
- Private Subnet 2개: EC2 & RDS용 
3. Gateway 연결:
- Internet Gateway: Public Subnet에 연결 (외부 통신용)
- NAT Gateway: Public Subnet에 만들고, Private Subnet 라우팅 테이블에 연결  

![vpc_1](image/aws_setting/vpc_1.png)

VPC and more 로 선택해야 서브넷이랑 라우팅 테이블까지 한번에 만들어짐  

![vpc_2](image/aws_setting/vpc_2.png)
![vpc_3](image/aws_setting/vpc_3.png)
![vpc_4](image/aws_setting/vpc_4.png)

create 버튼 눌러서 생성

---
# Step 2. 보안 그룹 (방화벽 규칙)
**서버를 만들기 전에 port 번호 규칙 설정**

1. ALB용 SG: Inbound: 80, 443 (Anywhere 0.0.0.0/0)
2. EC2용 SG: Inbound: ALB용 SG에서 오는 트래픽만 허용 (포트 8000, 3000, 8001 등)
3. RDS/Neo4j용 SG: Inbound: EC2용 SG에서 오는 트래픽만 허용 (포트 5432, 7687)
---
security group 생성
- ALB용 SG
![security_group_alb_1](image/aws_setting/security_group_alb_1.png)
![security_group_alb_2](image/aws_setting/security_group_alb_2.png)
![security_group_alb_3](image/aws_setting/security_group_alb_3.png)

- EC2용 SG
![security_group_ec2_1](image/aws_setting/security_group_ec2_1.png)
![security_group_ec2_2](image/aws_setting/security_group_ec2_2.png)
![security_group_ec2_3](image/aws_setting/security_group_ec2_3.png)

- RDS/Neo4j용 SG
![security_group_rds_neo4j_1](image/aws_setting/security_group_rds_neo4j_1.png)
![security_group_rds_neo4j_2](image/aws_setting/security_group_rds_neo4j_2.png)
---

Target Group 생성

![target_group_1](image/aws_setting/target_group_1.png)
![target_group_2](image/aws_setting/target_group_2.png)
![target_group_3](image/aws_setting/target_group_3.png)

다음 다음 후 저장 인스턴스는 추후 연결

![target_group_4](image/aws_setting/target_group_4.png)
![target_group_5](image/aws_setting/target_group_5.png)
![target_group_6](image/aws_setting/target_group_6.png)

다음 다음 후 저장 인스턴스는 추후 연결

---
Application Load Balancer 생성
![alb_1](image/aws_setting/alb_1.png)
![alb_2](image/aws_setting/alb_2.png)
![alb_3](image/aws_setting/alb_3.png)
![alb_4](image/aws_setting/alb_4.png)
1. 생성된 ALB를 클릭하고, 아래쪽 탭에서 [리스너 및 규칙(Listeners and rules)] 탭 클릭
2. HTTP:80 리스너를 체크하고 [Manage rules] (또는 규칙 편집 아이콘) 클릭
3. [+](규칙 추가) 버튼 클릭 ➡ [Insert rule] 클릭
4. 조건(Conditions):
- IF: Path (경로)
- Value: /api/* (입력)
5. 작업(Actions):
- THEN: Forward to (전달)
- Target Group: realestate-backend-tg 선택
6. [Save] (저장)
![alb_5](image/aws_setting/alb_5.png)
![alb_6](image/aws_setting/alb_6.png)
![alb_7](image/aws_setting/alb_7.png)
---


# Step 3. 데이터베이스 (RDS)
RDS (PostgreSQL) 생성
- 위치: Private Subnet
- 보안 그룹: 위에서 만든 RDS/Neo4j용 SG 적용

![rds_1](image/aws_setting/rds_1.png)
![rds_2](image/aws_setting/rds_2.png)
![rds_3](image/aws_setting/rds_3.png)
![rds_4](image/aws_setting/rds_4.png)
![rds_5](image/aws_setting/rds_5.png)
![rds_6](image/aws_setting/rds_6.png)
![rds_7](image/aws_setting/rds_7.png)
![rds_8](image/aws_setting/rds_8.png)
![rds_9](image/aws_setting/rds_9.png)
![rds_10](image/aws_setting/rds_10.png)
--- 

# Step 4. IAM 역할 & ECR (권한 및 저장소)
EC2가 ECR에서 이미지를 가져오고, 파라미터 스토어를 읽을 수 있게 권한을 주는 용도

1. IAM Role 생성:
- 대상: EC2
- 권한: AmazonEC2ContainerRegistryReadOnly (이미지 Pull용), AmazonSSMReadOnlyAccess (파라미터 읽기용)
![iam_1](image/aws_setting/iam_1.png)
![iam_2](image/aws_setting/iam_2.png)

2. ECR Repository 생성 (5개):
realestate-backend, realestate-frontend, realestate-rag, realestate-scripts
![ecr_1](image/aws_setting/ecr_1.png)

---

# Step 5. Parameter Store (환경변수 보관) -> 이거는 좀 나중에
1. Systems Manager > Parameter Store 이동
2. 키-값 쌍 등록:
/prod/DB_PASSWORD, /prod/SECRET_KEY, /prod/OPENAI_API_KEY 등등 필요한 모든 
.env
 값 입력

---

# Step 6. EC2 인스턴스 생성
1. App Server, RAG Server, Neo4j Server 각각 생성
- 위치: Private Subnet

**App Server**

![appserver_ec2_1](image/aws_setting/appserver_ec2_1.png)

인스턴스 타입 t3.small

키페어 생성

![appserver_ec2_2](image/aws_setting/appserver_ec2_2.png)

Edit 눌러서 네트워크 세팅 변경

![appserver_ec2_3](image/aws_setting/appserver_ec2_3.png)
![appserver_ec2_4](image/aws_setting/appserver_ec2_4.png)


**Rag Server**

![ragserver_ec2_1](image/aws_setting/ragserver_ec2_1.png)
![ragserver_ec2_2](image/aws_setting/ragserver_ec2_2.png)
![ragserver_ec2_3](image/aws_setting/ragserver_ec2_3.png)
![ragserver_ec2_4](image/aws_setting/ragserver_ec2_4.png)


**Neo4j Server**

![neo4jserver_ec2_1](image/aws_setting/neo4jserver_ec2_1.png)
![neo4jserver_ec2_2](image/aws_setting/neo4jserver_ec2_2.png)
![neo4jserver_ec2_3](image/aws_setting/neo4jserver_ec2_3.png)
![neo4jserver_ec2_4](image/aws_setting/neo4jserver_ec2_4.png)

---
여기부터는 도메인 사고 인증서 발급하고 로드밸런서, 라우트53 설정

# Step 7. 로드 밸런서 (ALB) & Route 53 (문패 달기)
1. Target Group 생성:
- Frontend용 (Port 3000)
- Backend용 (Port 8000)
2. ALB 생성:
- 위치: Public Subnet
- Listener: 80포트로 들어오면 443으로 리다이렉트 (HTTPS 쓸 경우)
- Rule: /api/* 로 들어오면 Backend Target Group으로, 나머지는 Frontend Target Group으로.
3. Route 53:
- 도메인 구입 후 A Record (Alias)로 ALB 주소 연결
