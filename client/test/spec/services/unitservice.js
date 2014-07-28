'use strict';

describe('Service: unitService', function () {

  // load the service's module
  beforeEach(module('dcmetrometricsApp'));

  // instantiate service
  var unitService;
  beforeEach(inject(function (_unitService_) {
    unitService = _unitService_;
  }));

  it('should do something', function () {
    expect(!!unitService).toBe(true);
  });

});
