// One PestPatrol environment (test or prod) (Part 3, Task 2 and higher grade).
// The pipeline compiles this file to an ARM template (main.json) and deploys it with the
// "ARM template deployment" task.
//
//   App Service plan (Linux)
//     ├── backend Web App   - Django container from Azure Container Registry
//     └── frontend Web App  - Angular build served by pm2 (zip deploy)
//   Log Analytics + Application Insights (Task 3.7 monitoring)

@allowed([
  'test'
  'prod'
])
param environmentName string

param location string = resourceGroup().location

@description('Name of the container registry made by shared.bicep')
param acrName string

@description('Resource group that holds the container registry')
param sharedResourceGroup string

@description('Full image name, e.g. pestpatrolfc2026.azurecr.io/pest-backend:123')
param backendImage string

@description('Build number, shown by /healthz so the pipeline can check the new version is live')
param appVersion string

@secure()
param djangoSecretKey string

@allowed([
  'B1'
  'B2'
  'S1'
])
param appServiceSku string = 'B1'

@description('Password for the demo admin account (user "admin"), used to sign in to /admin/')
@secure()
param demoAdminPassword string

@description('Sightings in 30 days before a HighActivity alert (Task 9.8)')
param alertThreshold int = 10

// Web App names must be unique across Azure, so a short hash of the resource group is added
var suffix = take(uniqueString(resourceGroup().id), 6)
var backendName = 'pestpatrol-api-${environmentName}-${suffix}'
var frontendName = 'pestpatrol-web-${environmentName}-${suffix}'
var tags = {
  project: 'PestPatrol'
  environment: environmentName
}

resource acr 'Microsoft.ContainerRegistry/registries@2023-07-01' existing = {
  name: acrName
  scope: resourceGroup(sharedResourceGroup)
}

resource logs 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: 'log-pestpatrol-${environmentName}'
  location: location
  tags: tags
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

resource insights 'Microsoft.Insights/components@2020-02-02' = {
  name: 'appi-pestpatrol-${environmentName}'
  location: location
  tags: tags
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logs.id
  }
}

resource plan 'Microsoft.Web/serverfarms@2023-12-01' = {
  name: 'asp-pestpatrol-${environmentName}'
  location: location
  tags: tags
  kind: 'linux'
  sku: {
    name: appServiceSku
  }
  properties: {
    reserved: true // required for Linux plans
  }
}

resource backend 'Microsoft.Web/sites@2023-12-01' = {
  name: backendName
  location: location
  tags: tags
  kind: 'app,linux,container'
  properties: {
    serverFarmId: plan.id
    httpsOnly: true
    siteConfig: {
      linuxFxVersion: 'DOCKER|${backendImage}'
      alwaysOn: true
      healthCheckPath: '/healthz'
      ftpsState: 'Disabled'
      minTlsVersion: '1.2'
      http20Enabled: true
    }
  }
}

resource frontend 'Microsoft.Web/sites@2023-12-01' = {
  name: frontendName
  location: location
  tags: tags
  kind: 'app,linux'
  properties: {
    serverFarmId: plan.id
    httpsOnly: true
    siteConfig: {
      linuxFxVersion: 'NODE|22-lts'
      // pm2 serves the static Angular files; --spa sends unknown paths to index.html
      appCommandLine: 'pm2 serve /home/site/wwwroot --no-daemon --spa'
      alwaysOn: true
      ftpsState: 'Disabled'
      minTlsVersion: '1.2'
      http20Enabled: true
    }
  }
}

// App settings are a separate resource so they can use both apps' host names
resource backendSettings 'Microsoft.Web/sites/config@2023-12-01' = {
  parent: backend
  name: 'appsettings'
  properties: {
    WEBSITES_PORT: '8000'
    WEBSITES_ENABLE_APP_SERVICE_STORAGE: 'false'
    DOCKER_REGISTRY_SERVER_URL: 'https://${acr.properties.loginServer}'
    DOCKER_REGISTRY_SERVER_USERNAME: acr.listCredentials().username
    DOCKER_REGISTRY_SERVER_PASSWORD: acr.listCredentials().passwords[0].value
    APP_VERSION: appVersion
    DJANGO_DEBUG: 'false'
    DJANGO_SECRET_KEY: djangoSecretKey
    DJANGO_ALLOWED_HOSTS: '${backend.properties.defaultHostName},localhost,127.0.0.1'
    CORS_ALLOWED_ORIGINS: 'https://${frontend.properties.defaultHostName}'
    APPLICATIONINSIGHTS_CONNECTION_STRING: insights.properties.ConnectionString
    ALERT_THRESHOLD: string(alertThreshold)
    // entrypoint.sh creates this account on first start (App Service settings set here
    // replace any added by hand, so all settings live in this template)
    DJANGO_SUPERUSER_USERNAME: 'admin'
    DJANGO_SUPERUSER_EMAIL: 'admin@pestpatrol.local'
    DJANGO_SUPERUSER_PASSWORD: demoAdminPassword
  }
}

resource frontendSettings 'Microsoft.Web/sites/config@2023-12-01' = {
  parent: frontend
  name: 'appsettings'
  properties: {
    SCM_DO_BUILD_DURING_DEPLOYMENT: 'false' // already built by the pipeline
    APPLICATIONINSIGHTS_CONNECTION_STRING: insights.properties.ConnectionString
  }
}

output backendAppName string = backend.name
output frontendAppName string = frontend.name
output backendUrl string = 'https://${backend.properties.defaultHostName}'
output frontendUrl string = 'https://${frontend.properties.defaultHostName}'