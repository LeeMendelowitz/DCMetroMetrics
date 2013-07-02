%# BASIC LAYOUT

<html>

<head>
    <link rel="stylesheet" type="text/css" href="/static/statusListing.css">
    <title>{{title or 'DC Metro Metrics'}}</title>

    <script>
      (function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){
      (i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),
      m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)
      })(window,document,'script','//www.google-analytics.com/analytics.js','ga');
      ga('create', 'UA-42172563-1', 'dcmetrometrics.com');
      ga('send', 'pageview');
    </script>

</head>

<!-- BEGIN BODY -->

<body>

<div id="maincontainer">

<div id="header">
%include header
</div>

<div id="leftcolumn">
%include left_column
</div>

<div id="contentwrapper">
%include 
</div>

<div id="footer">
%include footer
</div>

</div> <!-- END container -->
</body>

</html>

