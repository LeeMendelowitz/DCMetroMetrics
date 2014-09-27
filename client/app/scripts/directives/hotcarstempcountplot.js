'use strict';

/**
 * @ngdoc directive
 * @name dcmetrometricsApp.directive:hotcarstempcountplot
 * @description
 * # hotcarstempcountplot
 */
angular.module('dcmetrometricsApp')
  .directive('hotcarstempcountplot', ['hotCarDirectory', function (hotCarDirectory) {
    return {

      template: '<div class="dcmm-chart"></div>',
      restrict: 'E',
      link: function postLink(scope, element, attrs) {

        var totalWidth = 960;
        var totalHeight = 500;
        
        var margin = {top: 20, right: 20, bottom: 30, left: 50},
            width = totalWidth - margin.left - margin.right,
            height = totalHeight - margin.top - margin.bottom;

        var parseDate = d3.time.format("%Y-%m-%d").parse;
        var bisectDate = d3.bisector(function(d) { return d.day; }).left; // Finds value in sorted array

        var x = d3.time.scale()
            .range([0, width]);

        var y = d3.scale.linear()
            .range([height, 0]);

        var yTempScale = d3.scale.linear()
            .clamp(true)
            .range([height, 0]);

        var xAxis = d3.svg.axis()
            .scale(x)
            .orient("bottom");

        var yAxis = d3.svg.axis()
            .scale(y)
            .orient("left");

        var yAxisTemp = d3.svg.axis().scale(yTempScale)  // This is the new declaration for the 'Right', 'y1'
            .orient("right").ticks(10);           // and includes orientation of the axis to the right.

        var countArea = d3.svg.area()
          .x(function(d) { return x(d.day); })
          .y0(height)
          .y1(function(d) { return y(d.count); });

        var tempArea = d3.svg.area()
          .x(function(d) { return x(d.day); })
          .y0(height)
          .y1(function(d) { return yTempScale(d.temp); });

        var countLine = d3.svg.line()
            .x(function(d) { return x(d.day); })
            .y(function(d) { return y(d.count); });

        var temperatureLine = d3.svg.line()
            .x(function(d) { return x(d.day); })
            .y(function(d) { return yTempScale(d.temp); });

        var svgRoot = d3.select(element[0]).append("svg")
            .attr("width", width + margin.left + margin.right)
            .attr("height", height + margin.top + margin.bottom);

        var svg = svgRoot.append("g")
            .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

        var svgRootElem = svgRoot[0][0];
        var svgElem = svg[0][0];

        var lineSvg = svg.append("g");

        var focus = svg.append("g")
          .style("display", "none");  

        // Append a tooltip to the body
        var tooltipDiv = d3.select("body").append("div")   
          .attr("class", "hotcars-tooltip")               
          .style("opacity", 0);

        hotCarDirectory.get_daily_data().then( function(data) {
          
          var countData = data.counts;
          var tempData = data.temps;

          // Massage data for d3
          tempData.forEach(function(d) {
            d.day = parseDate(d.day);
            d.temp = +d.temp;
          });

          countData.forEach(function(d) {
            d.day = parseDate(d.day);
            d.count = +d.count;
          });

          x.domain(d3.extent(countData, function(d) { return d.day; }));
          y.domain(d3.extent(countData, function(d) { return d.count; }));
          yTempScale.domain([60, d3.max(tempData, function(d) { return d.temp; })]);
          //yTempScale.domain(d3.extent(tempData, function(d) { return d.temp; }));

          svg.append("g")
              .attr("class", "x axis")
              .attr("transform", "translate(0," + height + ")")
              .call(xAxis);

          svg.append("g")
              .attr("class", "y axis")
              .call(yAxis)
            .append("text")
              .attr("transform", "rotate(-90)")
              .attr("y", 6)
              .attr("dy", ".71em")
              .style("text-anchor", "end")
              .text("Daily Count");

          svg.append("g")
            .attr("class", "y axis")
            .attr("transform", "translate(" + width + ",0)")
            .call(yAxisTemp)
            .append("text")
              .attr("transform", "rotate(-90)")
              .attr("y", 6)
              .attr("dy", "-1em")
              .style("text-anchor", "end")
              .text("Temperature");

          // This draws the daily temperature curve with filled area
          lineSvg.append("path")
            .datum(tempData)
            .classed("area temperature", true)
            .attr("d", tempArea);

          lineSvg.append("path")
            .datum(tempData)
            .classed("line temperature", true)
            .attr("d", temperatureLine);

          // This draws the daily count curve with filled area
          lineSvg.append("path")
            .datum(countData)
            .attr("class", "area")
            .attr("d", countArea);

          lineSvg.append("path")
            .datum(countData)
            .attr("class", "line")
            .attr("d", countLine);


          // append the circle at the intersection               // **********
          var countTracker = focus.append("circle")                                 // **********
              .attr("class", "countTracker")                                // **********
              .attr("r", 4);  

          var tempTracker = focus.append("circle")                                 // **********
              .attr("class", "tempTracker")                                // **********
              .attr("r", 4);       
                                                 // **********
          
          // append the rectangle to capture mouse               // **********
          svg.append("rect")                                     // **********
              .attr("width", width)                              // **********
              .attr("height", height)                            // **********
              .style("fill", "none")                             // **********
              .style("pointer-events", "all")                    // **********
              .on("mouseover", function() { 
                  focus.style("display", null);
              })
              .on("mouseout", function() {

                  focus.style("display", "none");

                  tooltipDiv.transition()        
                    .duration(200)    
                    .style("opacity", 0.0);

              })
              .on("mousemove", mousemove);                       // **********

          function mousemove() {    
                                 
            var tempTrackerPos, countTrackerPos;   // **********
            
            var x0 = x.invert(d3.mouse(this)[0]),              // **********
                i = bisectDate(countData, x0, 1),                   // **********
                d0 = countData[i - 1],                              // **********
                d1 = countData[i],                                  // **********
                dCount = x0 - d0.day > d1.day - x0 ? d1 : d0;     // **********

            i = d3.min([bisectDate(tempData, x0, 1), tempData.length -1]);                 // **********
            d0 = tempData[i - 1];                            // **********
            d1 = tempData[i];                                  // **********
            var dTemp = x0 - d0.day > d1.day - x0 ? d1 : d0;  


            focus.select("circle.countTracker")                           // **********
                .attr("transform",                             // **********
                      "translate(" + x(dCount.day) + "," +         // **********
                                     y(dCount.count) + ")");        // **********

            focus.select("circle.tempTracker")                           // **********
                .attr("transform",                             // **********
                      "translate(" + x(dTemp.day) + "," +         // **********
                                     yTempScale(dTemp.temp) + ")");        // **********

            tempTrackerPos = tempTracker[0][0].getBoundingClientRect();
            countTrackerPos = countTracker[0][0].getBoundingClientRect();

            tooltipDiv.html(dCount.day.toDateString() + "<br>" + dTemp.temp + "F<br>" + dCount.count + " report" + (dCount.count != 1 ? "s" : ""))  
                .style("left", (tempTrackerPos.left + window.pageXOffset) + "px")     
                .style("top", (d3.min([tempTrackerPos.top, countTrackerPos.top]) + window.pageYOffset
                     - 80)  + "px");     

            // tooltipDiv.transition().duration(200)    
            //     .style("opacity", .9);  
            tooltipDiv.style("opacity", .9);  


          }                                                      // **********






        });

      } // end link

    };
  }]);
