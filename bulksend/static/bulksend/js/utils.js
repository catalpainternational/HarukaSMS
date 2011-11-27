function countChars(id_read, id_count,id_sms_count,id_msg_price){
    char_count = document.getElementById(id_read).value.length;

    document.getElementById(id_count).innerHTML=char_count;
    sms_count = Math.ceil(char_count/sms_length);
    msg_price = sms_count * sms_cost;
    document.getElementById(id_sms_count).innerHTML= sms_count;
    document.getElementById(id_msg_price).innerHTML= '$'+msg_price;
}

function showSpinnerAndRedirect(to_hide_id){
    document.getElementById('spinner').style.display='block';
    document.getElementById(to_hide_id).style.display='none';
    setTimeout(redirectAfterGet, (1 * 1000));
}
function redirectAfterGet() {
    var req = false;
    // For Safari, Firefox, and other non-MS browsers
    if (window.XMLHttpRequest) {
        try {
            req = new XMLHttpRequest();
        } catch (e) {
            req = false;
        }
    } else if (window.ActiveXObject) {
        // For Internet Explorer on Windows
        try {
            req = new ActiveXObject("Msxml2.XMLHTTP");
        } catch (e) {
            try {
                req = new ActiveXObject("Microsoft.XMLHTTP");
            } catch (e) {
                req = false;
            }
        }
    }
    if (req) {
        // Synchronous request, wait till we have it all
        req.open('HEAD', '/', false);
        req.send(null);
        window.location='/';
    } else {
        //alert('Could not get a XMLHttpRequest Object');
    }
}
