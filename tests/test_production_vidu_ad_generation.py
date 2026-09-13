from datetime import timedelta

import pytest

from ai_video.production.vidu_ad_contracts import AdGenerationRequest, AdImageBinding
from paid_provider_support import NOW


def test_request_seal_preserves_image_order_and_rejects_tampering():
    image = AdImageBinding(asset_id="product", sha256="1" * 64, size_bytes=12,
                           mime_type="image/png", width=128, height=128)
    request = AdGenerationRequest.create(
        task_id="shop-ad", submit_limit=1, project_id="shop", project_hash="2" * 64,
        registry_hash="3" * 64, profile_hash="4" * 64, images=(image,),
        prompt="九号广告", duration=28, aspect_ratio="9:16", language="zh", creative=False,
        policy_id="ad-policy", expires_at=NOW + timedelta(hours=1),
    )
    assert AdGenerationRequest.model_validate_json(request.model_dump_json()) == request
    with pytest.raises(ValueError):
        AdGenerationRequest.model_validate({**request.model_dump(), "duration": 29})
