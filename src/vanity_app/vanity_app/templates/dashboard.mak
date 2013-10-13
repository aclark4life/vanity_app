<%include file="header.html"/>
        <%include file="sidebar_manage.html"/>
        </div><!--/span-->
        <div class="span9">
          <div class="hero-unit-small overflow-hidden">
            <h1 class="featured-user">
                % if flash:
                <div class="alert">
                    <button class="close" data-dismiss="alert">×</button>
                    <h1>${flash}</h1>
                </div>
                % endif
                ${userid}&apos;s dashboard
            </h1>
            <a href="http://docs.pythonpackages.com/en/latest/introduction.html" class="btn btn-large btn-primary">How does it work?</a>
          </div>
          <%include file="main_entries.html"/>
<%include file="footer.html"/>
