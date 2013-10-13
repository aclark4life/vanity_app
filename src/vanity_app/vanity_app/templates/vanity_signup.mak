<%include file="header_center.html"/>
          <div class="hero-unit">
            % if submitted:
            <div class="alert">
                <button class="close" data-dismiss="alert">×</button>
                <h1>Thank you! Please check your e-mail</h1>
            </div>
            % endif
            <h1>Sign Up</h1>
            <br />
            <h2>We Help Package, Release And Promote Your Python Software With Just A Few Clicks</h2>
            <br />
            <p>Please enter your name, e-mail address and GitHub username, and select one or more <a href="http://pypi.python.org/pypi?%3Aaction=list_classifiers">classifiers</a> that apply to your work.</p>
            <br />
            <h6>We will not share your personal information</h6>
            <br />
            % if form:
                ${form|n}
            % endif
          </div>
<%include file="footer.html"/>
<script>
    $("#signup-tab").addClass("active");
</script>
