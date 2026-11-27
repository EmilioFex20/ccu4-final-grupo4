import argparse
import json

from aws_config import POLICY_FILE, find_exposed_credentials, load_json, validate_policy

POLICY_NAME = "CCU4-Grupo4-MicroOnly-AutoScaler"


def parse_args():
    parser = argparse.ArgumentParser(description="Configura la política IAM de instancias micro.")
    parser.add_argument("--apply", action="store_true", help="crea la política en AWS (por defecto solo simula)")
    parser.add_argument("--policy-name", default=POLICY_NAME, help="nombre de la política IAM")
    parser.add_argument("--profile", default=None, help="perfil de AWS CLI a utilizar")
    return parser.parse_args()


def main():
    args = parse_args()
    document = load_json(POLICY_FILE)
    errors = validate_policy(document) + find_exposed_credentials(document)
    if errors:
        print("Validación fallida:")
        for error in errors:
            print(" - " + error)
        raise SystemExit(1)

    print(f"Política validada localmente: {POLICY_FILE.name}")
    print(f"Nombre a crear: {args.policy_name}")
    print("Tipos permitidos: t2.micro, t3.micro | Región permitida: us-east-1")
    if not args.apply:
        print("MODO SIMULACIÓN: no se realizó ninguna llamada a AWS.")
        return

    import boto3

    session = boto3.Session(profile_name=args.profile)
    response = session.client("iam").create_policy(
        PolicyName=args.policy_name,
        PolicyDocument=json.dumps(document),
        Description="CCU4 Grupo 4: auto-scaler limitado a t2.micro/t3.micro en us-east-1",
    )
    print(f"Política creada: {response['Policy']['Arn']}")
    print("No se adjuntó la política a ningún usuario, grupo ni rol; eso requiere autorización explícita.")


if __name__ == "__main__":
    main()
