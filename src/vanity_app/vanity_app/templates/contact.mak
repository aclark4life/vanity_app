<%include file="header.html"/>
          <div class="well sidebar-nav">
           <ul class="nav nav-list">
              <li class="nav-header">Contact</li>
              <li><a href="mailto:info@pythonpackages.com"><i class="icon-envelope"></i> Email</a></li>
              <li><a href="http://bitbucket.org/pythonpackages"><i class="icon-trash"></i> bitbucket</a></li>
              <li><a href="http://github.com/pythonpackages"><i class="icon-thumbs-up"></i> GitHub</a></li>
              <li><a href="irc://irc.freenode.net/#pythonpackages"><i class="icon-comment"></i> IRC</a></li>
              <li><a href="http://twitter.com/pythonpackages"><i class="icon-user"></i> Twitter</a></li>
           </ul>
          </div>
        </div><!--/span-->
        <div class="span9">
          <div class="hero-unit hero-unit-small">
            % if submitted:
                <div class="alert alert-success">
                    <button class="close" data-dismiss="alert">×</button>
                    <h1>Sent! You will hear from us within 24 hours.</h1>
                </div>
            % endif
            <h1>Contact pythonpackages.com</h1>
            <br />
            <h6>We are here to help with your Python packaging needs. If you have trouble with the site, or if you need help deploying Python software in general, please <a href="mailto:info@pythonpackages.com">let us know</a>.</h6>
            <br />
            <div id="send-message">
            % if form:
                ${form|n}
            % endif
            </div>
          </div>
<%include file="footer.html"/>
<script>
    $("#manage_mail").addClass("active");
</script>
