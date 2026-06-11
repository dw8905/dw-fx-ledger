# Docker Compose 개발 실행

이 문서는 호스트 WSL에 Docker, Docker Compose, Git만 설치되어 있다는 전제로 개발 서버를 실행하는 방법을 정리합니다.

Docker Compose 개발 구성은 API, Web, Admin만 실행합니다. PostgreSQL 컨테이너는 포함하지 않으며 기존 외부 PostgreSQL에 접속합니다.

## 서비스 구성

| 서비스 | Dockerfile | 런타임 | 실행 위치 | 포트 |
| --- | --- | --- | --- | --- |
| `api` | `Dockerfile.api` | Python 3.12, uv, FastAPI/Uvicorn | `/app` (`apps/api`) | `8000` |
| `web` | `Dockerfile.web` | Node.js 22, pnpm, Next.js | `/repo` workspace | `3000` |
| `admin` | `Dockerfile.admin` | Node.js 22, pnpm, Next.js | `/repo` workspace | `3001` |

API 이미지에는 Node.js를 넣지 않고, Web/Admin 이미지에는 Python을 넣지 않습니다.

## 외부 TrueNAS DB 환경변수

Docker Compose 개발 구성은 외부 TrueNAS PostgreSQL을 사용합니다.

개발 DB 기준:

- Host: `192.168.0.3`
- Port: `30432`
- Database: `fx_ledger_dev`
- Username: `fx_ledger`
- Password: 커밋 금지

실제 비밀번호는 커밋하지 않습니다. 로컬 전용 파일을 만들어 주입합니다.

```bash
cp .env.docker.example .env.docker.local
vi .env.docker.local
```

`.env.docker.local` 예시:

```text
DATABASE_URL=postgresql+psycopg://fx_ledger:실제비밀번호@192.168.0.3:30432/fx_ledger_dev
SECRET_KEY=dev-secret-change-me
```

`.env.docker.local`은 `.gitignore`에 포함되어 있으므로 커밋하지 않습니다.

`docker-compose.dev.yml`에는 아래 placeholder 기본값만 들어갑니다. `.env.docker.local` 없이도 `docker compose config`는 동작하지만, DB가 필요한 API 기능은 실제 비밀번호 없이는 실패합니다.

```text
DATABASE_URL=postgresql+psycopg://fx_ledger:CHANGE_ME@192.168.0.3:30432/fx_ledger_dev
SECRET_KEY=dev-secret-change-me
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
NEXT_PUBLIC_API_BASE_URL=/api/backend
BACKEND_INTERNAL_URL=http://api:8000
```

## 실행

개발용 스크립트를 사용하는 방식을 권장합니다.

```bash
bash scripts/docker-dev-up.sh
```

스크립트는 `.env.docker.local`이 있으면 자동으로 `--env-file .env.docker.local`을 붙여 실행합니다.

직접 Docker Compose 명령을 사용할 수도 있습니다.

```bash
docker compose --env-file .env.docker.local -f docker-compose.dev.yml up --build
```

백그라운드로 띄우려면 아래처럼 실행합니다.

```bash
docker compose --env-file .env.docker.local -f docker-compose.dev.yml up --build -d
```

확인 URL:

- API: <http://127.0.0.1:8000/health>
- API Docs: <http://127.0.0.1:8000/docs>
- Web: <http://localhost:3000>
- Admin: <http://localhost:3001>

상태 확인:

```bash
bash scripts/docker-dev-ps.sh
docker compose --env-file .env.docker.local -f docker-compose.dev.yml ps
```

중지:

```bash
bash scripts/docker-dev-down.sh
docker compose --env-file .env.docker.local -f docker-compose.dev.yml down
```

의존성 볼륨까지 초기화해야 할 때:

```bash
docker compose --env-file .env.docker.local -f docker-compose.dev.yml down -v
```

## DB 연결 검증

`/health`가 `200`이어도 FastAPI 프로세스가 살아 있다는 뜻일 뿐, 외부 PostgreSQL 연결 성공을 보장하지 않습니다.

API 컨테이너 안에서 Alembic 현재 revision을 조회하면 DB 연결과 migration 테이블 접근을 함께 확인할 수 있습니다.

```bash
docker compose --env-file .env.docker.local -f docker-compose.dev.yml exec api uv run alembic current
```

스크립트로 컨테이너를 올린 뒤에도 같은 명령을 사용합니다.

```bash
bash scripts/docker-dev-up.sh
docker compose --env-file .env.docker.local -f docker-compose.dev.yml exec api uv run alembic current
```

## 로컬 실행 방식과의 관계

기존 로컬 실행 방식은 유지합니다.

```bash
pnpm start
pnpm stop
pnpm status
pnpm restart
```

Docker Compose 구성은 별도 파일인 `docker-compose.dev.yml`만 사용하므로 기존 `pnpm start/stop/status/restart` 스크립트와 직접 연결되지 않습니다.

`pnpm status`는 Docker 컨테이너 상태가 아니라 기존 로컬 실행 방식의 `.dev/*.pid` 상태를 확인합니다. Docker 상태는 아래 명령으로 확인합니다.

```bash
docker compose -f docker-compose.dev.yml ps
bash scripts/docker-dev-ps.sh
```

## 개발 중 변경 반영

`apps/api`, `apps/web`, `apps/admin`, `packages/shared`는 컨테이너에 bind mount됩니다.

- API는 Uvicorn `--reload`로 Python 코드 변경을 감지합니다.
- Web/Admin은 Next.js dev server가 파일 변경을 감지합니다.
- `package.json`, `pnpm-lock.yaml`, `pyproject.toml`, `uv.lock` 변경 후에는 이미지를 다시 빌드합니다.

```bash
docker compose -f docker-compose.dev.yml up --build
```

## 주의사항

- 이 compose 파일은 PostgreSQL을 띄우지 않습니다.
- 컨테이너에서 TrueNAS PostgreSQL `192.168.0.3:30432`로 직접 접속합니다.
- TrueNAS 방화벽, PostgreSQL listen address, 계정 권한, NAS 네트워크 접근을 별도로 확인해야 합니다.
- 실제 운영 비밀번호, JWT secret, DB 접속정보는 `.env`나 shell 환경변수로 주입하고 Git에 커밋하지 않습니다.
