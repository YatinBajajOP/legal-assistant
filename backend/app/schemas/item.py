from pydantic import BaseModel

class ItemBase(BaseModel):
    title: str | None = None
    description: str | None = None

class ItemCreate(ItemBase):
    title: str

class ItemUpdate(ItemBase):
    pass

class ItemPublic(ItemBase):
    id: int

    class ConfigDict:
        from_attributes = True
