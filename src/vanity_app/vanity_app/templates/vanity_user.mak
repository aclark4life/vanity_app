<%include file="header.html"/>
          <%include file="sidebar_user.html"/>
        </div><!--/span-->
        <div class="span9">
          <div class="hero-unit overflow-hidden">
            <h1 class="featured-user">
            % if avatar is not None:
                <img class="thumbnail" src="${avatar}" alt="">
            % endif
                <a href="http://github.com/${user}">${user}</a>&apos;s&nbsp;featured packages
            </h1>
          </div>
          <%include file="main_entries.html"/>
<%include file="footer.html"/>
