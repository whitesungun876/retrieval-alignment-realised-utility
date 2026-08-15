"""Neutral P renderer and paired abstract worked-protocol scaffold renderer."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import re
from typing import Any, Callable, Mapping, Sequence


COMMON_HEADER = (
    "Interaction record\n"
    "Format: chronological action-observation sequence\n\n"
)
COMMON_OUTCOME = "Interaction outcome: success\n"


@dataclass(frozen=True)
class RenderedPair:
    p_text: str
    c_text: str
    phases: tuple[str, ...]
    p_tokens: int
    c_tokens: int
    token_ratio: float


def phase_for_action(action: str) -> str:
    prefix = action.strip().lower().split(" ", 1)[0]
    if prefix in {"look", "read", "examine", "inventory"}:
        return "inspect"
    if prefix == "move":
        return "navigate"
    if prefix in {"take", "open", "close", "get", "pick"}:
        return "acquire"
    if prefix in {"slice", "dice", "chop", "cut", "cook", "fry", "roast", "grill"}:
        return "transform"
    if prefix == "prepare":
        return "complete"
    if prefix == "eat":
        return "stop"
    return "orient"


P_TASK_LABEL = "Concrete task specification is shown below."
C_TASK_LABEL = "An abstract task specification is shown below."


def _step_block(index: int, phase: str, action: str, observation: str) -> str:
    return (
        f"Step {index:02d} phase:\n{phase}\n"
        f"Step {index:02d} action:\n{action}\n"
        f"Step {index:02d} observation:\n{observation.strip()}\n\n"
    )


def render_p(source: Mapping[str, Any]) -> str:
    lines = [COMMON_HEADER, "Task description:\n", P_TASK_LABEL, "\n", str(source["recipe_text"]).strip(), "\n\n"]
    lines.extend(["Initial state:\n", str(source["initial_observation"]).strip(), "\n\n"])
    for index, step in enumerate(source["trajectory"], start=1):
        lines.append(_step_block(index, phase_for_action(str(step["action"])), str(step["action"]), str(step["observation"])))
    lines.append(COMMON_OUTCOME)
    return "".join(lines)


ABSTRACT_ACTION = {
    "inspect": "inspect the currently available information and identify what the episode requires",
    "navigate": "change the current context in order to reach the next relevant part of the episode",
    "acquire": "perform the next acquisition or access operation required by the episode plan",
    "transform": "apply the required transformation to the appropriate abstract task item",
    "complete": "combine the completed intermediate results and signal task completion",
    "stop": "perform the terminal action only after the task has been completed",
    "orient": "perform the next admissible operation in the abstract episode plan",
}

ABSTRACT_OBSERVATION = {
    "inspect": "The available information is updated, making the next procedural requirement explicit.",
    "navigate": "The interaction enters the intended next context and exposes the next relevant opportunity.",
    "acquire": "The required abstract resource or access state is now available for subsequent steps.",
    "transform": "The abstract task item now reflects the requested intermediate transformation.",
    "complete": "The required intermediate results have been assembled and the task is ready to terminate.",
    "stop": "The episode reaches a successful terminal state and no further action is required.",
    "orient": "The environment confirms a legal transition and the episode can proceed to its next phase.",
}

TASK_DETAILS = (
    "The episode has several abstract requirements whose concrete names and values are intentionally omitted.",
    "The worked record demonstrates how an agent can organise a multi-stage interaction without supplying task-specific content.",
    "The task should be completed through legal actions, state-dependent transitions, and an explicit terminal step.",
    "The example is chronological: later operations are attempted only after their prerequisites have become available.",
    "The record contains no concrete objects, locations, devices, recipes, commands, or observations from another task.",
)

INITIAL_DETAILS = (
    "The initial state exposes multiple possible actions and incomplete information about later requirements.",
    "The agent begins by orienting to the interaction, then gathers information before committing to dependent operations.",
    "No target-specific object, location, tool, or transformation is named in this abstract state description.",
    "The sequence below preserves the phase order and turn count of a worked interaction while withholding its concrete content.",
)

STEP_DETAILS = {
    "inspect": (
        "This step reduces uncertainty before a dependent choice is made.",
        "Its result is used to organise the remaining phase sequence.",
    ),
    "navigate": (
        "The transition changes context while preserving the outstanding task requirements.",
        "The agent continues only after the relevant abstract context becomes available.",
    ),
    "acquire": (
        "The operation establishes a prerequisite used by one or more later turns.",
        "The observation confirms access without revealing any concrete resource identity.",
    ),
    "transform": (
        "The operation is applied only after its abstract prerequisites have been satisfied.",
        "The resulting state records progress toward the final task configuration.",
    ),
    "complete": (
        "Completion occurs after the required intermediate states have been established.",
        "The record now moves from task construction to terminal handling.",
    ),
    "stop": (
        "The terminal operation is not taken prematurely.",
        "After success is observed, the interaction stops rather than adding unrelated actions.",
    ),
    "orient": (
        "The operation preserves chronological progress through the abstract plan.",
        "The observation supplies only the procedural consequence needed for the next turn.",
    ),
}


def _render_c(phases: Sequence[str], task_detail_count: int, initial_detail_count: int, per_step_details: Sequence[int], step_cycles: Sequence[int] | None = None) -> str:
    lines = [COMMON_HEADER, "Task description:\n", C_TASK_LABEL, "\n"]
    lines.extend(sentence + " " for sentence in TASK_DETAILS[:task_detail_count])
    lines.append("\n\nInitial state:\n")
    lines.extend(sentence + " " for sentence in INITIAL_DETAILS[:initial_detail_count])
    lines.append("\n\n")
    for index, phase in enumerate(phases, start=1):
        action = ABSTRACT_ACTION[phase]
        observation = ABSTRACT_OBSERVATION[phase]
        detail_count = per_step_details[index - 1]
        if detail_count:
            observation += " " + " ".join(STEP_DETAILS[phase][:detail_count])
        cycles = 0 if step_cycles is None else int(step_cycles[index - 1])
        for cycle in range(cycles):
            observation += (
                f" Abstract checkpoint {cycle + 1} records that prerequisite state "
                f"{index:02d}.{cycle + 1:02d} has been established, while concrete "
                "names, values, affordances, and task content remain intentionally omitted."
            )
        lines.append(_step_block(index, phase, action, observation))
    lines.append(COMMON_OUTCOME)
    return "".join(lines)


def render_c_matched(source: Mapping[str, Any], token_count: Callable[[str], int], minimum_ratio: float = 0.90, maximum_ratio: float = 1.10) -> RenderedPair:
    p_text = render_p(source)
    phases = tuple(phase_for_action(str(step["action"])) for step in source["trajectory"])
    p_tokens = token_count(p_text)
    details = [0] * len(phases)
    cycles = [0] * len(phases)
    c_text = _render_c(phases, 0, 0, details, cycles)
    c_tokens = token_count(c_text)
    candidates: list[tuple[str, int]] = []
    for step_index, phase in enumerate(phases):
        candidates.extend((f"step:{step_index}", detail_index) for detail_index in range(len(STEP_DETAILS[phase])))
    candidates.extend(("task", index) for index in range(len(TASK_DETAILS)))
    candidates.extend(("initial", index) for index in range(len(INITIAL_DETAILS)))
    task_count = initial_count = 0
    for field, detail_index in candidates:
        if c_tokens >= minimum_ratio * p_tokens:
            break
        previous = (task_count, initial_count, list(details), list(cycles), c_text, c_tokens)
        if field == "task":
            task_count = max(task_count, detail_index + 1)
        elif field == "initial":
            initial_count = max(initial_count, detail_index + 1)
        else:
            step_index = int(field.split(":", 1)[1])
            details[step_index] = max(details[step_index], detail_index + 1)
        candidate_text = _render_c(phases, task_count, initial_count, details, cycles)
        candidate_tokens = token_count(candidate_text)
        if candidate_tokens > maximum_ratio * p_tokens:
            task_count, initial_count, details, cycles, c_text, c_tokens = previous
            continue
        c_text, c_tokens = candidate_text, candidate_tokens
    checkpoint_round = 0
    while c_tokens < minimum_ratio * p_tokens and checkpoint_round < 12:
        for step_index in range(len(phases)):
            if c_tokens >= minimum_ratio * p_tokens:
                break
            cycles[step_index] += 1
            candidate_text = _render_c(phases, task_count, initial_count, details, cycles)
            candidate_tokens = token_count(candidate_text)
            if candidate_tokens > maximum_ratio * p_tokens:
                cycles[step_index] -= 1
                continue
            c_text, c_tokens = candidate_text, candidate_tokens
        checkpoint_round += 1
    ratio = c_tokens / p_tokens
    if not (minimum_ratio <= ratio <= maximum_ratio):
        raise ValueError(f"C length matching failed: P={p_tokens}, C={c_tokens}, ratio={ratio:.4f}")
    return RenderedPair(p_text, c_text, phases, p_tokens, c_tokens, ratio)


def body_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def normalize_shell(text: str) -> str:
    """Replace condition-variable field contents while preserving structural labels."""
    labels = re.findall(r"^(Task description:|Initial state:|Step \d+ phase:|Step \d+ action:|Step \d+ observation:|Interaction outcome: success)$", text, flags=re.MULTILINE)
    return "\n".join(labels)
