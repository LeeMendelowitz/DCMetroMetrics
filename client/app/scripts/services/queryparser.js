'use strict';

/**
 * @ngdoc service
 * @name dcmetrometricsApp.queryParser
 * @description
 * This was my attempt to build a parser for the filter searchString on the rankings page
 * to add logic for AND, OR, NOT, (), and "". I ended up defining a grammer for PEG.js.
 * I only make use of the matcherFunction function in this service.
 * The rest is dead code as of now.
 */
angular.module('dcmetrometricsApp')
  .service('queryParser', function queryParser() {
    // AngularJS will instantiate a singleton by calling "new" on this function

    // type in "TERM" or "OPERATOR"
    var Record = function(start, end, text) {
      text = text.trim().trim('"').trim("'");
      this.start = start || 0; // inclusive
      this.end = end || 0; // exclusive
      this.text = text || "";
      this.textUpper = text.toUpperCase();
      this.type = ((this.textUpper === "AND") || (this.textUpper === "OR")) ? "OPERATOR" : "TERM";
    };

    Record.prototype = {

      overlaps: function(other) {
        return !((other.end <= this.start) || (this.end <= other.start));
      }, 
      containsPt: function(pt) {
        return (pt >= this.start) && (pt < this.end);
      },
      isSane: function() {
        return (this.start < this.end);
      },
      isOperator: function() {
        return this.type === "OPERATOR";
      },
      isTerm: function() {
        return this.type === "TERM";
      },
      op: function(left, right) {
        if (!this.isOperator) {
          return false;
        }
        if(this.text === "OR") {
          return left || right;
        }
        return left && right;

      },
      // Test if this record is a text match to the query.
      match: function(query) {

        if( this.isOperator() ) {
          return false;
        }

        return query.toUpperCase().indexOf(this.textUpper) >= 0;
      }

    };

    var RecordGroup = function(records) {

      this.terms = [];
      this.operators = [];
      var i, rec;

      for(i = 0; i < records.length; i++) {
        rec = records[i];
        if (rec.isOperator()) {
          this.operators.push(rec);
        } else {
          this.terms.push(rec);
        }
      }

    };

    RecordGroup.prototype = {

      matchText: function(query) {

        var q = String(query);

        var ok, iTerm, iOp, op, term;

        if (this.terms.length === 0) {
          return true;
        }

        if(this.terms.length !== this.operators.length + 1) {
          throw "Operators length and Terms length not compatible";
        }

        // Test the first term.
        term = this.terms[0];
        ok = term.match(q);
        for(iTerm = 1, iOp = 0; iTerm < this.terms.length; iTerm++, iOp++) {
          term = this.terms[iTerm];
          op = this.operators[iOp];
          ok = op.op(ok, term.match(q));
        }

        return ok;

      },

      // Match and object or an array.
      // Return true if any property on the object matches or
      // any property on the array matches
      match : function(thing) {

        var i, n, k, ok;

        ok = false;

        if(angular.isObject(thing)) {

          angular.forEach(thing, function(value, key, obj) {
            if (this.match(value)) {
              ok = true;
            }
          }, this);

        } else {

          // Try to match text
          ok = this.matchText(thing);

        }

        return ok;

      }
    };


    var splitIntoRecords = function(text) {

      text = text.trim(); // Remove leading/trailing whitespace.

      var records = [];

      // Find all phrase records bound by quotes.
      var rec, recText, iLast, j, hasOverlap, curStart;
      var i = text.indexOf('"');
      while(i >= 0) {

        if( curStart !== undefined) {
          // This quote closes a phrase.
          recText = text.substring(curStart+1, i );

          // Include the indices of the quote mark
          rec = new Record(curStart, i+1, recText);
          records.push(rec);
          curStart = undefined;

        } else {
          curStart = i;
        }

        i = text.indexOf('"', i+1);

      }

      // Find all terms bound by spaces. Add non-overlapping
      // records to the list.
      iLast = 0;
      i = text.indexOf(' ', 1);
      if (i < 0) { i = text.length; }
      while(i >= 0 && i <= text.length && iLast < text.length) {

        if(i - iLast >= 1) {

          rec = new Record(iLast, i, text.substring(iLast, i).trim());

          // If this record does not overlap any existing record, add it.
          hasOverlap = false;
          for(j = 0; j < records.length; j++) {
            if (rec.overlaps(records[j])) {
              hasOverlap = true;
              break;
            }
          }

          if (!hasOverlap) { records.push(rec); }

        }

        iLast = i;
        i = text.indexOf(' ', i + 1);
        if (i < 0) { i = text.length; }

      }

      return records;

    };

    // Insert an OR operator between consecutive queries.
    var addInteriorOperators = function(records) {

      trimOperators(records);

      if (records.length === 0) {
        return [];
      }

      var revisedRecords = [records[0]];
      var lastRecord = records[0];
      var rec, newRec;

      for(var i = 1; i < records.length; i++) {
        rec = records[i];
        if(!rec.isOperator() && !lastRecord.isOperator()) {
          newRec = new Record(lastRecord.end, rec.start, "OR");
          revisedRecords.push(newRec);
        }
        revisedRecords.push(rec);
        lastRecord = rec;
      }

      return revisedRecords;
    };

    var trimOperators = function(records) {
      while(records.length > 0 && records[0].isOperator()) {
        records.shift();
      }

      while(records.length > 0 && records[records.length - 1].isOperator()) {
        records.pop();
      }

    };

    this.parseRecords = function(text) {
      var recs = splitIntoRecords(text);
      console.log("Records: ", recs);
      var revised = addInteriorOperators(recs);
      console.log("revised records: ", revised);
      var rg = new RecordGroup(revised);
      console.log('record group: ', rg);
      return rg;
    };

    /////////////////////////////////////////////////////////////////
    // Here's some code to do simple matches, given a single query string.
    // Simply use the angular filter.
    var matcherFunction = function(item, query) {
      var i, key, s;

      // If the item is an array, see if any entries match
      if(angular.isArray(item)) {
        for(i = 0; i < item.length; i++) {
          if (matcherFunction(item[i], query)) {
            return true;
          }
        }
        return false;
      // If the item is an object, see if any values match
      } else if (angular.isObject(item)) {
        for(key in item) {
          if (item.hasOwnProperty(key) && matcherFunction(item[key], query)) {
            return true;
          }
        }
        return false;
      // Otherwise just do string match
      } else {
        s = String(item);
        return s.toUpperCase().indexOf(query.toUpperCase()) >= 0;
      }

      return false;

    };

    this.matcherFunction = matcherFunction;

  });
