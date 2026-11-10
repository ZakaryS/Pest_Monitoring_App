// Shared resources used by every environment (Part 3, higher grade: ARM templates + containers).
// Deployed by the CI pipeline before the backend image is pushed.

@description('Globally unique registry name: 5-50 lowercase letters and numbers, e.g. pestpatrolfc2026')
@minLength(5)
@maxLength(50)
param acrName string

param location string = resourceGroup().location

// Admin user is on so App Service can pull with a username/password. This only needs
// Contributor rights; a managed identity + AcrPull role would need Owner rights to assign.
resource acr 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: acrName
  location: location
  tags: {
    project: 'PestPatrol'
    environment: 'shared'
  }
  sku: {
    name: 'Basic'
  }
  properties: {
    adminUserEnabled: true
  }
}

output loginServer string = acr.properties.loginServer