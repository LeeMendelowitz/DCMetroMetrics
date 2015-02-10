'use strict';

/**
 * @ngdoc service
 * @name dcmetrometricsApp.Unit
 * @description
 * # Unit
 * Factory in the dcmetrometricsApp.
 */
angular.module('dcmetrometricsApp')
  .factory('Page', function (UnitStatus) {

    var title = "DC Metro Metrics";
    var description = "";

    return {

      title: function(s) {
        title = s || title;
        return title;
      },
      setTitle: function(s) {
        title = s;
      },
      description: function(s) {
        description = s || description;
        return description;
      },
      setDescription: function(s) {
        description = s;
      }

    };

  });
