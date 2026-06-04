# DW FX Ledger

외화 환전 로트 관리 및 환차익 계산 서비스를 위한 모노레포입니다.

현재 단계는 프로젝트 구조만 준비한 초기 스캐폴딩 상태입니다. 비즈니스 로직, DB 테이블, 실제 PostgreSQL 연결은 아직 구현하지 않았습니다.

## Tech Stack

- Frontend: Next.js + TypeScript
- Admin: Next.js + TypeScript
- Backend: FastAPI
- Database: PostgreSQL
- ORM: SQLAlchemy
- Migration: Alembic
- Package manager: pnpm
- Python environment: uv
- Container: Docker Compose

## Project Structure

```text
apps/
  web/      # 사용자용 Next.js 앱
  admin/    # 관리자용 Next.js 앱
  api/      # FastAPI 앱
packages/
  shared/   # 공유 TypeScript 패키지
```

## Getting Started

### Install JavaScript dependencies

```bash
pnpm install
```

### Run web app

```bash
pnpm dev:web
```

Web app: http://localhost:3000

### Run admin app

```bash
pnpm dev:admin
```

Admin app: http://localhost:3001

### Run API

```bash
cd apps/api
uv sync
uv run uvicorn app.main:app --reload
```

API: http://localhost:8000

Health check: http://localhost:8000/health

### Run PostgreSQL container

```bash
docker compose up -d postgres
```

The compose file only provides a PostgreSQL container scaffold. The API does not connect to PostgreSQL yet.

## Environment Variables

Create local environment files only when needed. Do not commit `.env` files.

Use `.env.example` as the reference for expected variables.
