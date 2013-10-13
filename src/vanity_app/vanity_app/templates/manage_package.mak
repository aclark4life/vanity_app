<%include file="header.html"/>
        <% pages = 0 %>
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

            % if submitted:
            <div class="fade modal modal-package-release">
                <div class="modal-header">
                    <button class="close" data-dismiss="modal">×</button>
                    <h3>Command output</h3>
                </div>
                <div class="modal-body">
                    <pre>${error}</pre>
                </div>
                <div class="modal-footer">
                    <a href="#" class="btn" data-dismiss="modal">Close</a>
                </div>
            </div>
            % endif

            % if tree is None:
            <ul class="nav nav-tabs">
            <li
                % if org is None:
                    class="active"
                % endif 
                ><a href="/manage/package?slot=${slot}">${userid}</a></li>
            % for o in slots_org:
                <li
                    % if org == int(o):
                        class="active"
                    % endif
                    ><a href="/manage/package?slot=${slot}&org=${o}">${slots_org[o]}</a></li>
            % endfor
            </ul>
            % endif

            % if form is not None:
            % if num_repos > 100:
            <% pages = (num_repos/100) + 1 %>
            <div class="pagination">
                <ul>
                    % for repo in range(pages):
                        <% p = repo + 1 %>
                        % if org is not None:
                            <li
                                % if page == p:
                                class="active"
                                % endif
                                ><a href="/manage/package?slot=${slot}&org=${org}&page=${p}">${p}</a></li>
                        % else:
                            <li
                                % if page == p:
                                class="active"
                                % endif
                                ><a href="/manage/package?slot=${slot}&page=${p}">${p}</a></li>
                        % endif
                    % endfor
                </ul>
            </div>
            % endif
            <h1>Github Repositories <span class="label-before">(${num_repos})</span></h1>

            <br />

            % if org >= 0:
            <% action = "/manage/package?slot=%s&org=%s" % (slot, org) %>
            % else:
            <% action = "/manage/package?slot=%s" % slot %>
            % endif

            <form class="well form-search" action=${action} method="POST">
                <input type="text" class="input-xlarge search-query" placeholder="Repository name?" name="search" />
                <button type="submit" class="btn">Search</button>
            </form>

            % if num_repos > 100:
            <h2>Page ${page} of ${pages}</h2>
            % endif

            <br />
            ${form|n}
            % else:
            % if tree is not None:
            <form style="float: right; margin: 0 2em 2em 0;" class="dropdown form-actions" action="/manage/package?slot=${slot}" method="POST">
                <input type="text" name="package" value="${package}" style="display: none;"/>
                <a class="btn dropdown-toggle" data-toggle="dropdown" href="#">
                    <i class="icon-cog"></i>
                    <b class="caret"></b>
                </a>
                <ul class="dropdown-menu">
                    <li>
                        <input class="tooltip-package-tag-and-release" type="submit" name="tag-and-release"
                            data-original-title="Create a tag on GitHub, and release to PyPI."
                            value="Tag and Release"></input>
                    </li>
                    <li class="divider"></li>
                    <li>
                        <input class="tooltip-package-run-test-suite" type="submit" name="run-test-suite"
                            data-original-title="Run test suite on pythonpackages.com via `python setup.py test`."
                            value="Run Test Suite"></input>
                    </li>
                    <li>
                        <input class="tooltip-package-upload-to-test-index" type="submit" name="upload-to-test-index"
                            data-original-title="Test upload via `python setup.py sdist upload -r http://index.pythonpackages.com`."
                            value="Test Upload"></input>
                    </li>
                    <li>
                        <input class="tooltip-package-test-installation" type="submit" name="test-installation"
                            data-original-title="Test installation on pythonpackages.com via `python setup.py install`."
                            value="Test Installation"></input>
                    </li>
                    <li class="divider"></li>
                    <li>
                        <input class="tooltip-package-unselect-package" type="submit" name="unselect-package"
                            data-original-title="Unselect package to create an empty slot."
                            value="Unselect package"></input>
                    </li>
<!--
                    <li>
                        <input class="tooltip-package-unselect-package" type="submit" name="add-slot-here"
                            data-original-title="Add a new slot below the current slot."
                            value="Add slot here"></input>
                    </li>
-->
                </ul>
            </form>
            <h1>Manage Package</h1>
            <br />
            <table class="table table-bordered table-condensed table-striped">
                <thead>
                    <th><h2><a href="${url}" target="_blank">${package} <i class="icon-share-alt"></i></a></h2></th>
                </thead>
                <tbody>
                % if 'tree' in tree:
                    % for item in tree['tree']:
                        % if 'path' in item:
                            <tr><td><a href="${url}/${item['path']}" target="_blank">${item['path']} <i class="icon-share-alt"></i></a></td></tr>
                        % endif
                    % endfor
                % endif
                </tbody>
            </table>
            % endif
            % endif

            % if num_repos > 100:
            <div class="pagination">
                <ul>
                    % for repo in range(pages):
                        <% p = repo + 1 %>
                        % if org is not None:
                            <li
                                % if page == p:
                                class="active"
                                % endif
                                ><a href="/manage/package?slot=${slot}&org=${org}&page=${p}">${p}</a></li>
                        % else:
                            <li
                                % if page == p:
                                class="active"
                                % endif
                                ><a href="/manage/package?slot=${slot}&page=${p}">${p}</a></li>
                        % endif
                    % endfor
                </ul>
            </div>
            % endif
        </div> 
<%include file="footer.html"/>
<script>
    $("#manage_package").addClass("active");
</script>
