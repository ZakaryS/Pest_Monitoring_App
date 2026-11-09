// Karma settings for `ng test`. The CI pipeline runs `npm run test:ci`, which uses
// ChromeHeadlessCI and writes JUnit results and Cobertura coverage for Azure Pipelines.
const path = require('path');

module.exports = function (config) {
  config.set({
    basePath: '',
    frameworks: ['jasmine'],
    plugins: [
      require('karma-jasmine'),
      require('karma-chrome-launcher'),
      require('karma-jasmine-html-reporter'),
      require('karma-coverage'),
      require('karma-junit-reporter'),
    ],
    client: { jasmine: {}, clearContext: false },
    jasmineHtmlReporter: { suppressAll: true },
    coverageReporter: {
      dir: path.join(__dirname, 'coverage'),
      subdir: '.',
      // cobertura: Azure Pipelines coverage tab, lcovonly: SonarCloud
      reporters: [{ type: 'html' }, { type: 'text-summary' }, { type: 'cobertura' }, { type: 'lcovonly', file: 'lcov.info' }],
      check: { global: { statements: 60, lines: 60 } },
    },
    junitReporter: { outputDir: path.join(__dirname, 'test-results'), outputFile: 'junit.xml', useBrowserName: false },
    reporters: ['progress', 'kjhtml', 'junit'],
    browsers: ['Chrome'],
    customLaunchers: { ChromeHeadlessCI: { base: 'ChromeHeadless', flags: ['--no-sandbox'] } },
    restartOnFileChange: true,
  });
};
