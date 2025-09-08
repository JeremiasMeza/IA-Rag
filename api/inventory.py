# Archivo eliminado: funcionalidad migrada o eliminada
# api/inventory.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from db import get_session
from models import Product
from schemas import ProductCreate, ProductRead, ProductUpdate

router = APIRouter(tags=["inventory"])

@router.post("/", response_model=ProductRead)
async def create_product(
    product_in: ProductCreate,
    session: AsyncSession = Depends(get_session),
):
    product = Product(**product_in.dict())
    session.add(product)
    await session.commit()
    await session.refresh(product)
    return product

@router.get("/", response_model=list[ProductRead])
async def list_products(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Product))
    return result.scalars().all()

@router.get("/{product_id}", response_model=ProductRead)
async def get_product(product_id: int, session: AsyncSession = Depends(get_session)):
    product = await session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.put("/{product_id}", response_model=ProductRead)
async def update_product(
    product_id: int,
    product_in: ProductUpdate,
    session: AsyncSession = Depends(get_session),
):
    product = await session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    for field, value in product_in.dict(exclude_unset=True).items():
        setattr(product, field, value)
    await session.commit()
    await session.refresh(product)
    return product

@router.delete("/{product_id}")
async def delete_product(product_id: int, session: AsyncSession = Depends(get_session)):
    product = await session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    await session.delete(product)
    await session.commit()
    return {"ok": True, "deleted_id": product_id}
