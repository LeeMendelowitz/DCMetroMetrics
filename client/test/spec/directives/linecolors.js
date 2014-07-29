'use strict';

describe('Directive: lineColors', function () {

  // load the directive's module
  beforeEach(module('dcmetrometricsApp'));

  var element,
    scope;

  beforeEach(inject(function ($rootScope) {
    scope = $rootScope.$new();
  }));

  it('should make hidden element visible', inject(function ($compile) {
    element = angular.element('<line-colors></line-colors>');
    element = $compile(element)(scope);
    expect(element.text()).toBe('this is the lineColors directive');
  }));
});
