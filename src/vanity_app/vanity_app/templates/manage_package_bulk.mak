<%include file="header.html"/>
        <%include file="sidebar_manage.html"/>
        </div><!--/span-->
        <div class="span9">
          <div class="hero-unit">
            % if submitted:
            <div class="fade modal modal-package-release">
                <div class="modal-header">
                    <button class="close" data-dismiss="modal">×</button>
                    <h3>Results</h3>
                </div>
                <div class="modal-body">
                    <pre>${results}</pre>
                </div>
                <div class="modal-footer">
                    <a href="#" class="btn" data-dismiss="modal">Close</a>
                </div>
            </div>
            % endif
            <h1>Bulk Add</h1>
            <br />
            <h2>Use this form to bulk add repositories to available package slots</h2>
            <br />
            <p>Enter one repository per line, followed by an organization if needed. E.g.:</p>

            <pre>buildout.bootstrap collective
pypi.trashfinder pythonpackages
vanity</pre>

            <br />
            <div> 
              ${form|n}
            </div>
          </div>
<%include file="footer.html"/>
<script>
    $("#manage_package_bulk").addClass("active");
</script>
