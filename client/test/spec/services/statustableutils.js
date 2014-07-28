'use strict';

describe('Service: statusTableUtils', function () {

  // load the service's module
  beforeEach(module('dcmetrometricsApp'));

  // instantiate service
  var statusTableUtils;
  beforeEach(inject(function (_statusTableUtils_) {
    statusTableUtils = _statusTableUtils_;
  }));

  it('should do something', function () {
    expect(!!statusTableUtils).toBe(true);
  });

});
