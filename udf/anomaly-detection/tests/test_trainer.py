import json
import os
import unittest
from datetime import datetime
from unittest.mock import patch, Mock

from pynumaflow.sink import Datum

from src._constants import TESTS_DIR
from src.connectors.druid import DruidFetcher
from src.connectors.prometheus import Prometheus
from tests.tools import (
    mock_prom_query_metric,
    mock_druid_fetch_data,
)
from tests import redis_client, Train

DATA_DIR = os.path.join(TESTS_DIR, "resources", "data")
STREAM_DATA_PATH = os.path.join(DATA_DIR, "stream.json")


def as_datum(data: str | bytes | dict, msg_id="1") -> Datum:
    if type(data) is not bytes:
        data = json.dumps(data).encode("utf-8")
    elif type(data) == dict:
        data = json.dumps(data)

    return Datum(
        sink_msg_id=msg_id, value=data, event_time=datetime.now(), watermark=datetime.now(), keys=[]
    )


class TestTrainer(unittest.TestCase):
    train_payload = {
        "uuid": "1",
        "composite_keys": [
            "sandbox_numalogic_demo",
            "metric_1",
            "123456789",
        ],
        "metric": "metric_1",
    }

    train_payload2 = {
        "uuid": "2",
        "composite_keys": ["fciAsset", "5984175597303660107"],
        "metric": "failed",
    }

    def setUp(self) -> None:
        redis_client.flushall()

    @patch.object(Prometheus, "query_metric", Mock(return_value=mock_prom_query_metric()))
    def test_prometheus_01(self):
        _out = Train().run(datums=iter([as_datum(self.train_payload)]))
        self.assertTrue(_out[0].success)
        self.assertEqual("1", _out[0].id)

    @patch.object(DruidFetcher, "fetch_data", Mock(return_value=mock_druid_fetch_data()))
    def test_druid_01(self):
        _out = Train().run(datums=iter([as_datum(self.train_payload2)]))
        self.assertTrue(_out[0].success)
        self.assertEqual("2", _out[0].id)


if __name__ == "__main__":
    unittest.main()
