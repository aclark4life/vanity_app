<%include file="header.html"/>
        <%include file="sidebar_manage.html"/>
        </div><!--/span-->
        <div class="span9">
          <div class="hero-unit overflow-hidden">
            <%include file="security.html"/>
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
            <h1>GitHub account credentials</h1>
            <br />
            <form action="" method="POST">
                % if username is not None and password is not None:
                    <label>Username<span class="req">*</span></label><input type="text" name="username" value="${username}">
                    <label>Password<span class="req">*</span></label><input type="password" value="${password}" name="password"><br />
                % else:                                              
                    <label>Username<span class="req">*</span></label><input type="text" name="username">
                    <label>Password<span class="req">*</span></label><input type="password" name="password"><br />
                % endif
                <input class="btn btn-primary" name="submit" type="submit" value="Save">
                <input class="btn" name="clear" type="submit" value="Clear">
            </form>
          </div>
<%include file="footer.html"/>
<script>
    $("#manage_account_github").addClass("active");
</script>
