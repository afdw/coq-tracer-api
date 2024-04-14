from __future__ import annotations
from typing import Any, Literal, Annotated
from collections.abc import Iterable
from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, ValidatorFunctionWrapHandler, WrapValidator


type FullPath = str


class ReferenceConst(BaseModel):
    model_config = ConfigDict(frozen=True, strict=True, cache_strings=False)

    type: Literal["Const"] = "Const"
    path: FullPath


class ReferenceInd(BaseModel):
    model_config = ConfigDict(frozen=True, strict=True, cache_strings=False)

    type: Literal["Ind"] = "Ind"
    path: FullPath


class ReferenceConstruct(BaseModel):
    model_config = ConfigDict(frozen=True, strict=True, cache_strings=False)

    type: Literal["Construct"] = "Construct"
    ind_path: FullPath
    path: FullPath


type Reference = Annotated[ReferenceConst | ReferenceInd | ReferenceConstruct, Field(discriminator="type")]


class PrintingVariants(BaseModel):
    model_config = ConfigDict(frozen=True, strict=True, cache_strings=False)

    default: str
    full_path: str
    no_notations: str
    low_level: str
    default_pretty: str
    references: list[Reference]

    def __hash__(self) -> int:
        return hash((self.default, self.full_path, self.no_notations, self.low_level, tuple(self.references)))


class HypKindAssumption(BaseModel):
    model_config = ConfigDict(frozen=True, strict=True, cache_strings=False)

    type: Literal["Assumption"] = "Assumption"


class HypKindDefinition(BaseModel):
    model_config = ConfigDict(frozen=True, strict=True, cache_strings=False)

    type: Literal["Definition"] = "Definition"
    value: PrintingVariants


type HypKind = Annotated[HypKindAssumption | HypKindDefinition, Field(discriminator="type")]


class Hyp(BaseModel):
    model_config = ConfigDict(frozen=True, strict=True, cache_strings=False)

    name: str
    type_: PrintingVariants
    kind: HypKind


class Goal(BaseModel):
    model_config = ConfigDict(frozen=True, strict=True, cache_strings=False)

    hyps: list[Hyp]
    concl: PrintingVariants

    def __hash__(self) -> int:
        return hash((tuple(self.hyps), self.concl))


class TacticKindPrimitive(BaseModel):
    model_config = ConfigDict(frozen=True, strict=True, cache_strings=False)

    type: Literal["Primitive"] = "Primitive"
    s: str


class TacticKindBuiltin(BaseModel):
    model_config = ConfigDict(frozen=True, strict=True, cache_strings=False)

    type: Literal["Builtin"] = "Builtin"
    s: str


class TacticKindAlias(BaseModel):
    model_config = ConfigDict(frozen=True, strict=True, cache_strings=False)

    type: Literal["Alias"] = "Alias"
    s: str


class TacticKindML(BaseModel):
    model_config = ConfigDict(frozen=True, strict=True, cache_strings=False)

    type: Literal["ML"] = "ML"
    s: str


type TacticKind = Annotated[TacticKindPrimitive | TacticKindBuiltin | TacticKindAlias | TacticKindML, Field(discriminator="type")]


class EventSequence(BaseModel):
    model_config = ConfigDict(frozen=True, strict=True, cache_strings=False)

    type: Literal["Sequence"] = "Sequence"
    elements: list[Event]

    def __hash__(self) -> int:
        return hash(tuple(self.elements))


class EventDispatch(BaseModel):
    model_config = ConfigDict(frozen=True, strict=True, cache_strings=False)

    type: Literal["Dispatch"] = "Dispatch"
    goals_before: list[Goal]
    branches: list[Event]

    def __hash__(self) -> int:
        return hash(tuple(self.branches))


class EventTactic(BaseModel):
    model_config = ConfigDict(frozen=True, strict=True, cache_strings=False)

    type: Literal["Tactic"] = "Tactic"
    goals_before: list[Goal]
    goals_after: list[Goal]
    kind: TacticKind
    tactic: PrintingVariants
    details: Event


class EventMessage(BaseModel):
    model_config = ConfigDict(frozen=True, strict=True, cache_strings=False)

    type: Literal["Message"] = "Message"
    message: str


# Work around `Recursion error - cyclic reference detected`
def fix_event_tactic(v: Any, _handler: ValidatorFunctionWrapHandler, _info: ValidationInfo) -> EventTactic:
    return EventTactic.model_validate(v)


type Event = Annotated[EventSequence | EventDispatch | Annotated[EventTactic, WrapValidator(fix_event_tactic)] | EventMessage, Field(discriminator="type")]


class StepKindTactic(BaseModel):
    model_config = ConfigDict(frozen=True, strict=True, cache_strings=False)

    type: Literal["Tactic"] = "Tactic"
    goal_selector: str
    tactic_raw: str
    tactic: PrintingVariants
    event: Event


class StepKindStartSubproof(BaseModel):
    model_config = ConfigDict(frozen=True, strict=True, cache_strings=False)

    type: Literal["StartSubproof"] = "StartSubproof"


class StepKindEndSubproof(BaseModel):
    model_config = ConfigDict(frozen=True, strict=True, cache_strings=False)

    type: Literal["EndSubproof"] = "EndSubproof"


class StepKindBullet(BaseModel):
    model_config = ConfigDict(frozen=True, strict=True, cache_strings=False)

    type: Literal["Bullet"] = "Bullet"
    bullet: str


type StepKind = Annotated[StepKindTactic | StepKindStartSubproof | StepKindEndSubproof | StepKindBullet, Field(discriminator="type")]


class Step(BaseModel):
    model_config = ConfigDict(frozen=True, strict=True, cache_strings=False)

    goals_before: list[Goal]
    goals_after: list[Goal]
    kind: StepKind

    def __hash__(self) -> int:
        return hash((self.goals_before, self.goals_after, tuple(self.kind)))


class OutcomeAdmitted(BaseModel):
    model_config = ConfigDict(frozen=True, strict=True, cache_strings=False)

    type: Literal["Admitted"] = "Admitted"


class OutcomeProved(BaseModel):
    model_config = ConfigDict(frozen=True, strict=True, cache_strings=False)

    type: Literal["Proved"] = "Proved"


class OutcomeExact(BaseModel):
    model_config = ConfigDict(frozen=True, strict=True, cache_strings=False)

    type: Literal["Exact"] = "Exact"


class OutcomeAbort(BaseModel):
    model_config = ConfigDict(frozen=True, strict=True, cache_strings=False)

    type: Literal["Abort"] = "Abort"


class OutcomeFail(BaseModel):
    model_config = ConfigDict(frozen=True, strict=True, cache_strings=False)

    type: Literal["Fail"] = "Fail"


type Outcome = Annotated[OutcomeAdmitted | OutcomeProved | OutcomeExact | OutcomeAbort | OutcomeFail, Field(discriminator="type")]


class DeclarationKindInductive(BaseModel):
    model_config = ConfigDict(frozen=True, strict=True, cache_strings=False)

    type: Literal["Inductive"] = "Inductive"


class DeclarationKindConstructor(BaseModel):
    model_config = ConfigDict(frozen=True, strict=True, cache_strings=False)

    type: Literal["Constructor"] = "Constructor"
    ind_path: FullPath


class DeclarationKindAssumption(BaseModel):
    model_config = ConfigDict(frozen=True, strict=True, cache_strings=False)

    type: Literal["Assumption"] = "Assumption"


class DeclarationKindDefinition(BaseModel):
    model_config = ConfigDict(frozen=True, strict=True, cache_strings=False)

    type: Literal["Definition"] = "Definition"
    value: PrintingVariants
    equations: list[PrintingVariants]


class DeclarationKindInteractive(BaseModel):
    model_config = ConfigDict(frozen=True, strict=True, cache_strings=False)

    type: Literal["Interactive"] = "Interactive"
    steps: list[Step]
    outcome: Outcome

    def __hash__(self) -> int:
        return hash((tuple(self.steps), self.outcome))


type DeclarationKind = Annotated[
    DeclarationKindInductive | DeclarationKindConstructor | DeclarationKindAssumption | DeclarationKindDefinition | DeclarationKindInteractive,
    Field(discriminator="type"),
]


class Declaration(BaseModel):
    model_config = ConfigDict(frozen=True, strict=True, cache_strings=False)

    path: FullPath
    type_: PrintingVariants
    kind: DeclarationKind


class Trace(BaseModel):
    model_config = ConfigDict(frozen=True, strict=True, cache_strings=False)

    sub_filenames: Iterable[str]
    declarations: Iterable[Declaration]
