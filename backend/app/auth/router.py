from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.auth.schemas import AuthUserResponse, TokenResponse
from app.auth.service import AuthService
from app.shared.database import get_db
from app.shared.dependencies import get_current_user
from app.shared.security import create_access_token
from app.auth.models import Usuario

router = APIRouter(
    prefix="/api/v1/auth",
    tags=["auth"],
)


@router.post("/login", response_model=TokenResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> TokenResponse:
    user = AuthService.authenticate_user(
        db=db,
        email=form_data.username,
        senha=form_data.password,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha inválidos.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(subject=str(user.id))

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
    )


@router.get("/me", response_model=AuthUserResponse)
def get_me(
    current_user: Usuario = Depends(get_current_user),
) -> AuthUserResponse:
    return AuthUserResponse(
        id=current_user.id,
        nome=current_user.nome,
        email=current_user.email,
        ativo=current_user.ativo,
    )