%# BASIC LAYOUT

%description_default = "Sharing public and crowdsourced data related to the Washington DC Metrorail system, including data on escalator outages, escalator historical performance, and #wmata #hotcar's."
%description = get('description', description_default)

<!DOCTYPE html>
<html lang="en">

<head>
  <meta charset="utf-8">
    <title>{{title or 'DC Metro Metrics'}}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="{{description or description_default}}">
    <meta name="author" content="">

    <link href="http://netdna.bootstrapcdn.com/twitter-bootstrap/2.3.2/css/bootstrap-combined.min.css" rel="stylesheet">
    <link href="/static/styles.css" rel="stylesheet">

</head>

<!-- BEGIN BODY -->

<body>

<div id="header">
<div class="navbar navbar-inverse navbar-fixed-top">
  <div class="navbar-inner">
    <div class="container">

      <!-- Toggle for the collapsed navigation bar -->
      <button type="button" class="btn btn-navbar" data-toggle="collapse" data-target=".nav-collapse">
        <span class="icon-bar"></span>
        <span class="icon-bar"></span>
        <span class="icon-bar"></span>
      </button>

      <a class="brand" href="/">DC Metro Metrics</a>

      <!-- Content hidden at 940px or less -->
      <div class="nav-collapse collapse">
        <ul class="nav">
          <li class="dropdown">
            <a href="/escalators" class="dropdown-toggle" data-toggle="dropdown">Escalators <b class="caret"></b></a>
            <ul class="dropdown-menu">
              <li><a href="/escalators/directory">Directory</a></li>
              <li><a href="/escalators/outages">Outages</a></li>
              <li><a href="/escalators/rankings">Rankings</a></li>
            </ul>
          </li>
          <li><a href="/stations">Stations</a></li>
          <li><a href="/hotcars">Hot Cars</a></li>
          <li><a href="/data">Data</a></li>
          <li><a href="/press">Press</a></li>
          <li><a href="mailto:info@dcmetrometrics.com" target="_blank">Contact</a></li>
        </ul>
      </div><!--/.nav-collapse -->
    </div>
  </div>
</div>
</div>

<div id="contentwrapper">
%#INCLUDE THE MAIN CONTENT
%include 
</div>


<footer class="footer container">
  <p class="text-center">&copy; Lee M. Mendelowitz 2013</p>
  <p class="text-center"><a href="https://twitter.com/MetroEscalators" class="twitter-follow-button" data-show-count="false">Follow @MetroEscalators</a> <a href="https://twitter.com/MetroHotCars" class="twitter-follow-button" data-show-count="false">Follow @MetroHotCars</a></p>
</footer>



<!-- Le javascript
================================================== -->
<!-- Placed at the end of the document so the pages load faster -->
<script src="http://ajax.googleapis.com/ajax/libs/jquery/1.10.1/jquery.min.js"></script>
<script src="http://netdna.bootstrapcdn.com/twitter-bootstrap/2.3.2/js/bootstrap.min.js"></script>

%if defined('scriptsToInclude'):
%scriptsToInclude()
%end

<!-- twitter -->
<script src="https://platform.twitter.com/widgets.js"></script>

<!-- google analytics -->
<script>
  (function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){
  (i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),
  m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)
  })(window,document,'script','//www.google-analytics.com/analytics.js','ga');

  ga('create', 'UA-42172563-1', 'dcmetrometrics.com');
  ga('send', 'pageview');

</script>
</body>


</html>

