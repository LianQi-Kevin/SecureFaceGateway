import argparse
import logging

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers import token_router, user_router, face_router, app_router
from backend.tools.logging_utils import log_set

# init logging
log_set(logging.DEBUG)

# init Fastapi
app = FastAPI()
app.include_router(app_router)
app.include_router(token_router)  # include token_router
app.include_router(user_router)  # include user_router
app.include_router(face_router)  # include face_router

# allow CORS
# noinspection PyTypeChecker
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Run the FastAPI server")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host of the server")
    parser.add_argument("--port", type=int, default=12538, help="Port of the server")
    args = parser.parse_args()

    uvicorn.run(app, host=args.host, port=args.port)
