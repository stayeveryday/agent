import json

from intent_contract import build_intent_contract


CASES = [
    {
        "name": "valid_with_think",
        "raw": '<think>\n\n</think>\n\n{"intent":"ticket_query","ticket_id":"INC-1001","asset_tag":null,"priority":null,"category":"ticket"}',
        "expected_valid": True,
        "expected_route": "ticket_query",
    },
    {
        "name": "invalid_json",
        "raw": "intent=ticket_query ticket_id=INC-1001",
        "expected_valid": False,
        "expected_route": "fallback",
    },
    {
        "name": "extra_key",
        "raw": '{"intent":"ticket_query","ticket_id":"INC-1001","asset_tag":null,"priority":null,"category":"ticket","extra":"x"}',
        "expected_valid": False,
        "expected_route": "ticket_query",
    },
    {
        "name": "ticket_create_with_fake_ticket_id",
        "raw": '{"intent":"ticket_create","ticket_id":"INC-9999","asset_tag":null,"priority":"medium","category":"network"}',
        "expected_valid": False,
        "expected_route": "ticket_create",
    },
]


def main() -> None:
    results = []
    for case in CASES:
        contract = build_intent_contract(case["raw"])
        passed = (
            contract["is_valid"] == case["expected_valid"]
            and contract["route"] == case["expected_route"]
        )
        results.append(
            {
                "name": case["name"],
                "passed": passed,
                "contract": contract,
            }
        )

    print(json.dumps(results, ensure_ascii=False, indent=2))
    failed = [item for item in results if not item["passed"]]
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
