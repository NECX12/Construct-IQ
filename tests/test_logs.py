from app.logs import aggregate_actuals, parse_site_log


def test_parse_site_log():
    entries = parse_site_log("""Date: 02/09/2026
Activity: Blockwork
Workers: 12
Materials Used:
Cement - 8 bags
Blocks - 650 pcs
Sand - 3 m3
""")
    assert len(entries) == 3
    assert aggregate_actuals(entries)["blocks"] == 650
    assert entries[0].activity == "Blockwork"
