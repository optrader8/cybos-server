"""
Main Entry Point - 애플리케이션 진입점

Cybos Plus REST API 서버의 메인 진입점입니다.
극단적 모듈화 원칙에 따라 300라인 이하로 제한됩니다.
"""

import os
import sys
import uvicorn
import argparse
from pathlib import Path
from dotenv import load_dotenv

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.api.app import create_app
from src.cybos.connection.validator import validate_connection


def load_environment():
    """환경 변수 로드"""
    # .env 파일 로드
    env_file = project_root / ".env"
    if env_file.exists():
        load_dotenv(env_file)
        print(f"✅ Loaded environment from {env_file}")
    else:
        print(f"⚠️  .env file not found, using default values")

    # 기본값 설정
    os.environ.setdefault("DATABASE_PATH", "data/cybos.db")
    os.environ.setdefault("API_HOST", "0.0.0.0")
    os.environ.setdefault("API_PORT", "8000")
    os.environ.setdefault("LOG_LEVEL", "INFO")


def check_cybos_connection():
    """Cybos Plus 연결 확인"""
    print("\n🔍 Checking Cybos Plus connection...")

    try:
        result = validate_connection()

        if result["is_connected"]:
            print("✅ Cybos Plus is connected")
            print(f"   - User ID: {result.get('user_id', 'N/A')}")
            print(f"   - Server: {result.get('server_type', 'N/A')}")
            return True
        else:
            print("❌ Cybos Plus is not connected")
            print(f"   - Reason: {result.get('message', 'Unknown')}")
            return False

    except Exception as e:
        print(f"❌ Error checking Cybos Plus connection: {e}")
        return False


def check_database():
    """데이터베이스 확인"""
    db_path = os.getenv("DATABASE_PATH", "data/cybos.db")
    print(f"\n🔍 Checking database at {db_path}...")

    db_file = Path(db_path)
    if db_file.exists():
        file_size_mb = db_file.stat().st_size / (1024 * 1024)
        print(f"✅ Database exists ({file_size_mb:.2f} MB)")
        return True
    else:
        print(f"⚠️  Database not found at {db_path}")
        print("   Please run: python scripts/init_database.py")
        return False


def create_server_config():
    """서버 설정 생성"""
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    debug = os.getenv("API_DEBUG", "false").lower() == "true"
    reload = os.getenv("API_RELOAD", "false").lower() == "true"
    workers = int(os.getenv("API_WORKERS", "1"))

    return {
        "host": host,
        "port": port,
        "log_level": os.getenv("LOG_LEVEL", "info").lower(),
        "reload": reload,
        "workers": workers if not reload else 1  # reload 시에는 단일 워커
    }


def print_banner():
    """시작 배너 출력"""
    banner = """
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║    🚀 Cybos Plus REST API Server                         ║
║                                                           ║
║    실시간 국내 주식 시세 API 서버                          ║
║    극단적 모듈화 & 마이크로 아키텍처 기반                   ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
    """
    print(banner)


def main():
    """메인 함수"""
    # 명령행 인자 파싱
    parser = argparse.ArgumentParser(description="Cybos Plus REST API Server")
    parser.add_argument("--host", type=str, help="Host address")
    parser.add_argument("--port", type=int, help="Port number")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--skip-checks", action="store_true", help="Skip pre-flight checks")
    args = parser.parse_args()

    # 배너 출력
    print_banner()

    # 환경 변수 로드
    load_environment()

    # 사전 체크 (옵션)
    if not args.skip_checks:
        # Cybos Plus 연결 확인
        if not check_cybos_connection():
            print("\n⚠️  Warning: Cybos Plus is not connected")
            print("   API will work with limited functionality")
            print("   Please login to Cybos Plus HTS\n")

        # 데이터베이스 확인
        if not check_database():
            print("\n⚠️  Warning: Database not found")
            print("   Please initialize database first\n")

    # 서버 설정
    config = create_server_config()

    # 명령행 인자로 오버라이드
    if args.host:
        config["host"] = args.host
    if args.port:
        config["port"] = args.port
    if args.reload:
        config["reload"] = True
        config["workers"] = 1

    # FastAPI 앱 생성
    print("\n🔧 Creating FastAPI application...")
    app = create_app()

    # 서버 시작
    print(f"\n🚀 Starting server on {config['host']}:{config['port']}...")
    print(f"   - Log level: {config['log_level']}")
    print(f"   - Workers: {config['workers']}")
    print(f"   - Reload: {config['reload']}")
    print("\n" + "=" * 60)
    print("📡 Server is ready to accept connections")
    print("=" * 60 + "\n")

    try:
        uvicorn.run(
            app,
            host=config["host"],
            port=config["port"],
            log_level=config["log_level"],
            reload=config["reload"],
            workers=config["workers"]
        )
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped by user")
    except Exception as e:
        print(f"\n\n❌ Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
