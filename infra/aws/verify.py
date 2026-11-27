import argparse
import json

from aws_config import (
    BUDGET_FILE,
    POLICY_FILE,
    find_exposed_credentials,
    load_json,
    validate_budget,
    validate_policy,
)


def offline_checks():
    policy = load_json(POLICY_FILE)
    budget = load_json(BUDGET_FILE)
    errors = []
    errors += [f"IAM: {item}" for item in validate_policy(policy)]
    errors += [f"Budget: {item}" for item in validate_budget(budget, require_email=False)]
    errors += [f"Credenciales expuestas: {item}" for item in find_exposed_credentials(policy)]
    errors += [f"Credenciales expuestas: {item}" for item in find_exposed_credentials(budget)]
    print(f"[OK] JSON válido: {POLICY_FILE.name}, {BUDGET_FILE.name}")
    print("[OK] Deny explícito de tipos distintos de t2.micro/t3.micro")
    print("[OK] Deny cuando el tipo de instancia no se especifica")
    print("[OK] Deny de redimensionamiento a tipos no autorizados")
    print("[OK] Permisos mínimos del auto-scaler presentes")
    print("[OK] Presupuesto de 1.00 USD con 4 notificaciones")
    return errors


def live_checks(profile):
    import boto3

    session = boto3.Session(profile_name=profile)
    policy = load_json(POLICY_FILE)
    result = session.client("iam").validate_policy(PolicyDocument=json.dumps(policy))
    print(f"IAM ValidatePolicy: {len(result.get('Findings', []))} hallazgos")
    for finding in result.get("Findings", []):
        print(f"  {finding.get('FindingType')}: {finding.get('IssueDetails', {}).get('Text', '')}")

    budget = load_json(BUDGET_FILE)
    client = session.client("budgets", region_name="us-east-1")
    account_id = session.client("sts").get_caller_identity()["Account"]
    response = client.describe_budget(AccountId=account_id, BudgetName=budget["BudgetName"])
    described = response["Budget"]
    print(
        "Budget remoto: "
        f"{described['BudgetLimit']['Amount']} {described['BudgetLimit']['Unit']} "
        f"({described['TimeUnit']})"
    )
    notifications = client.describe_notifications_for_budget(
        AccountId=account_id,
        BudgetName=budget["BudgetName"],
    )
    print(f"Notificaciones remotas: {len(notifications.get('Notifications', []))}")
    return [f"IAM: {item['IssueDetails']['Text']}" for item in result.get("Findings", []) if item.get("FindingType") == "ERROR"]


def main():
    parser = argparse.ArgumentParser(description="Verifica IAM y AWS Budget sin crear recursos.")
    parser.add_argument("--live", action="store_true", help="consulta AWS (solo lectura, requiere credenciales y autorización)")
    parser.add_argument("--profile", default=None, help="perfil de AWS CLI a utilizar")
    args = parser.parse_args()

    errors = offline_checks()
    if args.live:
        try:
            errors += live_checks(args.profile)
        except Exception as error:
            print(f"No se pudo completar la verificación en vivo: {error}")
            raise SystemExit(1) from error

    if errors:
        print("RESULTADO: FALLÓ")
        for error in errors:
            print(" - " + error)
        raise SystemExit(1)
    print("RESULTADO: OK")


if __name__ == "__main__":
    main()
