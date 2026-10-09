import argparse

import uvicorn

from app.config.settings import Settings


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Surya Sach API")
    parser.add_argument("--reload", action="store_true", help="Reload on code changes")
    args = parser.parse_args()
    settings = Settings()
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=args.reload,
    )


if __name__ == "__main__":
    main()
