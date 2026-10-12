"""Express existing approved-first-frame product fidelity in native prose."""


def product_fidelity_sentences(requirement) -> tuple[str, ...]:
    fidelity = requirement.product_fidelity_requirement
    if fidelity is None:
        return ()
    return (
        f"Product identity: product_id={fidelity.product_id}, sku_id={fidelity.sku_id}.",
        "Use the approved first-frame product without replacing its packaging or identity.",
        f"Preserve packaging form: {fidelity.packaging_form}.",
        f"Preserve bottle silhouette: {fidelity.bottle_silhouette}.",
        f"Preserve dominant color: {fidelity.dominant_color}.",
        f"Preserve cap color: {fidelity.cap_color}.",
        f"Preserve logo and label identity: {fidelity.logo_label_identity}.",
        "Keep protected text zones legible and unchanged: " + ", ".join(fidelity.protected_text_zones) + ".",
        "Product source identity: product_source_asset_hashes=" + ",".join(fidelity.product_source_asset_hashes) + ".",
    )
