"""Pytest customizations and fixtures for the quipucords tests."""

from camayoc.config import settings


def scan_list(source_types=None):
    """Generate list of network / VCenter / Satellite scan objects found in config file.

    Optionally filter by a custom iterable of source types (network, vcenter, satellite).
    """
    scans = []
    if source_types is None:
        supported_source_types = ("network", "vcenter", "satellite")
    else:
        supported_source_types = source_types
    source_names_types = {s.name: s.type for s in settings.sources}
    for scan in settings.scans:
        source_types = [source_names_types.get(source) for source in scan.sources]
        if not all(source_type in supported_source_types for source_type in source_types):
            continue
        scans.append(scan)
    return scans
