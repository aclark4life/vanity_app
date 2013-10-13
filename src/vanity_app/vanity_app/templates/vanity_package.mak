<%include file="header.html"/>
          <div class="well sidebar-nav">
            <%include file="sidebar_package.html"/>
          </div>
          <br />
        </div><!--/span-->
        % if python3_status:
        <style>
        .nav-tabs > .active > a {
            background: #DFF0D8;
        }
        .nav-tabs > .active > a:hover {
            background: #DFF0D8;
        }
        .nav-tabs > li > a:hover {
            background: #DFF0D8;
            border: 1px solid #DDDDDD;
        }
        </style>
        % endif
        <div class="span9">
            <div class="hero-unit"
              % if python3_status:
                style="background: #DFF0D8;"
              % endif
              >
              <ul class="nav nav-tabs">
                  <li
                      % if request.query_string == 'tab=downloaded':
                          class="active"
                      % endif
                      ><a href="/package/${package}#downloaded" data-toggle="tab">Downloaded</a></li>
                  <li
                      % if request.query_string == 'tab=featured':
                          class="active"
                      % endif
                      ><a href="/package/${package}#featured" data-toggle="tab">Featured</a></li>
                  <li
                      % if request.query_string == 'tab=info' or request.query_string == '':
                          class="active"
                      % endif
                      ><a href="/package/${package}#info" data-toggle="tab">Info</a></li>
                  <li
                      % if request.query_string == 'tab=quality':
                              class="active"
                      % endif
                      ><a href="/package/${package}#quality" data-toggle="tab">Quality</a></li>
              </ul>
              <div class="tab-content">
                  <div class="overflow-hidden tab-pane
                    % if request.query_string == 'tab=downloaded':
                        active
                    % endif
                    " id="downloaded">
                    % for classifier in classifiers:
                        <% stub = classifier.split('::')[0].strip() %>
                        % if stub == 'Development Status':
                            <% icon="icon-cog icon-white" %>
                        % elif stub == 'Environment':
                            <% icon="icon-globe icon-white" %>
                        % elif stub == 'Intended Audience':
                            <% icon="icon-user icon-white" %>
                        % elif stub == 'License':
                            <% icon="icon-certificate icon-white" %>
                        % elif stub == 'Operating System':
                            <% icon="icon-hdd icon-white" %>
                        % elif stub == 'Programming Language':
                            <% icon="icon-wrench icon-white" %>
                        % elif stub == 'Topic':
                            <% icon="icon-heart icon-white" %>
                        % elif stub == 'Natural Language':
                            <% icon="icon-bullhorn icon-white" %>
                        % elif stub == 'Framework':
                            <% icon="icon-home icon-white" %>
                        % else:
                            <% icon="icon-home icon-white" %>
                        % endif
                        <span class="badge mini-classifier-pop-up" data-original-title="${classifier}" style="background: ${colors[stub][1]}"><i class="${icon}"></i></span>
                    % endfor
                      <div> 
                          <% p = package.replace('.', '-') %>
                          % if count == 0:
                                  <h1><a href="/package/${package}">${p}</a> has been downloaded <br />
                                  <span class="num-large"><span class="downloads-not-applicable" rel="popover" data-content="This package is either new, does not exist, or does not host its downloads on the Python package index" data-original-title="Download count not applicable">N/A</span></span><br />
                                  times!</h1>
                          % else:
                                  <h1><a href="/package/${package}">${p}</a> has been downloaded <br />
                                  <span class="num-large">${downloads}</span> <br />
                                  times!</h1>
                          % endif
                        <br />
                        <p>Powered by <a href="/package/vanity">vanity</a></p>
                      </div>
                  </div>
                  <div class="overflow-hidden tab-pane
                    %   if request.query_string == 'tab=featured':
                            active
                    %   endif
                    " id="featured">
                    % for classifier in classifiers:
                        <% stub = classifier.split('::')[0].strip() %>
                        % if stub == 'Development Status':
                            <% icon="icon-cog icon-white" %>
                        % elif stub == 'Environment':
                            <% icon="icon-globe icon-white" %>
                        % elif stub == 'Intended Audience':
                            <% icon="icon-user icon-white" %>
                        % elif stub == 'License':
                            <% icon="icon-certificate icon-white" %>
                        % elif stub == 'Operating System':
                            <% icon="icon-hdd icon-white" %>
                        % elif stub == 'Programming Language':
                            <% icon="icon-wrench icon-white" %>
                        % elif stub == 'Topic':
                            <% icon="icon-heart icon-white" %>
                        % elif stub == 'Natural Language':
                            <% icon="icon-bullhorn icon-white" %>
                        % elif stub == 'Framework':
                            <% icon="icon-home icon-white" %>
                        % else:
                            <% icon="icon-home icon-white" %>
                        % endif
                        <span class="badge mini-classifier-pop-up" data-original-title="${classifier}" style="background: ${colors[stub][1]}"><i class="${icon}"></i></span>
                    % endfor
                    <div> 
                        <% p = package.replace('.', '-') %>
                        <h1><a href="/package/${package}">${p}</a> has been featured <br />
                        <span class="num-large">${score}</span> <br />
                        times!</h1>
                        <br />
                    </div>
                  </div>
                  <div class="overflow-hidden tab-pane
                    % if request.query_string == 'tab=info' or request.query_string == '':
                              active
                    % endif
                    " id="info">
                    % for classifier in classifiers:
                        <% stub = classifier.split('::')[0].strip() %>
                        % if stub == 'Development Status':
                            <% icon="icon-cog icon-white" %>
                        % elif stub == 'Environment':
                            <% icon="icon-globe icon-white" %>
                        % elif stub == 'Intended Audience':
                            <% icon="icon-user icon-white" %>
                        % elif stub == 'License':
                            <% icon="icon-certificate icon-white" %>
                        % elif stub == 'Operating System':
                            <% icon="icon-hdd icon-white" %>
                        % elif stub == 'Programming Language':
                            <% icon="icon-wrench icon-white" %>
                        % elif stub == 'Topic':
                            <% icon="icon-heart icon-white" %>
                        % elif stub == 'Natural Language':
                            <% icon="icon-bullhorn icon-white" %>
                        % elif stub == 'Framework':
                            <% icon="icon-home icon-white" %>
                        % else:
                            <% icon="icon-home icon-white" %>
                        % endif
                        <span class="badge mini-classifier-pop-up" data-original-title="${classifier}" style="background: ${colors[stub][1]}"><i class="${icon}"></i></span>
                    % endfor
                      <div class="package-info">
                          <% p = package.replace('.', '-') %>
                          <h1>${p}</h1><br />
                          <h2>${summary}</h2><br />
                          <h3>${version}</h3><br />
                          <p>
                          <form action="/" method="POST">
                            <input class="input-xlarge" type="text" name="package:info" value="${package}" style="display: none;"/>
                            % if userid:
                            <input class="btn btn-primary btn-large" type="submit" value="Feature package" />
                            % endif
                          </form>
                          </p>
                          <br />
                          % if featured_by != 'anonymous':
                          <span class="label-before timestamp"
                              data-original-title="${timestamp}">Last featured by <a
                                  href="/user/${featured_by}">${featured_by}</a></span>
                          % else:
                              <span class="label-before timestamp"
                                  data-original-title="${timestamp}">Last featured by ${featured_by}</span>
                          % endif
                      </div>
                  </div>
                  <div class="overflow-hidden tab-pane
                    %   if request.query_string == 'tab=quality':
                            active
                    %   endif
                    " id="quality">
                    % for classifier in classifiers:
                        <% stub = classifier.split('::')[0].strip() %>
                        % if stub == 'Development Status':
                            <% icon="icon-cog icon-white" %>
                        % elif stub == 'Environment':
                            <% icon="icon-globe icon-white" %>
                        % elif stub == 'Intended Audience':
                            <% icon="icon-user icon-white" %>
                        % elif stub == 'License':
                            <% icon="icon-certificate icon-white" %>
                        % elif stub == 'Operating System':
                            <% icon="icon-hdd icon-white" %>
                        % elif stub == 'Programming Language':
                            <% icon="icon-wrench icon-white" %>
                        % elif stub == 'Topic':
                            <% icon="icon-heart icon-white" %>
                        % elif stub == 'Natural Language':
                            <% icon="icon-bullhorn icon-white" %>
                        % elif stub == 'Framework':
                            <% icon="icon-home icon-white" %>
                        % else:
                            <% icon="icon-home icon-white" %>
                        % endif
                        <span class="badge mini-classifier-pop-up" data-original-title="${classifier}" style="background: ${colors[stub][1]}"><i class="${icon}"></i></span>
                    % endfor
                    <div>
                      <% p = package.replace('.', '-') %>
                      <h1><a href="/package/${package}">${p}</a> package quality</h1>
                      <br />
                      <div id="trash_report">
                      <% package_quality %>
                      <% trash_report %>
                      % if package_quality: 
                        <p>
                          <h1><span class="num-large">OK</span></h1>
                        </p>
                      % else:
                        <p>
                          <h1><span class="num-large">Poor</span></h1>
                          <ul>
                          % for line in trash_report:
                            <li>${line}</li>
                          % endfor
                          </ul>
                        </p>
                      % endif
                      </div>
                      <br />
                      <p>Powered by <a href="/package/pypi.trashfinder">pypi.trashfinder</a></p>
                    </div>
                  </div>
              </div>
            </div>
            <div> 
            <br />
            <div class="hero-unit overflow-hidden">
                % if 'description' in metadata:
                    % if metadata['description'] != 'UNKNOWN' and metadata['description'] != '':
                        <a name="description"></a>
                        <h6><a class="permalink" href="/package/${package}#description"><span class="permalink-title">Description&nbsp;</span><span class="permalink-symbol">&#182;</span></a></h6>
                        <br />
                        <div id="package-description">
                            % if render_failed:
                                <pre>${description|n, h}</pre>
                            % else:
                                ${description|n}
                            % endif
                        </div>
                    % endif
                % endif
                <br />
                <div >
                % for field in metadata:
                    % if field != 'description': 
                    <div id="metadata" >
                        <h6>${field.replace('_', ' ')}</h6>
                        % if field.endswith('_url') or field == 'home_page':
                            <% url = metadata[field] %>
                            % if not url.startswith('http'):
                            <% url = 'http://' + url %>
                            % endif
                            <p><i class="icon-share meta-icon"></i> <a href="${url}">${url}</a></p><br />
                        % elif field == 'requires' or field == 'provides' or field == 'obsoletes':
                            <p><i class="icon-check meta-icon"></i> ${', '.join(metadata[field])}</p> <br />
                        % elif field == 'keywords': 
                            <p><i class="icon-tags meta-icon"></i> ${metadata[field]}</p> <br />
                        % elif field == 'license': 
                            <p><i class="icon-file meta-icon"></i> ${metadata[field]}</p> <br />
                        % elif field.endswith('_email'): 
                            <p><i class="icon-envelope meta-icon"></i> ${metadata[field].replace('@', ' __at__ ')}</p> <br />
                        % elif field == 'author' or field == 'maintainer':
                            <p><i class="icon-user meta-icon"></i> ${metadata[field]}</p> <br />
                        % else:
                            % if field != 'description':
                                <p><i class="icon-check meta-icon"></i> ${metadata[field]}</p> <br />
                            % endif
                        % endif
                    </div>
                    % endif
                % endfor
                </div>
                % if classifiers:
                    <a name="classifiers"></a>
                    <div>
                        <span ><h6><a class="permalink" href="/package/${package}#classifiers"><span class="permalink-title">Classifiers&nbsp;</span><span class="permalink-symbol">&#182;</span></a></h6></span>
                    </div>
                % endif
                <br />
                <div >
                    % if classifiers is not None:
                         % for classifier in classifiers:
                             <% stub = classifier.split('::')[0].strip() %> 
                             <div style="background: ${colors[stub][1]}" class="trove-classifier">
                                 <h3 style="color: ${colors[stub][0]}">${classifier}</h3>
                             </div>
                         % endfor
                         <br />
                    % endif
                </div>
            </div>
            <br />
            <div class="arrow-up"><a href="/package/${package_lower}#">Back to top</a></div>
        </div>
        <!-- Example row of columns -->
<%include file="footer.html"/>
