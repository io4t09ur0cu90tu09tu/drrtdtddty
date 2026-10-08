import sys
from pathlib import Path
from copy import deepcopy
import pytest

# Додаємо шлях до сумісності з автотестером
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

try:
    from core import (
        MobileUser,
        apply_loyalty_discount,
        calculate_usage_cost,
        calculate_user_monthly_cost,
        process_orders_pure,
        make_processor,
        make_mobile_processor,
    )
except ImportError:
    from lab01.core import (
        MobileUser,
        apply_loyalty_discount,
        calculate_usage_cost,
        calculate_user_monthly_cost,
        process_orders_pure,
        make_processor,
        make_mobile_processor,
    )


@pytest.fixture
def sample_user() -> MobileUser:
    return {
        "id": 101,
        "name": "Тестовий Користувач",
        "plan": "Basic",
        "usage": {"minutes": 100, "sms": 10, "data_gb": 5.0},
        "bonus_points": 20,
    }


def test_referential_transparency(sample_user: MobileUser) -> None:
    """Перевірка референтної прозорості."""
    tariff = lambda u: calculate_usage_cost(u, 1.0, 0.5, 5.0)
    res1 = calculate_user_monthly_cost(sample_user, tariff, apply_loyalty_discount)
    res2 = calculate_user_monthly_cost(sample_user, tariff, apply_loyalty_discount)
    assert res1 == res2


def test_no_mutation(sample_user: MobileUser) -> None:
    """Перевірка відсутності мутації вхідних даних."""
    original = deepcopy(sample_user)
    tariff = lambda u: calculate_usage_cost(u, 1.0, 0.5, 5.0)
    calculate_user_monthly_cost(sample_user, tariff, apply_loyalty_discount)

    assert sample_user == original
    assert "monthly_cost" not in sample_user


def test_callable_policies(sample_user: MobileUser) -> None:
    """Перевірка параметризації політик через Callable."""
    tariff = lambda u: 100.0
    discount = lambda cost, bonus=0: cost - float(bonus)

    processor = make_mobile_processor(tariff, discount)
    res = processor([sample_user])

    assert res["count"] == 1
    assert res["orders"][0]["monthly_cost"] == 80.0
    assert res["revenue"] == 80.0
