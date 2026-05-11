from cart.constants import (
     EXPRESS_SHIPPING_COST, STANDARD_SHIPPING_COST,
    INSURANCE_OPTIONAL_MIN, INSURANCE_OPTIONAL_MAX, INSURANCE_OPTIONAL_COST,
    INSURANCE_MANDATORY_MIN,INSURANCE_THRESHOLD_1,
    INSURANCE_THRESHOLD_2,INSURANCE_THRESHOLD_3,INSURANCE_COST_50_TO_125,
    INSURANCE_COST_125_TO_250,INSURANCE_COST_250_TO_375,
    INSURANCE_COST_ABOVE_375,
)
class AmountMismatchError(Exception):
    pass

def get_total_centimes(total_articles_euros, add_insurance, add_shipping) -> int:
    total_centimes = int(round(total_articles_euros * 100))

    if total_centimes > INSURANCE_MANDATORY_MIN:
        if total_centimes > INSURANCE_THRESHOLD_3:
            total_centimes += INSURANCE_COST_ABOVE_375
        elif total_centimes > INSURANCE_THRESHOLD_2:
            total_centimes += INSURANCE_COST_250_TO_375
        elif total_centimes > INSURANCE_THRESHOLD_1:
            total_centimes += INSURANCE_COST_125_TO_250
        else:
            total_centimes += INSURANCE_COST_50_TO_125
    elif INSURANCE_OPTIONAL_MIN < total_centimes <= INSURANCE_OPTIONAL_MAX:
        if add_insurance:
            total_centimes += INSURANCE_OPTIONAL_COST

    total_centimes += EXPRESS_SHIPPING_COST if add_shipping else STANDARD_SHIPPING_COST

    if total_centimes <= 0:
        raise ValueError("Invalid total amount")

    return total_centimes

def verify_total(total_articles_euros, add_insurance, add_shipping, front_total) -> int:
    
    total_centimes = get_total_centimes(total_articles_euros, add_insurance, add_shipping)
    front_total_centimes = int(round(front_total * 100))
    
    if front_total_centimes != total_centimes:
        raise AmountMismatchError(f"Front: {front_total_centimes}, Back: {total_centimes}")
    
    return total_centimes
