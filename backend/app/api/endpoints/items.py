from fastapi import APIRouter

router = APIRouter()

@router.get("/items/")
async def read_items():
    return [{"name": "Item One"}, {"name": "Item Two"}]

@router.get("/items/{item_id}")
async def read_item(item_id: int):
    return {"name": f"Item {item_id}", "item_id": item_id} 