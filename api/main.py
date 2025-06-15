from fastapi import FastAPI
import uvicorn
from fastapi.middleware.cors import CORSMiddleware

from api.routers import clients, invoices, payments, auth, tenant, settings
from api.cors_middleware import CustomCORSMiddleware
from api.models.database import engine
from api.models import models

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Invoice API",
    description="API for the Invoice Management System",
    version="1.0.0"
)

# Add built-in CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add our custom CORS middleware
app.add_middleware(CustomCORSMiddleware)

# Include routers (they already have their own prefixes)
app.include_router(auth.router, prefix="/api")
app.include_router(tenant.router, prefix="/api")
app.include_router(clients.router, prefix="/api")
app.include_router(invoices.router, prefix="/api")
app.include_router(payments.router, prefix="/api")
app.include_router(settings.router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "Welcome to the Invoice API"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True) 