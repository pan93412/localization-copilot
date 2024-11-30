from logging import Logger
from typing import Generator
from .extractor import BaseExtractor
from structure import Translatable, Translation

import polib


class GettextExtractor(BaseExtractor):
    log = Logger("GettextExtractor")

    def extract(self, input_filename: str) -> Generator[Translatable, None, None]:
        po = polib.pofile(input_filename)

        for entry in po:
            if entry.obsolete:
                continue

            if entry.fuzzy or not entry.msgstr:
                self.log.info("Found untranslated / fuzzy string: %s", entry.msgid)

                if entry.previous_msgid:
                    # write references
                    reference = Translation(
                        source=entry.previous_msgid,
                        context=entry.previous_msgctxt,
                        translation=entry.msgstr,
                        fuzzy=False  # old translation; considering it as non-fuzzy
                    )
                elif entry.fuzzy and entry.msgstr != "":
                    # write references
                    reference = Translation(
                        source=entry.msgid,
                        context=entry.msgctxt,
                        translation=entry.msgstr,
                        fuzzy=True
                    )
                else:
                    reference = None

                if reference is not None:
                    yield Translatable(entry.msgid, entry.msgctxt, references=[reference])
                else:
                    yield Translatable(entry.msgid, entry.msgctxt)
