from __future__ import annotations

import pytest

from changeguard.datahub_gateway import DataHubGateway
from changeguard.models import AnalysisResult, Decision


def test_writeback_requires_confirmation_before_any_client_access() -> None:
    gateway = object.__new__(DataHubGateway)
    result = AnalysisResult(
        dataset_urn="urn:li:dataset:(urn:li:dataPlatform:postgres,orders,PROD)",
        decision=Decision.BLOCK,
        risk_score=90,
        findings=(),
        owners=(),
        downstream_count=0,
        evidence_source="test",
    )
    with pytest.raises(PermissionError, match="explicit confirmation"):
        gateway.writeback(result, confirm=False)
