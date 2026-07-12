from fastapi import Depends, HTTPException, status


def get_current_user() -> dict[str, str]:
    # TODO: Replace with real JWT authentication.
    return {"user_id": "dev", "role": "admin"}


def require_admin(user: dict[str, str] = Depends(get_current_user)) -> dict[str, str]:
    if user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    return user
