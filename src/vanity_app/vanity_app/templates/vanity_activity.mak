<%include file="header.html"/>
          <%include file="sidebar_releases.html"/>
          <%include file="sidebar_most_downloaded.html"/>
          <%include file="sidebar_most_featured.html"/>
        </div><!--/span--> 
        <div class="span9">
          <div class="hero-unit-small"> 
            % if flash:
            <div class="alert alert-success">
                <button class="close" data-dismiss="alert">×</button>
                <h1>You featured ${flash[0]}!</h1>
            </div>
            % endif
            <h1>Changelog Entries</h1>
            <br />
            <p>Powered by <a href="/package/yolk">yolk</a></p>
          </div><!--/row--> 
          <%include file="main_log.html"/>
<%include file="footer.html"/>
<script>
    $("#activity-tab").addClass("active");
</script>
