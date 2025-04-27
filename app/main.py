from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.database import engine
from app.models import users, problems, contests, submissions
from app.auth.router import router as auth_router
from app.routers.users import router as users_router
from app.routers.problems import router as problems_router
from app.routers.contests import router as contests_router
from app.routers.submissions import router as submissions_router

# Tạo instance của FastAPI
app = FastAPI(
    title="Coding Platform API",
    description="API for a competitive programming platform",
    version="1.0.0"
)

# Cấu hình CORS
origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:8000",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Thêm các routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(problems_router)
app.include_router(contests_router)
app.include_router(submissions_router)

@app.get("/", tags=["Root"])
async def root():
    return {"message": "Welcome to the Coding Platform API"}

@app.get("/api/health", tags=["Health"])
async def health_check():
    return {"status": "ok"}

# Xử lý lỗi 404
@app.exception_handler(404)
async def not_found_exception_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"detail": "The requested resource was not found"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)