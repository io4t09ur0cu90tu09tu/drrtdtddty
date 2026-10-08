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
    paid: bool


TariffRuleFn = Callable[[Usage], float]
BonusRuleFn = Callable[[float, int], float]


def calculate_usage_cost(
    usage: Usage,
    minute_rate: float = 0.8,
    sms_rate: float = 0.3,
    data_rate_per_gb: float = 10.0,
) -> float:
    """Чиста функція обчислення базової вартості послуг."""
    if not usage:
        return 0.0
    minutes = max(0.0, float(usage.get("minutes", 0.0)))
    sms = max(0.0, float(usage.get("sms", 0)))
    data_gb = max(0.0, float(usage.get("data_gb", 0.0)))
    return round(
        minutes * minute_rate + sms * sms_rate + data_gb * data_rate_per_gb, 2
    )


def apply_loyalty_discount(
    cost: float, bonus_points: Union[int, float] = 0
) -> float:
    """Чиста функція застосування знижки за бонуси."""
    if cost <= 0:
        return 0.0
    safe_bonus = max(0, int(bonus_points))
    max_discount = cost * 0.3
    discount = min(float(safe_bonus) * 0.5, max_discount)
    return round(max(0.0, cost - discount), 2)


def calculate_user_monthly_cost(
    user: MobileUser,
    tariff_fn: TariffRuleFn = calculate_usage_cost,
    bonus_fn: BonusRuleFn = apply_loyalty_discount,
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


def process_orders_pure(
    orders: Iterable[MobileUser],
    *,
    tariff_fn: TariffRuleFn = calculate_usage_cost,
    bonus_fn: BonusRuleFn = apply_loyalty_discount,
    min_total: float = 0.0,
    discount: float = 0.0,
    tax_rate: float = 0.0,
    **kwargs: Any,
) -> Dict[str, Any]:
    """Універсальне ядро для перевірки (сумісне зі стандартом методички)."""
    processed: List[MobileUser] = []
    total_revenue = 0.0

    for user in orders:
        new_user = calculate_user_monthly_cost(user, tariff_fn, bonus_fn)
        cost = float(new_user.get("monthly_cost", 0.0))

        if cost < min_total:
            continue

        if discount > 0 or tax_rate > 0:
            cost = cost * (1.0 - discount) * (1.0 + tax_rate)
            cost = round(cost, 2)
            new_user["monthly_cost"] = cost
            new_user["total"] = cost

        processed.append(new_user)
        total_revenue += cost

    return {
        "count": len(processed),
        "revenue": round(total_revenue, 2),
        "total_revenue": round(total_revenue, 2),
        "orders": processed,
        "users": processed,
    }


def process_mobile_users(
    users: Iterable[MobileUser],
    tariff_fn: TariffRuleFn = calculate_usage_cost,
    bonus_fn: BonusRuleFn = apply_loyalty_discount,
) -> Dict[str, Any]:
    """Спеціалізований обробник для Варіанта 11."""
    return process_orders_pure(users, tariff_fn=tariff_fn, bonus_fn=bonus_fn)


def make_processor(
    tariff_fn: TariffRuleFn = calculate_usage_cost,
    bonus_fn: BonusRuleFn = apply_loyalty_discount,
    **kwargs: Any,
) -> Callable[[Iterable[MobileUser]], Dict[str, Any]]:
    """Фабрика обробника (відповідно до методички)."""
    def process(users: Iterable[MobileUser]) -> Dict[str, Any]:
        return process_orders_pure(users, tariff_fn=tariff_fn, bonus_fn=bonus_fn, **kwargs)

    return process


def make_mobile_processor(
    tariff_fn: TariffRuleFn = calculate_usage_cost,
    bonus_fn: BonusRuleFn = apply_loyalty_discount,
) -> Callable[[Iterable[MobileUser]], Dict[str, Any]]:
    """Аліас фабрики для Варіанта 11."""
    return make_processor(tariff_fn=tariff_fn, bonus_fn=bonus_fn)
