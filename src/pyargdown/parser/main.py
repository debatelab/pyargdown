"Main entrypoint for parsing Argdown text documents"

import logging

from pyargdown.model import Argdown, ArgdownMultiDiGraph
from pyargdown.parser.preprocessor import (
    Preprocessor,
    ArgdownCodeBlock,
    ArgumentBlock,
    ArgumentMapBlock,
    RemoveCommentsHandler,
    RemoveWhitespaceHandler,
    RemoveTrailingWhitespaceHandler,
    CollapseLinesHandler,
)
from pyargdown.parser import ArgumentMapParser, ArgumentParser

logger = logging.getLogger(__name__)

def parse_argdown(texts: str | list[str]) -> Argdown:
    """
    Parse an Argdown text document as an argument map.

    Args:
        text (str | list[str]): The Argdown code snippet(s) to parse.

    Returns:
        Argdown: The parsed argument map.
    """

    if isinstance(texts, str):
        texts = [texts]

    argdown = ArgdownMultiDiGraph()
    preprocessor = Preprocessor()
    preprocessor.add_handler(
        RemoveCommentsHandler()
    ).add_handler(
        RemoveWhitespaceHandler()
    ).add_handler(
        CollapseLinesHandler()
    ).add_handler(
        RemoveCommentsHandler()
    ).add_handler(
        RemoveTrailingWhitespaceHandler()
    )

    # splitting
    codeblocks: list[ArgumentMapBlock | ArgumentBlock] = []
    for text in texts:
        codeblocks.extend(Preprocessor.split_blocks(text))


    # preprocess and parse each codeblock
    argument_parser = ArgumentParser()
    argument_map_parser = ArgumentMapParser()
    for codeblock in codeblocks:
        logger.debug(f"Found codeblock of type {type(codeblock)} starting with {str(codeblock)[:20]}...")
        codeblock = preprocessor.process(codeblock)
        if not codeblock.strip("\n "):
            continue
        # parsing
        parser: ArgumentMapParser | ArgumentParser
        if isinstance(codeblock, ArgumentMapBlock):
            parser = argument_map_parser
        elif isinstance(codeblock, ArgumentBlock):
            parser = argument_parser
        else:
            raise ValueError(
                f"Internal error: invalid code block type {type(codeblock)}"
            )
        tree = parser(codeblock)
        # ingestion
        argdown = parser.ingest_in_argmap(tree, argdown)  # type: ignore


    return argdown
