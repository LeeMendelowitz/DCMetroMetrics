'use strict';

describe('Service: directory', function () {

  // load the service's module
  beforeEach(module('dcmetrometricsApp'));

  // instantiate service
  var directory;
  beforeEach(inject(function (_directory_) {
    directory = _directory_;
  }));

  it('should do something', function () {
    expect(!!directory).toBe(true);
  });

});
