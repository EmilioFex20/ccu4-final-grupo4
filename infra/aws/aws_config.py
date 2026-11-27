import json
import re
from copy import deepcopy
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
POLICY_FILE = BASE_DIR / "iam-policy-micro-only.json"
BUDGET_FILE = BASE_DIR / "budget.json"
ALLOWED_TYPES = ("t2.micro", "t3.micro")
ALLOWED_REGION = "us-east-1"
EMAIL_PLACEHOLDER = "__AWS_BUDGET_EMAIL__"
REQUIRED_ALLOW_ACTIONS = {
    "ec2:DescribeInstances",
    "ec2:DescribeInstanceStatus",
    "ec2:DescribeImages",
    "ec2:DescribeSubnets",
    "ec2:DescribeVpcs",
    "ec2:DescribeSecurityGroups",
    "ec2:DescribeKeyPairs",
    "ec2:DescribeNetworkInterfaces",
    "ec2:RunInstances",
    "ec2:CreateTags",
    "ec2:TerminateInstances",
}
ALLOWED_ACTION_PREFIXES = ("ec2:",)


def load_json(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def statement_actions(statement):
    actions = statement.get("Action", [])
    return actions if isinstance(actions, list) else [actions]


def find_statements(document, effect):
    return [s for s in document.get("Statement", []) if s.get("Effect") == effect]


def validate_policy(document):
    errors = []
    if document.get("Version") != "2012-10-17":
        errors.append("La versión de la política debe ser 2012-10-17")

    denies = find_statements(document, "Deny")
    allows = find_statements(document, "Allow")

    type_denies = [
        s for s in denies
        if "ec2:RunInstances" in statement_actions(s)
        and "StringNotEquals" in s.get("Condition", {})
        and "ec2:InstanceType" in s.get("Condition", {}).get("StringNotEquals", {})
    ]
    if not type_denies:
        errors.append("Falta un Deny con StringNotEquals sobre ec2:InstanceType")
    else:
        configured = type_denies[0]["Condition"]["StringNotEquals"]["ec2:InstanceType"]
        configured = configured if isinstance(configured, list) else [configured]
        if set(configured) != set(ALLOWED_TYPES):
            errors.append(f"Los tipos permitidos deben ser exactamente {', '.join(ALLOWED_TYPES)}")

    if not any(
        "ec2:RunInstances" in statement_actions(s)
        and s.get("Condition", {}).get("Null", {}).get("ec2:InstanceType") == "true"
        for s in denies
    ):
        errors.append("Falta un Deny cuando ec2:InstanceType no está presente en RunInstances")

    if not any(
        "ec2:ModifyInstanceAttribute" in statement_actions(s)
        and "ec2:InstanceType" in s.get("Condition", {}).get("StringNotEquals", {})
        for s in denies
    ):
        errors.append("Falta un Deny para redimensionar instancias a tipos no autorizados")

    if not any(
        s.get("Condition", {}).get("StringNotEquals", {}).get("aws:RequestedRegion") == ALLOWED_REGION
        for s in denies
    ):
        errors.append(f"Falta el Deny de regiones distintas a {ALLOWED_REGION}")

    granted = set()
    for statement in allows:
        for action in statement_actions(statement):
            if not action.startswith(ALLOWED_ACTION_PREFIXES):
                errors.append(f"acción fuera de EC2 en un Allow: {action}")
            granted.add(action)
    missing = REQUIRED_ALLOW_ACTIONS - granted
    if missing:
        errors.append("Faltan permisos para el auto-scaler: " + ", ".join(sorted(missing)))

    return errors


def validate_budget(document, require_email=True):
    errors = []
    if document.get("BudgetLimit", {}).get("Amount") != "1.00":
        errors.append("El límite del presupuesto debe ser 1.00 USD")
    if document.get("BudgetLimit", {}).get("Unit") != "USD":
        errors.append("La unidad del presupuesto debe ser USD")
    if document.get("TimeUnit") != "MONTHLY":
        errors.append("El periodo del presupuesto debe ser MONTHLY")
    if document.get("BudgetType") != "COST":
        errors.append("El tipo de presupuesto debe ser COST")

    notifications = document.get("NotificationsWithSubscribers", [])
    actual = [
        item for item in notifications
        if item.get("Notification", {}).get("NotificationType") == "ACTUAL"
    ]
    forecasted = [
        item for item in notifications
        if item.get("Notification", {}).get("NotificationType") == "FORECASTED"
    ]
    actual_thresholds = {
        item["Notification"].get("Threshold") for item in actual
    }
    if not {50, 80, 100}.issubset(actual_thresholds):
        errors.append("Deben existir notificaciones ACTUAL en 50, 80 y 100 por ciento")
    if not forecasted:
        errors.append("Debe existir una notificación FORECASTED al 100 por ciento")

    for item in notifications:
        subscribers = item.get("Subscribers", [])
        if not subscribers:
            errors.append("Toda notificación debe tener al menos un suscriptor")
        for subscriber in subscribers:
            address = subscriber.get("Address", "")
            if require_email and address != EMAIL_PLACEHOLDER and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", address):
                errors.append(f"Dirección de notificación inválida: {address!r}")

    return errors


def render_budget(document, email):
    rendered = deepcopy(document)
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email or ""):
        raise ValueError("El correo de notificación no es válido")
    for item in rendered.get("NotificationsWithSubscribers", []):
        for subscriber in item.get("Subscribers", []):
            if subscriber.get("Address") == EMAIL_PLACEHOLDER:
                subscriber["Address"] = email
    return rendered


def find_exposed_credentials(document):
    text = json.dumps(document)
    patterns = (
        r"AKIA[0-9A-Z]{16}",
        r"(?i)aws_secret_access_key\s*[:=]",
        r"(?i)password\s*[:=]\s*['\"][^'\"]{4,}",
    )
    return [pattern for pattern in patterns if re.search(pattern, text)]
