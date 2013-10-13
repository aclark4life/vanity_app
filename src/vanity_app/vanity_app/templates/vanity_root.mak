<%include file="header_center.html" />
        % if not userid:
        <div class="hero-unit overflow-hidden">
            <h1>Package, Release, Promote Your Python Software Quickly and Easily</h1>
            <br />
            <br />
            <a class="btn btn-large btn-primary" href="/signup" style="font-size: 300%"> &nbsp;Sign Up &raquo;</a>
            &nbsp;
            <a class="btn btn-large" href="http://www.youtube.com/watch?v=v80cAfxo8hg" style="font-size: 300%">Watch The Video</a>
        </div>
        % endif
        % if userid:
        <div class="hero-unit-small">
          % if error:
          <div class="alert alert-error">
              <button class="close" data-dismiss="alert">×</button>
              <h1>Please enter a valid Python package name</h1>
          </div>
          % endif
          % if flash:
          <div class="alert alert-success">
              <button class="close" data-dismiss="alert">×</button>
              <h1>You featured ${flash[0]}!</h1>
          </div>
          % endif
          <div class="row-fluid">
            <div class="span8">
              <form action="/" method="POST">
                <p>
                  <input class="input-xlarge package-input" type="text" name="package" placeholder="Python package?" />
                </p>
                <p>
                  <input class="btn btn-large btn-primary" type="submit" value="Feature it &raquo;" />
                  <a href="http://docs.pythonpackages.com/en/latest/basic-features/package-featuring.html" class="btn btn-large">How does it work?</a>
                </p>
              </form>
            </div>
          </div>
        </div><!--/row-->
        % endif
        <%include file="main_entries.html"/>
<%include file="footer.html"/>
