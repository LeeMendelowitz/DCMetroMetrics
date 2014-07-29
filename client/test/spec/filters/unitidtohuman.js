'use strict';

describe('Filter: unitIdToHuman', function () {

  // load the filter's module
  beforeEach(module('dcmetrometricsApp'));

  // initialize a new instance of the filter before each test
  var unitIdToHuman;
  beforeEach(inject(function ($filter) {
    unitIdToHuman = $filter('unitIdToHuman');
  }));

  it('should return the input prefixed with "unitIdToHuman filter:"', function () {
    var text = 'angularjs';
    expect(unitIdToHuman(text)).toBe('unitIdToHuman filter: ' + text);
  });

});
