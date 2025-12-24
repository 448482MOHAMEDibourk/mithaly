from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from ..schemas.user import UserCreate, UserUpdate, UserResponse

router = APIRouter(prefix="/api/users", tags=["users"])


# دالة مصادقة مؤقتة (ستحل لاحقاً)
def get_current_user():
    """محاكاة للمصادقة - سيتم استبدالها بمصادقة حقيقية"""
    return {"id": "user123", "username": "test_user", "is_admin": False}


# خدمة مؤقتة (ستحل لاحقاً)
class MockUserService:
    async def get_all_users(self):
        return []

    async def get_user_by_id(self, user_id: str):
        if user_id == "user123":
            return {"id": "user123", "username": "test_user", "email": "test@example.com", "created_at": "2025-01-01T00:00:00Z", "updated_at": "2025-01-01T00:00:00Z"}
        return None

    async def update_user(self, user_id: str, updates):
        data = updates.dict(exclude_unset=True)
        return {"id": user_id, **data, "updated_at": "2025-01-01T00:00:00Z"}

    async def create_user(self, user):
        data = user.dict()
        return {"id": "new_user", **data, "created_at": "2025-01-01T00:00:00Z", "updated_at": "2025-01-01T00:00:00Z"}


@router.get("/", response_model=List[UserResponse])
async def get_users(service: MockUserService = Depends(lambda: MockUserService())):
    """الحصول على قائمة المستخدمين"""
    return await service.get_all_users()


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: str, service: MockUserService = Depends(lambda: MockUserService())):
    """الحصول على مستخدم محدد"""
    user = await service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    updates: UserUpdate,
    current_user: dict = Depends(get_current_user),
    service: MockUserService = Depends(lambda: MockUserService()),
):
    """
    تحديث بيانات المستخدم مع حماية الحقول الحساسة
    """
    # التحقق من الملكية
    if current_user["id"] != user_id and not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this user"
        )

    # حماية الحقول الحساسة
    protected_fields = ["role", "is_admin", "password_hash", "created_at"]
    update_dict = updates.dict(exclude_unset=True)

    for field in protected_fields:
        if field in update_dict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=f"Cannot update protected field: {field}"
            )

    return await service.update_user(user_id, updates)


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, service: MockUserService = Depends(lambda: MockUserService())):
    """إنشاء مستخدم جديد"""
    return await service.create_user(user)
