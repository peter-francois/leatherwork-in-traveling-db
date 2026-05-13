from django.test import TestCase
from cart.services.pricing_services import (
    calculate_total_centimes,
    calculate_insurance_cost_centimes,
    verify_total,
    convert_centimes_to_euros,
    convert_euros_to_centimes,
    AmountMismatchError,
    AmountNegatifError,
)
from cart.constants import (
    HOME_DELIVERY_SHIPPING_COST, STANDARD_SHIPPING_COST,
    INSURANCE_OPTIONAL_MIN, INSURANCE_OPTIONAL_MAX, INSURANCE_OPTIONAL_COST,
    INSURANCE_MANDATORY_MIN, INSURANCE_THRESHOLD_1,
    INSURANCE_THRESHOLD_2, INSURANCE_THRESHOLD_3,
    INSURANCE_COST_50_TO_125, INSURANCE_COST_125_TO_250,
    INSURANCE_COST_250_TO_375, INSURANCE_COST_ABOVE_375,
)


class CalculateInsuranceCostCentimesTest(TestCase):
    """Tests for calculate_insurance_cost_centimes"""

    def test_returns_zero_below_optional_min(self):
        """Should return 0 when total is below optional insurance threshold"""
        result = calculate_insurance_cost_centimes(INSURANCE_OPTIONAL_MIN, is_optional_insurance=False)
        self.assertEqual(result, 0)

    def test_returns_zero_in_optional_range_without_insurance(self):
        """Should return 0 in optional range when is_optional_insurance is False"""
        total = INSURANCE_OPTIONAL_MIN + 1
        result = calculate_insurance_cost_centimes(total, is_optional_insurance=False)
        self.assertEqual(result, 0)

    def test_returns_optional_cost_in_optional_range_with_insurance(self):
        """Should return optional cost when is_optional_insurance is True in optional range"""
        total = INSURANCE_OPTIONAL_MIN + 1
        result = calculate_insurance_cost_centimes(total, is_optional_insurance=True)
        self.assertEqual(result, INSURANCE_OPTIONAL_COST)

    def test_returns_tier_1_cost_just_above_mandatory_min(self):
        """Should return tier 1 cost just above mandatory threshold"""
        total = INSURANCE_MANDATORY_MIN + 1
        result = calculate_insurance_cost_centimes(total, is_optional_insurance=False)
        self.assertEqual(result, INSURANCE_COST_50_TO_125)

    def test_returns_tier_2_cost_above_threshold_1(self):
        """Should return tier 2 cost above threshold 1"""
        total = INSURANCE_THRESHOLD_1 + 1
        result = calculate_insurance_cost_centimes(total, is_optional_insurance=False)
        self.assertEqual(result, INSURANCE_COST_125_TO_250)

    def test_returns_tier_3_cost_above_threshold_2(self):
        """Should return tier 3 cost above threshold 2"""
        total = INSURANCE_THRESHOLD_2 + 1
        result = calculate_insurance_cost_centimes(total, is_optional_insurance=False)
        self.assertEqual(result, INSURANCE_COST_250_TO_375)

    def test_returns_tier_4_cost_above_threshold_3(self):
        """Should return tier 4 cost above threshold 3"""
        total = INSURANCE_THRESHOLD_3 + 1
        result = calculate_insurance_cost_centimes(total, is_optional_insurance=False)
        self.assertEqual(result, INSURANCE_COST_ABOVE_375)


class CalculateTotalCentimesTest(TestCase):
    """Tests for calculate_total_centimes"""

    def test_adds_standard_shipping_when_no_express(self):
        """Should add standard shipping cost when is_home_delivery is False"""
        result = calculate_total_centimes(1000, is_optional_insurance=False, is_home_delivery=False)
        self.assertEqual(result, 1000 + STANDARD_SHIPPING_COST)

    def test_adds_express_shipping_when_requested(self):
        """Should add home delivery shipping cost when is_home_delivery is True"""
        result = calculate_total_centimes(1000, is_optional_insurance=False, is_home_delivery=True)
        self.assertEqual(result, 1000 + HOME_DELIVERY_SHIPPING_COST)

    def test_adds_optional_insurance_when_requested(self):
        """Should add optional insurance cost when in optional range and is_optional_insurance is True"""
        total = INSURANCE_OPTIONAL_MIN + 1
        result = calculate_total_centimes(total, is_optional_insurance=True, is_home_delivery=False)
        self.assertEqual(result, total + INSURANCE_OPTIONAL_COST + STANDARD_SHIPPING_COST)

    def test_adds_mandatory_insurance_automatically(self):
        """Should add mandatory insurance regardless of is_optional_insurance flag"""
        total = INSURANCE_MANDATORY_MIN + 1
        excepted = total + INSURANCE_COST_50_TO_125 + STANDARD_SHIPPING_COST
        result = calculate_total_centimes(total, is_optional_insurance=False, is_home_delivery=False)
        self.assertEqual(result, excepted)

    def test_raises_amount_negatif_error_when_total_is_zero(self):
        """Should raise AmountNegatifError when total is zero or negative"""
        with self.assertRaises(AmountNegatifError):
            calculate_total_centimes(0, is_optional_insurance=False, is_home_delivery=False)

    def test_returns_correct_total_with_all_options(self):
        """Should return correct total with insurance and express shipping"""
        total = INSURANCE_MANDATORY_MIN + 1
        expected = total + INSURANCE_COST_50_TO_125 + HOME_DELIVERY_SHIPPING_COST
        result = calculate_total_centimes(total, is_optional_insurance=True, is_home_delivery=True)
        self.assertEqual(result, expected)


class VerifyTotalTest(TestCase):
    """Tests for verify_total"""

    def test_does_not_raise_when_totals_match(self):
        """Should not raise when front and back totals match"""
        try:
            verify_total(10500, 10500)
        except AmountMismatchError:
            self.fail("verify_total raised AmountMismatchError unexpectedly")

    def test_raises_when_totals_mismatch(self):
        """Should raise AmountMismatchError when totals don't match"""
        with self.assertRaises(AmountMismatchError):
            verify_total(10500, 10000)


class ConvertCentimesToEurosTest(TestCase):
    """Tests for convert_centimes_to_euros"""

    def test_converts_correctly(self):
        """Should convert centimes to euros correctly"""
        self.assertEqual(convert_centimes_to_euros(1000), 10.0)
        self.assertEqual(convert_centimes_to_euros(10500), 105.0)
        self.assertEqual(convert_centimes_to_euros(1), 0.01)

    def test_rounds_to_2_decimals(self):
        """Should round to 2 decimal places"""
        self.assertEqual(convert_centimes_to_euros(1005), 10.05)

    def test_handles_string_input(self):
        """Should handle string input"""
        self.assertEqual(convert_centimes_to_euros('1000'), 10.0)


class ConvertEurosToCentimesTest(TestCase):
    """Tests for convert_euros_to_centimes"""

    def test_converts_correctly(self):
        """Should convert euros to centimes correctly"""
        self.assertEqual(convert_euros_to_centimes(10.0), 1000)
        self.assertEqual(convert_euros_to_centimes(105.0), 10500)

    def test_handles_string_input(self):
        """Should handle string input"""
        self.assertEqual(convert_euros_to_centimes('10.0'), 1000)

    def test_rounds_correctly(self):
        """Should round correctly"""
        self.assertEqual(convert_euros_to_centimes(10.005), 1001)