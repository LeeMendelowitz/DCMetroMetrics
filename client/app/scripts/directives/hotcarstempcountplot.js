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
        var totalHeight = 1000;

        var brushDim = {top: 10, mainHeight : 100};
        var lineDim = {top: 150, mainHeight: 300};
        var scatterDim = {top: 650, mainHeight: 300};
        
        var margin = {top: lineDim.top, right: 50, bottom: totalHeight - (lineDim.top + lineDim.mainHeight), left: 50},
            margin2 = {top: brushDim.top, right: 50, bottom: totalHeight - (brushDim.top + brushDim.mainHeight), left: 50},
            marginScatter = {top: scatterDim.top, right: 50, bottom: totalHeight - (scatterDim.top + scatterDim.mainHeight), left: 50},
            width = totalWidth - margin.left - margin.right,
            height = totalHeight - margin.top - margin.bottom,
            height2 = totalHeight - margin2.top - margin2.bottom,
            heightScatter = totalHeight - marginScatter.top - marginScatter.bottom;

      

        var parseDate = d3.time.format("%Y-%m-%d").parse;
        var bisectDate = d3.bisector(function(d) { return d.day; }).left; // Finds value in sorted array

        var x = d3.time.scale().range([0, width]),
            x2 = d3.time.scale().range([0, width]),
            y = d3.scale.linear().range([height, 0]),
            y2 = d3.scale.linear().range([height2, 0]),
            yTempScale = d3.scale.linear().clamp(true).range([height, 0]),
            xScatter = d3.scale.linear().range([0, width]),
            yScatter = d3.scale.linear().range([heightScatter, 0]);

        var colorScatter = d3.scale.category10();

        var xAxis = d3.svg.axis().scale(x).orient("bottom"),
            xAxis2 = d3.svg.axis().scale(x2).orient("bottom"),
            yAxis = d3.svg.axis().scale(y).orient("left"),
            yAxisTemp = d3.svg.axis().scale(yTempScale).orient("right").ticks(10),
            xAxisScatter  = d3.svg.axis().scale(xScatter).orient("bottom"),
            yAxisScatter = d3.svg.axis().scale(yScatter).orient("left");      

        var brush = d3.svg.brush()
          .x(x2)
          .on("brush", brushed);

        function brushed() {
            x.domain(brush.empty() ? x2.domain() : brush.extent());
            // Re-draw the areas and x axis based on brush.
            lineSvg.select(".x.axis").call(xAxis)
              .selectAll("text")
              .attr("y", 0)
              .attr("x", 0)
              .attr("dx", "0.3em")
              .attr("dy", "1em")
              .attr("transform", "rotate(-30)")
              .style("text-anchor", "end");

            lineSvg.select(".area.count").attr("d", countArea);
            lineSvg.select(".area.temperature").attr("d", tempArea);
            lineSvg.select(".line.count").attr("d", countLine);
            lineSvg.select(".line.temperature").attr("d", temperatureLine);
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
            .interpolate("monotone")
            .x(function(d) { return x(d.day); })
            .y(function(d) { return y(d.count); });

        var temperatureLine = d3.svg.line()
            .interpolate("monotone")
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

        var scatter = svg.append("g")
          .attr("class", "scatter")
          .attr("transform", "translate(" + marginScatter.left + "," + marginScatter.top + ")");

        hotCarDirectory.get_daily_data().then( function(data) {
          
          var dailyData = data.daily_series;

          // Massage data for d3
          dailyData.forEach(function(d) {
            d.day = parseDate(d.day);
            d.temp = d.temp ? +d.temp : null;
            d.count = d.count ? +d.count : null;
            d.year = d.day.getFullYear();
          });


          x.domain(d3.extent(dailyData, function(d) { return d.day; }));
          y.domain(d3.extent(dailyData, function(d) { return d.count; }));
          x2.domain(x.domain());
          y2.domain(y.domain());
          yTempScale.domain([60, d3.max(dailyData, function(d) { return d.temp; })]);
          xScatter.domain(d3.extent(dailyData, function(d) { return d.temp; }));
          yScatter.domain([0, d3.max(dailyData, function(d) { return d.count; })]);
          //yTempScale.domain(d3.extent(dailyData, function(d) { return d.temp; }));

          lineSvg.append("g")
              .attr("class", "x axis")
              .attr("transform", "translate(0," + height + ")")
              .call(xAxis)
              .selectAll("text")
              .attr("y", 0)
              .attr("x", 0)
              .attr("dx", "0.3em")
              .attr("dy", "1em")
              .attr("transform", "rotate(-30)")
              .style("text-anchor", "end");

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
            .datum(dailyData)
            .attr("class", "area temperature")
            .attr('clip-path', 'url(#clip)')
            .attr("d", tempArea);

          lineSvg.append("path")
            .datum(dailyData)
            .attr("class", "line temperature")
            .attr('clip-path', 'url(#clip)')
            .attr("d", temperatureLine);

          // This draws the daily count curve with filled area
          lineSvg.append("path")
            .datum(dailyData)
            .attr("class", "area count")
            .attr('clip-path', 'url(#clip)')
            .attr("d", countArea);

          lineSvg.append("path")
            .datum(dailyData)
            .attr("class", "line count")
            .attr('clip-path', 'url(#clip)')
            .attr("d", countLine);

          context.append("path")
            .datum(dailyData)
            .attr("class", "area")
            .attr('clip-path', 'url(#clip)')
            .attr("d", countArea2);

          context.append("g")
              .attr("class", "x axis")
              .attr("transform", "translate(0," + height2 + ")")
              .call(xAxis2)
              .selectAll("text")
              .attr("y", 0)
              .attr("x", 0)
              .attr("dx", "0.3em")
              .attr("dy", "1em")
              .attr("transform", "rotate(-30)")
              .style("text-anchor", "end");

          context.append("g")
              .attr("class", "x brush")
              .call(brush)
            .selectAll("rect")
              .attr("y", -6)
              .attr("height", height2 + 7);


          scatter.append("g")
            .selectAll("circle")
            .data(dailyData)
            .enter()
            .append("circle")
            .attr("class", "scatter")
            .attr("cx", function(d) { return xScatter(d.temp + (Math.random() * .4)); })
            .attr("cy", function(d) { return yScatter(d.count + (Math.random() * .4)); })
            .attr("r", 2)
            .style("fill", function(d) { return colorScatter(d.year); });

          scatter.append("g")
              .attr("class", "x axis")
              .attr("transform", "translate(0," + heightScatter + ")")
              .call(xAxisScatter);

          scatter.append("g")
            .attr("class", "y axis")
            .call(yAxisScatter);

          scatter.append("text")
            .attr("transform", "rotate(-90)")
            .attr("y", 0 - marginScatter.left)
            .attr("x",0 - (heightScatter / 2))
            .attr("dy", "1em")
            .style("text-anchor", "middle")
            .text("Daily Reports");

          scatter.append("text")
            .attr("y", heightScatter + marginScatter.bottom)
            .attr("x", width / 2)
            .attr("dy", "-1em")
            .style("text-anchor", "middle")
            .text("Temperature");

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
                i = bisectDate(dailyData, x0, 1),                   // **********
                d0 = dailyData[i - 1],                              // **********
                d1 = dailyData[i],                                  // **********
                dCount = x0 - d0.day > d1.day - x0 ? d1 : d0;     // **********

            i = d3.min([bisectDate(dailyData, x0, 1), dailyData.length -1]);                 // **********
            d0 = dailyData[i - 1];                            // **********
            d1 = dailyData[i];                                  // **********
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
