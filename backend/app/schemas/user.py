from pydantic import BaseModel, ConfigDict, Field


class UserBase(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    employee_no: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=64)
    department: str = Field(min_length=1, max_length=128)
    position: str = Field(min_length=1, max_length=128)
    role: str = Field(pattern='^(admin|employee)$')


class UserCreate(UserBase):
    password: str = Field(min_length=6, max_length=64)
    permissions: list[str] = Field(default_factory=list)


class UserUpdate(UserBase):
    pass


class UserPermissionsUpdate(BaseModel):
    permissions: list[str] = Field(default_factory=list)


class UserOut(UserBase):
    id: int
    permissions: list[str]

    model_config = ConfigDict(from_attributes=True)


class UserListResponse(BaseModel):
    total: int
    items: list[UserOut]


class PermissionOptionsResponse(BaseModel):
    items: list[str]
