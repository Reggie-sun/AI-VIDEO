from __future__ import annotations

import pytest

import ai_video.production as production


def _binding(
    asset_id: str,
    *,
    view: str,
    digest: str,
) -> production.ProductReferenceAssetBinding:
    return production.ProductReferenceAssetBinding(
        asset_id=asset_id,
        asset_sha256=digest,
        mime_type="image/png",
        width=1080,
        height=1080,
        view=view,
        purpose="product_truth",
    )


def test_product_reference_set_seals_canonical_exact_product_dimension() -> None:
    reference_set = production.ProductReferenceSet.create(
        artifact_id="product-reference-qingyan",
        revision=1,
        product_id="qingyan-spray",
        sku_id="qingyan-yellow-50ml",
        formal_name="青颜净味喷雾",
        truth_reference_ids=("truth-packaging", "truth-label"),
        registry_revision_id="a" * 64,
        registry_content_hash="a" * 64,
        assets=(
            _binding("asset-label", view="label", digest="2" * 64),
            _binding("asset-front", view="front", digest="1" * 64),
        ),
        packaging_form="yellow carton and spray bottle",
        bottle_silhouette="slender rounded-shoulder bottle",
        dominant_color="#F5D400",
        cap_color="#FFFFFF",
        logo_label_identity="QINGYAN yellow label",
        protected_text_zones=("front-label",),
    )

    assert reference_set.schema_version == "product-reference-set/1"
    assert tuple(item.asset_id for item in reference_set.assets) == (
        "asset-front",
        "asset-label",
    )
    assert reference_set.content_hash != "0" * 64


def test_product_reference_set_rejects_missing_label_and_duplicate_asset() -> None:
    front = _binding("asset-front", view="front", digest="1" * 64)

    with pytest.raises(ValueError, match="front and label"):
        production.ProductReferenceSet.create(
            artifact_id="product-reference-qingyan",
            revision=1,
            product_id="qingyan-spray",
            sku_id="qingyan-yellow-50ml",
            formal_name="青颜净味喷雾",
            truth_reference_ids=("truth-packaging",),
            registry_revision_id="a" * 64,
            registry_content_hash="a" * 64,
            assets=(front,),
            packaging_form="carton and bottle",
            bottle_silhouette="slender bottle",
            dominant_color="#F5D400",
            cap_color="#FFFFFF",
            logo_label_identity="QINGYAN",
            protected_text_zones=("front-label",),
        )

    with pytest.raises(ValueError, match="duplicate"):
        production.ProductReferenceSet.create(
            artifact_id="product-reference-qingyan",
            revision=1,
            product_id="qingyan-spray",
            sku_id="qingyan-yellow-50ml",
            formal_name="青颜净味喷雾",
            truth_reference_ids=("truth-packaging",),
            registry_revision_id="a" * 64,
            registry_content_hash="a" * 64,
            assets=(front, front.model_copy(update={"view": "label"})),
            packaging_form="carton and bottle",
            bottle_silhouette="slender bottle",
            dominant_color="#F5D400",
            cap_color="#FFFFFF",
            logo_label_identity="QINGYAN",
            protected_text_zones=("front-label",),
        )
