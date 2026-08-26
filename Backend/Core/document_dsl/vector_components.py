from __future__ import annotations

from dataclasses import dataclass

from Backend.Core.document_dsl.components import Diagram, Graph, Table


@dataclass(frozen=True)
class EconomicCurve(Graph):
    curve_kind: str = "demand-supply"


@dataclass(frozen=True)
class MathematicalPlot(Graph):
    expression: str = ""


@dataclass(frozen=True)
class StatisticalChart(Graph):
    chart_kind: str = "line"


@dataclass(frozen=True)
class AccountingTable(Table):
    accounting_standard: str = "UK-GAAP"


@dataclass(frozen=True)
class ProgramTraceTable(Table):
    language: str = "pseudocode"


@dataclass(frozen=True)
class LogicCircuit(Diagram):
    pass


@dataclass(frozen=True)
class ScientificApparatus(Diagram):
    pass


@dataclass(frozen=True)
class Molecule(Diagram):
    pass
