# Backend

백엔드는 이곳에 프로젝트를 생성합니다.

pip install -r requirements.txt 를 통해 팀원이 추가한 라이브러리를 로컬 환경에 추가하고 시작합니다.

python -m venv .venv (가상환경 생성)

.venv\Scripts\activate (가상환경 활성화) , mac: - source .venv/bin/activate

pip install -r requirements-dev.txt (개발에 필요한 모든 라이브러리 설치)

pre-commit install