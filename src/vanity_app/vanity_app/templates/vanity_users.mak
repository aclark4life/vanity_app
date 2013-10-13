<%include file="header.html"/>
          <div class="well sidebar-nav">
            <%include file="sidebar_users.html"/>
          </div><!--/.well -->
        </div><!--/span-->
        <div class="span9">
          <div class="hero-unit-small">
            <h1>Recent Users</h1>
            <br />
          </div>
          <%include file="main_users.html"/>
<%include file="footer.html"/>
<script>
    $("#users-tab").addClass("active");
</script>
