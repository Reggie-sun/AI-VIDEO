"""Measure requested aspect ratio independently of adaptive output raster."""


def matches_video_geometry(output, *, width: int, height: int) -> bool:
    expected_width = getattr(output, "width", None)
    expected_height = getattr(output, "height", None)
    if (expected_width is not None and width != expected_width
            or expected_height is not None and height != expected_height):
        return False
    if expected_width is not None and expected_height is not None:
        return True
    ratio = getattr(output, "ratio", "adaptive")
    if ratio == "adaptive":
        return True
    ratio_width, ratio_height = (int(value) for value in ratio.split(":"))
    return width * ratio_height == height * ratio_width
