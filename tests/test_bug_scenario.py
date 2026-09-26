import pytest

from relaygrid.analytics.kpi import restoration_curve
from relaygrid.reliability.indices import CustomerInterruption, saidi, saifi
from relaygrid.services.outage_service import OutageService


def test_late_outage_evidence_does_not_rewrite_reliability_history():
    outages = OutageService()
    outages.add("G1", customers=10, start_min=0.0, end_min=10.0)
    outages.add("G1", customers=20, start_min=20.0, end_min=30.0)
    assert outages.customer_minutes() == pytest.approx(300.0)
    assert outages.group_summaries()["G1"]["customer_minutes"] == pytest.approx(300.0)

    duplicate = CustomerInterruption("E1", customers=50, duration_min=30.0)
    assert saidi([duplicate, duplicate], customers_served=100) == pytest.approx(15.0)
    assert saifi([duplicate, duplicate], customers_served=100) == pytest.approx(0.5)

    curve = restoration_curve([(0.0, 20), (10.0, 80), (20.0, 60)], total_customers=100)
    assert curve == [(0.0, 0.2), (10.0, 0.8), (20.0, 0.8)]
