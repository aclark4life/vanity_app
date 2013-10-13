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
            % if submit:
                <div class="alert alert-success">
                    <button class="close" data-dismiss="alert">×</button>
                    <h1>Saved!</h1>
                </div>
            % endif
            <h1>PyPI account</h1>
            <br />
            <form action="" method="POST">
                % if not pypi_oauth_test:
                    <h2>In order to register new packages, upload new files and upload new documentation on your behalf on PyPI,
                        we need your authorization. Note: You must <a target="_blank"
                        href="http://pypi.python.org/pypi?%3Aaction=login">Sign In To PyPI</a> first.</h2>
                    <br />
                    <input class="btn btn-primary btn-large" style="font-size: 300%" name="pypi_oauth" type="submit" value="Authorize pythonpackages.com">
                % else:
                    <h2>You have authorized pythonpackages.com to register new packages, upload new files and upload new documentation on your behalf on PyPI.</h2>
                    <br />
                    <input class="btn btn-large" style="font-size: 300%" name="clear" type="submit" value="Remove authorization">
                % endif
            </form>
          </div>
<%include file="footer.html"/>
<script>
    $("#manage_account_pypi").addClass("active");
</script>
