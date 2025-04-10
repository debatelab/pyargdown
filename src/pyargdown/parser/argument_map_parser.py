"parser.py"

import copy
import logging
from textwrap import dedent

import lark
from lark import Lark, Transformer, UnexpectedInput
from lark.indenter import Indenter 

from pyargdown.model import (
    Argdown,
    ArgdownEdge,
    Argument,
    DialecticalType,
    Proposition,
    Valence,
)
from pyargdown.parser.base import ArgdownParser, ArgdownSyntaxError, ReasonRelation, _UNNAMED_PROPOSITION

logger = logging.getLogger(__name__)

ARGDOWN_MAP_GRAMMAR = r"""
    start: _NL* root (_NL* root)*

    root: reason _NL [_INDENT child+ _DEDENT]
    child: _relation reason _NL [_INDENT child+ _DEDENT]
    reason: _label ":" TEXT | _label | TEXT
    _label: PROPOSITION_LABEL | ARGUMENT_LABEL
    _relation: LEFT_PRO | LEFT_CON | RIGHT_PRO | RIGHT_CON | CONTRADICT | LEFT_UNDERCUT | RIGHT_UNDERCUT

    PROPOSITION_LABEL: "[" /[^\]]+/ "]"
    ARGUMENT_LABEL: "<" /[^\>]+/ ">"
    TEXT: /([^\n]+)/
    LEFT_PRO: "+ " | "<+ "
    RIGHT_PRO: "+> "
    LEFT_CON: "- " | "<- "
    RIGHT_CON: "-> "
    LEFT_UNDERCUT: "<_ "
    RIGHT_UNDERCUT: "_> "
    CONTRADICT: ">< "

    %import common.CNAME -> NAME
    %import common.ESCAPED_STRING   -> STRING
    %import common.WS_INLINE
    %declare _INDENT _DEDENT
    %ignore WS_INLINE

    _NL: /(\r?\n[\t ]*)+/
"""



class ArgdownMapUnknownRelation(ArgdownSyntaxError):
    label = "Unrecognized dialectical relation type"

class ArgdownArgumentMapMissingArgumentLabelColon(ArgdownSyntaxError):
    label = "Missing colon after argument label"

class ArgdownArgumentMapMissingPropositionLabelColon(ArgdownSyntaxError):
    label = "Missing colon after proposition label"



_ERROR_EXAMPLES = {
    ArgdownMapUnknownRelation: [
        dedent("""
        [root]: root text
            <+ reason
            < [child]: child text
        """).strip(),
        dedent("""
        [root]: root text
            <+ reason
                < [child]: child text
        """).strip(),
        dedent("""
        [root]: root text
            <+ reason
                <+ reason
            < [child]: child text
        """).strip(),
        dedent("""
        [root]: root text
            <+ reason
                <+ reason
                < [child]: child text
        """).strip(),
        dedent("""
        [root]: root text
            > [child]: child text
        """).strip(),
        dedent("""
        [root]: root text
            <~ [child]: child text
        """).strip(),
        dedent("""
        [root]: root text
            ~> [child]: child text
        """).strip(),
        dedent("""
        [root]: root text
            <– [child]: child text
        """).strip(),
        dedent("""
        [root]: root text
            –> [child]: child text
        """).strip(),
        dedent("""
        [root]: root text
            <? [child]: child text
        """).strip(),
        dedent("""
        [root]: root text
            ?> [child]: child text
        """).strip(),
        dedent("""
        [root]: root text
            ~ [child]: child text
        """).strip(),
        dedent("""
        [root]: root text
            = [child]: child text
        """).strip(),
    ],
    ArgdownArgumentMapMissingArgumentLabelColon: [
        dedent("""
        <Argument> argument
        """).strip(),
        dedent("""
        [Claim]: claim
            + <L> text
        """).strip(),
        dedent("""
        [Claim]: claim
            + reason
            + <L> text
        """).strip(),
        dedent("""
        [Claim]: claim
            + reason
                + <L> text
        """).strip(),
        dedent("""
        [Claim]: claim
            + reason
               + reason
            + <L> text
        """).strip(),
    ],
    ArgdownArgumentMapMissingPropositionLabelColon: [
        dedent("""
        [Argument] argument
        """).strip(),
        dedent("""
        [Claim]: claim
            + [L] text
        """).strip(),
        dedent("""
        [Claim]: claim
            + reason
            + [L] text
        """).strip(),
        dedent("""
        [Claim]: claim
            + reason
                + [L] text
        """).strip(),
        dedent("""
        [Claim]: claim
            + reason
               + reason
            + [L] text
        """).strip(),
    ],}


class ArgdownMapIndenter(Indenter):
    NL_type = "_NL"
    OPEN_PAREN_types = []
    CLOSE_PAREN_types = []
    INDENT_type = "_INDENT"
    DEDENT_type = "_DEDENT"
    tab_len = 4


class ArgumentMapTreeTransformer(Transformer):

    def __init__(self, argdown: Argdown, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.argdown = argdown

    @lark.v_args(inline=True)
    def reason(self, *args):
        kwargs = {t.type: t.value for t in args}
        text = kwargs.get("TEXT")
        text, yaml = ArgdownParser.extract_yaml(text) if text else ("", {})
        text = text.strip()

        is_proposition = "ARGUMENT_LABEL" not in kwargs

        if is_proposition:
            label = kwargs.get("PROPOSITION_LABEL")
            label = label[1:-1] if label else None
            if label is None:
                label = self.argdown.make_label_unique(_UNNAMED_PROPOSITION)
            proposition = Proposition(label=label, texts=[text] if text else [], data=yaml)
            self.argdown.add_proposition(
                proposition,
                allow_exists=True,
            )
        else:
            label = kwargs["ARGUMENT_LABEL"][1:-1]
            argument = Argument(label=label, gists=[text] if text else [], data=yaml)
            self.argdown.add_argument(
                argument,
                allow_exists=True,
            )
        return label

    def process_children(self, root_label: str, children: list[tuple[ReasonRelation, str]]):
        for child_rel, child_label in children:
            if child_rel in [
                ReasonRelation.LEFT_PRO,
                ReasonRelation.LEFT_CON,
                ReasonRelation.LEFT_UNDERCUT,
                ReasonRelation.CONTRADICT,
            ]:
                source = child_label
                target = root_label
            else:
                source = root_label
                target = child_label

            if child_rel in [
                ReasonRelation.LEFT_PRO,
                ReasonRelation.RIGHT_PRO
            ]:
                valence = Valence.SUPPORT
            elif child_rel in [
                ReasonRelation.LEFT_CON,
                ReasonRelation.RIGHT_CON
            ]:
                valence = Valence.ATTACK
            elif child_rel in [
                ReasonRelation.LEFT_UNDERCUT,
                ReasonRelation.RIGHT_UNDERCUT,
            ]:
                valence = Valence.UNDERCUT
            elif child_rel == ReasonRelation.CONTRADICT:
                valence = Valence.CONTRADICT
            else:
                raise ValueError(
                    f"Internal error: Unknown reason relation {child_rel}. Please report this issue."
                )
            dialectic = DialecticalType.SKETCHED
            if self.argdown.get_proposition(root_label) and self.argdown.get_proposition(child_label):
                dialectic = DialecticalType.AXIOMATIC
            self.argdown.add_dialectical_relation(
                ArgdownEdge(
                    source=source,
                    target=target,
                    valence=valence,
                    dialectics=[dialectic],
                )
            )

    @lark.v_args(inline=True)
    def child(self, relation, reason_label, *children):
        reason_relation = ReasonRelation(relation.type)
        self.process_children(reason_label, children)
        return reason_relation, reason_label

    @lark.v_args(inline=True)
    def root(self, reason_label, *children):
        self.process_children(reason_label, children)
        return reason_label



class ArgumentMapParser(ArgdownParser):
    def __init__(self):
        self.parser = Lark(
            ARGDOWN_MAP_GRAMMAR,
            parser="lalr",
            postlex=ArgdownMapIndenter(),
            maybe_placeholders=False,
        )

    def parse(self, text: str) -> lark.Tree:
        try:
            text = text + "\n"  # Ensure the last line is terminated
            tree = self.parser.parse(text)
        except UnexpectedInput as u:
            exc_class = u.match_examples(
                self.parser.parse, _ERROR_EXAMPLES, use_accepts=True
            )
            if not exc_class:
                raise
            raise exc_class(u.get_context(text), u.line, u.column)
        return tree

    @staticmethod
    def ingest_in_argmap(tree: lark.Tree, argdown: Argdown) -> Argdown:
        working_argdown = copy.deepcopy(argdown)
        try:
            ArgumentMapTreeTransformer(
                argdown=working_argdown, visit_tokens=True
            ).transform(tree)
        except Exception as e:
            logger.error(f"Error when ingesting argdown argument: {e}. Returning original argdown document.")
            return argdown
        working_argdown._update()
        return working_argdown
