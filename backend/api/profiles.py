from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..auth import get_current_user, oauth2_scheme
from ..models.user import User
from ..models.user_profile import UserProfile
from ..schemas.user_profile import ProfileCreate, ProfileUpdate, ProfileRead

router = APIRouter(prefix="/api/profiles", tags=["profiles"])


def _optional_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """Try to get current user but don't fail if unauthenticated."""
    if not token:
        return None
    try:
        return get_current_user(token, db)
    except Exception:
        return None


@router.get("", response_model=List[ProfileRead])
def list_profiles(
    user: Optional[User] = Depends(_optional_current_user),
    db: Session = Depends(get_db),
):
    if user:
        return db.query(UserProfile).filter(
            (UserProfile.user_id == user.id) | (UserProfile.user_id.is_(None))
        ).all()
    return db.query(UserProfile).filter(UserProfile.user_id.is_(None)).all()


@router.get("/default", response_model=ProfileRead)
def get_default_profile(
    user: Optional[User] = Depends(_optional_current_user),
    db: Session = Depends(get_db),
):
    # Try user's own default first
    if user:
        p = db.query(UserProfile).filter(
            UserProfile.user_id == user.id,
            UserProfile.profile_name == "default",
        ).first()
        if p:
            return p

    # Fall back to system default (no user_id)
    p = db.query(UserProfile).filter(
        UserProfile.profile_name == "default",
        UserProfile.user_id.is_(None),
    ).first()
    if not p:
        raise HTTPException(status_code=404, detail="No default profile found")
    return p


@router.get("/{profile_id}", response_model=ProfileRead)
def get_profile(profile_id: str, db: Session = Depends(get_db)):
    p = db.query(UserProfile).filter(UserProfile.id == profile_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Profile not found")
    return p


@router.post("", response_model=ProfileRead, status_code=201)
def create_profile(
    data: ProfileCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    p = UserProfile(**data.model_dump(), user_id=user.id)
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


@router.patch("/{profile_id}", response_model=ProfileRead)
def update_profile(profile_id: str, data: ProfileUpdate, db: Session = Depends(get_db)):
    p = db.query(UserProfile).filter(UserProfile.id == profile_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Profile not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(p, field, value)
    db.commit()
    db.refresh(p)
    return p


@router.delete("/{profile_id}", status_code=204)
def delete_profile(profile_id: str, db: Session = Depends(get_db)):
    p = db.query(UserProfile).filter(UserProfile.id == profile_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Profile not found")
    db.delete(p)
    db.commit()
