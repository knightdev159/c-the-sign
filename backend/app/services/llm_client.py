"""LLM client with Vertex AI primary and mock fallback."""

from __future__ import annotations


class LLMClient:
    def __init__(self, provider: str, model_name: str, project: str | None, location: str | None) -> None:
        self.provider = provider
        self.model_name = model_name
        self.project = project
        self.location = location

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        if self.provider == "vertex":
            try:
                return self._generate_vertex(system_prompt, user_prompt)
            except Exception:
                pass
        return self._generate_mock(system_prompt, user_prompt)

    def _generate_vertex(self, system_prompt: str, user_prompt: str) -> str:
        import vertexai
        from vertexai.generative_models import GenerativeModel

        if not self.project or not self.location:
            raise ValueError("project and location are required for Vertex generation")

        vertexai.init(project=self.project, location=self.location)
        model = GenerativeModel(self.model_name)
        response = model.generate_content(f"{system_prompt}\n\n{user_prompt}")
        if hasattr(response, "text") and response.text:
            return response.text
        return ""

    @staticmethod
    def _generate_mock(system_prompt: str, user_prompt: str) -> str:
        preview = user_prompt.strip().splitlines()[0][:220]
        return (
            "[MOCK_LLM] Grounded response generated in mock mode. "
            f"Input preview: {preview}"
        )
