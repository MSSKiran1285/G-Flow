from smt.data.f4_miner import MasterDataEntry, rows_to_entries


def test_rows_to_entries_skips_header_and_joins_description():
    # Shape mirrors the real "Sales Organization" F4 popup mined live: header row 1
    # ("SOrg." / "Name"), data starting at row 3.
    rows = {
        1: {1: "SOrg.", 7: "Name"},
        3: {1: "0001", 7: "Test Org"},
        4: {1: "G999", 7: "genpact Sales Org"},
    }

    entries = rows_to_entries(rows)

    assert entries == [
        MasterDataEntry(key="0001", description="Test Org"),
        MasterDataEntry(key="G999", description="genpact Sales Org"),
    ]


def test_rows_to_entries_skips_rows_missing_the_key_column():
    rows = {
        1: {1: "Key", 5: "Desc"},
        2: {5: "no key here"},
        3: {1: "OK", 5: "fine"},
    }

    entries = rows_to_entries(rows)

    assert entries == [MasterDataEntry(key="OK", description="fine")]


def test_rows_to_entries_honors_explicit_key_column():
    # Mirrors the vendor hit-list layout: the leftmost column (1) is NOT the key.
    rows = {
        1: {1: "SearchTerm", 53: "Name", 79: "Vendor"},
        3: {1: "", 53: "ARJUN PVT LTD", 79: "91"},
    }

    entries = rows_to_entries(rows, key_column=79)

    assert entries == [MasterDataEntry(key="91", description="ARJUN PVT LTD")]


def test_rows_to_entries_respects_max_entries():
    rows = {1: {1: "Key"}, **{i: {1: str(i)} for i in range(2, 10)}}

    entries = rows_to_entries(rows, max_entries=3)

    assert len(entries) == 3
