#!/usr/bin/env python3
"""Confere os cálculos publicados em entrega-grupo-aula01.md.

Prova determinística (Decimal, sem float solto) para SLA 1.3, custos 2.2,
egress 3.3 e contagem de linhas Terraform/Bicep.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

AULA01 = Path(__file__).resolve().parents[1]
ENTREGA = AULA01 / "entrega-grupo-aula01.md"
BICEP = AULA01 / "bicep" / "main.bicep"
TF_FILES = [
    AULA01 / "terraform" / "main.tf",
    AULA01 / "terraform" / "variables.tf",
    AULA01 / "terraform" / "outputs.tf",
    AULA01 / "terraform" / "versions.tf",
]


def money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def almost(label: str, got: Decimal | float, expected: Decimal | float, places: int = 4) -> None:
    delta = abs(float(got) - float(expected))
    limit = 10 ** (-places)
    if delta > limit:
        raise AssertionError(f"{label}: got {got}, expected {expected} (delta={delta})")
    print(f"ok  {label}: {got}")


@dataclass(frozen=True)
class Check:
    name: str


def check_sla() -> None:
    """Prova determinística do Exercício 1.3 (ano comercial 8760 h)."""
    hours_year = Decimal("8760")  # 365 * 24
    sla_999 = Decimal("0.999")
    hourly_loss = Decimal("50000")

    print("=== prova SLA 1.3 (Decimal) ===")
    print(f"premissa: hours_year = 365 * 24 = {hours_year}")

    downtime_h = hours_year * (Decimal("1") - sla_999)
    almost("1.3a downtime horas", downtime_h, Decimal("8.76"))
    almost("1.3a downtime minutos", downtime_h * 60, Decimal("525.6"))

    impact = downtime_h * hourly_loss
    almost("1.3b impacto anual", impact, Decimal("438000"))

    max_downtime_h = hourly_loss / hourly_loss
    almost("1.3c downtime máximo", max_downtime_h, Decimal("1"))

    downtime_pct = (max_downtime_h / hours_year) * Decimal("100")
    almost("1.3c % downtime", downtime_pct, Decimal("0.011415525114"), places=6)

    availability = (Decimal("1") - max_downtime_h / hours_year) * Decimal("100")
    almost("1.3c disponibilidade", availability, Decimal("99.988584474886"), places=6)

    sla_9999_downtime_h = hours_year * Decimal("0.0001")
    almost("1.3 99.99% horas", sla_9999_downtime_h, Decimal("0.876"))
    almost("1.3 99.99% minutos", sla_9999_downtime_h * 60, Decimal("52.56"))
    almost("1.3 99.99% impacto", sla_9999_downtime_h * hourly_loss, Decimal("43800"))
    print("=== fim prova SLA ===")


def check_costs() -> None:
    hours = Decimal("730")
    azure_vm_h = Decimal("0.0832")
    aws_vm_h = Decimal("0.0832")
    gcp_vm_h = Decimal("0.067")

    azure_vms = money(2 * azure_vm_h * hours)
    aws_vms = money(2 * aws_vm_h * hours)
    gcp_vms = money(2 * gcp_vm_h * hours)
    almost("2.2 Azure 2x VM", azure_vms, Decimal("121.47"))
    almost("2.2 AWS 2x VM", aws_vms, Decimal("121.47"))
    almost("2.2 GCP 2x VM", gcp_vms, Decimal("97.82"))

    azure_storage = money(Decimal("500") * Decimal("0.0208"))
    aws_storage = money(Decimal("500") * Decimal("0.023"))
    gcp_storage = money(Decimal("500") * Decimal("0.020"))
    almost("2.2 Azure 500GB", azure_storage, Decimal("10.40"))
    almost("2.2 AWS 500GB", aws_storage, Decimal("11.50"))
    almost("2.2 GCP 500GB", gcp_storage, Decimal("10.00"))

    azure_db = Decimal("234")
    aws_db = Decimal("117")
    gcp_db = Decimal("110")
    azure_fn = Decimal("1.80")
    aws_fn = Decimal("1.80")
    gcp_fn = Decimal("2.00")

    azure_month = money(azure_vms + azure_storage + azure_db + azure_fn)
    aws_month = money(aws_vms + aws_storage + aws_db + aws_fn)
    gcp_month = money(gcp_vms + gcp_storage + gcp_db + gcp_fn)
    almost("2.2 Azure mensal (exato)", azure_month, Decimal("367.67"))
    almost("2.2 AWS mensal (exato)", aws_month, Decimal("251.77"))
    almost("2.2 GCP mensal (exato)", gcp_month, Decimal("219.82"))

    almost("2.2 Azure anual 12x 368", Decimal("368") * 12, Decimal("4416"))
    almost("2.2 AWS anual 12x 252", Decimal("252") * 12, Decimal("3024"))
    almost("2.2 GCP anual 12x 220", Decimal("220") * 12, Decimal("2640"))
    almost("2.2 gap Azure-GCP", Decimal("368") - Decimal("220"), Decimal("148"))


def check_egress() -> None:
    total_gb = Decimal("10000")
    free_gb = Decimal("100")
    billable = total_gb - free_gb
    almost("3.3 billable GB", billable, Decimal("9900"))

    premium = money(billable * Decimal("0.181"))
    isp = money(billable * Decimal("0.12"))
    aws_dto = money(billable * Decimal("0.09"))
    almost("3.3 Azure Premium", premium, Decimal("1791.90"))
    almost("3.3 Azure ISP", isp, Decimal("1188.00"))
    almost("3.3 AWS DTO", aws_dto, Decimal("891.00"))


def count_lines(path: Path) -> int:
    return len(path.read_text(encoding="utf-8").splitlines())


def check_line_counts() -> None:
    bicep_lines = count_lines(BICEP)
    tf_lines = sum(count_lines(path) for path in TF_FILES)
    almost("linhas Bicep", bicep_lines, 191, places=0)
    almost("linhas Terraform", tf_lines, 216, places=0)

    text = ENTREGA.read_text(encoding="utf-8")
    for needle in ("| 191 |", "| 216 |", "| 237 |"):
        if needle not in text:
            raise AssertionError(f"entrega não contém {needle}")
    print("ok  entrega cita 191/216/237")


def main() -> int:
    try:
        check_sla()
        check_costs()
        check_egress()
        check_line_counts()
    except AssertionError as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        return 1
    print("todos os cálculos conferem")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
