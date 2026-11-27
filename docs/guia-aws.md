# Guía de IAM y AWS Budget · CCU4 Grupo 4

Responsable: Johana (SRE). Alcance: control de seguridad y gasto del Milestone 1.

## Estado de ejecución

Los archivos y scripts están implementados y validados **en modo local**. **No se crearon ni modificaron recursos reales de AWS**: no se ejecutó `--apply`, no se adjuntó la política a usuarios/roles y no se creó el presupuesto. Los permisos de la cuenta siguen intactos.

## Archivos

| Archivo | Contenido |
|---|---|
| `infra/aws/iam-policy-micro-only.json` | Política IAM con Deny explícito de tipos no autorizados y permisos mínimos del auto-scaler |
| `infra/aws/budget.json` | Plantilla de presupuesto de 1.00 USD mensual con 4 notificaciones |
| `infra/aws/setup_iam.py` | Creación reproducible de la política (simulación por defecto) |
| `infra/aws/setup_budget.py` | Creación reproducible del presupuesto (simulación por defecto) |
| `infra/aws/verify.py` | Validación local y, opcionalmente, verificación remota de solo lectura |
| `infra/aws/aws_config.py` | Validaciones compartidas sin dependencias externas |
| `infra/aws/requirements.txt` | `boto3` para los scripts de creación |

## Política IAM

Restricciones:

- `DenyNonMicroInstanceTypes`: bloquea `ec2:RunInstances` si `ec2:InstanceType` no es `t2.micro` o `t3.micro`.
- `DenyMissingInstanceType`: bloquea `ec2:RunInstances` si el tipo no se especifica (evita que el tipo por defecto de la AMI sea otro).
- `DenyResizeToNonMicro`: bloquea `ec2:ModifyInstanceAttribute` hacia tipos no autorizados.
- `DenyOtherRegions`: limita todas las acciones EC2 a `us-east-1`, la región usada por el despliegue local de Floci (`infra/floci/deploy.bat`).
- Permisos concedidos solo a `ec2:*`: lectura de instancias, imágenes, redes y grupos de seguridad, más `RunInstances`, `CreateTags` y `TerminateInstances`. No se conceden IAM, S3, Lambda ni `iam:PassRole`.

### Contrato con el auto-scaler de Emilio

El controller debe llamar a `RunInstances` con el parámetro `InstanceType` explícito (`t2.micro` o `t3.micro`) y en `us-east-1`. Si el controller necesita otro tipo de instancia o región, debe coordinarse con Johana para actualizar la política; no se debe ampliar el permiso de forma unilateral. La política no adjunta perfiles de instancia: si el controller pasa un `IamInstanceProfile`, se requiere revisión adicional.

**No se asume que t2.micro o t3.micro sean gratuitas**: el free tier tiene límites de horas y de región, y el costo depende de la cuenta. El presupuesto es una alerta, no una garantía.

## AWS Budget

- Límite: **1.00 USD por mes**, tipo `COST`, moneda USD.
- Notificaciones reales: `ACTUAL` al 50 %, 80 % y 100 %, y `FORECASTED` al 100 %.
- Destinatario: se toma de `AWS_BUDGET_EMAIL` o de `--email`. La plantilla versionada contiene solo el marcador `__AWS_BUDGET_EMAIL__`; no hay correos ni credenciales reales en el repositorio.
- Un AWS Budget **no detiene los gastos**: solo avisa. La terminación de instancias es responsabilidad del controller de Emilio y debe respetar la regla del README de 5 a 10 minutos de vida.

## Comandos reproducibles

Requisitos: Python 3.10+ y, solamente para las acciones con `--apply`, `boto3` y credenciales AWS configuradas (`aws configure --profile ccu4` o variables de entorno).

```powershell
python -m pip install -r infra/aws/requirements.txt

python infra/aws/verify.py
python infra/aws/setup_iam.py
python infra/aws/setup_budget.py --email tu-correo@ejemplo.com
```

Salida esperada: validaciones locales en verde y el mensaje `MODO SIMULACIÓN: no se realizó ninguna llamada a AWS.`

### Aplicación real (requiere autorización explícita)

```powershell
python infra/aws/setup_iam.py --apply --profile ccu4
$env:AWS_BUDGET_EMAIL = "tu-correo@ejemplo.com"
python infra/aws/setup_budget.py --apply --profile ccu4

python infra/aws/verify.py --live --profile ccu4
```

`--apply` solo **crea** los recursos; la política no se adjunta a ningún principal. `--live` únicamente consulta (`iam:ValidatePolicy`, `budgets:DescribeBudget`, `budgets:DescribeNotificationsForBudget`, `sts:GetCallerIdentity`).

## Criterios de verificación

1. `verify.py` termina con `RESULTADO: OK`.
2. En la consola IAM, la política `CCU4-Grupo4-MicroOnly-AutoScaler` contiene los cuatro `Deny`.
3. En AWS Budgets, el presupuesto `ccu4-final-grupo4-mensual-1usd` muestra 1.00 USD y cuatro notificaciones.
4. Una prueba controlada con `ec2:RunInstances` de `t3.small` debe ser rechazada; una con `t3.micro` debe ser permitida (solo en cuenta de prueba y con autorización).
