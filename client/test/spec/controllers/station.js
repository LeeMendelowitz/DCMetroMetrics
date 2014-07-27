'use strict';

describe('Controller: StationCtrl', function () {

  // load the controller's module
  beforeEach(module('dcmetrometricsApp'));

  var StationCtrl,
    scope;

  // Initialize the controller and a mock scope
  beforeEach(inject(function ($controller, $rootScope) {
    scope = $rootScope.$new();
    StationCtrl = $controller('StationCtrl', {
      $scope: scope
    });
  }));

  it('should attach a list of awesomeThings to the scope', function () {
    expect(scope.awesomeThings.length).toBe(3);
  });
});
