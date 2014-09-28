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

        var totalWidth = 700;
        var totalHeight = 500;
        
        var margin = {top: 10, right: 40, bottom: 100, left: 40},
            margin2 = {top: 430, right: 40, bottom: 20, left: 40},
            width = totalWidth - margin.left - margin.right,
            height = totalHeight - margin.top - margin.bottom,
            height2 = totalHeight - margin2.top - margin2.bottom;

        var parseDate = d3.time.format("%Y-%m-%d").parse;
        var bisectDate = d3.bisector(function(d) { return d.day; }).left; // Finds value in sorted array

        var x = d3.time.scale().range([0, width]),
            x2 = d3.time.scale().range([0, width]),
            y = d3.scale.linear().range([height, 0]),
            y2 = d3.scale.linear().range([height2, 0]),
            yTempScale = d3.scale.linear().clamp(true).range([height, 0]);

        var xAxis = d3.svg.axis().scale(x).orient("bottom"),
            xAxis2 = d3.svg.axis().scale(x2).orient("bottom"),
            yAxis = d3.svg.axis().scale(y).orient("left"),
            yAxisTemp = d3.svg.axis().scale(yTempScale).orient("right").ticks(10);       

        var brush = d3.svg.brush()
          .x(x2)
          .on("brush", brushed);

        function brushed() {
            x.domain(brush.empty() ? x2.domain() : brush.extent());
            // Re-draw the areas and x axis based on brush.
            lineSvg.select(".area.count").attr("d", countArea);
            lineSvg.select(".x.axis").call(xAxis);
            lineSvg.select(".area.temperature").attr("d", tempArea);
          }    

        var countArea = d3.svg.area()
          .interpolate("monotone")
          .x(function(d) { return x(d.day); })
          .y0(height)
          .y1(function(d) { return y(d.count); });

        var countArea2 = d3.svg.area()
          .interpolate("monotone")
          .x(function(d) { return x2(d.day); })
          .y0(height2)
          .y1(function(d) { return y2(d.count); });

        var tempArea = d3.svg.area()
          .interpolate("monotone")
          .x(function(d) { return x(d.day); })
          .y0(height)
          .y1(function(d) { return yTempScale(d.temp); });

        var countLine = d3.svg.line()
            .x(function(d) { return x(d.day); })
            .y(function(d) { return y(d.count); });

        var temperatureLine = d3.svg.line()
            .x(function(d) { return x(d.day); })
            .y(function(d) { return yTempScale(d.temp); });

        var svg = d3.select(element[0]).append("svg")
            .attr("width", width + margin.left + margin.right)
            .attr("height", height + margin.top + margin.bottom);

        var svgElem = svg[0][0];

        svg.append("defs").append("clipPath")
          .attr("id", "clip")
          .append("rect")
          .attr("width", width)
          .attr("height", height);

        var mainSvg = svg.append("g")
            .attr("class", "line-svg")
            .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

        var lineSvg = mainSvg.append("g");

        var focus = mainSvg.append("g")
          .style("display", "none");  

        // Append a tooltip to the body
        var tooltipDiv = d3.select("body").append("div")   
          .attr("class", "hotcars-tooltip")               
          .style("opacity", 0);

        // This is the area that allows brushing
        var context = svg.append("g")
          .attr("class", "context")
          .attr("transform", "translate(" + margin2.left + "," + margin2.top + ")");

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
          x2.domain(x.domain());
          y2.domain(y.domain());
          yTempScale.domain([60, d3.max(tempData, function(d) { return d.temp; })]);
          //yTempScale.domain(d3.extent(tempData, function(d) { return d.temp; }));

          lineSvg.append("g")
              .attr("class", "x axis")
              .attr("transform", "translate(0," + height + ")")
              .call(xAxis);

          lineSvg.append("g")
              .attr("class", "y axis")
              .call(yAxis)
            .append("text")
              .attr("transform", "rotate(-90)")
              .attr("y", 6)
              .attr("dy", ".71em")
              .style("text-anchor", "end")
              .text("Daily Count");

          lineSvg.append("g")
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
            .attr('clip-path', 'url(#clip)')
            .attr("d", tempArea);

          // lineSvg.append("path")
          //   .datum(tempData)
          //   .classed("line temperature", true)
          //   .attr("d", temperatureLine);

          // This draws the daily count curve with filled area
          lineSvg.append("path")
            .datum(countData)
            .attr("class", "area count")
            .attr('clip-path', 'url(#clip)')
            .attr("d", countArea);

          // lineSvg.append("path")
          //   .datum(countData)
          //   .attr("class", "line")
          //   .attr("d", countLine);

          context.append("path")
            .datum(countData)
            .attr("class", "area")
            .attr("d", countArea2);

          context.append("g")
              .attr("class", "x axis")
              .attr("transform", "translate(0," + height2 + ")")
              .call(xAxis2);

          context.append("g")
              .attr("class", "x brush")
              .call(brush)
            .selectAll("rect")
              .attr("y", -6)
              .attr("height", height2 + 7);


          // append the circle at the intersection               // **********
          var countTracker = focus.append("circle")                                 // **********
              .attr("class", "countTracker")                                // **********
              .attr("r", 4);  

          var tempTracker = focus.append("circle")                                 // **********
              .attr("class", "tempTracker")                                // **********
              .attr("r", 4);       
                                                 // **********
          
          // append the rectangle to capture mouse               // **********
          lineSvg.append("rect")                                     // **********
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

            tooltipDiv.html(dCount.day.toDateString() + "<br>" + dTemp.temp + "F<br>" + dCount.count + " report" + (dCount.count !== 1 ? "s" : ""))  
                .style("left", (tempTrackerPos.left + window.pageXOffset) + "px")     
                .style("top", (d3.min([tempTrackerPos.top, countTrackerPos.top]) + window.pageYOffset - 80)  + "px");     

            // tooltipDiv.transition().duration(200)    
            //     .style("opacity", .9);  
            tooltipDiv.style("opacity", 0.9);  


          } 






        });



      }, // end link
      replace: true

    };
  }]);
