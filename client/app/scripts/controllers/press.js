'use strict';

/**
 * @ngdoc function
 * @name dcmetrometricsApp.controller:PressCtrl
 * @description
 * # PressCtrl
 * Controller of the dcmetrometricsApp
 */
angular.module('dcmetrometricsApp')
  .controller('PressCtrl', ['$scope', 'Page', function ($scope, Page) {

    Page.title('DC Metro Metrics: Press');
    Page.description('Articles and blog posts about DC Metro Metrics, @MetroEscalators, @MetroElevators, and @MetroHotCars.');


    var Item = function(data) {
      this.date_string = data[0];
      this.publisher = data[1];
      this.url = data[2];
      this.title = data[3];
    };

    var item_data = [

      ["11/21/2014",
      "WAMU 88.5",
      "http://wamu.org/news/14/11/21/despite_replacements_some_of_metro_escalators_spend_more_time_down_than_going_down",
      "Despite Work, Some Metro Escalators Are Down More Often Than Going Down"
      ],


      ["10/29/2014",
      "Greater Greater Washington",
       "http://greatergreaterwashington.org/post/24466/ask-ggw-how-much-pain-will-riders-face-while-metro-replaces-the-bethesda-escalators/",
        "Ask GGW: How much pain will riders face while Metro replaces the Bethesda escalators?"
      ],


      [
        "10/6/2014",
        "Roosevelt Reader",
        "http://www.gwrooseveltinstitute.org/blog/a-little-known-policy-makes-your-metro-trip-tougher",
        "A Little-Known Policy Makes Your Metro Trip Tougher"
        
      ],


      [
        "9/14/2014",
        "dcist",
        "http://dcist.com/2014/09/project_to_replace_metro_escalators.php",
        "Replacement Of Bethesda Metro Escalators Expected To Take Over Two Years"
        
      ],



      [
        "1/6/2014",
        "Mobility Lab",
        "http://mobilitylab.org/2014/01/06/techies-tackle-wmata-data-at-metro-hack-night/",
        "Techies Tackle WMATA Data at Metro Hack Night"
        
      ],


      [
        "12/12/2013",
        "Washington City Paper",
       "http://www.washingtoncitypaper.com/blogs/citydesk/2013/12/12/the-worst-metro-escalators-of-2013/",
        "The Worst Metro Escalators of 2013"
       

      ],


      [
        "9/24/2013",
        "WAMU 88.5",
        "http://m.wamu.org/#/news/13/09/24/phd_students_tracks_ups_and_downs_of_metros_escalators",
        "Maryland Ph.D. Student Tracks Ups And Downs Of Metro's Escalators"
        
      ],

      [
        "9/22/2013",
        "The Transit Wire",
        "http://www.thetransitwire.com/2013/09/22/analyst-questions-wmata-escalator-stats/",
        "Analyst questions WMATA escalator stats"
        
      ],

      [
        "9/13/2013",
        "Unsuck DC Metro",
        "http://unsuckdcmetro.blogspot.com/2013/09/new-transit-grade-escalators-among.html",
        "New, 'Transit Grade' Escalators Among Metro's Worst"
        
      ],

      [
        "9/11/2013",
        "WUSA9",
        "http://www.wusa9.com/news/article/274386/0/Report-94-percent-of-Metro-escalators-are-working",
          "Report: 94 percent of Metro escalators are working"
        
      ],



      [
        "9/20/2013",
        "dcist",
        "http://dcist.com/2013/09/despite_numerous_upgrades_metro_esc.php",
        "Despite Higher Reported Availability, Some Metro Escalator Outages Seemingly Go Unreported"
        
      ],


      [
        "8/21/2013",
        "All Kinds of Currency",
        "http://allkindsofcurrency.com/tag/metro-escalators/",
        "The Metro escalator data you haven’t seen"
        
      ],

      [
        "7/25/2013", 
        "The Washington Post",
        "http://www.washingtonpost.com/blogs/dr-gridlock/wp/2013/07/25/a-programmer-is-giving-metro-a-hand-with-hot-cars/",
        "Programmer gives Metro a hand with hot cars"
        
      ],

      [
        
        "7/19/2013",
        "The Washington Post",
        "http://www.washingtonpost.com/blogs/dr-gridlock/wp/2013/07/19/twitter-and-metros-hot-cars/",
        "Twitter and Metro’s hot cars"
        

      ],

      [
        
        "7/18/2013",
        "WUSA9",
        "http://www.wusa9.com/news/article/266991/158/Help-WUSA9-Report-on-Metro-Hot-Cars-and-Other-Problems-Join-Alfarones-Army",
        "Report Metro Hot Cars and Other Problems. Join WUSA9's Debra Alfarone's Army!"
        

      ],

      [
        
        "5/29/2013",
        "Architect Magazine",
        "http://www.architectmagazine.com/architecture/metro-architect-plans-to-revise-harry-weese-station-design.aspx",
        "Metro Architect Plans to Revise Harry Weese Station Design"

      ],


      [
        
        "5/16/2013",
        "dcist",
        "http://dcist.com/2013/05/a_guide_to_recognizing_your_metro_c.php",
        "A Guide to Recognizing Your Metro Critics"

      ],


      [
        
        "5/3/2013",
        "Unsuck DC Metro",
        "http://unsuckdcmetro.blogspot.com/2013/05/unspinning-metros-escalator-issues.html",
        "Unspinning Metro's Escalator Issues"
        

      ],


      [
        
        "4/10/2013",
        "Unsuck DC Metro",
        "http://unsuckdcmetro.blogspot.com/2013/04/metro-escalator-boss-to-run-rails.html",
       "Metro Escalator Boss To Run Rails"
       

      ],



      [
        
        "4/10/2013",
        "Daily Caller",
        "http://dailycaller.com/2013/04/10/the-guy-in-charge-of-dc-metro-escalators-just-got-promoted/",
        "The guy in charge of DC Metro escalators just got promoted"

      ]
    ];

  var items = item_data.map(function(d) { return new Item(d); });
  $scope.items = items;

}]);