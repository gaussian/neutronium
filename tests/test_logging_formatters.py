import json
import logging

import pytest

from neutronium.logging.formatters import JsonFormatter


@pytest.mark.parametrize(
    ("extra", "expected"),
    [
        ({"task.id": "abc-123"}, {"task.id": "abc-123"}),
        ({"task.name": "sapeum.ingest"}, {"task.name": "sapeum.ingest"}),
        ({"task.state": "succeeded"}, {"task.state": "succeeded"}),
        ({"task.next": "final"}, {"task.next": "final"}),
        ({"object.id": 42}, {"object.id": 42}),
        ({"not_allowlisted": "secret"}, {"not_allowlisted": None}),
    ],
)
def test_json_formatter_context_fields(extra, expected):
    record = logging.makeLogRecord({"msg": "task run", **extra})
    payload = json.loads(JsonFormatter().format(record))
    for key, value in expected.items():
        assert payload.get(key) == value
