from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import ApiConfig
from app.schemas import ApiConfigCreate, ApiConfigUpdate, ApiConfigOut
from app.services.llm import mask_api_key

router = APIRouter(prefix="/api/configs", tags=["configs"])


def _mask_config(config: ApiConfig) -> ApiConfigOut:
    """将 ORM 对象转换为输出 Schema，并对 Key 脱敏"""
    return ApiConfigOut(
        id=config.id,
        name=config.name,
        base_url=config.base_url,
        api_key=mask_api_key(config.api_key),
        default_model=config.default_model,
        is_active=config.is_active,
        created_at=config.created_at,
        updated_at=config.updated_at,
    )


@router.get("", response_model=list[ApiConfigOut])
async def list_configs(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ApiConfig).order_by(ApiConfig.id))
    configs = result.scalars().all()
    return [_mask_config(c) for c in configs]


@router.post("", response_model=ApiConfigOut)
async def create_config(data: ApiConfigCreate, db: AsyncSession = Depends(get_db)):
    config = ApiConfig(**data.model_dump())
    db.add(config)
    await db.commit()
    await db.refresh(config)
    return _mask_config(config)


@router.patch("/{config_id}", response_model=ApiConfigOut)
async def update_config(config_id: int, data: ApiConfigUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ApiConfig).where(ApiConfig.id == config_id))
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(config, key, value)
    await db.commit()
    await db.refresh(config)
    return _mask_config(config)


@router.delete("/{config_id}")
async def delete_config(config_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ApiConfig).where(ApiConfig.id == config_id))
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    await db.delete(config)
    await db.commit()
    return {"ok": True}
