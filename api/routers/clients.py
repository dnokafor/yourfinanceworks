from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from api.models.database import get_db
from api.models.models import Client, User
from api.schemas.client import ClientCreate, ClientUpdate, Client as ClientSchema
from api.routers.auth import get_current_user

router = APIRouter(prefix="/clients", tags=["clients"])

@router.get("/", response_model=List[ClientSchema])
def read_clients(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    clients = db.query(Client).filter(
        Client.tenant_id == current_user.tenant_id
    ).offset(skip).limit(limit).all()
    return clients

@router.get("/{client_id}", response_model=ClientSchema)
def read_client(
    client_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    client = db.query(Client).filter(
        Client.id == client_id,
        Client.tenant_id == current_user.tenant_id
    ).first()
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    return client

@router.post("/", response_model=ClientSchema)
def create_client(
    client: ClientCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_client = Client(**client.dict(), tenant_id=current_user.tenant_id)
    db.add(db_client)
    db.commit()
    db.refresh(db_client)
    return db_client

@router.put("/{client_id}", response_model=ClientSchema)
def update_client(
    client_id: int, 
    client: ClientUpdate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_client = db.query(Client).filter(
        Client.id == client_id,
        Client.tenant_id == current_user.tenant_id
    ).first()
    if db_client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    
    client_data = client.dict(exclude_unset=True)
    for key, value in client_data.items():
        setattr(db_client, key, value)
    
    db.commit()
    db.refresh(db_client)
    return db_client

@router.delete("/{client_id}")
def delete_client(
    client_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    client = db.query(Client).filter(
        Client.id == client_id,
        Client.tenant_id == current_user.tenant_id
    ).first()
    if client is None:
        raise HTTPException(status_code=404, detail="Client not found")
    
    db.delete(client)
    db.commit()
    return {"message": "Client deleted successfully"} 