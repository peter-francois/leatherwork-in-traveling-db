from cart.constants import (
    HOME_DELIVERY_SHIPPING_COST,
    INSURANCE_COST_50_TO_125,
    INSURANCE_COST_125_TO_250,
    INSURANCE_COST_250_TO_375,
    INSURANCE_COST_ABOVE_375,
    INSURANCE_MANDATORY_MIN,
    INSURANCE_OPTIONAL_COST,
    INSURANCE_OPTIONAL_MAX,
    INSURANCE_OPTIONAL_MIN,
    INSURANCE_THRESHOLD_1,
    INSURANCE_THRESHOLD_2,
    INSURANCE_THRESHOLD_3,
    STANDARD_SHIPPING_COST,
)


class AmountMismatchError(Exception):
    pass


class AmountNegatifError(Exception):
    pass


def calculate_total_centimes(
    total_articles_centimes, is_optional_insurance, is_home_delivery
) -> int:
    if total_articles_centimes <= 0:
        raise AmountNegatifError(
            f"Invalid articles total amount: {total_articles_centimes}"
        )

    total_centimes = total_articles_centimes

    total_centimes += calculate_insurance_cost_centimes(
        total_centimes, is_optional_insurance
    )

    total_centimes += (
        HOME_DELIVERY_SHIPPING_COST if is_home_delivery else STANDARD_SHIPPING_COST
    )

    return total_centimes


def calculate_insurance_cost_centimes(total_centimes, is_optional_insurance) -> int:
    if total_centimes > INSURANCE_MANDATORY_MIN:
        if total_centimes > INSURANCE_THRESHOLD_3:
            return INSURANCE_COST_ABOVE_375
        elif total_centimes > INSURANCE_THRESHOLD_2:
            return INSURANCE_COST_250_TO_375
        elif total_centimes > INSURANCE_THRESHOLD_1:
            return INSURANCE_COST_125_TO_250
        else:
            return INSURANCE_COST_50_TO_125

    elif INSURANCE_OPTIONAL_MIN < total_centimes <= INSURANCE_OPTIONAL_MAX:
        if is_optional_insurance:
            return INSURANCE_OPTIONAL_COST

    return 0


def verify_total(total_centimes, front_total_centimes) -> None:
    if front_total_centimes != total_centimes:
        raise AmountMismatchError(
            f"Front: {front_total_centimes}, Back: {total_centimes}"
        )


def convert_centimes_to_euros(centimes):
    return round(int(centimes) / 100, 2)


def convert_euros_to_centimes(euros):
    return int(round(float(euros) * 100))
