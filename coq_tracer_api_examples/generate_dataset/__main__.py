import pathlib
import argparse

import coq_tracer_api
from coq_tracer_api.tracer_types import StepKindTactic, Step, DeclarationKindInteractive, Declaration


def process_step(step: Step) -> list[str]:
    match step.kind:
        case StepKindTactic(tactic=tactic):
            return [feature.path for feature in tactic.references]
        case _:
            return []


def process_declaration(declaration: Declaration) -> list[str]:
    match declaration.kind:
        case DeclarationKindInteractive(steps=steps):
            return [path for step in steps for path in process_step(step)]
        case _:
            return []


parser = argparse.ArgumentParser(description="Generate an example dataset from a trace file.")
parser.add_argument("input", type=pathlib.Path)
args = parser.parse_args()

trace = coq_tracer_api.load_trace(args.input, deep=True)

for declaration in trace.declarations:
    print(declaration.path + ": " + ", ".join(process_declaration(declaration)))
