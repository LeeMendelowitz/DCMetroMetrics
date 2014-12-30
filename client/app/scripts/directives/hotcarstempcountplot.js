'use strict';

/**
 * @ngdoc directive
 * @name dcmetrometricsApp.directive:hotcarstempcountplot
 * @description
 * # hotcarstempcountplot
 */

/*
  LMM: Warning: this directive is a complete mess and hard to work with. Would be better
  to use Angular controllers to manage state. Instead, this directive is built in a "non-Angular" way
  as one massive complicated D3 script. You've been warned.
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
        var scatterCircles, // to be defined when circles are drawn
            scatterCoords = []; // An array of [x,y] for Report Count vs. Day scatter.
        var dailyData = [], dailyDataInView = [];

        var xAxis = d3.svg.axis().scale(x).orient("bottom"),
            xAxis2 = d3.svg.axis().scale(x2).orient("bottom"),
            yAxis = d3.svg.axis().scale(y).orient("left"),
            yAxisTemp = d3.svg.axis().scale(yTempScale).orient("right").ticks(10),
            xAxisScatter  = d3.svg.axis().scale(xScatter).orient("bottom"),
            yAxisScatter = d3.svg.axis().scale(yScatter).orient("left");      

        var brush = d3.svg.brush()
          .x(x2)
          .clamp(true)
          .on("brushend", brushended)
          .on("brush", brushed);


        function brushed() {

            var scatterPtsNode = scatterPts[0][0];
            var e = brush.extent();

            x.domain(brush.empty() ? x2.domain() : e);
            var domain = x.domain();

            // Select the dailyData that is in view.
            // console.log("brushed. Domain: ", domain);

            dailyDataInView = dailyData.filter(function(d) {
              return d.day >= domain[0] && d.day <= domain[1];
            });
            drawVoronoi(dailyDataInView);

            

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

              scatterCircles.classed("scatter-hidden", false);

            } else {

              // Hide scatter points outside of the date range.

              scatterCircles.classed("scatter-hidden", function(d) {
                var startDay = e[0], endDay = e[1];
                return d.day < startDay || d.day > endDay;
              });

              // Move scatterCircles that are in view to the "top" by appending.
              // This will move them in the DOM.
              scatterCircles.filter(function(d) {
                var startDay = e[0], endDay = e[1];
                return d.day >= startDay && d.day <= endDay;
              }).each(function(d,i) {
                scatterPtsNode.appendChild(this);
              })


            }
        }    

        function brushended() {

          // Round the brush extent to the nearest day.

          var extent0 = brush.extent(),
              extent1 = extent0.map(d3.time.day.round);

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


        // On the scatter plot, we use hidden voronoi polygons to focus on the 
        // closest scatter point.
        // This class assists in showing/hiding the focus.
        // NOTE: It's not necessary to use this provided we don't transition/fade the
        // tooltip. Browsers seems to handle a path exit before entering another.
        // var scatterFocusTracker = (function() {

        //   var curPoint;
        //   var num_enters = 0;
        //   var num_exits = 0;

        //   return {

        //     handle_exit: function(point) {
        //       num_exits += 1;
        //       console.log("handle_exit: ", curPoint === point, num_exits);
        //       console.log(d3.select(point).datum().point);

        //       if (point !== curPoint) {
        //         // Some other point is active, so don't do anything with
        //         // respect to showing/hiding tooltips
        //         return;
        //       }

        //       // We must hide the focus.
        //       curPoint = null;

        //       focus.style("display", "none");

        //       // Fadeout the tooltip
        //       tooltipDiv.style("opacity", 0.0);

        //       scatterPts.selectAll('circle.focused').call(scatterDefault);

        //     },

        //     handle_enter: function(point) {

        //       num_enters += 1;
        //       console.log("handle_enter: ", curPoint === point, num_enters);
        //       console.log(d3.select(point).datum().point);

        //       curPoint = point;

        //       // Show the focus element
        //       focus.style("display", null);



        //     }

        //   };

        // }());

        // Draw voronoi paths
        function drawVoronoi(dailyDataInView) {

          var polygon = function(d) {
            // console.log("polygon d: ", d);
            return "M" + d.join("L") + "Z";
          }

          // Set functions for accessing the x & y coordinates from data.
          voronoi.x(function(d) {
            return d.xScatter;
          }).y(function(d) {
            return d.yScatter;
          });

          // console.log("voronoi entries before processing: ", dailyDataInView.filter(function(d) { return d.temp !== null; }));

          // Use d3.nest to remove duplicate scatter points before calling Voronoi.
          // Using voronoi with conincident scatter points will cause problems.
          var unique_data = d3.nest()
              .key(function(d) { return d.xScatter + "," + d.yScatter; })
              .rollup(function(v) { return v[0]; })
              .entries(dailyDataInView.filter(function(d) { return d.temp !== null; })) // This concludes the nest part
              .map(function(d) { return d.values; }) // This extracts the unique values from the nest operation.

          var vData = voronoi(unique_data);

          var lbefore = vData.length;
          vData = vData.filter(function(d) {
              return (d.length > 0) && angular.isDefined(d.point);
            });

          var lafter = vData.length;

          // console.log("vdata filter. length before: ", lbefore, " length after: ", lafter);
          // console.log("vData: ", vData);

          // Join data on the voronoi polygon paths.
          // We use the polygon as the key function.
          // The voronoi geom will assign the data
          // it computes the voronoi path from as the "point" attribute on the array.
          // For eaxmple, see the use of ".datum(function(d) { return d.point; })" 
          // here: http://bl.ocks.org/mbostock/8033015
          //
          // Example of d.point:
          // { count: 7
          //      dateString: "2013--5-28",
          //      day: [date object],
          //      scatterPt: [circle svg element],
          //      temp: 85,
          //      xScatter: 495.0,
          //      yScatter: 173.58,
          //      year: 2013
          //    
          var paths = voronoiPath.selectAll("path").data(vData, polygon);

          // Remove paths which have been deleted
          paths.exit().remove();

          // Add new paths.
          paths.enter().append("path")
              .attr("class", "voronoi")
              .attr("d", function(d) {
                // Compute the polygon from the voronoi data
                return polygon(d);
              });

          paths.on("mouseover" , function(d) {

            // scatterFocusTracker.handle_enter(this);

            // Show the focus element
            focus.style("display", null);

            d3.select(this).classed("voronoi--hover", true);
            focusScatterPt(d.point);

            // Populate the tooltip 
            // Set the locations of the countTracker, tempTracker, and lineTracker
            setLinePlotTracker(d.point, x(d.point.day), y(d.point.count), yTempScale(d.point.temp));

            var tempTrackerPos = tempTrackerElem.getBoundingClientRect();
            var countTrackerPos = countTrackerElem.getBoundingClientRect();

            // Update the data on the scope to update the tooltip.
            tooltipScope.$apply(function() {
              tooltipScope.d = d.point;
            });
                
            tooltipDiv
                .style("left", (tempTrackerPos.left + window.pageXOffset + 30) + "px")     
                .style("top", (d3.min([tempTrackerPos.top, countTrackerPos.top]) + window.pageYOffset)  + "px");     
  
            tooltipDiv.style("opacity", 0.9);  


          }).on("mouseout", function() {
            // scatterFocusTracker.handle_exit(this);

            focus.style("display", "none");

            // Fadeout the tooltip
            tooltipDiv.style("opacity", 0.0);

            scatterPts.selectAll('circle.focused').call(scatterDefault);
       
          })


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

        var lineSvgRoot = mainSvg.append("g");
        var lineSvg = lineSvgRoot.append("g");

        // Element for showing line data points in focus based on mouse
        var focus = lineSvgRoot.append("g")
          .style("display", "none");  

        // Circle which highlights the active hot car report data point in the line plot          
        var countTracker = focus.append("circle")                                
            .attr("class", "countTracker")                               
            .attr("r", 4);  

        var countTrackerElem = countTracker[0][0];

        // Circle which highlights the active temperature data point in the line plot
        var tempTracker = focus.append("circle")                                
            .attr("class", "tempTracker")                               
            .attr("r", 4);

        var tempTrackerElem = tempTracker[0][0];      

        // Line which shows the actively selected day in the line plot
        var lineTracker = focus.append("line")
          .attr("class", "lineTracker")
          .attr("x1", 0)
          .attr("y1", 0)
          .attr("x2", 0)
          .attr("y2", height);

        //////////////////////////////////////////////////
        // Show the tracker line in the line series plot.
        function setLinePlotTracker(datum, xCount, yCount, yTemp) {
          // console.log("setLinePlotTracker: ", datum, xCount, yCount, yTemp);
          focus.datum(datum);
          focus.attr("transform", "translate(" + xCount + ",0)");
          countTracker.attr("transform",                            
                    "translate(0, " + yCount + ")");       
          tempTracker.attr("transform", "translate(0, " + yTemp + ")");       
              
        }



        // Append a tooltip to the body
        var tooltipDiv = d3.select("body").append("div")   
          .attr("class", "hotcars-tooltip")               
          .style("opacity", 0);




        // Angular template!
        var tooltipHtml = '\
        <table class="table table-striped table-bordered table-condensed">\
        <!-- <table class="table-striped"> -->\
          <tr><th>Date</th><td>{{ d.day | date : "EEE M/d/yy" }}</td></tr>\
          <tr><th>Temperature</th><td>{{ d.temp }}&deg;</td></tr>\
          <tr><th>Report Count</th><td>{{ d.count }}</td></tr>\
        </table>';

        // Compile the tooltip html and link it with a new
        // scope.
        var tooltipLink = $compile(tooltipHtml);
        var tooltipScope = $rootScope.$new(true);
        var tooltipElem = tooltipLink(tooltipScope);
        tooltipDiv.html("");
        $(tooltipDiv[0][0]).append(tooltipElem);

        // This is the area that allows brushing
        var context = svg.append("g")
          .attr("class", "context")
          .attr("transform", "translate(" + margin2.left + "," + margin2.top + ")");

        // This is the scatter plot of number of reports vs daily temperature
        var scatter = svg.append("g")
          .attr("class", "scatter")
          .attr("transform", "translate(" + marginScatter.left + "," + marginScatter.top + ")");

        var voronoi = d3.geom.voronoi().clipExtent([[0, 0], [width, heightScatter]]);
        var scatterPts = scatter.append("g");
        var scatterAxes = scatter.append("g");
        var voronoiPath = scatter.append("g");

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

        //////////////////////////////////////////////////
        // Focus on a point in the scatter plot.
        // Select the point based on its data.
        function focusScatterPt(ptData) {

          // Reset styles on any points that are already focused
          scatterPts.selectAll('circle.focused').call(scatterDefault);

          // Find the data point in the scatterplot and style it!
          d3.select(ptData.scatterPt).call(scatterFocused);

          // Show the tooltip


        }

        
        hotCarDirectory.get_daily_data().then( function(data) {
          
          ////////////////////////////////////////////////
          // Extract and process data
          dailyData = data.daily_series;

          // Massage data for d3
          dailyData.forEach(function(d) {

            d.dateString = d.day;
            d.day = parseDate(d.day);
            d.temp = d.temp ? +d.temp : null;
            d.count = +d.count;
            d.year = d.day.getFullYear();

          });

          dailyDataInView = dailyData;

          x.domain(d3.extent(dailyData, function(d) { return d.day; }));
          y.domain(d3.extent(dailyData, function(d) { return d.count; }));
          x2.domain(x.domain());
          y2.domain(y.domain());
          yTempScale.domain([60, d3.max(dailyData, function(d) { return d.temp; })]);
          xScatter.domain(d3.extent(dailyData, function(d) { return d.temp; }));
          yScatter.domain([0, d3.max(dailyData, function(d) { return d.count; })]);
          //yTempScale.domain(d3.extent(dailyData, function(d) { return d.temp; }));

          // Compute the scatter coordinates. Add some jitter.
          dailyData.forEach(function(d) {
            d.xScatter = xScatter(d.temp);
            d.yScatter = yScatter(d.count);
          });

          ////////////////////////////////////////////////////////////
          // Draw line graph

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
              .attr("class", "y axis count")
              .call(yAxis)
              .append("text")
              .attr("transform", "rotate(-90)")
              .attr("y", 0 - margin.left)
              .attr("x",0 - (height / 2))
              .attr("dy", "1em")
              .style("text-anchor", "middle")
              .text("Daily Report Count");


          lineSvg.append("g")
            .attr("class", "y axis temperature")
            .attr("transform", "translate(" + width + ",0)")
            .call(yAxisTemp)
            .append("text")
            .attr("transform", "rotate(90)")
            .attr("y", 0 - margin.right)
            .attr("x", 0 + (height / 2))
            .attr("dy", "1em")
            .style("text-anchor", "middle")
            .text("Temperature");
            // .append("text")
            //   .attr("transform", "rotate(-90)")
            //   .attr("y", 6)
            //   .attr("dy", "-1em")
            //   .style("text-anchor", "end")
            //   .text("Temperature");

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


          ///////////////////////////////////////////////////
          // Draw scatter

          scatterPts
            .selectAll("circle")
            .data(dailyData.filter(function(d){ return d.temp !== null; }))
            .enter()
            .append("circle")
            .attr("class", "scatter")
            .attr("cx", function(d) { return d.xScatter; })
            .attr("cy", function(d) { return d.yScatter; })
            .attr("id", function(d) { return d.dateString; })
            .datum( function(d) { 
              d.scatterPt = this; // Little trick to add the scatterPoint to the dailyData.
              return d;
            })
            .call(scatterDefault);

          scatterCircles = scatterPts.selectAll("circle");

          
          drawVoronoi(dailyDataInView);
          

          scatterAxes.append("g")
              .attr("class", "x axis")
              .attr("transform", "translate(0," + heightScatter + ")")
              .call(xAxisScatter);

          scatterAxes.append("g")
            .attr("class", "y axis")
            .call(yAxisScatter);

          scatterAxes.append("text")
            .attr("transform", "rotate(-90)")
            .attr("y", 0 - marginScatter.left)
            .attr("x",0 - (heightScatter / 2))
            .attr("dy", "1em")
            .style("text-anchor", "middle")
            .text("Daily Report Count");

          scatterAxes.append("text")
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

            var scatterLegend = scatterAxes.append("g")
              .attr("transform", "translate(10,0)");

            // scatterLegend  
            //   .append("rect")
            //   .attr("class", "legend-frame")
            //   .attr("width", 100)
            //   .attr("height", 10 + 10 + legendData.length * lineHeight);

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




                                                
          // append the rectangle to capture mouse              
          lineSvgRoot.append("rect")                                    
              .attr("width", width)                             
              .attr("height", height)                           
              .style("fill", "none")                            
              .style("pointer-events", "all")                   
              .on("mouseover", function() { 
                  focus.style("display", null);
              })
              .on("mouseout", function() {


                  focus.style("display", "none");

                  // Fadeout the tooltip
                  tooltipDiv.style("opacity", 0.0);

                  scatterPts.selectAll('circle.focused').call(scatterDefault);

              })
              .on("mousemove", mousemoveLinePlot);                  


          //////////////////////////////////////////////////
          function mousemoveLinePlot() {    
                                 
            var tempTrackerPos, countTrackerPos;  
            
            var x0 = x.invert(d3.mouse(this)[0]),             
                i = bisectDate(dailyDataInView, x0, 1),                  
                d0 = dailyDataInView[i - 1],                             
                d1 = dailyDataInView[i],                                 
                d = x0 - d0.day > d1.day - x0 ? d1 : d0;    

            // Set the locations of the countTracker, tempTracker, and lineTracker
            setLinePlotTracker(d, x(d.day), y(d.count), yTempScale(d.temp));
            focusScatterPt(d);


            tempTrackerPos = tempTrackerElem.getBoundingClientRect();
            countTrackerPos = countTrackerElem.getBoundingClientRect();

            // Update the data on the scope to update the tooltip.
            tooltipScope.$apply(function() {
              tooltipScope.d = d;
            });
                
            tooltipDiv
                .style("left", (tempTrackerPos.left + window.pageXOffset + 30) + "px")     
                .style("top", (d3.min([tempTrackerPos.top, countTrackerPos.top]) + window.pageYOffset)  + "px");     
  
            tooltipDiv.style("opacity", 0.9);  

          } 



        });



      }, // end link
      replace: true

    };
  }]);
