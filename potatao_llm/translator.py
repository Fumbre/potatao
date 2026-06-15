'''
Ollama + strategy pattern
'''
from abc import ABC, abstractmethod

class BaseTranslator(ABC):
    @abstractmethod
    def translate(self, text: str, target_language: str) -> str:
        """
        Receives transcribed text and target language name (e.g. "French").
        Returns the translated text.
        """
        pass


class OllamaTranslator(BaseTranslator):
    def __init__(self, model: str = "mistral", host: str = "http://localhost:11434"):
        """
        model         Ollama model to use for translation.
                      Good lightweight options: mistral, llama3, phi3
        host          Ollama server address (default: localhost)

        To install Ollama and pull a model:
            curl -fsSL https://ollama.com/install.sh | sh
            ollama pull mistral
        """
        import ollama
        self.model  = model
        self.client = ollama.Client(host=host)
        print(f"[Translator] Using Ollama model: {model}")

    def translate(self, text: str, target_language: str) -> str:
        """
        Sends a translation prompt to the local LLM via Ollama.
        Uses a strict prompt to prevent the model from adding explanations.
        """
        prompt = (
            f"Translate the following text to {target_language}. "
            f"Reply with ONLY the translated text, no explanations, no notes:\n\n"
            f"{text}"
        )

        # TODO: What role is for?
        response = self.client.chat(
            model=self.model,
            messages=[{"role": "user", "content": prompt}]
        )

        translated = response["message"]["content"].strip()
        print(f"[Translator] Translated to {target_language}: {translated}")
        return translated


class OpenAITranslator(BaseTranslator):
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        """
        api_key         Your OpenAI API key (store in .env, never hardcode)
        model           GPT model to use: gpt-4o-mini is cheap and accurate
        """
        import openai
        self.client = openai.OpenAI(api_key=api_key)
        self.model  = model
        print(f"[Translator] Using OpenAI model: {model}")

    def translate(self, text: str, target_language: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            # TODO: okay I think I udernstad why we need role
            messages=[
                {
                    "role": "system",
                    "content": "You are a translator. Reply with ONLY the translated text, no explanations."
                },
                {
                    "role": "user",
                    "content": f"Translate to {target_language}:\n\n{text}"
                }
            ]
        )

        translated = response.choices[0].message.content.strip()
        print(f"[Translator] Translated to {target_language}: {translated}")
        return translated
    
