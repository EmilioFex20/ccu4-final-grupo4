import argparse
import json
import os

from aws_config import BUDGET_FILE, find_exposed_credentials, load_json, render_budget, validate_budget

BUDGET_NAME = "ccu4-final-grupo4-mensual-1usd"


def parse_args():
    parser = argparse.ArgumentParser(description="Configura el presupuesto AWS de 1 USD con notificaciones.")
    parser.add_argument("--email", default=os.environ.get("AWS_BUDGET_EMAIL"), help="correo para las alertas")
    parser.add_argument("--apply", action="store_true", help="crea el presupuesto en AWS (por defecto solo simula)")
    parser.add_argument("--profile", default=None, help="perfil de AWS CLI a utilizar")
    return parser.parse_args()


def main():
    args = parse_args()
    document = load_json(BUDGET_FILE)
    errors = validate_budget(document, require_email=False) + find_exposed_credentials(document)
    if errors:
        print("Validación fallida:")
        for error in errors:
            print(" - " + error)
        raise SystemExit(1)

    if not args.email:
        print("Se requiere --email o la variable AWS_BUDGET_EMAIL para las notificaciones.")
        print("MODO SIMULACIÓN: no se realizó ninguna llamada a AWS.")
        rendered = document
    else:
        try:
            rendered = render_budget(document, args.email)
        except ValueError as error:
            print(str(error))
            raise SystemExit(1) from error

    print("Presupuesto validado: 1.00 USD mensual, tipo COST")
    print("Umbrales: ACTUAL 50/80/100 por ciento, FORECASTED 100 por ciento")
    print(f"Nombre: {rendered.get('BudgetName', BUDGET_NAME)}")
    if not args.apply:
        print("MODO SIMULACIÓN: no se realizó ninguna llamada a AWS.")
        return
    if not args.email:
        print("No se puede crear el presupuesto sin correo de notificación.")
        raise SystemExit(1)

    import boto3

    session = boto3.Session(profile_name=args.profile)
    account_id = session.client("sts").get_caller_identity()["Account"]
    session.client("budgets", region_name="us-east-1").create_budget(
        AccountId=account_id,
        Budget=rendered,
    )
    print(f"Presupuesto creado en la cuenta ...{account_id[-4:]}")
    print("AWS Budget solo notifica: NO detiene los gastos ni termina instancias.")


if __name__ == "__main__":
    main()
