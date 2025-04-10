"preprocessor.py"

from abc import ABC
import re

# TODO:
# Define the preprocessor class
# static method for splitting Argdown documents into blocks
# handlers / chain of responsibility for processing blocks

class ArgdownCodeBlock(str):
    pass

class ArgumentMapBlock(ArgdownCodeBlock):
    pass

class ArgumentBlock(ArgdownCodeBlock):
    pass


def remove_html_comments(text: str) -> str:
    # Regular expression pattern to match HTML comments
    multiline_pattern = re.compile(r'<!--(.*?)-->', re.DOTALL)
    comment_pattern = re.compile(r'<!--(.*?)-->')

    # Collapse multiline comments
    text = re.sub(multiline_pattern, '<!-- c -->', text)
    
    clean_lines = []
    for line in text.split("\n"):
        if not line.strip():
            clean_lines.append(line)
            continue
        clean_line = re.sub(comment_pattern, '', line)
        if clean_line.strip():
            clean_lines.append(clean_line)
    
    return "\n".join(clean_lines)


def remove_js_comments(text: str) -> str:
    # Regular expression pattern to match JavaScript comments
    multiline_pattern = re.compile(r'/\*(.*?)\*/', re.DOTALL)
    comment_pattern = re.compile(r'/\*(.*?)\*/')

    # Collapse multiline comments
    text = re.sub(multiline_pattern, '/* c */', text)  
    
    clean_lines = []
    for line in text.split("\n"):
        if not line.strip():
            clean_lines.append(line)
            continue
        if line.strip().startswith("//"):
            continue        
        clean_line = re.sub(comment_pattern, '', line)
        if clean_line.strip():
            clean_lines.append(clean_line)
    
    return "\n".join(clean_lines)


def _maybe_remove_initial_comment(lines: list[str]) -> list[str]:
    if lines[0].strip().startswith("//"):
        return lines[1:]
    return lines    
    
def _next_non_comment_line(block: str) -> str:
    lines = block.split("\n")
    lines = [line for line in lines if line.strip()]
    while lines:
        lines = _maybe_remove_initial_comment(lines)
        if lines and lines[0].strip():
            return lines[0]
        lines = [line for line in lines if line.strip()]
    return None



def _maybe_pcs_line(line: str) -> bool:
    line = line.strip()
    regex = r"^\([A-Z]*\d+\)\s"
    match = re.match(regex, line)
    return match is not None

def _maybe_reason_line(line: str) -> bool:
    return _maybe_root_reason_line(line) or _maybe_dialectic_relation_line(line)

def _maybe_root_reason_line(line: str) -> bool:
    line = line.strip()
    seqs = ["[", "<"]
    maybe_root_reason_line = any(line.startswith(seq) for seq in seqs)
    return maybe_root_reason_line

def _maybe_dialectic_relation_line(line: str) -> bool:
    line = line.strip()
    seqs = ["+", "-", "+>", "->", "<+", "<-", "><", "_>", "<_"]
    maybe_dialectic_relation_line = any(line.startswith(seq) for seq in seqs)
    return maybe_dialectic_relation_line

def _maybe_inference_line(line: str) -> bool:
    line = line.strip()
    return line.startswith("--")


class AbstractPreprocessorHandler(ABC):
    def __call__(self, block: ArgdownCodeBlock) -> ArgdownCodeBlock:
        pass


class RemoveWhitespaceHandler(AbstractPreprocessorHandler):
    def __call__(self, block: ArgdownCodeBlock) -> ArgdownCodeBlock:
        if isinstance(block, ArgumentMapBlock):
            return block
        lines = [line.strip() for line in block.split("\n")]
        return ArgumentBlock("\n".join(lines))

class RemoveTrailingWhitespaceHandler(AbstractPreprocessorHandler):
    def __call__(self, block: ArgdownCodeBlock) -> ArgdownCodeBlock:
        if isinstance(block, ArgumentMapBlock):
            return block
        lines = [line.rstrip() for line in block.split("\n")]
        return ArgumentBlock("\n".join(lines))

# NOTE: needs to be applied twice: before and after collapsing lines
class RemoveCommentsHandler(AbstractPreprocessorHandler):
    def __call__(self, block: ArgdownCodeBlock) -> ArgdownCodeBlock:
        block_class = type(block)
        # match multiline comments
        regex_html_comment = r"<!--.*?-->"
        regex_js_comment = r"/\*.*?\*/"
        cleaned_lines = []
        for line in block.split("\n"):
            if line.strip().startswith("//"):
                continue
            cleaned_line = re.sub(regex_html_comment, "", line)
            cleaned_line = re.sub(regex_js_comment, "", cleaned_line)
            if line.strip() and not cleaned_line.strip():
                continue
            if "//" in cleaned_line:
                cleaned_line = cleaned_line.split("//")[0].rstrip()
            cleaned_lines.append(cleaned_line)
        return block_class("\n".join(cleaned_lines))

class CollapseLinesHandler(AbstractPreprocessorHandler):
    def __call__(self, block: ArgdownCodeBlock) -> ArgdownCodeBlock:
        block_class = type(block)
        collapsed_lines = []
        for line in block.split("\n"):
            empty_line = not line.strip()
            if not collapsed_lines or empty_line:
                collapsed_lines.append(line)
            elif (
                _maybe_pcs_line(line) or 
                _maybe_reason_line(line) or
                _maybe_inference_line(line) or 
                _maybe_inference_line(collapsed_lines[-1])
            ):
                collapsed_lines.append(line)
            else:
                collapsed_lines[-1] = collapsed_lines[-1].rstrip() + " " + line.lstrip()
        return block_class("\n".join(collapsed_lines))
            

class Preprocessor:

    @staticmethod
    def split_blocks(text: str) -> list[ArgumentBlock | ArgumentMapBlock]:
        """
        splits text into blocks at empty lines,
        unless empty lines are succeeded by a PCS line
        """
        codeblocks = []
        for block in text.split("\n\n"):
            if not block.strip():
                continue

            if not codeblocks:
                codeblocks.append(ArgumentMapBlock(block))
                continue

            next_content_line = _next_non_comment_line(block)
            if next_content_line and _maybe_pcs_line(next_content_line):
                codeblocks[-1] = ArgumentBlock(str(codeblocks[-1]) + "\n\n" + block)
                continue

            codeblocks.append(ArgumentMapBlock(block))

        codeblocks = [block for block in codeblocks if block.strip("\n ")]
        return codeblocks

    def __init__(self):
        self.handlers: AbstractPreprocessorHandler = []

    def add_handler(self, handler: AbstractPreprocessorHandler) -> "Preprocessor":
        self.handlers.append(handler)
        return self

    def process(self, block: ArgumentBlock | ArgumentMapBlock) -> ArgumentBlock | ArgumentMapBlock:
        for handler in self.handlers:
            block = handler(block)
        return block