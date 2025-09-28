from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from decimal import Decimal

import httpx
from ufaas import exceptions, services

from server.config import Settings

from .saas import UsageCreateSchema, UsageSchema

resource_variant = getattr(Settings, "UFAAS_RESOURCE_VARIANT", "ocr")


@asynccontextmanager
async def get_ufaas_client() -> AsyncGenerator[services.AccountingClient]:
    async with httpx.AsyncClient(
        base_url="https://saas.uln.me/api/saas/v1/",
        headers={"x-api-key": Settings.finance_api_key},
    ) as client:
        yield client


async def meter_cost(
    user_id: str, amount: float, meta_data: dict | None = None
) -> UsageSchema:
    return UsageSchema(
        tenant_id="",
        user_id=user_id,
        consumptions=[],
        asset="coin",
        amount=amount,
        variant=resource_variant,
        meta_data=meta_data,
    )
    async with get_ufaas_client() as ufaas_client:
        usage_schema = UsageCreateSchema(
            user_id=user_id,
            asset="coin",
            amount=amount,
            variant=resource_variant,
            meta_data=meta_data,
        )
        usage = await ufaas_client.saas.usages.create_item(
            usage_schema.model_dump(mode="json"), timeout=30
        )
        return usage


async def get_quota(user_id: str) -> Decimal:
    return 100
    async with get_ufaas_client() as ufaas_client:
        quotas = await ufaas_client.saas.enrollments.get_quotas(
            user_id=user_id,
            asset="coin",
            variant=resource_variant,
            timeout=30,
        )
    return quotas.quota


async def cancel_usage(usage_id: str) -> None:
    if usage_id is None:
        return
    async with get_ufaas_client() as ufaas_client:
        await ufaas_client.saas.usages.cancel_item(usage_id)


async def check_quota(
    user_id: str, coin: float, *, raise_exception: bool = True
) -> Decimal:
    return 100
    quota = await get_quota(user_id)
    if raise_exception and (quota is None or quota < coin):
        raise exceptions.InsufficientFundsError(
            f"You have only {quota} coins, while you need {coin} coins."
        )
    return quota
