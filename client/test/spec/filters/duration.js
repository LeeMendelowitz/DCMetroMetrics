'use strict';

describe('Filter: duration', function () {

  // load the filter's module
  beforeEach(module('dcmetrometricsApp'));

  // initialize a new instance of the filter before each test
  var duration;
  beforeEach(inject(function ($filter) {
    duration = $filter('duration');
  }));

  it('should return the input prefixed with "duration filter:"', function () {
    var text = 'angularjs';
    expect(duration(text)).toBe('duration filter: ' + text);
  });

});
