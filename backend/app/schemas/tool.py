from pydantic import BaseModel, Field, ConfigDict


class ToolBase(BaseModel):
    tool_code: str = Field(min_length=1, max_length=64)
    tool_type: str = Field(min_length=1, max_length=64)
    tool_name: str = Field(min_length=1, max_length=128)
    stock: int = Field(ge=0, le=99999)
    team: str = Field(min_length=1, max_length=128)
    image_url: str = ''


class ToolCreate(ToolBase):
    pass


class ToolUpdate(ToolBase):
    pass


class ToolOut(ToolBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class ToolListResponse(BaseModel):
    total: int
    items: list[ToolOut]
