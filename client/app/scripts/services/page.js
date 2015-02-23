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
    var h;
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
      },
      navbarHeight: function() {
        var ret = h || (h = $('.dcmm-navbar').height()); // compute once and cache.
        return ret;
      }

    };

  });
