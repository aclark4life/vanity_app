<%include file="header.html"/>
        <%include file="sidebar_manage.html"/>
        </div><!--/span-->
        <div class="span9">
          <div class="hero-unit overflow-hidden">
            % if flash:
            <div class="alert">
                <button class="close" data-dismiss="alert">×</button>
                <h1>${flash}</h1>
            </div>
            % endif
            <h1>GitHub Organizations</h1>
            <br />
            <div id="github-orgs">${form|n}</div>
          </div>
<%include file="footer.html"/>
<script>
    $("#manage_org").addClass("active");
</script>
