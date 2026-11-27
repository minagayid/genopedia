"""Adapter contract tests; the upstream HTTP service is mocked, not live inference."""
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import HTTPException
from genopedia.api import ai


class AIAdapterTests(unittest.TestCase):
    def setUp(self):
        self.user = SimpleNamespace(id=1)
        self.db = SimpleNamespace(get=lambda _model, _id: None)
        self.settings = patch.multiple(
            ai, AI_MODEL_BASE_URL="https://router.example/v1", AI_MODEL_NAME="tested-model",
            AI_MODEL_API_KEY="test-key", AI_MODEL_STATE="available"
        )
        self.settings.start()
        self.addCleanup(self.settings.stop)

    def test_training_state_remains_off(self):
        with patch.object(ai, "AI_MODEL_STATE", "training"), patch.object(ai.httpx, "post") as post:
            with self.assertRaises(HTTPException) as error:
                ai.ai_query(ai.AIQuery(question="hello", consent_to_model_processing=True), self.db, self.user)
            self.assertEqual(error.exception.status_code, 503)
            post.assert_not_called()

    def test_consent_required_before_request(self):
        with patch.object(ai.httpx, "post") as post:
            with self.assertRaises(HTTPException) as error:
                ai.ai_query(ai.AIQuery(question="hello"), self.db, self.user)
            self.assertEqual(error.exception.status_code, 400)
            post.assert_not_called()

    def test_sends_consented_question_to_openai_compatible_endpoint(self):
        fake = SimpleNamespace(raise_for_status=lambda: None, json=lambda: {"choices": [{"message": {"content": "Mock answer"}}]})
        with patch.object(ai.httpx, "post", return_value=fake) as post:
            result = ai.ai_query(ai.AIQuery(question="hello", consent_to_model_processing=True), self.db, self.user)
            self.assertEqual(result["answer"], "Mock answer")
            args, kwargs = post.call_args
            self.assertEqual(args[0], "https://router.example/v1/chat/completions")
            self.assertEqual(kwargs["headers"]["Authorization"], "Bearer test-key")
            self.assertEqual(kwargs["json"]["model"], "tested-model")
            self.assertEqual(kwargs["json"]["messages"][1]["content"], "hello")

    def test_other_users_analysis_is_not_forwarded(self):
        db = SimpleNamespace(get=lambda _model, _id: SimpleNamespace(user_id=2))
        with patch.object(ai.httpx, "post") as post:
            with self.assertRaises(HTTPException) as error:
                ai.ai_query(ai.AIQuery(question="hello", analysis_id=1, consent_to_model_processing=True), db, self.user)
            self.assertEqual(error.exception.status_code, 404)
            post.assert_not_called()


if __name__ == "__main__":
    unittest.main()
