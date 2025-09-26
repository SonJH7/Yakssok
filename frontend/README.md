# Yakssok Frontend

Google OAuth와 Google Calendar 연동 흐름을 확인할 수 있는 React + Vite + TypeScript 기반 SPA입니다.

## 주요 기능

- Google OAuth 로그인 / 재인증 흐름
- JWT 로컬 저장 및 Axios 인터셉터를 통한 자동 인증 헤더 주입
- 주간 / 월간 캘린더 뷰와 기간 이동
- Google 권한 만료 시 재인증 안내 배너
- Tailwind CSS를 활용한 아이보리 톤 UI

## 환경 변수

`.env` 파일을 생성하여 아래 값을 설정하세요.

```bash
VITE_API_BASE_URL=http://localhost:8000
VITE_FRONTEND_URL=http://localhost:5173
```

## 개발 서버 실행

```bash
npm install
npm run dev
```

## 프로덕션 빌드

```bash
npm run build
```
