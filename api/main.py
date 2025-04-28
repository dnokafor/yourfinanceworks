from fastapi import FastAPI
import uvicorn
from fastapi.middleware.cors import CORSMiddleware

from routers import clients, invoices, payments, settings
from cors_middleware import CustomCORSMiddleware

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

# Include routers
app.include_router(clients.router, prefix="/api", tags=["clients"])
app.include_router(invoices.router, prefix="/api", tags=["invoices"])
app.include_router(payments.router, prefix="/api", tags=["payments"])
app.include_router(settings.router, prefix="/api", tags=["settings"])

@app.get("/")
def read_root():
    return {"message": "Welcome to the Invoice API"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 