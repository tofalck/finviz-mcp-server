import pytest
from unittest.mock import patch, Mock

from src.finviz_client.base import FinvizClient


def _response(text: str):
    r = Mock()
    r.text = text
    return r


def test_get_option_chain_json_default_expiry():
    client = FinvizClient(api_key="test-key")

    payload = """
    {
      "ticker": "AAPL",
      "currentExpiry": "2026-05-16",
      "expiries": ["2026-05-16", "2026-06-20"],
      "options": [
        {
          "type": "call",
          "strike": 150,
          "exDate": "2026-05-16",
          "bidPrice": 5.1,
          "askPrice": 5.3,
          "lastClose": 5.2,
          "lastVolume": 100,
          "openInterest": 1000,
          "iv": 0.25,
          "delta": 0.55,
          "gamma": 0.01,
          "theta": -0.03
        }
      ]
    }
    """

    with patch.object(client, "_make_request", return_value=_response(payload)) as mock_request:
        result = client.get_option_chain("aapl")

    assert result["ticker"] == "AAPL"
    assert result["expiries_fetched"] == ["2026-05-16"]
    assert "2026-06-20" in result["all_expiries"]
    assert len(result["options"]) == 1
    assert result["options"][0]["type"] == "call"
    assert result["options"][0]["strike"] == pytest.approx(150.0)

    call_args = mock_request.call_args.args
    assert call_args[1]["ty"] == "oc"
    assert call_args[1]["t"] == "AAPL"


def test_get_option_chain_range_fetches_additional_expiry():
    client = FinvizClient(api_key="test-key")

    default_payload = """
    {
      "ticker": "MSFT",
      "currentExpiry": "2026-05-16",
      "expiries": ["2026-05-16", "2026-06-20"],
      "options": [{"type": "call", "strike": 400, "exDate": "2026-05-16"}]
    }
    """

    second_payload = """
    {
      "ticker": "MSFT",
      "currentExpiry": "2026-06-20",
      "expiries": ["2026-05-16", "2026-06-20"],
      "options": [{"type": "put", "strike": 390, "exDate": "2026-06-20"}]
    }
    """

    with patch.object(
        client,
        "_make_request",
        side_effect=[_response(default_payload), _response(second_payload)],
    ) as mock_request:
        result = client.get_option_chain(
            "msft",
            expiry_start_date="2026-05-16",
            expiry_end_date="2026-06-20",
        )

    assert result["ticker"] == "MSFT"
    assert result["expiries_fetched"] == ["2026-05-16", "2026-06-20"]
    assert len(result["options"]) == 2

    first_call = mock_request.call_args_list[0].args[1]
    second_call = mock_request.call_args_list[1].args[1]
    assert first_call["ty"] == "oc"
    assert first_call["t"] == "MSFT"
    assert "e" not in first_call
    assert second_call["e"] == "2026-06-20"
