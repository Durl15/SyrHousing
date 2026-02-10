from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models.watchlist import WatchlistEntry
from ..schemas.watchlist import WatchlistCreate, WatchlistUpdate, WatchlistRead

router = APIRouter(prefix="/api/watchlist", tags=["watchlist"])


@router.get("", response_model=List[WatchlistRead])
def list_watchlist(active_only: bool = True, db: Session = Depends(get_db)):
    q = db.query(WatchlistEntry)
    if active_only:
        q = q.filter(WatchlistEntry.is_active == True)
    return q.all()


@router.get("/{program_key}", response_model=WatchlistRead)
def get_watchlist_entry(program_key: str, db: Session = Depends(get_db)):
    e = db.query(WatchlistEntry).filter(WatchlistEntry.program_key == program_key).first()
    if not e:
        raise HTTPException(status_code=404, detail="Watchlist entry not found")
    return e


@router.post("", response_model=WatchlistRead, status_code=201)
def create_watchlist_entry(data: WatchlistCreate, db: Session = Depends(get_db)):
    existing = db.query(WatchlistEntry).filter(WatchlistEntry.program_key == data.program_key).first()
    if existing:
        raise HTTPException(status_code=409, detail="program_key already exists")
    e = WatchlistEntry(**data.model_dump())
    db.add(e)
    db.commit()
    db.refresh(e)
    return e


@router.patch("/{program_key}", response_model=WatchlistRead)
def update_watchlist_entry(program_key: str, data: WatchlistUpdate, db: Session = Depends(get_db)):
    e = db.query(WatchlistEntry).filter(WatchlistEntry.program_key == program_key).first()
    if not e:
        raise HTTPException(status_code=404, detail="Watchlist entry not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(e, field, value)
    db.commit()
    db.refresh(e)
    return e


@router.delete("/{program_key}", status_code=204)
def delete_watchlist_entry(program_key: str, db: Session = Depends(get_db)):
    e = db.query(WatchlistEntry).filter(WatchlistEntry.program_key == program_key).first()
    if not e:
        raise HTTPException(status_code=404, detail="Watchlist entry not found")
    e.is_active = False
    db.commit()
