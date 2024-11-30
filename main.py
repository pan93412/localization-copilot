import asyncio
import argparse
import csv
import logging
import os
import random
from typing import cast
from rich.logging import RichHandler
from rich.status import Status

from extractors import GettextExtractor, BaseExtractor
from structure import Translation
from structure.translatable import Translatable
from translators import Gpt4oTranslator, BaseTranslator

FORMAT = "%(message)s"
logging.basicConfig(
    level="INFO", format=FORMAT, datefmt="[%X]", handlers=[RichHandler(rich_tracebacks=True)]
)

extractor_class_map: dict[str, BaseExtractor] = {
    "po": GettextExtractor(),
}

translator_class_map: dict[str, BaseTranslator] = {
    "gpt-4o": Gpt4oTranslator(),
}

async def main() -> None:
    logger = logging.getLogger("main")

    parser = argparse.ArgumentParser(description="Translate the given file in GPT model to CSV for proofreading in Chinese (Taiwan).")
    parser.add_argument("input_filename", type=str, help="The input file to translate")
    parser.add_argument("--output", type=str, help="The output file to write the translations to (by default, it is <input_filename>.csv)", default=None)
    parser.add_argument("--format", type=str, help=f"The file format. Currently supported: {list(extractor_class_map.keys())}.", default=None)
    parser.add_argument("--model", type=str, help=f"The model to translate the strings. Currently supported: {list(translator_class_map.keys())}.", default=None)
    parser.add_argument("--test-mode", action="store_true", help="Test mode (only picks 3 strings to translate)", default=False)
    args = parser.parse_args()

    if args.output is None:
        args.output = args.input_filename + ".csv"

    if args.format is None:
        _, ext = os.path.splitext(cast(str, args.input_filename))
        args.format = ext[1:]
        logger.info("No format specified. Using file extension to determine format (%s).", args.format)

    if args.model is None:
        args.model = "gpt-4o"
        logger.info("No model specified. Using default model (%s).", args.model)

    # check if the input file exists
    if not os.path.exists(args.input_filename):
        raise FileNotFoundError(f"Input file {args.input_filename!r} does not exist.")

    """
    Extractors:

    Extract the translatable strings from the input file.
    """
    extractor = extractor_class_map[args.format]
    logger.info(f"Using extractor {extractor!r}")

    translatables = extractor.extract(args.input_filename)

    if args.test_mode:
        logger.warning("Test mode is enabled. Only translating 3 strings.")
        translatables = random.choices(list(translatables), k=3)

    """
    Translators:

    Translate the translatable strings to the desired language with LLMs.
    """
    with Status("Translating…"):
        translator = translator_class_map[args.model]
        logger.info(f"Using translator {translator!r}")

        translated = await asyncio.gather(*(
            translate(translator, translatable)
            for translatable in translatables
        ))
        translated_without_none = list(filter(None, translated))

    """
    CSV Writers:

    Write the translations to a CSV file.
    """
    with Status("Writing to CSV…"):
        with open(args.output, "w") as f:
            writer = csv.DictWriter(f, fieldnames=["source", "translation", "context", "confidence", "fuzzy"])

            writer.writeheader()
            writer.writerows({
                "source": translation.source,
                "translation": translation.translation,
                "context": translation.context,
                "confidence": translation.confidence,
                "fuzzy": translation.fuzzy,
            } for translation in translated_without_none)


semaphore = asyncio.Semaphore(16)

async def translate(translator: BaseTranslator, translatable: Translatable) -> Translation | None:
    async with semaphore:
        logger = logging.getLogger("translate_and_write_to_csv")

        logger.info("Translating: %s", translatable)

        try:
            translation = await translator.translate(translatable)
            logger.info("Translated: %s", translation)
            return translation

        except Exception:
            logger.exception("Failed to translate: %s", translatable)
            return None

if __name__ == "__main__":
    asyncio.run(main())
