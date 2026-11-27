
from collections import Counter
from pathlib import Path

from bible_study_ai.ingestion.usfm_parser import parse_usfm


CORPUS = Path("~/Downloads/engwebu_usfm").expanduser()

BIBLE_BOOK_IDS = {
    # Old Testament
    "GEN", "EXO", "LEV", "NUM", "DEU",
    "JOS", "JDG", "RUT", "1SA", "2SA",
    "1KI", "2KI", "1CH", "2CH", "EZR",
    "NEH", "EST", "JOB", "PSA", "PRO",
    "ECC", "SNG", "ISA", "JER", "LAM",
    "EZK", "DAN", "HOS", "JOL", "AMO",
    "OBA", "JON", "MIC", "NAM", "HAB",
    "ZEP", "HAG", "ZEC", "MAL",

    # New Testament
    "MAT", "MRK", "LUK", "JHN", "ACT",
    "ROM", "1CO", "2CO", "GAL", "EPH",
    "PHP", "COL", "1TH", "2TH", "1TI",
    "2TI", "TIT", "PHM", "HEB", "JAS",
    "1PE", "2PE", "1JN", "2JN", "3JN",
    "JUD", "REV",
}

# These verse numbers are present in the WEB source but have no
# canonical reading text. Their footnotes explain manuscript variants.
EXPECTED_EMPTY_VERSES = {
    ("LUK", 17, "36"),
    ("ACT", 8, "37"),
    ("ACT", 15, "34"),
    ("ACT", 24, "7"),
    ("ROM", 16, "25"),
}


def collect_spans(nodes: list[dict], counts: Counter) -> None:
    """Count inline spans recursively, including nested spans."""
    for node in nodes:
        if node["type"] == "span":
            counts[node["name"]] += 1
            collect_spans(node["children"], counts)


def validate_book(path: Path) -> dict:
    """Parse and validate one canonical Bible book."""
    book = parse_usfm(path.read_text(encoding="utf-8"))

    book_id = book["usfm_id"]
    chapters = book["chapters"]

    verses = [
        verse
        for chapter in chapters
        for verse in chapter["verses"]
    ]

    empty_verses = []

    for chapter in chapters:
        for verse in chapter["verses"]:
            if not verse["text"].strip():
                empty_verses.append(
                    (book_id, chapter["number"], verse["number"])
                )

    structural_markers = Counter()
    inline_spans = Counter()

    for chapter in chapters:
        for element in chapter["elements"]:
            if element["type"] == "marker":
                structural_markers[element["name"]] += 1
            elif element["type"] == "verse":
                collect_spans(element["children"], inline_spans)

    return {
        "book_id": book_id,
        "filename": path.name,
        "chapters": len(chapters),
        "verses": len(verses),
        "empty_verses": empty_verses,
        "structural_markers": structural_markers,
        "inline_spans": inline_spans,
        "errors": [],
    }


def main() -> None:
    print("WORLD ENGLISH BIBLE — FULL CORPUS VALIDATION")
    print(f"Corpus directory: {CORPUS}")

    if not CORPUS.is_dir():
        print(f"\nERROR: Corpus directory does not exist: {CORPUS}")
        return

    files = sorted(CORPUS.glob("*.usfm"))

    if not files:
        print("\nERROR: No USFM files found.")
        return

    print(f"\nUSFM files discovered: {len(files)}")

    results = []
    failed_files = []
    skipped_files = []
    seen_book_ids = set()
    all_empty_verses = set()

    total_chapters = 0
    total_verses = 0

    all_structural_markers = Counter()
    all_inline_spans = Counter()

    for path in files:
        try:
            book = parse_usfm(path.read_text(encoding="utf-8"))
            book_id = book["usfm_id"]

            if book_id not in BIBLE_BOOK_IDS:
                skipped_files.append((path.name, book_id))
                continue

            result = validate_book(path)

            if book_id in seen_book_ids:
                result["errors"].append(
                    f"Duplicate canonical book ID: {book_id}"
                )
            else:
                seen_book_ids.add(book_id)

            if not result["chapters"]:
                result["errors"].append("No chapters parsed")

            results.append(result)

            total_chapters += result["chapters"]
            total_verses += result["verses"]

            all_empty_verses.update(result["empty_verses"])

            all_structural_markers.update(
                result["structural_markers"]
            )
            all_inline_spans.update(result["inline_spans"])

        except Exception as exc:
            failed_files.append((path.name, str(exc)))

    unexpected_empty = all_empty_verses - EXPECTED_EMPTY_VERSES
    missing_expected = EXPECTED_EMPTY_VERSES - all_empty_verses

    print("\n" + "=" * 65)
    print("CANONICAL BOOK VALIDATION")
    print("=" * 65)

    print(
        f"{'BOOK':<8} {'CHAPTERS':>10} "
        f"{'VERSES':>10} {'EMPTY':>8} {'STATUS':>10}"
    )
    print("-" * 65)

    for result in results:
        book_id = result["book_id"]

        book_unexpected_empty = [
            reference
            for reference in result["empty_verses"]
            if reference not in EXPECTED_EMPTY_VERSES
        ]

        if result["errors"] or book_unexpected_empty:
            status = "WARNING"
        else:
            status = "OK"

        print(
            f"{book_id:<8} "
            f"{result['chapters']:>10} "
            f"{result['verses']:>10} "
            f"{len(result['empty_verses']):>8} "
            f"{status:>10}"
        )

        for error in result["errors"]:
            print(f"    - {error}")

    missing_books = BIBLE_BOOK_IDS - seen_book_ids

    print("\n" + "=" * 65)
    print("EMPTY VERSE VALIDATION")
    print("=" * 65)

    print(f"Expected empty verses: {len(EXPECTED_EMPTY_VERSES)}")
    print(f"Found expected empty verses: "
          f"{len(all_empty_verses & EXPECTED_EMPTY_VERSES)}")
    print(f"Unexpected empty verses: {len(unexpected_empty)}")
    print(f"Expected empty verses not found: {len(missing_expected)}")

    if all_empty_verses:
        print("\nAll empty verse references:")
        for book_id, chapter, verse in sorted(all_empty_verses):
            classification = (
                "EXPECTED"
                if (book_id, chapter, verse) in EXPECTED_EMPTY_VERSES
                else "UNEXPECTED"
            )
            print(f"  {book_id} {chapter}:{verse} — {classification}")

    if missing_expected:
        print("\nExpected empty verses not found:")
        for book_id, chapter, verse in sorted(missing_expected):
            print(f"  {book_id} {chapter}:{verse}")

    if unexpected_empty:
        print("\nUnexpected empty verses:")
        for book_id, chapter, verse in sorted(unexpected_empty):
            print(f"  {book_id} {chapter}:{verse}")

    print("\n" + "=" * 65)
    print("CORPUS SUMMARY")
    print("=" * 65)

    print(f"USFM files discovered: {len(files)}")
    print(f"Canonical books parsed: {len(results)}")
    print(f"Unique canonical book IDs: {len(seen_book_ids)}")
    print(f"Non-canonical files skipped: {len(skipped_files)}")
    print(f"Files that failed parsing: {len(failed_files)}")
    print(f"Missing canonical books: {len(missing_books)}")
    print(f"Total chapters: {total_chapters}")
    print(f"Total verses: {total_verses}")

    if missing_books:
        print("\nMISSING BOOK IDS:")
        print(", ".join(sorted(missing_books)))

    if skipped_files:
        print("\nSKIPPED FILES:")
        for filename, book_id in skipped_files:
            print(f"  {filename} (ID: {book_id})")

    if failed_files:
        print("\nFAILED FILES:")
        for filename, error in failed_files:
            print(f"  {filename}: {error}")

    print("\nSTRUCTURAL MARKERS:")
    print(dict(all_structural_markers))

    print("\nINLINE SPANS:")
    print(dict(all_inline_spans))

    has_book_warnings = any(
        result["errors"] for result in results
    )

    passed = (
        not failed_files
        and not has_book_warnings
        and not unexpected_empty
        and not missing_expected
        and not missing_books
        and len(seen_book_ids) == 66
    )

    print("\n" + "=" * 65)

    if passed:
        print("ALL 66 CANONICAL BOOKS PASSED VALIDATION")
    else:
        print("VALIDATION COMPLETED WITH ISSUES")

    print("=" * 65)


if __name__ == "__main__":
    main()
