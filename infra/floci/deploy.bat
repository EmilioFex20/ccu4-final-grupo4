@echo off
set AWS_ENDPOINT_URL=http://localhost:4566
set AWS_DEFAULT_REGION=us-east-1
set AWS_ACCESS_KEY_ID=test
set AWS_SECRET_ACCESS_KEY=test

for %%s in (postgres redis api web) do (
  aws ecs register-task-definition --cli-input-json file://infra/floci/%%s-task.json >nul
  aws ecs create-service --cluster cafeteria --service-name %%s --task-definition cafeteria-%%s --desired-count 1 >nul
  echo Servicio %%s creado
  if "%%s"=="redis" timeout /t 10 >nul
)