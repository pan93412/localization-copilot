import json
from logging import Logger
from typing import TypedDict, cast

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam
from structure import Translatable, Translation
from .translator import BaseTranslator


class Gpt4oTranslator(BaseTranslator):
    prompt = """
You are a professional software translator. Translate the following text to Chinese (Traditional, Taiwan). Use the word which Taiwanese usually says, for example, no "視頻". No explanation of your translation. You can reorder the arguments, but location tag (%s → %1$s) must be mapped (for example, `components %s of service %s is rejected` should be `服務 %2$s 的元件 %1$s 被拒絕`). Use Chinese quote (「」) for English quotes ("``", "''", '""', '“”'). Preserve the format (quotes, prefix, suffix, etc.) and space in translation.

I will give you a XML, like:

```
<source context="{context}">{source}</source>
<references>
    <translation source="{old-source}" context="{old-context}" fuzzy>{old-trans}</translation>
</references>
```

Reference "reference" and "context", translate source and return a JSON according to the schema.
```
    """.strip()

    logger = Logger("Gpt4oTranslator")

    def __init__(self, model: str = "gpt-4o") -> None:
        self.openai = AsyncOpenAI()
        self.model = model

    async def translate(self, translatable: Translatable) -> Translation:
        input = _construct_input(translatable)
        messages: list[ChatCompletionMessageParam] = [
            {
                "role": "system",
                "content": self.prompt
            },
            {
                "role": "user",
                "content": input
            }
        ]

        try:
            completion = await self.openai.chat.completions.create(
                messages=messages,
                model=self.model,
                temperature=0.2,
                n=1,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "translation",
                        "description": "The object with the translated text.",
                        "schema": {
                            "type": "object",
                            "properties": {
                                "translation": {
                                    "type": "string"
                                },
                                "confidence": {
                                    "type": "number"
                                },
                            },
                            "required": ["translation", "confidence"],
                            "additionalProperties": False
                        },
                        "strict": True,
                    }
                }
            )

            content = completion.choices[0].message.content if completion.choices else None

            if not content:
                raise Exception("No completion content found.")

            tt = cast(TranslatedText, json.loads(content))
            self.logger.debug("Got response %s; confidence = %f", tt["translation"], tt["confidence"])

            return Translation(source=translatable.source, context=translatable.context, translation=tt["translation"], fuzzy=tt["confidence"] < 0.5, confidence=tt["confidence"])
        except Exception as e:
            self.logger.error("GPT-4o failed to translate %s: %s", translatable.source, e)
            raise e

class TranslatedText(TypedDict):
    translation: str
    confidence: float


def _construct_input(translatable: Translatable) -> str:
    input = "<source "
    if translatable.context:
        input += f"context=\"{translatable.context}\" "
    input = input.strip() + f">{translatable.source}</source>\n"

    if len(translatable.references) > 0:
        input += "<references>\n"
        for reference in translatable.references:
            reference_input = f'<translation source="{reference.source}" '
            if reference.context:
                reference_input += f'context="{reference.context}" '
            if reference.fuzzy:
                reference_input += "fuzzy "
            reference_input = reference_input.strip() + ">"

            reference_input += f"{reference.translation}</translation>"
            input += "\t" + reference_input + "\n"
        input += "</references>\n"

    return input
