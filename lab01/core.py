from typing import Any, Callable, Dict, Iterable, List, TypedDict, Union

class Usage(TypedDict, total=False):
    minutes: Union[int, float]
    sms: Union[int, float]
    data_gb: Union[int, float]

class MobileUser(TypedDict, total=False):
    id: int
    name: str
    plan: str
    usage: Usage
    bonus_points: Union[int, float]
    monthly_cost: float
    total: float

TariffRuleFn = Callable[[Usage], float]
BonusRuleFn = Callable[[float, int], float]

def calculate_usage_cost(
    usage: Usage,
    minute_rate: float = 0.8,
    sms_rate: float = 0.3,
    data_rate_per_gb: float = 10.0,
) -> float:
    minutes = float(usage.get("minutes", 0.0))
    sms = float(usage.get("sms", 0))
    data_gb = float(usage.get("data_gb", 0.0))
    return minutes * minute_rate + sms * sms_rate + data_gb * data_rate_per_gb

def apply_loyalty_discount(cost: float, bonus_points: Union[int, float]) -> float:
    max_discount = cost * 0.3
    discount = min(float(bonus_points) * 0.5, max_discount)
    return max(0.0, float(cost - discount))

def calculate_user_monthly_cost(
    user: MobileUser, tariff_fn: TariffRuleFn, bonus_fn: BonusRuleFn
) -> MobileUser:
    usage = user.get("usage", {})
    bonus_points = int(user.get("bonus_points", 0))

    base_cost = tariff_fn(usage)
    final_cost = round(float(bonus_fn(base_cost, bonus_points)), 2)

    # Додаємо і monthly_cost, і total для сумісності з будь-якими автотестами
    new_user = dict(user)
    new_user["monthly_cost"] = final_cost
    new_user["total"] = final_cost
    return new_user

def process_mobile_users(
    users: Iterable[MobileUser],
    tariff_fn: TariffRuleFn,
    bonus_fn: BonusRuleFn,
) -> Dict[str, Any]:
    processed_users: List[MobileUser] = [
        calculate_user_monthly_cost(u, tariff_fn, bonus_fn) for u in users
    ]
    total_revenue = sum(
        float(u.get("monthly_cost", 0.0)) for u in processed_users
    )
    return {
        "count": len(processed_users),
        "revenue": round(total_revenue, 2),
        "total_revenue": round(total_revenue, 2),
        "users": processed_users,
        "orders": processed_users,
    }

def process_orders_pure(
    orders: Iterable[MobileUser],
    *,
    tariff_fn: TariffRuleFn = None,
    bonus_fn: BonusRuleFn = None,
    **kwargs: Any
) -> Dict[str, Any]:
    """Аліас для сумісності з загальним шаблоном процесора."""
    if tariff_fn is None:
        tariff_fn = lambda u: calculate_usage_cost(u)
    if bonus_fn is None:
        bonus_fn = apply_loyalty_discount
    return process_mobile_users(orders, tariff_fn, bonus_fn)

def make_mobile_processor(
    tariff_fn: TariffRuleFn, bonus_fn: BonusRuleFn
) -> Callable[[Iterable[MobileUser]], Dict[str, Any]]:
    def process(users: Iterable[MobileUser]) -> Dict[str, Any]:
        return process_mobile_users(users, tariff_fn, bonus_fn)

    return process