import os
import gzip
import xml.etree.ElementTree as ET

import db
import events
import file_utils

# First real use of the entries table by any module. 'record' was chosen
# over 'thought'/'idea'/etc because a dependency scan is finalized,
# machine-derived structured data about a real project, not something
# still maturing — see the content maturity ladder in SYSTEM_OVERVIEW.md.
TAXONOMY_STAGE = "record"


def _parse_als(path):
    """
    Decompresses and parses a single .als file, returning the raw list of
    sample dependencies it references (unclassified — existence checks
    happen separately in _classify_dependency, against the scanned
    folder, not against any path reconstructed from the XML).

    Two known FileRef shapes, both captured by 'name' + diagnostic
    'historical_path' (never used for current-existence checks — it
    reflects where a file was the last time the project was saved, not
    necessarily where it is now):

    - Newer versions: a flat <Path Value=".."/> absolute-path attribute.
      NOT validated against a real file — only ever seen the older shape
      below in a real (Live 9.5) export. is_library_resource is left
      unset (None) here rather than guessed, since the discriminator
      below was only confirmed against the other shape.

    - Older versions (confirmed against a real Live 9.5 .als): no flat
      absolute path at all — a <RelativePath> chain of
      <RelativePathElement Dir=".."/> nodes (this chain is NOT reliably
      resolvable to a current path — empty Dir values appear to mean
      'go up a level' and aren't decoded here) plus a sibling
      <Name Value=".."/> for the filename. A populated
      <SearchHint><PathHint> gives a real historical absolute path and,
      empirically, was present for genuine user samples and absent for
      Ableton's own factory device presets (reverb/delay/etc reused as
      FileRefs too) — that presence/absence is used as the
      is_library_resource signal. Confirmed against exactly one real
      file so far; only 2 sample types and 2 device-preset types were
      observed, so this hasn't been stress-tested against Ableton's
      full preset taxonomy (racks, macros, etc).

    If a FileRef matches neither shape, the raw element is captured
    instead of silently dropped — an unrecognized structure should be
    visible and fixable, not invisible.

    Raises on total parse failure (corrupt gzip, non-XML content) —
    this function stays pure and lets the caller decide how to handle
    a bad file.
    """
    with gzip.open(path, "rb") as f:
        tree = ET.parse(f)
    root = tree.getroot()

    dependencies = []
    for file_ref in root.iter("FileRef"):
        path_el = file_ref.find("Path")

        if path_el is not None and path_el.get("Value"):
            relpath_el = file_ref.find("RelativePath")
            dependencies.append({
                "name": os.path.basename(path_el.get("Value")),
                "source": "stored_absolute",
                "historical_path": path_el.get("Value"),
                "relative_path_hint": relpath_el.get("Value") if relpath_el is not None else None,
                "is_library_resource": None,  # unvalidated discriminator for this shape — not guessed
                "raw_unrecognized": None,
            })
            continue

        name_el = file_ref.find("Name")
        relpath_container = file_ref.find("RelativePath")
        if name_el is not None and name_el.get("Value") and relpath_container is not None:
            name = name_el.get("Value")
            rel_dirs = [el.get("Dir", "") for el in relpath_container.findall("RelativePathElement")]

            pathhint_el = file_ref.find("SearchHint/PathHint")
            hint_dirs = (
                [el.get("Dir") for el in pathhint_el.findall("RelativePathElement") if el.get("Dir")]
                if pathhint_el is not None else []
            )
            historical_path = ("/" + "/".join(hint_dirs) + "/" + name) if hint_dirs else None

            dependencies.append({
                "name": name,
                "source": "resolved_from_relative_chain",
                "historical_path": historical_path,
                "relative_path_hint": "/".join(rel_dirs) if rel_dirs else None,
                "is_library_resource": historical_path is None,
                "raw_unrecognized": None,
            })
            continue

        # Neither known shape matched. Don't drop this silently — log the
        # raw XML so a real schema mismatch is diagnosable instead of
        # producing a quietly-incomplete dependency list.
        dependencies.append({
            "name": None,
            "source": "unrecognized",
            "historical_path": None,
            "relative_path_hint": None,
            "is_library_resource": None,
            "raw_unrecognized": ET.tostring(file_ref, encoding="unicode")[:500],
        })

    return dependencies


def _classify_dependency(dep, root_folder):
    """
    Adds the current-existence check: does a file with this exact name
    exist directly in the folder being scanned? This replaced trying to
    reconstruct a 'current' absolute path from the XML's relative-path
    data — that data reflects the file's location at last save, and for
    the mixed-folder scenario this module exists for, that's frequently
    stale. Checking the scanned folder directly matches how the files
    actually sit on disk right now.
    """
    name = dep.get("name")
    if not name:
        dep["exists_in_scanned_folder"] = None
        dep["current_path"] = None
        return dep

    candidate = os.path.join(root_folder, name)
    exists = os.path.isfile(candidate)
    dep["exists_in_scanned_folder"] = exists
    dep["current_path"] = candidate if exists else None
    return dep


def scan_folder(folder_path):
    """
    Chunk 1 of the Ableton Partner (Project Collector brain): parse-only.

    Walks every .als file directly inside folder_path (not recursive —
    matches the single messy folder this was built for), extracts each
    one's sample dependency list, and logs one 'record'-stage entry per
    .als to the entries table. Never moves, copies, renames, or modifies
    any file — that's Chunk 2/3, not this.

    Factory/library device-preset dependencies (is_library_resource=True)
    are kept in the output, not dropped — they're excluded from
    move/copy consideration in later chunks, but still visible here for
    inspection.

    A corrupt/unparseable .als is skipped and logged, never raised —
    one bad file must not stop the batch. No Crier yet, so the
    end-of-batch report is a console printout + events.log entries;
    that's the whole notification story until Crier exists.

    Manual-trigger only — not wired into the config.yaml claims-based
    registry, since there's nothing to match against (no
    file_extension/keyword/folder/event claim applies to a batch scan
    you kick off yourself).

    Returns {"succeeded": [...], "failed": [...]}.
    """
    folder_path = os.path.expanduser(folder_path)
    als_files = sorted(
        f for f in os.listdir(folder_path)
        if f.lower().endswith(".als") and not file_utils.is_hidden(f)
    )

    succeeded = []
    failed = []

    for filename in als_files:
        full_path = os.path.join(folder_path, filename)
        try:
            dependencies = _parse_als(full_path)
            dependencies = [_classify_dependency(d, folder_path) for d in dependencies]

            entry_id = db.create_entry(
                silo="file_lord",
                raw_text=filename,
                taxonomy_stage=TAXONOMY_STAGE,
                tags=["ableton", "project_collector", "dependency_scan"],
                metadata={
                    "als_path": full_path,
                    "dependency_count": len(dependencies),
                    "dependencies": dependencies,
                },
            )

            result = {"file": filename, "entry_id": entry_id, "dependency_count": len(dependencies)}
            succeeded.append(result)
            events.emit("ableton_scan_success", result)

        except Exception as e:
            result = {"file": filename, "error": str(e)}
            failed.append(result)
            events.emit("ableton_scan_failure", result)
            events.log("ableton_scanner", f"Skipping '{filename}' — couldn't parse it: {e}")

    _print_summary(folder_path, succeeded, failed)
    return {"succeeded": succeeded, "failed": failed}


def _print_summary(folder_path, succeeded, failed):
    print()
    print(f"[ableton_scanner] Scan complete: {folder_path}")
    print(f"[ableton_scanner]   {len(succeeded)} project(s) parsed successfully")
    if failed:
        print(f"[ableton_scanner]   {len(failed)} project(s) FAILED — not 100% clean:")
        for f in failed:
            print(f"[ableton_scanner]     - {f['file']}: {f['error']}")
    else:
        print("[ableton_scanner]   0 failures.")
    print()
