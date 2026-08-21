"""Typer CLI entry point. M1 scope: `run-steps` drives a YAML step list through
either a real SapGuiAgent (--target host:port) or the FakeUiAgent (--fixture path),
satisfying the M1 acceptance demo ("scripted VA01 from a YAML step list through the
agent") without requiring a live SAP session to exercise the wiring.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer
import yaml

from smt.adapter.client import UiAgentClient
from smt.adapter.fake_agent import FakeUiAgent
from smt.adapter.generated import uiadapter_pb2 as pb
from smt.adapter.port import UiAgentPort

app = typer.Typer(help="SapModelTest core CLI")


def _build_action_request(session_id: str, step: dict) -> pb.ActionRequest:
    op_name = step["op"]
    if not hasattr(pb, op_name):
        raise typer.BadParameter(f"unknown ActionOp: {op_name!r}")
    params_fields = {
        k: v
        for k, v in step.items()
        if k not in ("component_id", "op") and hasattr(pb.ActionParams, "DESCRIPTOR")
    }
    return pb.ActionRequest(
        session_id=session_id,
        component_id=step["component_id"],
        op=getattr(pb, op_name),
        params=pb.ActionParams(**params_fields),
        allow_fragile_fallback=step.get("allow_fragile_fallback", False),
    )


def _open_agent(target: Optional[str], fixture: Optional[Path]) -> UiAgentPort:
    if target:
        return UiAgentClient(target)
    if fixture:
        return FakeUiAgent(fixture)
    raise typer.BadParameter("pass either --target host:port or --fixture path")


@app.command("run-steps")
def run_steps(
    yaml_path: Path = typer.Argument(..., help="YAML file with `session` + `steps`"),
    target: Optional[str] = typer.Option(None, help="SapGuiAgent gRPC target, e.g. localhost:50051"),
    fixture: Optional[Path] = typer.Option(None, help="FakeUiAgent fixture JSON, for offline runs"),
) -> None:
    """Drive a YAML step list through the agent (real or fake) and print results."""
    spec = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    agent = _open_agent(target, fixture)

    handle = agent.open_session(pb.OpenSessionRequest(**spec.get("session", {})))
    typer.echo(f"session opened: {handle.session_id}")

    for i, step in enumerate(spec["steps"], start=1):
        request = _build_action_request(handle.session_id, step)
        result = agent.execute_action(request)
        status = "OK" if result.success else f"FAILED: {result.error_message}"
        typer.echo(f"  step {i} [{step['op']} {step['component_id']}] -> {status}")
        for msg in result.statusbar_deltas:
            typer.echo(f"      statusbar: {msg.type} {msg.text}")

    agent.close_session(handle)


if __name__ == "__main__":
    app()
