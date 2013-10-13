<%include file="header.html"/>
        <%include file="sidebar_manage.html"/>
        </div><!--/span-->
        <div class="span9">
          <div class="hero-unit">
            % if submitted:
                <div class="alert alert-success">
                    <button class="close" data-dismiss="alert">×</button>
                    <h1>Sent!</h1>
                </div>
            % endif
            <h1>Send tweet</h1>
            <br />
            ${form|n}
          </div>
<%include file="footer.html"/>
<script>
    $("#manage_twitter").addClass("active");
</script> 
