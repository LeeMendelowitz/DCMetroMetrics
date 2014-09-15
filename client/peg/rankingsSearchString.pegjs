{
  // The parser will return a compiled function of the form function isMatch(matcher, item).
  // where matcher is a callback function you must provide which returns true if a query matches
  // an item.
  //
  // For example, here a simple matching function assuming item and query are strings:
  //
  //    function matcher(item, query) {
  //        return item.indexOf(query) >= 0;
  //    }
  //
  //
  //
  // Assuming this parser module is built with pegjs into object named searchStringParser,
  // here is the usage:
  //
  //  var phrase = '"green eggs" OR ham';
  //  var s1 = "eggs are my favorite";
  //  var s2 = "eggs with ham are my favorite";
  //  var matcher = function(item, query) {
  //        return item.indexOf(query) >= 0;
  //  };
  //  var compiled = searchStringParser.parse(phrase); 
  //  compiled(matcher, s1); // Returns false
  //  compiled(matcher, s2); // Returns true
  //
  //
  
  var makeMatchFunc = function(query) {

    var isMatch = function(matcher, item) {
      return matcher(item, query);
    };

    return isMatch;

  };

  var negateFunction = function(f) {

    var opposite = function(matcher, item) {
      return !f(matcher, item);
    };

    return opposite;

  };

  var makeAndFunction = function(f1, f2) {

    var andFunc = function(matcher, item) {
      return f1(matcher, item) && f2(matcher, item);
    };

    return andFunc;
  };

  var makeOrFunction = function(f1, f2) {

    var orFunc = function(matcher, item) {
      return f1(matcher, item) || f2(matcher, item);
    };

    return orFunc;
  };

}

start 
 = or

ws
  = chars:[\t ]+ { return " "; }

qt
 = ['"]+

word
 = chars:[a-zA-z0-9]+ { var q =  chars.join(""); return q; }

multiword
 = ws? w1:word ws w2:multiword ws? { var q =  w1 + " " + w2; return q;}
 / word

phrase
 = qt w:multiword qt { return w; }

ander
 = "&&"
 / "AND"i
 / "+"

orer
  = "\|\|"
  / "OR"i

notter
  = "!"
  / "NOT"i

primary
 =  notter ws? primary:primary { return negateFunction(primary);  }
   / w:word { return makeMatchFunc(w); }
   / p:phrase { return makeMatchFunc(p); }
   / "(" ws? or:or ws? ")" { return or; }

or =
  left:and ws orer ws right:or { return makeOrFunction(left, right); }
  / left:and ws right:or { return makeOrFunction(left, right); }
  / and

and =
   left:primary ws ander ws right:and { return makeAndFunction(left, right); }
  / primary