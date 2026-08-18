from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PaidProviderPermitDouble:
    binding: dict[str, str]
    consumed: bool = False

    def _validate_paid_provider_operation_permit(self, **binding: str) -> bool:
        return not self.consumed and binding == self.binding

    def _consume_paid_provider_operation_permit(self, **binding: str) -> bool:
        if not self._validate_paid_provider_operation_permit(**binding):
            return False
        self.consumed = True
        return True


def assert_video_provider_contract(*, provider: object) -> None:
    capabilities = provider.capabilities()
    assert capabilities.variants
    assert provider.call_counts.capabilities == 1
