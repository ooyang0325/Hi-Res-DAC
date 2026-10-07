"""Gate result plumbing: findings, statuses and the gate registry."""

from __future__ import annotations

from dataclasses import dataclass, field

FAIL = "FAIL"
WARN = "WARN"
INFO = "INFO"
PASS = "PASS"
SKIP = "SKIP"

_ORDER = {PASS: 0, INFO: 1, SKIP: 1, WARN: 2, FAIL: 3}


@dataclass
class Finding:
    severity: str
    code: str
    message: str
    detail: dict = field(default_factory=dict)

    def to_dict(self):
        return {
            "severity": self.severity,
            "code": self.code,
            "message": self.message,
            "detail": self.detail,
        }


@dataclass
class GateResult:
    gate_id: str
    title: str
    criterion: str
    sources: list = field(default_factory=list)
    findings: list = field(default_factory=list)
    metrics: dict = field(default_factory=dict)
    assumptions: list = field(default_factory=list)
    status: str = PASS
    error: str = ""

    def add(self, severity, code, message, **detail):
        self.findings.append(Finding(severity, code, message, detail))
        if _ORDER[severity] > _ORDER[self.status]:
            self.status = severity if severity in (FAIL, WARN) else self.status
        return self

    def fail(self, code, message, **detail):
        return self.add(FAIL, code, message, **detail)

    def warn(self, code, message, **detail):
        return self.add(WARN, code, message, **detail)

    def info(self, code, message, **detail):
        return self.add(INFO, code, message, **detail)

    def skip(self, message, **detail):
        """Mark the gate as not evaluated.

        A gate that could not run is explicitly *not* a pass: the distinction
        matters, because a missing simulation must never be read as evidence
        that the design is sound.
        """
        self.add(SKIP, "GATE_SKIPPED", message, **detail)
        self.status = SKIP
        return self

    def note(self, message, **detail):
        """Record a passing observation worth quoting in the report."""
        return self.add(INFO, "NOTE", message, **detail)

    def assume(self, text):
        self.assumptions.append(text)
        return self

    def counts(self):
        out = {FAIL: 0, WARN: 0, INFO: 0}
        for f in self.findings:
            out[f.severity] = out.get(f.severity, 0) + 1
        return out

    def to_dict(self):
        return {
            "gate": self.gate_id,
            "title": self.title,
            "status": self.status,
            "criterion": self.criterion,
            "sources": self.sources,
            "assumptions": self.assumptions,
            "metrics": self.metrics,
            "counts": self.counts(),
            "findings": [f.to_dict() for f in self.findings],
            "error": self.error,
        }


_REGISTRY = []


def gate(gate_id, title, criterion, sources=()):
    """Register a gate function ``fn(model, ctx, result) -> None``."""

    def deco(fn):
        _REGISTRY.append(
            {
                "id": gate_id,
                "title": title,
                "criterion": criterion,
                "sources": list(sources),
                "fn": fn,
            }
        )
        return fn

    return deco


def registered():
    return sorted(_REGISTRY, key=lambda g: g["id"])
