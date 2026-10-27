import io
import json
import os
import unittest
import urllib.error
from unittest.mock import patch
from provider import complete, ModelError


class ProviderTests(unittest.TestCase):
    def test_missing_key(self):
        with patch.dict(os.environ, {}, clear=True), self.assertRaises(ModelError):
            complete([])

    @patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-only-placeholder"})
    def test_request_and_response(self):
        data = {"choices": [{"message": {"content": "Тема: Дякую\nДякую за матеріали."}, "finish_reason": "stop"}]}
        with patch("urllib.request.urlopen", return_value=io.BytesIO(json.dumps(data).encode())) as send:
            self.assertIn("Дякую", complete([{"role": "user", "content": "Матеріали отримано"}]))
            request = send.call_args.args[0]
            self.assertEqual(json.loads(request.data)["model"], "openrouter/free")
            self.assertNotIn("test-only-placeholder", request.data.decode())
            self.assertEqual(send.call_args.kwargs["timeout"], 60)

    @patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-only-placeholder"})
    def test_error_never_exposes_provider_body(self):
        error = urllib.error.HTTPError("https://example.test", 429, "private-details", {}, None)
        with patch("urllib.request.urlopen", side_effect=error):
            with self.assertRaises(ModelError) as caught:
                complete([])
            self.assertNotIn("private-details", str(caught.exception))
            self.assertIn("ліміту", str(caught.exception))

    @patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-only-placeholder"})
    def test_malformed_response(self):
        with patch("urllib.request.urlopen", return_value=io.BytesIO(b'{}')):
            with self.assertRaises(ModelError):
                complete([])

    @patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-only-placeholder"})
    def test_non_letter_is_rejected(self):
        data = {"choices": [{"message": {"content": "User Safety: safe"}, "finish_reason": "stop"}]}
        with patch("urllib.request.urlopen", return_value=io.BytesIO(json.dumps(data).encode())):
            with self.assertRaises(ModelError):
                complete([])


if __name__ == "__main__":
    unittest.main()
