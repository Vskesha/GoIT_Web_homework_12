from typing import List, Optional

from fastapi import Path, Depends, HTTPException, Query, status, APIRouter
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.database.db import get_db
from src.schemas import ContactModel, ContactFavoriteModel, ContactResponse
from src.repository import contacts as repos_contacts


router = APIRouter(prefix="/contacts", tags=["contact"])


@router.get("", response_model=List[ContactResponse])
async def get_contact(
        skip: int = 0,
        limit: int = Query(default=10, le=100, ge=10),
        favorite: bool = None,
        db: Session = Depends(get_db), ):
    contacts = await repos_contacts.get_contacts(db=db, skip=skip, limit=limit, favorite=favorite)
    return contacts


@router.get("/{contact_id}", response_model=ContactResponse)
async def get_contact(contact_id: int = Path(ge=1), db: Session = Depends(get_db)):
    contact = await repos_contacts.get_contact_by_id(contact_id, db)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return contact


@router.post("", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def create_contact(body: ContactModel, db: Session = Depends(get_db)):
    contact = await repos_contacts.get_contact_by_email(body.email, db)
    if contact:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=f"Email is exist!"
        )
    try:
        contact = await repos_contacts.create(body, db)
    except IntegrityError as err:
        raise HTTPException(
            status_code=status.HTTP_404_INVALID_REQUEST, detail=f"Error: {err}"
        )
    return contact


@router.put("/{contact_id}", response_model=ContactResponse)
async def update_contact(
        body: ContactModel, contact_id: int = Path(ge=1), db: Session = Depends(get_db)):
    contact = await repos_contacts.update(contact_id, body, db)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return contact


@router.patch("/{contact_id}/favorite", response_model=ContactResponse)
async def favorite_update(
        body: ContactFavoriteModel,
        contact_id: int = Path(ge=1),
        db: Session = Depends(get_db)
):
    contact = await repos_contacts.favorite_update(contact_id, body, db)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return contact


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_contact(contact_id: int = Path(ge=1), db: Session = Depends(get_db)):
    contact = await repos_contacts.delete(contact_id, db)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return None


@router.get("/search/{query}", response_model=List[ContactResponse],
            summary="Search contacts by name, lastname, email")
async def search_by(query: Optional[str] = None,
                    db: Session = Depends(get_db)):
    contacts = await repos_contacts.search_contacts(query, db)
    if not contacts:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact Not Found")

    return contacts


@router.get("/birthdays/next_week", response_model=List[ContactResponse])
async def search_contacts(
        days: int = Query(default=7, le=30, ge=1),
        skip: int = 0,
        limit: int = Query(default=10, le=30, ge=1),
        db: Session = Depends(get_db)
):
    contacts = None
    if days:
        par = {
            "days": days,
            "skip": skip,
            "limit": limit,
        }
        contacts = await repos_contacts.search_birthday(par, db)
    if not contacts:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No contacts found")
    return contacts
