import sys
import logging
import logging.config
from pathlib import Path
import time
import uvicorn

# Get the absolute path of the directory containing this script
current_file = Path(__file__).resolve()
parent_directory = current_file.parent
project_directory = parent_directory.parent

sys.path.insert(0, str(project_directory))

# 在导入应用模块之前配置日志，确保 uvicorn 不会覆盖我们的设置
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
    },
    "root": {
        "level": "INFO",
        "handlers": ["default"],
    },
    "loggers": {
        "uvicorn": {"handlers": ["default"], "level": "INFO", "propagate": False},
        "uvicorn.error": {"level": "INFO", "propagate": True},
        "uvicorn.access": {"handlers": ["default"], "level": "INFO", "propagate": False},
    },
}

logging.config.dictConfig(LOGGING_CONFIG)

from api.app import create_app
from api.config import settings

api = create_app(settings)

if __name__ == "__main__":
    time.sleep(10)
    uvicorn.run("asgi:api", host="0.0.0.0", port=8000, reload=True, log_config=LOGGING_CONFIG)
