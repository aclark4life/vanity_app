<%include file="header.html"/>
        <%include file="sidebar_manage.html"/>
        </div><!--/span-->
        <div class="span9">
          <div class="hero-unit-small overflow-hidden">
            % if flash:
            <div class="alert">
                <button class="close" data-dismiss="alert">×</button>
                <h1>${flash}</h1>
            </div>
            % endif
            <h1>Select plan</h1>
            <br />
            ${form|n}
            % if plan:
                % if display_cc:
                <div class="fade modal modal-plan-select"> 
                    <div class="modal-header"> 
                        <button class="close" data-dismiss="modal">×</button>
                        <h3>Purchase ${plans_choices[plans_data[plan][0]][1]}</h3>
                    </div>
                    <div class="modal-body" style="background: url('/static/img/img04.png'); color: white">
                        <!-- to display errors returned by createToken -->
                        <div class="text-align: center">
                        <div style="margin: 0px auto; width: 50%">
                        <span style="margin: 0; padding: 0" class="payment-errors"></span>
                        <form action="/manage/billing" method="POST" id="payment-form">
                            <input type="hidden" name="plan" value="${plan}" />
                            <div class="form-row">
                                <label>Card Number</label>
                                <input type="text" maxlength="20" autocomplete="off" class="card-number" style="width: 130px" />
                            </div>
                            <div class="form-row">
                                <label>CVC</label>
                                <input type="text" maxlength="4" autocomplete="off" class="card-cvc" style="width: 40px" />
                            </div>
                            <div class="form-row">
                                <label>Expiration (MM/YYYY)</label>
                                <input type="text" maxlength="2" class="card-expiry-month" style="width: 15px"/>
                                <span> / </span>
                                <input type="text" maxlength="4" class="card-expiry-year" style="width: 30px"/>
                            </div>
                            <br />
                            <button type="submit" class="btn btn-large submit-button">Submit Payment</button>
                        </form>
                        </div>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <a href="#" class="btn" data-dismiss="modal">Close</a>
                    </div>
                </div>
                % endif
            % endif
          </div>
<%include file="footer.html"/>
<script>
    $("#manage_billing").addClass("active");

    // this identifies your website in the createToken call below
    Stripe.setPublishableKey('pk_37yYnJ08bF1l4Mkii6wtMvHX1OcRU');
    function stripeResponseHandler(status, response) {
        if (response.error) {
            // re-enable the submit button
            $('.submit-button').removeAttr("disabled");
            // show the errors on the form
            $(".payment-errors").addClass("alert alert-error");
            $(".payment-errors").html(response.error.message);
        } else {
            var form$ = $("#payment-form");
            // token contains id, last4, and card type
            var token = response['id'];
            // insert the token into the form so it gets submitted to the server
            form$.append("<input type='hidden' name='stripeToken' value='" + token + "' />");
            // and submit
            form$.get(0).submit();
        }
    }

    $(document).ready(function() {
        $("#payment-form").submit(function(event) {
            // disable the submit button to prevent repeated clicks
            $('.submit-button').attr("disabled", "disabled");
            // createToken returns immediately - the supplied callback submits the form if there are no errors
            Stripe.createToken({
                number: $('.card-number').val(),
                cvc: $('.card-cvc').val(),
                exp_month: $('.card-expiry-month').val(),
                exp_year: $('.card-expiry-year').val()
            }, stripeResponseHandler);
            return false; // submit from callback
        });
    });
    if (window.location.protocol === 'file:') {
        alert("stripe.js does not work when included in pages served over file:// URLs. Try serving this page over a webserver. Contact support@stripe.com if you need assistance.");
    }
</script>
