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
    """Обчислює вартість використаних послуг."""
    if not usage:
        return 0.0
    minutes = max(0.0, float(usage.get("minutes", 0.0)))
    sms = max(0.0, float(usage.get("sms", 0)))
    data_gb = max(0.0, float(usage.get("data_gb", 0.0)))
    return round(
        minutes * minute_rate + sms * sms_rate + data_gb * data_rate_per_gb, 2
    )


def apply_loyalty_discount(
    cost: float, bonus_points: Union[int, float]
) -> float:
    """Застосовує знижку за накопичені бонуси."""
    if cost <= 0:
        return 0.0
    safe_bonus = max(0, int(bonus_points))
    max_discount = cost * 0.3
    discount = min(float(safe_bonus) * 0.5, max_discount)
    return round(max(0.0, cost - discount), 2)


def calculate_user_monthly_cost(
    user: MobileUser, tariff_fn: TariffRuleFn, bonus_fn: BonusRuleFn
) -> MobileUser:
    """Обчислює суму до сплати та повертає новий словник без мутації вхідного."""
    usage = user.get("usage", {})
    bonus_points = int(user.get("bonus_points", 0))

    base_cost = tariff_fn(usage)
    final_cost = bonus_fn(base_cost, bonus_points)

    new_user = dict(user)
    new_user["monthly_cost"] = round(float(final_cost), 2)
    new_user["total"] = round(float(final_cost), 2)
    return new_user


def process_mobile_users(
    users: Iterable[MobileUser],
    tariff_fn: TariffRuleFn,
    bonus_fn: BonusRuleFn,
) -> Dict[str, Any]:
    """Чиста функція обробки списку акаунтів."""
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


def make_mobile_processor(
    tariff_fn: TariffRuleFn, bonus_fn: BonusRuleFn
) -> Callable[[Iterable[MobileUser]], Dict[str, Any]]:
    """Фабрика вищого порядку."""
    def process(users: Iterable[MobileUser]) -> Dict[str, Any]:
        return process_mobile_users(users, tariff_fn, bonus_fn)

    return process
