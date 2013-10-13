<%include file="header.html"/>
        <%include file="sidebar_manage.html"/>
        </div><!--/span-->
        <div class="span9">
          % if submitted:
          <div class="fade modal modal-package-new">
              <div class="modal-header">
                  <button class="close" data-dismiss="modal">×</button>
                  <h3>Command output</h3>
              </div>
              <div class="modal-body">
                  <pre>${out}</pre>
              </div>
              <div class="modal-footer">
                  <a href="#" class="btn" data-dismiss="modal">Close</a>
              </div>
          </div>
          % endif
          <div class="hero-unit-small">
            <ul class="nav nav-tabs">
            <li
                % if org is None:
                    class="active"
                % endif
                ><a href="/manage/package/new">${userid}</a></li>
            % for o in slots_org:
                <li
                    % if org == o:
                        class="active"
                    % endif
                    ><a href="/manage/package/new?org=${o}">${slots_org[o]}</a></li>
            % endfor
            </ul>

            % if error == 1:
            <div class="alert alert-error">
                <button class="close" data-dismiss="alert">×</button>
                <h1>Please enter a valid Python package name</h1>
            </div>
            % endif
            % if error == 2:
            <div class="alert alert-error">
                <button class="close" data-dismiss="alert">×</button>
                <h1>Create repo failed</h1>
            </div>
            % endif
            % if error == 3:
            <div class="alert alert-error">
                <button class="close" data-dismiss="alert">×</button>
                <h1>Package created but unable to `git push`, bad credentials?</h1>
            </div>
            % endif
            % if error == 4:
            <div class="alert alert-error">
                <button class="close" data-dismiss="alert">×</button>
                <h1>Package created but unable to `git add`, repo exists?</h1>
            </div>
            % endif

            <h1>Create new package</h1>
            <br />
            ${form|n}
            <br />
            <p>Powered by <a href="/package/pastescript">PasteScript</a></p>
        </div> 
<%include file="footer.html"/>
<script>
    $("#manage_package_new").addClass("active");
</script>
