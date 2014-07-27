'use strict';

describe('Controller: StationdirectoryCtrl', function () {

  // load the controller's module
  beforeEach(module('dcmetrometricsApp'));

  var StationdirectoryCtrl,
    scope;

  // Initialize the controller and a mock scope
  beforeEach(inject(function ($controller, $rootScope) {
    scope = $rootScope.$new();
    StationdirectoryCtrl = $controller('StationdirectoryCtrl', {
      $scope: scope
    });
  }));

  it('should attach a list of awesomeThings to the scope', function () {
    expect(scope.awesomeThings.length).toBe(3);
  });
});
