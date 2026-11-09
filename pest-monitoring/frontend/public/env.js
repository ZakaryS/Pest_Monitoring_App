// Runtime settings for the deployed app (Part 3, Task 2).
// The release pipeline overwrites this file for each environment, so the same build
// can be deployed to test and production with different API addresses.
window.__env = { apiUrl: '/api', azureMapsKey: '' };