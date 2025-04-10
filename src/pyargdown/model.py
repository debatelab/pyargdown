"pyargdown data model"

from abc import ABC, abstractmethod
from copy import deepcopy
from dataclasses import dataclass, field, asdict
import enum
import logging
from typing import Sequence

import networkx as nx  # type: ignore

logger = logging.getLogger(__name__)


class Valence(enum.Enum):
    SUPPORT = enum.auto()
    ATTACK = enum.auto()
    CONTRADICT = enum.auto()
    UNDERCUT = enum.auto()


class DialecticalType(enum.Enum):
    SKETCHED = enum.auto()  # explicitly
    # stated in argdown source document
    GROUNDED = enum.auto()  # can be inferred
    # from logical relations between propositions
    AXIOMATIC = enum.auto()  # logico-semantic
    # relation between two propositions explicitly
    # defined in argdown source document


@dataclass
class Proposition:
    label: str | None = None
    texts: list[str] = field(default_factory=list)
    data: dict = field(default_factory=dict)
    type: str = "Proposition"


@dataclass
class PropositionReference:
    proposition_label: str
    label: str


@dataclass
class Conclusion(PropositionReference):
    inference_info: str | None = None
    inference_data: dict = field(default_factory=dict)


@dataclass
class Argument:
    label: str | None = None
    gists: list[str] = field(default_factory=list)
    data: dict = field(default_factory=dict)
    pcs: list[PropositionReference] = field(default_factory=list)
    type: str = "Argument"

    @staticmethod
    def from_dict(data: dict) -> "Argument":
        data = deepcopy(data)
        if "pcs" in data:
            pcs = []
            for pr in data["pcs"]:
                if isinstance(pr, PropositionReference) or isinstance(pr, Conclusion):
                    pcs.append(pr)
                    continue
                try:
                    pcs.append(PropositionReference(**pr))
                    continue
                except TypeError:
                    pass
                try:
                    pcs.append(Conclusion(**pr))
                except TypeError:
                    raise ValueError(
                        f"Cannot convert proposition reference {pr} to PropositionReference."
                    )
            data["pcs"] = pcs
        return Argument(**data)
    


@dataclass
class ArgdownEdge:
    source: str
    target: str
    valence: Valence
    dialectics: list[DialecticalType] = field(default_factory=list)
    data: dict = field(default_factory=dict)

    @staticmethod
    def from_dict(data: dict) -> "ArgdownEdge":
        data = deepcopy(data)
        if "valence" in data:
            if not isinstance(data["valence"], Valence):
                try:
                    data["valence"] = Valence[data["valence"]]
                except KeyError:
                    raise ValueError(
                        f"Cannot convert valence {data['valence']} to Valence."
                    )
        if "dialectics" in data:
            dialectics = []
            for ds in data["dialectics"]:
                if isinstance(ds, DialecticalType):
                    dialectics.append(ds)
                    continue
                try:
                    dialectics.append(DialecticalType[ds])
                except KeyError:
                    raise ValueError(
                        f"Cannot convert dialectical type {ds} to DialecticalType."
                    )
            data["dialectics"] = dialectics
        return ArgdownEdge(**data)


class Argdown(ABC):

    @abstractmethod
    def add_proposition(self, proposition: Proposition, allow_exists: bool = False, **kwargs):
        """
        Adds a proposition to the argdown document.
        """

    @abstractmethod
    def update_proposition(self, label: str, proposition: Proposition, **kwargs):
        """
        Updates a proposition in the argument map.
        Throws an error if the proposition does not exist.
        """

    @abstractmethod
    def remove_proposition(self, label: str):
        """
        Removes a proposition from the argument map.
        Throws an error if the proposition does not exist.
        """

    @abstractmethod
    def get_proposition(self, label: str) -> Proposition | None:
        """
        Gets a proposition from the argument map.
        """

    @abstractmethod
    def add_argument(
        self, argument: Argument, allow_exists: bool = False, check_legal: bool = True, **kwargs
    ):
        """
        Adds an argument to the argdown document.
        """

    @abstractmethod
    def update_argument(self, label: str, argument: Argument, check_legal: bool = True, **kwargs):
        """
        Updates an argument in the argument map.
        Throws an error if the argument does not exist.
        """

    @abstractmethod
    def remove_argument(self, label: str):
        """
        Removes an argument from the argument map.
        Throws an error if the argument does not exist.
        """

    @abstractmethod
    def get_argument(self, label: str) -> Argument | None:
        """
        Gets an argument from the argument map.
        """

    @abstractmethod
    def add_dialectical_relation(self, edge: ArgdownEdge, allow_exists: bool = True, **kwargs):
        """
        Adds a dialectical relation to the argument map.
        """

    @abstractmethod
    def update_dialectical_relation(self, edge: ArgdownEdge, **kwargs):
        """
        Updates a dialectical relation in the argument map.
        Throws an error if the relation does not exist.
        """

    @abstractmethod
    def remove_dialectical_relation(self, source: str, target: str):
        """
        Removes a dialectical relation from the argument map.
        Throws an error if the relation does not exist.
        """

    @abstractmethod
    def get_dialectical_relation(self, source: str, target: str) -> list[ArgdownEdge] | None:
        """
        Gets a dialectical relation from the argument map.
        """

    @abstractmethod
    def make_label_unique(self, label: str) -> str:
        """
        Makes a label unique by appending a number to it.
        """

    @abstractmethod
    def has_legal_pcs(self, argument) -> tuple[bool, str | None]:
        """
        Checks if the PCS of an argument is legal, returns optional error message
        """

    @abstractmethod
    def _update(self):
        """
        Updates the dialectical relations (especially dialectical type GROUNDED) in the argument map.
        """

    @property
    @abstractmethod
    def propositions(self) -> Sequence[Proposition]:
        """
        Returns all propositions in the argument map.
        """

    @property
    @abstractmethod
    def arguments(self) -> Sequence[Argument]:
        """
        Returns all arguments in the argument map.
        """

    @property
    @abstractmethod
    def dialectical_relations(self) -> Sequence[ArgdownEdge]:
        """
        Returns all dialectical relations in the argument map.
        """




class ArgdownMultiDiGraph(Argdown, nx.MultiDiGraph):
    def __init__(self):
        super().__init__()

    def add_proposition(self, proposition: Proposition, allow_exists: bool = False, **kwargs):
        if proposition.label is not None and proposition.label in self.nodes:
            if not allow_exists:
                raise ValueError(
                    f"Proposition with label {proposition.label} already exists."
                )
            self.update_proposition(proposition.label, proposition)
            return

        self.add_node(proposition.label, **asdict(proposition))
        if kwargs.get("update_edges", False):
            self._update()

    def update_proposition(self, label: str, proposition: Proposition, **kwargs):
        new_data = asdict(proposition)
        self.nodes[label]["texts"].extend(new_data["texts"])
        self.nodes[label]["texts"] = list(set(self.nodes[label]["texts"]))
        self.nodes[label]["data"].update(new_data["data"])
        if kwargs.get("update_edges", False):
            self._update()

    def remove_proposition(self, label: str):
        raise NotImplementedError("Method not implemented.")

    def get_proposition(self, label: str) -> Proposition | None:
        if label not in self.nodes:
            return None
        if not self.nodes[label]["type"] == Proposition.__name__:
            return None
        return Proposition(**self.nodes[label])

    @property
    def propositions(self):
        return [
            Proposition(**data)
            for _, data in self.nodes(data=True)
            if data["type"] == Proposition.__name__
        ]

    def add_argument(
        self, argument: Argument, allow_exists: bool = False, check_legal: bool = True, **kwargs
    ):
        if argument.label is not None and argument.label in self.nodes:
            if not allow_exists:
                raise ValueError(
                    f"Argument with label {argument.label} already exists."
                )
            self.update_argument(argument.label, argument, check_legal=check_legal)
            return

        if check_legal and argument.pcs:
            is_legal, msg = self.has_legal_pcs(argument)
            if not is_legal:
                logger.error(
                    f"PCS of argument {argument.label} is not legal. Error: {msg}"
                )
                return

        # check if all referenced propositions exist
        for pr in argument.pcs:
            if pr.proposition_label not in self.nodes:
                raise ValueError(
                    f"Proposition with label {pr.proposition_label} is referenced in argument {argument.label} but does not exist."
                )

        self.add_node(argument.label, **asdict(argument))
        if kwargs.get("update_edges", False):
            self._update()

    def update_argument(self, label: str, argument: Argument, check_legal: bool = True, **kwargs):
        if check_legal and argument.pcs:
            is_legal, msg = self.has_legal_pcs(argument)
            if not is_legal:
                logger.error(
                    f"PCS of argument {argument.label} is not legal. Will not update argument. Error: {msg}"
                )
                return
        new_data = asdict(argument)
        self.nodes[label]["gists"].extend(new_data["gists"])
        self.nodes[label]["gists"] = list(set(self.nodes[label]["gists"]))
        self.nodes[label]["data"].update(new_data["data"])

        if new_data["pcs"]:
            logger.warning(
                "Overwriting PCS of argument <%s> while updating argument.", label
            )
        self.nodes[label]["pcs"] = new_data["pcs"]

        if kwargs.get("update_edges", False):
            self._update()

    def remove_argument(self, label: str):
        raise NotImplementedError("Method not implemented.")

    def get_argument(self, label: str) -> Argument | None:
        if label not in self.nodes:
            return None
        if not self.nodes[label]["type"] == Argument.__name__:
            return None
        return Argument.from_dict(self.nodes[label])

    @property
    def arguments(self):
        return [
            Argument.from_dict(data)
            for _, data in self.nodes(data=True)
            if data["type"] == Argument.__name__
        ]

    def add_dialectical_relation(self, edge: ArgdownEdge, allow_exists: bool = True, **kwargs):
        s = edge.source
        t = edge.target
        if not self.has_node(s) or not self.has_node(t):
            raise ValueError(
                f"Nodes {s} and {t} must exist before adding a dialectical relation."
            )
        if self.has_edge(s, t):
            if not allow_exists:
                raise ValueError(
                    f"Dialectical relation between {s} and {t} already exists."
                )
            if self.has_edge(s, t, edge.valence.name):
                self.update_dialectical_relation(edge)
                return
        edge_data = asdict(edge)
        edge_data["valence"] = edge.valence.name
        edge_data["dialectics"] = [ds.name for ds in edge.dialectics]
        self.add_edge(s, t, edge.valence.name, **edge_data)
        if kwargs.get("update_edges", False):
            self._update()

    def update_dialectical_relation(self, edge: ArgdownEdge, **kwargs):
        s = edge.source
        t = edge.target
        key = edge.valence.name
        if not self.has_edge(s, t, key):
            raise ValueError(
                f"Dialectical relation with valence {key} between {s} and {t} does not exist and cannot be updated."
            )
        self.edges[s, t, key]["dialectics"].extend([ds.name for ds in edge.dialectics])
        self.edges[s, t, key]["dialectics"] = list(set(self.edges[s, t, key]["dialectics"]))
        self.edges[s, t, key]["data"].update(edge.data)
        if kwargs.get("update_edges", False):
            self._update()

    def remove_dialectical_relation(self, source: str, target: str):
        raise NotImplementedError("Method not implemented.")

    def get_dialectical_relation(self, source: str, target: str) -> list[ArgdownEdge] | None:
        if not self.has_edge(source, target):
            return None
        argdown_edges = []
        for edge_data in self.get_edge_data(source, target).values():
            argdown_edges.append(ArgdownEdge.from_dict(edge_data))
        return argdown_edges    

    @property
    def dialectical_relations(self):
        return [
            ArgdownEdge.from_dict(edge_data) for _, _, edge_data in self.edges(data=True)
        ]

    def has_legal_pcs(self, argument) -> tuple[bool, str | None]:
        pcs = argument.pcs
        if not pcs:
            return False, "No premise conclusion structure found."
        if any(not isinstance(pr, PropositionReference) for pr in pcs):
            raise ValueError("PCS contains items other than PropositionReference.")
        if isinstance(pcs[0], Conclusion):
            return (
                False,
                "Premise conclusion structure starts with a conclusion, but must start with a premise.",
            )
        if not isinstance(pcs[-1], Conclusion):
            return False, "Premise conclusion structure does not end with a conclusion."
        return True, None

    def make_label_unique(self, label: str) -> str:
        if label not in self.nodes:
            return label

        i = 1
        while f"{label}_{i}" in self.nodes:
            i += 1

        return f"{label}_{i}"

    def _entails(self, p1: Proposition, p2: Proposition) -> bool:
        if not isinstance(p1, Proposition) or not isinstance(p2, Proposition):
            raise ValueError(f"Can check for entailment only between propositions, but got {type(p1)} and {type(p2)}.")
        if p1.label is None or p2.label is None:
            return False
        if p1.label == p2.label:
            return True
        if not self.has_edge(p1.label, p2.label):
            return False
        drelations = self.get_dialectical_relation(p1.label, p2.label)
        if drelations is None:
            return False
        return bool([
            r for r in drelations
            if DialecticalType.AXIOMATIC in r.dialectics and r.valence == Valence.SUPPORT
        ])
    
    def _contradicts(self, p1: Proposition, p2: Proposition) -> bool:
        if not isinstance(p1, Proposition) or not isinstance(p2, Proposition):
            raise ValueError(f"Can check for contradiction only between propositions, but got {type(p1)} and {type(p2)}.")
        if p1.label is None or p2.label is None:
            return False
        lr = self.get_dialectical_relation(p1.label, p2.label) or []
        rl = self.get_dialectical_relation(p2.label, p1.label) or []
        return bool([
            r for r in lr + rl
            if DialecticalType.AXIOMATIC in r.dialectics and r.valence in [Valence.ATTACK, Valence.CONTRADICT]
        ])

    def _update(self):
        for u in self.nodes:
            for v in self.nodes:
                if u == v:
                    continue
                ou = Proposition(**self.nodes[u]) if self.nodes[u]["type"] == Proposition.__name__ else Argument.from_dict(self.nodes[u])
                ov = Proposition(**self.nodes[v]) if self.nodes[v]["type"] == Proposition.__name__ else Argument.from_dict(self.nodes[v])
                if isinstance(ou, Proposition) and isinstance(ov, Proposition):
                    continue

                # remove all grounded relations from u to v
                if self.has_edge(u, v):
                    for data in self.get_edge_data(u, v).values():
                        if DialecticalType.GROUNDED.name in data["dialectics"]:
                            data["dialectics"].remove(DialecticalType.GROUNDED.name)

                if isinstance(ou, Argument) and not self.has_legal_pcs(ou)[0]:
                    continue
                if isinstance(ov, Argument) and not self.has_legal_pcs(ov)[0]:
                    continue

                source_anchor_proposition = ou if isinstance(ou, Proposition) else self.get_proposition(ou.pcs[-1].proposition_label)
                target_anchor_propositions = [ov] if isinstance(ov, Proposition) else [
                     self.get_proposition(pr.proposition_label) for pr in ov.pcs
                     if not isinstance(pr, Conclusion)
                ]


                if any(self._entails(source_anchor_proposition, tp) for tp in target_anchor_propositions):
                    self.add_dialectical_relation(ArgdownEdge(u, v, Valence.SUPPORT, [DialecticalType.GROUNDED]))
                if any(self._contradicts(source_anchor_proposition, tp) for tp in target_anchor_propositions):
                    self.add_dialectical_relation(ArgdownEdge(u, v, Valence.ATTACK, [DialecticalType.GROUNDED]))

                # remove all edges with empty dialectics!
                if self.has_edge(u, v):
                    for data in list(self.get_edge_data(u, v).values()):
                        if not data["dialectics"]:
                            self.remove_edge(u, v, data["valence"])