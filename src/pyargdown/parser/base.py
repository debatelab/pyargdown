"base.py"


from abc import ABC, abstractmethod
import enum
import yaml  # type: ignore

from lark import Tree

from pyargdown.model import Argdown, Argument, Proposition

_UNNAMED_ARGUMENT = "UNNAMED_ARGUMENT"
_UNNAMED_PROPOSITION = "UNNAMED_PROPOSITION"

class ReasonRelation(enum.Enum):
    LEFT_PRO = "LEFT_PRO"
    LEFT_CON = "LEFT_CON"
    RIGHT_PRO = "RIGHT_PRO"
    RIGHT_CON = "RIGHT_CON"
    CONTRADICT = "CONTRADICT"
    LEFT_UNDERCUT = "LEFT_UNDERCUT"
    RIGHT_UNDERCUT = "RIGHT_UNDERCUT"

class ArgdownSyntaxError(SyntaxError):
    def __str__(self):
        context, line, column = self.args
        return '%s at line %s, column %s.\n\n%s' % (self.label, line, column, context)


class ArgdownParser(ABC):

    @staticmethod
    def is_unlabeled(obj: Argument | Proposition) -> bool:
        """
        Check if the object is unlabeled.
        Propositions introduced in in pcs are considered to be labeled.
        """
        label = obj.label
        if not label or label.startswith(_UNNAMED_ARGUMENT) or label.startswith(_UNNAMED_PROPOSITION):
            return True
        return False

    @staticmethod
    def extract_yaml(text: str) -> tuple[str, dict]:
        data = {}
        if text.rstrip().endswith('}'):
            idx = 0
            while True:
                try:
                    idx = text.index('{', idx)
                except ValueError:
                    break
                try:
                    data = yaml.safe_load(text[idx:])
                    text = text[:idx].rstrip()
                    break
                except yaml.YAMLError:
                    idx += 1
        return text, data

    @abstractmethod
    def parse(self, text: str) -> Tree:
        pass

    @staticmethod
    @abstractmethod
    def ingest_in_argmap(tree: Tree, argdown: Argdown):
        pass

    def __call__(self, text: str) -> Tree:
        return self.parse(text)

