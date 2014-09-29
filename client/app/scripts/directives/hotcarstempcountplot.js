'use strict';

/**
 * @ngdoc directive
 * @name dcmetrometricsApp.directive:hotcarstempcountplot
 * @description
 * # hotcarstempcountplot
 */
angular.module('dcmetrometricsApp')
  .directive('hotcarstempcountplot', ['hotCarDirectory', '$compile', '$rootScope', function (hotCarDirectory, $compile, $rootScope) {
    return {

      template: '<div class="dcmm-chart"></div>',
      restrict: 'E',
      link: function postLink(scope, element, attrs) {

        var totalWidth = 700;
        var totalHeight = 700;

        var brushDim = {top: 10, mainHeight : 100};
        var lineDim = {top: 150, mainHeight: 200};
        var scatterDim = {top: 400, mainHeight: 200};
        
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
        var scatterCircles; // to be defined when circles are drawn

        var xAxis = d3.svg.axis().scale(x).orient("bottom"),
            xAxis2 = d3.svg.axis().scale(x2).orient("bottom"),
            yAxis = d3.svg.axis().scale(y).orient("left"),
            yAxisTemp = d3.svg.axis().scale(yTempScale).orient("right").ticks(10),
            xAxisScatter  = d3.svg.axis().scale(xScatter).orient("bottom"),
            yAxisScatter = d3.svg.axis().scale(yScatter).orient("left");      

        var brush = d3.svg.brush()
          .x(x2)
          .clamp(true)
          .on("brushstart", function() {
            console.log('brush start!');
          })
          .on("brushend", brushended)
          .on("brush", brushed);

        function brushed() {
            console.log("brushed!")
            var e = brush.extent();

            x.domain(brush.empty() ? x2.domain() : e);

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

            // Apply classes to the relevant points in the scatter plot
            if( brush.empty() ) {
              console.log("showing all points: ");
              scatterCircles.classed("scatter-hidden", false);

            } else {
              // Hide scatter points outside of the date range.
              console.log('hiding some points');
              scatterCircles.classed("scatter-hidden", function(d) {
                var startDay = e[0], endDay = e[1];
                return d.day < startDay || d.day > endDay;
              });
            }
            
        }    

        function brushended() {

          console.log("brush end!")
          console.log('source event: ', d3.event.sourceEvent);
          
          var extent0 = brush.extent(),
              extent1 = extent0.map(d3.time.day.round);

          console.log('extent0: ', extent0);
          console.log('extent1: ', extent1);

          // if empty when rounded, use floor & ceil instead
          if (!brush.empty() && extent1[0] >= extent1[1]) {
            extent1[0] = d3.time.day.floor(extent0[0]);
            extent1[1] = d3.time.day.ceil(extent0[1]);
          }

          if (!d3.event.sourceEvent) return; // only transition after input.

          if (brush.empty()){

            d3.select(this).transition()
              .call(brush.event); // This will trigger the brushstart, brush, and brushend events

          } else {

            d3.select(this).transition()
              .call(brush.extent(extent1))
              .call(brush.event); // This will trigger the brushstart, brush, and brushend events
          }

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

        // Angular template!
        var tooltipHtml = '\
        <table class="table table-striped table-bordered table-condensed">\
          <tr><th>Date</th><td>{{ d.day | date : "EEE M/d/yy" }}</td></tr>\
          <tr><th>Temperature:</th><td>{{ d.temp }}&deg;</td></tr>\
          <tr><th>Report Count:</th><td>{{ d.count }}</td></tr>\
        </table>';

        var tLink = $compile(tooltipHtml);
        var iScope = $rootScope.$new(true);
        var t = tLink(iScope);
        tooltipDiv.html("");
        $(tooltipDiv[0][0]).append(t);

        // This is the area that allows brushing
        var context = svg.append("g")
          .attr("class", "context")
          .attr("transform", "translate(" + margin2.left + "," + margin2.top + ")");

        var scatter = svg.append("g")
          .attr("class", "scatter")
          .attr("transform", "translate(" + marginScatter.left + "," + marginScatter.top + ")");

        // Style the selection according to the default styles
        function scatterDefault(selection) {

          selection
            .attr("r", 2)
            .classed('focused', false)
            .style("fill", function(d) { return colorScatter(d.year); });

        }

        // Style the selection according to the focused styles.
        function scatterFocused(selection) {

          selection
            .attr("r", 4)
            .classed('focused', true);

        }

        hotCarDirectory.get_daily_data().then( function(data) {
          
          var dailyData = data.daily_series;

          // Massage data for d3
          dailyData.forEach(function(d) {
            d.day = parseDate(d.day);
            d.temp = d.temp ? +d.temp : null;
            d.count = +d.count;
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
            .call(scatterDefault);

          scatterCircles = scatter.selectAll("circle");

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
            .text("Daily Report Count");

          scatter.append("text")
            .attr("y", heightScatter)
            .attr("x", width / 2)
            .attr("dy", "2.5em")
            .style("text-anchor", "middle")
            .text("Temperature");

          function drawScatterLegend() {

            // Get sorted unique values for years
            var years = d3.set(dailyData.map(function(d) { return d.year; }))
              .values()
              .sort(d3.ascending);

            var legendData = years.map(function(y) {
              return {value: y,
                      color: colorScatter(y)};
            });

            var lineHeight = 20;

            var scatterLegend = scatter.append("g")
              .attr("transform", "translate(10,0)");

            scatterLegend  
              .append("rect")
              .attr("class", "legend-frame")
              .attr("width", 100)
              .attr("height", 10 + 10 + legendData.length * lineHeight);

            var legendItems = scatterLegend
              .selectAll("g.legend-item")
              .data(legendData)
              .enter()
              .append("g")
              .attr("class", "legend-item")
              .attr("transform", function(d, i) {
                return "translate(0," + (i+1)*lineHeight + ")";
              });

            legendItems
              .append("circle")
              .attr("r", 5)
              .attr("cx", "1em")
              .attr("cy", 0)
              .style("fill", function(d, i) { return d.color; });

            legendItems
              .append("text")
              .text(function(d, i) {
                return d.value;
              })
              .attr('x', 0)
              .attr('dx', "2em")
              .attr('y', 0)
              .attr('dy', '0.3em')
              .attr('text-anchor', 'left')

          }

          drawScatterLegend();

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

                  scatter.selectAll('circle.focused').call(scatterDefault);

              })
              .on("mousemove", mousemove);                       // **********






          function mousemove() {    
                                 
            var tempTrackerPos, countTrackerPos;   // **********
            
            var x0 = x.invert(d3.mouse(this)[0]),              // **********
                i = bisectDate(dailyData, x0, 1),                   // **********
                d0 = dailyData[i - 1],                              // **********
                d1 = dailyData[i],                                  // **********
                d = x0 - d0.day > d1.day - x0 ? d1 : d0;     // **********

            focus.select("circle.countTracker")                           // **********
                .attr("transform",                             // **********
                      "translate(" + x(d.day) + "," +         // **********
                                     y(d.count) + ")");        // **********

            focus.select("circle.tempTracker")                           // **********
                .attr("transform",                             // **********
                      "translate(" + x(d.day) + "," +         // **********
                                     yTempScale(d.temp) + ")");        // **********
 

            var yCountText = y(d.count);
            var yTempText = yTempScale(d.temp);

            var minSpacing = 40;
            
            // Fix the spacing between them:
            if (Math.abs(yCountText - yTempText) < minSpacing) {
              if (yCountText < yTempText) {
                yCountText = yTempText - minSpacing;
              } else {
                yTempText = yCountText - minSpacing;
              }
            }

            // Reset styles on any points that are already focused
            scatter.selectAll('circle.focused').call(scatterDefault);

            // Find the data point in the scatterplot and style it!
            scatterCircles.filter(function(ptData) {
              return ptData.day === d.day;
            }).call(scatterFocused);


            tempTrackerPos = tempTracker[0][0].getBoundingClientRect();
            countTrackerPos = countTracker[0][0].getBoundingClientRect();

            // Update the data on the scope to update the tooltip.
            iScope.$apply(function() {
              iScope.d = d;
            });

            //tooltipDiv.html(d.day.toDateString() + "<br>" + d.temp + "F<br>" + d.count + " report" + (d.count !== 1 ? "s" : ""))  
                
            tooltipDiv
                .style("left", (tempTrackerPos.left + window.pageXOffset + 30) + "px")     
                .style("top", (d3.min([tempTrackerPos.top, countTrackerPos.top]) + window.pageYOffset)  + "px");     

            // tooltipDiv.transition().duration(200)    
            //     .style("opacity", .9);  
            tooltipDiv.style("opacity", 0.9);  


          } 






        });



      }, // end link
      replace: true

    };
  }]);
