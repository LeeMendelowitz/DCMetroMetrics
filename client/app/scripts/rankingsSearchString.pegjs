{

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

word
 = chars:[a-zA-z0-9]+ { var q =  chars.join(""); return q; }

multiword
 = ws? w1:word ws w2:multiword ws? { var q =  w1 + " " + w2; return q;}
 / word

phrase
 = '"' w:multiword '"' { return w; }

ander
 = "&&"
 / "AND"
 / "+"

orer
  = "\|\|"
  / "OR"

notter
  = "!"
  / "NOT"

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